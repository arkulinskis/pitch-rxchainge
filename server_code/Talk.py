"""Talking to an agent: the public page (#talk/<slug>, anyone), the editor's Try tab (current approved topics, before
publishing) and the landing page's demo face.

Every answer comes from an approved topic. A question nothing fits is logged as a gap the team sees in the editor;
a question touching a refused subject gets a polite "not my place" instead.
"""
import anvil.server
from anvil.tables import app_tables
import anvil.tables as tables

from . import common as C
from . import Agents, DemoData, Engine, Versions

LINES = {
    "en": {"refuse": "That's outside what I'm allowed to talk about ({s}). Please ask the people who can help with it directly.",
           "unknown": "I don't have an approved answer for that yet. I've passed your question on to {e}, so it may be added soon.",
           "unknown_noexp": "I don't have an approved answer for that yet. I've passed your question on to my team.",
           "hello": "Hello! Ask me anything about {d}."},
    "fr": {"refuse": "Ça dépasse ce dont j'ai le droit de parler ({s}). Adressez-vous directement aux personnes qui peuvent vous aider.",
           "unknown": "Je n'ai pas encore de réponse approuvée pour ça. J'ai transmis votre question à {e}, elle pourrait être ajoutée bientôt.",
           "unknown_noexp": "Je n'ai pas encore de réponse approuvée pour ça. J'ai transmis votre question à mon équipe.",
           "hello": "Bonjour! Posez-moi vos questions sur {d}."},
}


def public_view(a, snap):
    tops = snap.get("topics") or []
    return {"slug": a["slug"], "name": snap.get("name") or a["name"], "tagline_en": snap.get("tagline_en") or "",
            "tagline_fr": snap.get("tagline_fr") or "", "greeting_en": snap.get("greeting_en") or "",
            "greeting_fr": snap.get("greeting_fr") or "", "face": snap.get("face") or {},
            "expert_name": snap.get("expert_name") or "", "expert_title": snap.get("expert_title") or "",
            "version": a["live_version"] or 0, "domain": a["domain"] or "",
            "suggest_en": [t["question_en"] for t in tops if t.get("question_en")][:6],
            "suggest_fr": [t["question_fr"] for t in tops if t.get("question_fr")][:6], "topics": len(tops)}


def live_snapshot(a):
    if not a or not a["live_version"]:
        return None
    v = app_tables.versions.get(agent=a, number=a["live_version"])
    return v["snapshot"] if v else None


@anvil.server.callable
def get_public_agent(slug):
    DemoData.ensure_loaded()
    a = app_tables.agents.get(slug=C.text(slug, 60)) if slug else None
    snap = live_snapshot(a)
    if snap is None:
        return C.fail("This agent isn't published, or the link is wrong.")
    return C.ok(agent=public_view(a, snap))


@anvil.server.callable
def get_landing():
    """The landing page's guides: the live demo agents, with a few questions each for the hero face to answer."""
    DemoData.ensure_loaded()
    out = []
    for a in app_tables.agents.search(tables.order_by("created"), is_demo=True):
        snap = live_snapshot(a)
        if not snap:
            continue
        view = public_view(a, snap)
        view["samples"] = [{"q_en": t["question_en"], "a_en": t["answer_en"], "q_fr": t["question_fr"],
                            "a_fr": t["answer_fr"], "by": t.get("approved_by") or ""}
                           for t in (snap.get("topics") or [])[:3]]
        out.append(view)
    return {"guides": out}


def strength(score):
    return "strong" if score >= 0.9 else "good" if score >= 0.6 else "close"


def why(kind, version, expert="", t=None, score=0.0, subject="", words=None):
    """The "Why this answer?" receipt: plain facts the chat shows under a reply (the client words them)."""
    w = {"kind": kind, "version": version, "expert": expert}
    if kind == "answer" and t is not None:
        w.update(question_en=t.get("question_en") or "", question_fr=t.get("question_fr") or "",
                 approved_by=t.get("approved_by") or "", approved_at=t.get("approved_at") or "",
                 used=list(t.get("used") or [])[:6], strength=strength(score), score=round(score, 2),
                 words=list(words or [])[:6])
    elif kind == "refused":
        w["subject"] = subject
    return w


