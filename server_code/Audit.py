"""Trust: the approval audit trail (who did what to which answer, and when) and the coverage report (how much of
what people ask the agent can answer, and which themes it can't).

    log(agent, action, actor, topic=None, detail="", version=None)   one event; never breaks the action it records
    get_trust(agent_id)       the Trust tab: coverage + the audit trail (owner, expert, demo viewer, admin)
    topic_history(topic_id)   one topic's events, for the topic editor
    resolve_gaps(agent_id, ids)  close every question in a coverage cluster (after writing a topic for it)

The audit table is new (2026-11-20): until the user accepts the Schema Mismatch, log() quietly skips and the Trust tab
says the trail starts once the table exists.
"""
import re
from typing import Any

import anvil.server
from anvil.tables import app_tables
import anvil.tables as tables

from . import common as C
from . import Agents, Engine

ACTIONS = {
    "agent_created": "Agent created", "created": "Topic created", "edited": "Topic edited", "reopened": "Approved topic edited: back to draft",
    "submitted": "Sent to the expert", "approved": "Approved", "changes": "Changes asked", "deleted": "Topic deleted",
    "published": "Version published", "rollback": "Older version made live", "unpublished": "Taken offline",
    "expert": "Expert changed", "source_added": "Source added", "source_removed": "Source removed",
}
KINDS = {"review": ("submitted", "approved", "changes", "reopened"),
         "content": ("agent_created", "created", "edited", "deleted", "source_added", "source_removed"),
         "publish": ("published", "rollback", "unpublished", "expert")}


def _table():
    return getattr(app_tables, "audit", None)


def topic_label(t):
    if t is None:
        return ""
    try:
        return (t["question_en"] or t["question_fr"] or "")[:160]
    except Exception:
        return ""


def log(agent, action, actor, topic=None, detail="", version=None, when=None, demo=None):
    """Record one event. Any problem (table not accepted yet) is swallowed: the trail must never block the work."""
    tb = _table()
    if tb is None or agent is None:
        return
    try:
        tb.add_row(agent=agent, topic_id=topic.get_id() if topic is not None else "", topic=topic_label(topic),
                   action=action, actor=C.text(actor, 80) if isinstance(actor, str) else C.name_of(actor),
                   detail=C.text(detail, 400, multiline=True), version=version, when=when or C.now(),
                   is_demo=bool(agent["is_demo"]) if demo is None else bool(demo))
    except Exception as e:  # noqa: BLE001  the audit row is a record, not a gate
        print("audit log skipped: %s" % e)


def event_dict(r):
    a = r["action"] or ""
    return {"id": r.get_id(), "action": a, "label": ACTIONS.get(a, a.replace("_", " ").capitalize()),
            "kind": next((k for k, acts in KINDS.items() if a in acts), "content"), "topic": r["topic"] or "",
            "topic_id": r["topic_id"] or "", "actor": r["actor"] or "", "detail": r["detail"] or "",
            "version": r["version"] or 0, "when": C.iso(r["when"])}


def events_for(agent, limit=300):
    tb = _table()
    if tb is None:
        return None
    try:
        rows = tb.search(tables.order_by("when", ascending=False), agent=agent)
        return [event_dict(r) for r in rows[:limit]]
    except Exception:
        return None


# ---------------------------------------------------------------- coverage
def _group(toks) -> Any:
    return {"tokens": set(toks), "words": {}, "questions": [], "ids": [], "langs": set()}


