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


def answer(question, lang, snap, expert, domain):
    lang = lang if lang in ("en", "fr") else Engine.lang_of(question)
    L = LINES[lang]
    if Engine.is_greeting(question):
        g = snap.get("greeting_" + lang) or L["hello"].format(d=domain or "this")
        return {"text": g, "lang": lang, "kind": "greeting", "topic_id": None, "by": ""}
    subject = Engine.refused(question, snap.get("refuse"))
    if subject:
        return {"text": L["refuse"].format(s=subject), "lang": lang, "kind": "refused", "topic_id": None, "by": ""}
    t, score = Engine.best_topic(question, snap.get("topics") or [])
    if t is None:
        text = L["unknown"].format(e=expert) if expert else L["unknown_noexp"]
        return {"text": text, "lang": lang, "kind": "unknown", "topic_id": None, "by": ""}
    text = t.get("answer_" + lang) or t.get("answer_en") or t.get("answer_fr")
    return {"text": text, "lang": lang, "kind": "answer", "topic_id": t.get("id"), "by": t.get("approved_by") or "",
            "question": t.get("question_" + lang) or t.get("question_en"), "score": round(score, 2)}


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
    r = answer(question, lang, snap, snap.get("expert_name") or "", a["domain"] or "")
    if r["kind"] in ("answer", "unknown") and not (mode == "preview" and a["is_demo"]):
        app_tables.asks.add_row(agent=a, question=question, lang=r["lang"], topic_id=r["topic_id"] or "",
                                answered=r["kind"] == "answer", version=version, mode=mode, resolved=False,
                                created=C.now(), is_demo=bool(a["is_demo"]))
    return C.ok(reply=r)
