"""Topics (one question + its approved answer, English and French side by side) and sources (what drafts are built from).

Life of a topic:  draft -> in_review (sent to the expert) -> approved   (or -> changes, with the expert's note)
Editing an approved topic's text puts it back to draft: nothing reaches the public agent without approval.
With no expert invited, the owner approves (shown as "approved by the owner, no expert yet").
"""
import anvil.server
from anvil.tables import app_tables
import anvil.tables as tables

from . import common as C
from . import Agents, Audit, Engine

STATUSES = ["draft", "in_review", "approved", "changes"]


def topic_dict(t):
    return {"id": t.get_id(), "question_en": t["question_en"] or "", "question_fr": t["question_fr"] or "",
            "answer_en": t["answer_en"] or "", "answer_fr": t["answer_fr"] or "", "keywords": t["keywords"] or "",
            "status": t["status"] or "draft", "review_note": t["review_note"] or "",
            "approved_by": t["approved_by"] or "", "approved_at": C.iso(t["approved_at"]),
            "used": list(t["used"] or []), "updated": C.iso(t["updated"]),
            "missing_fr": not (t["question_fr"] and t["answer_fr"])}


def _topic(topic_id, need=("owner", "expert")):
    me = C.require_user()
    t = C.row_by_id(app_tables.topics, topic_id)
    if t is None:
        raise anvil.server.PermissionDenied("That topic no longer exists.")
    role = Agents.role_of(t["agent"], me)
    if role not in need:
        raise anvil.server.PermissionDenied("You don't have access to that topic.")
    return t, me, role


def _touch(agent):
    agent["updated"] = C.now()


def actor(me, role, a):
    """How a person appears in the audit trail: name + role."""
    if role == "expert":
        return "%s (expert)" % (a["expert_name"] or C.name_of(me))
    return "%s (%s)" % (C.name_of(me), "owner" if role == "owner" else role or "member")


@anvil.server.callable(require_user=True)
def save_topic(agent_id, topic_id, fields):
    """Create (topic_id None) or update a topic. Changing the words of an approved topic sends it back to draft."""
    if topic_id:
        t, me, role = _topic(topic_id)
        a = t["agent"]
    else:
        a, me, role = Agents.load_agent(agent_id, need=("owner", "expert"))
        t = None
    if not isinstance(fields, dict):
        return C.fail("Nothing to save.")
    f = {k: C.text(fields.get(k), 160 if k.startswith("question") else 1600, multiline=k.startswith("answer"))
         for k in ("question_en", "question_fr", "answer_en", "answer_fr")}
    if len(f["question_en"]) < 4 and len(f["question_fr"]) < 4:
        return C.fail("Write the question people will ask (in English or French).")
    kw = C.text(fields.get("keywords"), 200) or Engine.keywords_for(f["question_en"], f["question_fr"])
    used = [C.text(x, 80) for x in (fields.get("used") or []) if isinstance(x, str)][:6]
    if t is None:
        if len(app_tables.topics.search(agent=a)) >= 200:
            return C.fail("An agent can hold 200 topics. Merge or delete some first.")
        n = len(app_tables.topics.search(agent=a))
        t = app_tables.topics.add_row(agent=a, status="draft", review_note="", approved_by="", position=n,
                                      used=used, updated=C.now(), is_demo=False, keywords=kw, **f)
        Audit.log(a, "created", actor(me, role, a), t)
    else:
        changed = any((t[k] or "") != f[k] for k in f)
        t.update(keywords=kw, updated=C.now(), **f)
        if used:
            t["used"] = used
        if changed and t["status"] == "approved":
            t.update(status="draft", approved_by="", approved_at=None)
            Audit.log(a, "reopened", actor(me, role, a), t, "The approved wording changed, so it needs approval again.")
        elif changed:
            Audit.log(a, "edited", actor(me, role, a), t)
    _touch(a)
    return C.ok(topic=topic_dict(t))


@anvil.server.callable(require_user=True)
def draft_answer(agent_id, question, lang="en"):
    """A first answer from the agent's sources, in the agent's tone (the expert edits and approves it)."""
    a, me, role = Agents.load_agent(agent_id, need=("owner", "expert"))
    question = C.text(question, 160)
    if len(question) < 4:
        return C.fail("Write the question first, then draft its answer.")
    srcs = [{"title": s["title"], "body": s["body"], "lang": s["lang"]} for s in app_tables.sources.search(agent=a)]
    if not srcs:
        return C.fail("Add a source on the Knowledge tab first: drafts are built from your sources.")
    d = Engine.draft(question, srcs, a["tone"] or "warm", "fr" if lang == "fr" else "en")
    return C.ok(text=d["text"], used=d["used"], found=d["found"])