def answer(question, lang, snap, expert, domain, version=0):
    lang = lang if lang in ("en", "fr") else Engine.lang_of(question)
    L = LINES[lang]
    if Engine.is_greeting(question):
        g = snap.get("greeting_" + lang) or L["hello"].format(d=domain or "this")
        return {"text": g, "lang": lang, "kind": "greeting", "topic_id": None, "by": "", "why": None}
    subject = Engine.refused(question, snap.get("refuse"))
    if subject:
        return {"text": L["refuse"].format(s=subject), "lang": lang, "kind": "refused", "topic_id": None, "by": "",
                "why": why("refused", version, expert, subject=subject)}
    t, score = Engine.best_topic(question, snap.get("topics") or [])
    if t is None:
        text = L["unknown"].format(e=expert) if expert else L["unknown_noexp"]
        return {"text": text, "lang": lang, "kind": "unknown", "topic_id": None, "by": "",
                "why": why("unknown", version, expert)}
    text = t.get("answer_" + lang) or t.get("answer_en") or t.get("answer_fr")
    topic_words = set(Engine.tokens(" ".join([t.get("question_en", ""), t.get("question_fr", ""),
                                              t.get("keywords", "")])))
    shared = [w for w in dict.fromkeys(Engine.tokens(question)) if w in topic_words]
    return {"text": text, "lang": lang, "kind": "answer", "topic_id": t.get("id"), "by": t.get("approved_by") or "",
            "question": t.get("question_" + lang) or t.get("question_en"), "score": round(score, 2),
            "why": why("answer", version, expert, t, score, words=shared)}


@anvil.server.callable
def talk_ask(ref, question, lang="", mode="live"):
    """ref = slug (live) or agent id (preview: the editor's Try tab, current approved topics, team only)."""
    question = C.text(question, 300)
    if len(question) < 2:
        return C.fail("Type a question first.")
    if C.rate_limited("talk", 40, 600):
        return C.fail("That's a lot of questions in a few minutes. Take a breather and try again soon.")
    if mode == "preview":
        a, me, role = Agents.load_agent(ref, need=("owner", "expert", "viewer", "admin"))
        snap = Versions.snapshot(a)
        version = 0
    else:
        a = app_tables.agents.get(slug=C.text(ref, 60)) if ref else None
        snap = live_snapshot(a)
        if a is None or snap is None:
            return C.fail("This agent isn't published any more.")
        version = a["live_version"] or 0
    r = answer(question, lang, snap, snap.get("expert_name") or "", a["domain"] or "", version)
    if r["kind"] in ("answer", "unknown") and not (mode == "preview" and a["is_demo"]):
        app_tables.asks.add_row(agent=a, question=question, lang=r["lang"], topic_id=r["topic_id"] or "",
                                answered=r["kind"] == "answer", version=version, mode=mode, resolved=False,
                                created=C.now(), is_demo=bool(a["is_demo"]))
    return C.ok(reply=r)


# ---------------------------------------------------------------- presenter mode (#demo)
GAP_FALLBACKS = ["Where can I get my bicycle repaired?", "Can you recommend a dentist?",
                 "What's the weather like tomorrow?"]


def _pick(cands, snap, kind, lang):
    for q in cands:
        if q and answer(q, lang, snap, "", "")["kind"] == kind:
            return q
    return ""


