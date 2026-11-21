"""Versions: publishing freezes the approved topics into a numbered snapshot; the public agent always answers from
the live snapshot. Rolling back = making an older snapshot live again (one click, nothing is deleted)."""
import anvil.server
from anvil.tables import app_tables
import anvil.tables as tables

from . import common as C
from . import Agents, Audit


def snapshot(a):
    tops = [{"id": t.get_id(), "question_en": t["question_en"] or "", "question_fr": t["question_fr"] or "",
             "answer_en": t["answer_en"] or "", "answer_fr": t["answer_fr"] or "", "keywords": t["keywords"] or "",
             "approved_by": t["approved_by"] or "", "approved_at": C.iso(t["approved_at"]),
             "used": list(t["used"] or [])}
            for t in app_tables.topics.search(tables.order_by("position"), agent=a, status="approved")]
    return {"name": a["name"] or "", "tagline_en": a["tagline_en"] or "", "tagline_fr": a["tagline_fr"] or "",
            "greeting_en": a["greeting_en"] or "", "greeting_fr": a["greeting_fr"] or "", "face": a["face"] or {},
            "tone": a["tone"] or "warm", "refuse": list(a["refuse"] or []), "expert_name": a["expert_name"] or "",
            "expert_title": a["expert_title"] or "", "topics": tops}


def version_list(a):
    live = a["live_version"] or 0
    return [{"number": v["number"], "note": v["note"] or "", "by": v["published_by"] or "",
             "when": C.iso(v["published_at"]), "topics": len((v["snapshot"] or {}).get("topics") or []),
             "live": v["number"] == live}
            for v in app_tables.versions.search(tables.order_by("number", ascending=False), agent=a)]


@anvil.server.callable(require_user=True)
def publish(agent_id, note=""):
    a, me, role = Agents.load_agent(agent_id, need=("owner",))
    snap = snapshot(a)
    if len(snap["topics"]) < 1:
        return C.fail("Approve at least one topic before publishing: the public agent only says approved answers.")
    if not (a["greeting_en"] and a["name"]):
        return C.fail("Add a name and an English greeting on the Overview tab first.")
    n = max([v["number"] for v in app_tables.versions.search(agent=a)] or [0]) + 1
    app_tables.versions.add_row(agent=a, number=n, note=C.text(note, 140) or "Version %d" % n, snapshot=snap,
                                published_by=C.name_of(me), published_at=C.now(), is_demo=False)
    a.update(live_version=n, status="live", updated=C.now())
    Audit.log(a, "published", C.name_of(me) + " (owner)", detail="%s: %s" % (
        C.text(note, 140) or "Version %d" % n, "%d approved topics" % len(snap["topics"])), version=n)
    return C.ok(number=n, versions=version_list(a), slug=a["slug"])


@anvil.server.callable(require_user=True)
def rollback(agent_id, number):
    a, me, role = Agents.load_agent(agent_id, need=("owner",))
    v = app_tables.versions.get(agent=a, number=number) if isinstance(number, (int, float)) else None
    if v is None:
        return C.fail("That version doesn't exist.")
    a.update(live_version=v["number"], status="live", updated=C.now())
    Audit.log(a, "rollback", C.name_of(me) + " (owner)", detail="Version %d is live again." % v["number"],
              version=v["number"])
    return C.ok(versions=version_list(a))


@anvil.server.callable(require_user=True)
def unpublish(agent_id):
    a, me, role = Agents.load_agent(agent_id, need=("owner",))
    a.update(live_version=0, status="draft", updated=C.now())
    Audit.log(a, "unpublished", C.name_of(me) + " (owner)", detail="The public page stopped answering.")
    return C.ok(versions=version_list(a))