@anvil.server.callable(require_user=True)
def submit_topic(topic_id):
    t, me, role = _topic(topic_id)
    if not (t["answer_en"] or t["answer_fr"]):
        return C.fail("Write or draft an answer before sending it for review.")
    t.update(status="in_review", review_note="", updated=C.now())
    _touch(t["agent"])
    Audit.log(t["agent"], "submitted", actor(me, role, t["agent"]), t)
    return C.ok(topic=topic_dict(t))


@anvil.server.callable(require_user=True)
def review_topic(topic_id, decision, note=""):
    """The expert approves, or asks for changes with a note. With no expert invited, the owner approves."""
    t, me, role = _topic(topic_id)
    a = t["agent"]
    if a["expert_email"] and role != "expert":
        return C.fail("Only %s (the expert) can approve this agent's answers." % (a["expert_name"] or "the expert"))
    if decision == "approve":
        if not (t["answer_en"] and t["answer_fr"]):
            return C.fail("Approve needs both the English and the French answer.")
        who = (a["expert_name"] or C.name_of(me)) if role == "expert" else C.name_of(me) + " (owner, no expert yet)"
        t.update(status="approved", approved_by=who, approved_at=C.now(), review_note="", updated=C.now())
        Audit.log(a, "approved", who, t, "English and French answers approved.")
    elif decision == "changes":
        note = C.text(note, 400, multiline=True)
        if len(note) < 3:
            return C.fail("Say what should change, so the writer knows what to fix.")
        t.update(status="changes", review_note=note, approved_by="", approved_at=None, updated=C.now())
        Audit.log(a, "changes", actor(me, role, a), t, note)
    else:
        return C.fail("Pick approve or ask for changes.")
    _touch(a)
    return C.ok(topic=topic_dict(t))


@anvil.server.callable(require_user=True)
def delete_topic(topic_id):
    t, me, role = _topic(topic_id)
    a = t["agent"]
    Audit.log(a, "deleted", actor(me, role, a), t)
    t.delete()
    _touch(a)
    return C.ok()


@anvil.server.callable(require_user=True)
def review_queue():
    """Topics waiting for me: as the invited expert (in review), or as an owner with no expert (in review)."""
    me = C.require_user()
    email = (me["email"] or "").lower()
    out = []
    for a in app_tables.agents.search():
        mine = a["expert_email"] and a["expert_email"].lower() == email
        owner_no_expert = a["owner"] == me and not a["expert_email"]
        if not (mine or owner_no_expert):
            continue
        for t in app_tables.topics.search(tables.order_by("updated", ascending=False), agent=a, status="in_review"):
            d = topic_dict(t)
            d.update(agent_id=a.get_id(), agent_name=a["name"], face=a["face"] or {})
            out.append(d)
    return {"items": out}


@anvil.server.callable(require_user=True)
def resolve_gap(ask_id):
    me = C.require_user()
    q = C.row_by_id(app_tables.asks, ask_id)
    if q is None:
        return C.ok()
    if Agents.role_of(q["agent"], me) not in ("owner", "expert"):
        raise anvil.server.PermissionDenied("You don't have access to that question.")
    key = " ".join(Engine.words(q["question"]))
    for other in app_tables.asks.search(agent=q["agent"], answered=False, resolved=False):
        if " ".join(Engine.words(other["question"])) == key:  # every time it was asked
            other["resolved"] = True
    return C.ok()


# ---------------------------------------------------------------- sources
@anvil.server.callable(require_user=True)
def add_source(agent_id, title, kind, body):
    a, me, role = Agents.load_agent(agent_id, need=("owner", "expert"))
    title, body = C.text(title, 80), C.text(body, 40000, multiline=True)
    if len(title) < 2:
        return C.fail("Give the source a title (at least 2 characters).")
    if len(body.split()) < 10:
        return C.fail("Paste or upload at least a few sentences: drafts are built from this text.")
    if len(app_tables.sources.search(agent=a)) >= 40:
        return C.fail("An agent can hold 40 sources. Delete one you no longer need first.")
    kind = kind if kind in Agents.KINDS else "notes"
    s = app_tables.sources.add_row(agent=a, title=title, kind=kind, lang=Engine.lang_of(body), body=body,
                                   words=len(body.split()), created=C.now(), is_demo=False)
    _touch(a)
    Audit.log(a, "source_added", actor(me, role, a), detail=title)
    return C.ok(id=s.get_id(), lang=s["lang"], words=s["words"])


@anvil.server.callable(require_user=True)
def delete_source(source_id):
    me = C.require_user()
    s = C.row_by_id(app_tables.sources, source_id)
    if s is None:
        return C.ok()
    role = Agents.role_of(s["agent"], me)
    if role not in ("owner", "expert"):
        raise anvil.server.PermissionDenied("You don't have access to that source.")
    a = s["agent"]
    Audit.log(a, "source_removed", actor(me, role, a), detail=s["title"] or "")
    s.delete()
    _touch(a)
    return C.ok()