def _clusters(asks):
    """Group unanswered questions that share words (greedy, by overlap of their tokens). Most-asked first."""
    groups: list[Any] = []
    for q in asks:
        toks = set(Engine.tokens(q["question"]))
        best: Any = None
        best_s = 0.0
        for g in groups:
            inter = len(toks & g["tokens"])
            s = inter / max(1, min(len(toks), len(g["tokens"])))
            if inter and s >= 0.5 and s > best_s:
                best, best_s = g, s
        if best is None:
            best = _group(toks)
            groups.append(best)
        for w in set(re.findall(r"\w+", (q["question"] or "").lower())):  # theme words keep their accents
            if Engine.strip_accents(w) not in Engine.STOP and len(w) > 2:
                best["words"][w] = best["words"].get(w, 0) + 1
        if q["question"] not in best["questions"]:
            best["questions"].append(q["question"])
        best["ids"].append(q.get_id())
        best["langs"].add(q["lang"] or "en")
    out = []
    for g in groups:
        words = sorted(g["words"].items(), key=lambda kv: (-kv[1], kv[0]))
        theme = ", ".join(w for w, n in words[:3]) or "other"
        out.append({"theme": theme, "count": len(g["ids"]), "questions": g["questions"][:4], "ids": g["ids"][:60],
                    "example": g["questions"][0] if g["questions"] else "", "langs": sorted(g["langs"])})
    out.sort(key=lambda c: (-c["count"], c["theme"]))
    return out[:12]


def coverage(a):
    live = list(app_tables.asks.search(agent=a, mode="live"))
    asked = len(live)
    unanswered = [q for q in live if not q["answered"]]
    rate = round(100 * (asked - len(unanswered)) / asked) if asked else 0
    miss = 100 - rate if asked else 0
    verdict = ("none" if not asked else "good" if miss < 10 else "ok" if miss <= 20 else "gaps")
    by_lang = {"en": {"asked": 0, "missed": 0}, "fr": {"asked": 0, "missed": 0}}
    for q in live:
        L = by_lang.get(q["lang"] or "en", by_lang["en"])
        L["asked"] += 1
        L["missed"] += 0 if q["answered"] else 1
    open_gaps = sorted([q for q in app_tables.asks.search(agent=a, answered=False, resolved=False)],
                       key=lambda q: q["created"] or C.now(), reverse=True)
    topics = list(app_tables.topics.search(agent=a))
    approved = [t for t in topics if t["status"] == "approved"]
    live_ids: set = set()
    if a["live_version"]:
        v = app_tables.versions.get(agent=a, number=a["live_version"])
        live_ids = set(x.get("id") for x in ((v["snapshot"] or {}).get("topics") or [])) if v else set()
    return {"asked": asked, "answered": asked - len(unanswered), "rate": rate, "missed": miss, "verdict": verdict,
            "by_lang": by_lang, "open": len(open_gaps), "clusters": _clusters(open_gaps),
            "topics": len(topics), "approved": len(approved),
            "missing_fr": len([t for t in topics if not (t["question_fr"] and t["answer_fr"])]),
            "unpublished": len([t for t in approved if t.get_id() not in live_ids]),
            "waiting": len([t for t in topics if t["status"] == "in_review"])}


@anvil.server.callable(require_user=True)
def get_trust(agent_id):
    a, me, role = Agents.load_agent(agent_id)
    ev = events_for(a)
    return {"coverage": coverage(a), "events": ev or [], "trail_ready": ev is not None,
            "can_edit": Agents.can_edit(role), "name": a["name"] or "Agent"}


@anvil.server.callable(require_user=True)
def topic_history(topic_id):
    me = C.require_user()
    t = C.row_by_id(app_tables.topics, topic_id)
    if t is None:
        return {"events": []}
    if Agents.role_of(t["agent"], me) not in ("owner", "expert", "viewer", "admin"):
        raise anvil.server.PermissionDenied("You don't have access to that topic.")
    tb = _table()
    if tb is None:
        return {"events": []}
    try:
        rows = tb.search(tables.order_by("when", ascending=False), agent=t["agent"], topic_id=topic_id)
        return {"events": [event_dict(r) for r in rows[:40]]}
    except Exception:
        return {"events": []}


@anvil.server.callable(require_user=True)
def resolve_gaps(agent_id, ids):
    a, me, role = Agents.load_agent(agent_id, need=("owner", "expert"))
    n = 0
    for i in (ids if isinstance(ids, list) else [])[:100]:
        q = C.row_by_id(app_tables.asks, i) if isinstance(i, str) else None
        if q is not None and q["agent"] == a and not q["resolved"]:
            q["resolved"] = True
            n += 1
    return C.ok(resolved=n)