def demo_script(a, snap):
    """The presenter steps for one live demo guide. Each question is checked against the guide's live version, so
    every step gets the reply it promises (a step whose question can't be found is left out)."""
    tops = snap.get("topics") or []
    expert = snap.get("expert_name") or "the expert"
    name = snap.get("name") or a["name"] or "the guide"
    ok_q = _pick([t.get("question_en") for t in tops], snap, "answer", "en")
    ok_t = next((t for t in tops if t.get("question_en") == ok_q), {})
    fr_q = _pick([t.get("question_fr") for t in tops if t is not ok_t] + [ok_t.get("question_fr")], snap, "answer", "fr")
    refuse = list(snap.get("refuse") or [])
    no_q = _pick(["Can you give me %s?" % r for r in refuse] + ["Can you help with %s?" % r for r in refuse],
                 snap, "refused", "en")
    gaps = [q["question"] for q in app_tables.asks.search(agent=a, answered=False) if (q["lang"] or "en") == "en"]
    gap_q = _pick(gaps[:8] + GAP_FALLBACKS, snap, "unknown", "en")
    steps = [
        {"key": "meet", "title": "Meet %s" % name, "ask": "", "lang": "en", "expect": "greeting",
         "say": "This is %s, a talking guide built in Agent Studio. Everything %s says comes from %s, the expert who "
                "approved every answer. Nothing is improvised." % (name, name, expert),
         "do": "Turn Voice on so the room hears the guide. Point at the face: it blinks, glances and lip-syncs."},
        {"key": "answer", "title": "An approved answer", "ask": ok_q, "lang": "en", "expect": "answer",
         "say": "A real visitor question. The answer is word for word what %s approved, and it says so under the "
                "reply." % expert,
         "do": "Run the step, then press “Why this answer?” under the reply: the matched topic, who approved it "
               "and when, the live version and the sources it was drafted from."},
        {"key": "french", "title": "Same rules in French", "ask": fr_q, "lang": "fr", "expect": "answer",
         "say": "Montréal is bilingual, so every topic has an English and a French answer, and both are approved "
                "before anything goes live.",
         "do": "Run the step: the chat switches to Français and answers from the French side of an approved topic."},
        {"key": "refuse", "title": "It knows where to stop", "ask": no_q, "lang": "en", "expect": "refused",
         "say": "Some subjects are off limits by design (%s). The agent declines politely instead of guessing."
                % (", ".join(refuse) or "none set"),
         "do": "Run the step. In a clinical agent, this is where dosage or diagnosis questions go to people."},
        {"key": "gap", "title": "It admits what it doesn't know", "ask": gap_q, "lang": "en", "expect": "unknown",
         "say": "No approved topic covers this, so the guide says so and passes it to %s. No invented answer." % expert,
         "do": "Run the step. The question lands in the studio's coverage report, grouped with similar ones."},
        {"key": "behind", "title": "Behind the scenes", "ask": "", "lang": "en", "expect": "",
         "say": "Producers build the agent, the expert approves each answer, and the owner publishes numbered "
                "versions with one-click rollback. Every step is in the audit trail.",
         "do": "Sign in, open this guide in the Studio and show the Trust tab (coverage, audit trail, CSV), then "
               "Publish (versions and rollback)."},
    ]
    return [st for st in steps if st["ask"] or st["expect"] in ("", "greeting")]


@anvil.server.callable
def get_demo_script(slug=""):
    """Presenter mode: the live demo guides to choose from, and the chosen one's view + steps. Anyone may call it."""
    DemoData.ensure_loaded()
    guides = []
    for g in app_tables.agents.search(tables.order_by("created"), is_demo=True):
        snap = live_snapshot(g)
        if snap:
            guides.append((g, snap))
    if not guides:
        return C.fail("The demo guides aren't loaded. An admin can load them from Admin, Demo data.")
    slug = C.text(slug, 60)
    a, snap = next(((g, sn) for g, sn in guides if g["slug"] == slug), guides[0])
    return C.ok(slug=a["slug"], agent=public_view(a, snap), steps=demo_script(a, snap),
                guides=[{"slug": g["slug"], "name": sn.get("name") or g["name"], "face": sn.get("face") or {},
                         "on": g["slug"] == a["slug"]} for g, sn in guides])
