"""Agents: the studio list, creating (blank or from a template), the editor's data, settings, face, expert, copy, delete.

Who may do what (role_of):
  owner   the producer who made it: everything
  expert  the person invited by email (agents.expert_email): edit, draft and approve topics; can't publish or delete
  viewer  anyone signed in, on a demo agent: look around, make a copy
  admin   like owner for looking (admins can open anything); editing still needs owner or expert
"""
import random
import re
import string

import anvil.server
from anvil.tables import app_tables
import anvil.tables as tables

from . import common as C
from . import DemoContent, DemoData, Engine

TONES = ["warm", "witty", "precise", "calm"]
KINDS = ["guide", "notes", "faq", "leaflet", "review"]


def role_of(agent, me):
    if agent is None or me is None:
        return None
    if agent["owner"] == me:
        return "owner"
    if agent["expert_email"] and (me["email"] or "").lower() == agent["expert_email"].lower():
        return "expert"
    if C.is_admin(me):
        return "admin"
    if agent["is_demo"]:
        return "viewer"
    return None


def can_edit(role):
    return role in ("owner", "expert")


def load_agent(agent_id, need=("owner", "expert", "viewer", "admin")):
    """(agent, me, role) or raises PermissionDenied: the check every agent callable starts with."""
    me = C.require_user()
    agent = C.row_by_id(app_tables.agents, agent_id)
    role = role_of(agent, me)
    if agent is None or role not in need:
        raise anvil.server.PermissionDenied("You don't have access to that agent.")
    return agent, me, role


def new_slug(name):
    base = re.sub(r"[^a-z0-9]+", "-", Engine.strip_accents((name or "agent").lower())).strip("-")[:24] or "agent"
    while True:
        slug = base + "-" + "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4))
        if app_tables.agents.get(slug=slug) is None:
            return slug


def counts(agent):
    tops = app_tables.topics.search(agent=agent)
    st = {"draft": 0, "in_review": 0, "approved": 0, "changes": 0}
    for t in tops:
        st[t["status"] or "draft"] = st.get(t["status"] or "draft", 0) + 1
    st["total"] = len(tops)
    st["sources"] = len(app_tables.sources.search(agent=agent))
    st["gaps"] = len(app_tables.asks.search(agent=agent, answered=False, resolved=False))
    return st


def agent_card(a, me):
    role = role_of(a, me)
    return {"id": a.get_id(), "slug": a["slug"], "name": a["name"] or "Untitled agent", "tagline": a["tagline_en"] or "",
            "domain": a["domain"] or "", "face": a["face"] or {}, "status": a["status"] or "draft",
            "live_version": a["live_version"] or 0, "expert": a["expert_name"] or "", "role": role,
            "demo": bool(a["is_demo"]), "updated": C.iso(a["updated"]), "counts": counts(a)}


def agent_full(a, role):
    return {"id": a.get_id(), "slug": a["slug"], "name": a["name"] or "", "tagline_en": a["tagline_en"] or "",
            "tagline_fr": a["tagline_fr"] or "", "domain": a["domain"] or "", "expert_name": a["expert_name"] or "",
            "expert_title": a["expert_title"] or "", "expert_email": (a["expert_email"] or "") if role == "owner" else "",
            "has_expert": bool(a["expert_email"]), "tone": a["tone"] or "warm", "scope_en": a["scope_en"] or "",
            "scope_fr": a["scope_fr"] or "", "refuse": list(a["refuse"] or []), "greeting_en": a["greeting_en"] or "",
            "greeting_fr": a["greeting_fr"] or "", "face": a["face"] or {}, "status": a["status"] or "draft",
            "live_version": a["live_version"] or 0, "owner": C.name_of(a["owner"]), "demo": bool(a["is_demo"]),
            "updated": C.iso(a["updated"])}


def checklist(a, n):
    steps = [
        ("name", "Name and introduce your agent", bool(a["name"] and a["tagline_en"] and a["greeting_en"])),
        ("face", "Give it a face and a voice", bool(a["face"])),
        ("sources", "Add at least one source", n["sources"] > 0),
        ("expert", "Invite the expert who approves", bool(a["expert_email"])),
        ("topics", "Get three topics approved", n["approved"] >= 3),
        ("publish", "Publish a version", bool(a["live_version"])),
    ]
    return [{"key": k, "label": label, "done": done} for k, label, done in steps]


@anvil.server.callable(require_user=True)
def list_studio():
    """The studio page: my agents, agents I review as the expert, and the demo agents to look around."""
    DemoData.ensure_loaded()
    me = C.require_user()
    email = (me["email"] or "").lower()
    mine, review, demo = [], [], []
    for a in app_tables.agents.search(tables.order_by("updated", ascending=False)):
        if a["owner"] == me:
            mine.append(agent_card(a, me))
        elif a["expert_email"] and a["expert_email"].lower() == email:
            review.append(agent_card(a, me))
        elif a["is_demo"]:
            demo.append(agent_card(a, me))
    return {"mine": mine, "review": review, "demo": demo, "templates": DemoContent.template_list()}


@anvil.server.callable(require_user=True)
def create_agent(template_key="", name=""):
    me = C.require_user()
    if C.rate_limited("create_agent", 12, 3600):
        return C.fail("That's a lot of new agents in an hour. Take a break and try again later.")
    if len(app_tables.agents.search(owner=me)) >= 25:
        return C.fail("You already have 25 agents. Delete one you no longer need first.")
    t = DemoContent.template(template_key) if template_key else None
    name = C.text(name, 40) or (t["name"] if t else "")
    if len(name) < 2:
        return C.fail("Give your agent a name (at least 2 characters).")
    a = app_tables.agents.add_row(owner=me, slug=new_slug(name), name=name, status="draft", live_version=0,
                                  created=C.now(), updated=C.now(), is_demo=False, refuse=[], face=None,
                                  tone="warm", template=template_key or "")
    if t:
        DemoData.fill_from_template(a, t, as_drafts=True)
        a["name"] = name
    return C.ok(id=a.get_id())


@anvil.server.callable(require_user=True)
def copy_agent(agent_id):
    """Make my own copy of a demo agent (topics come back as drafts: my expert approves them again)."""
    src, me, role = load_agent(agent_id)
    if C.rate_limited("create_agent", 12, 3600):
        return C.fail("That's a lot of new agents in an hour. Take a break and try again later.")
    a = app_tables.agents.add_row(owner=me, slug=new_slug(src["name"]), name=(src["name"] or "Agent") + " (my copy)",
                                  tagline_en=src["tagline_en"], tagline_fr=src["tagline_fr"], domain=src["domain"],
                                  tone=src["tone"], scope_en=src["scope_en"], scope_fr=src["scope_fr"],
                                  refuse=list(src["refuse"] or []), greeting_en=src["greeting_en"],
                                  greeting_fr=src["greeting_fr"], face=dict(src["face"] or {}), status="draft",
                                  live_version=0, template="copy", created=C.now(), updated=C.now(), is_demo=False)
    for s in app_tables.sources.search(agent=src):
        app_tables.sources.add_row(agent=a, title=s["title"], kind=s["kind"], lang=s["lang"], body=s["body"],
                                   words=s["words"], created=C.now(), is_demo=False)
    for t in app_tables.topics.search(tables.order_by("position"), agent=src):
        app_tables.topics.add_row(agent=a, question_en=t["question_en"], question_fr=t["question_fr"],
                                  answer_en=t["answer_en"], answer_fr=t["answer_fr"], keywords=t["keywords"],
                                  status="draft", review_note="", approved_by="", used=list(t["used"] or []),
                                  position=t["position"], updated=C.now(), is_demo=False)
    return C.ok(id=a.get_id())


@anvil.server.callable(require_user=True)
def get_agent(agent_id):
    """Everything the editor needs in one call."""
    a, me, role = load_agent(agent_id)
    from . import Topics, Versions
    n = counts(a)
    sources = [{"id": s.get_id(), "title": s["title"], "kind": s["kind"] or "notes", "lang": s["lang"] or "en",
                "words": s["words"] or 0, "preview": (s["body"] or "")[:180], "created": C.iso(s["created"])}
               for s in app_tables.sources.search(tables.order_by("created", ascending=False), agent=a)]
    topics = [Topics.topic_dict(t) for t in app_tables.topics.search(tables.order_by("position"), agent=a)]
    versions = Versions.version_list(a)
    gaps: list = []
    seen: dict = {}
    for q in app_tables.asks.search(tables.order_by("created", ascending=False), agent=a, answered=False, resolved=False):
        key = " ".join(Engine.words(q["question"]))
        if key in seen:  # the same question asked again: one row with a count
            seen[key]["count"] += 1
            continue
        seen[key] = {"id": q.get_id(), "question": q["question"], "lang": q["lang"] or "en", "when": C.iso(q["created"]),
                     "mode": q["mode"] or "live", "count": 1}
        gaps.append(seen[key])
    gaps = gaps[:40]
    asked = len(app_tables.asks.search(agent=a, mode="live"))
    return {"agent": agent_full(a, role), "role": role, "can_edit": can_edit(role), "is_owner": role == "owner",
            "counts": n, "checklist": checklist(a, n), "sources": sources, "topics": topics, "versions": versions,
            "gaps": gaps, "asked": asked, "tones": TONES, "kinds": KINDS}


FIELDS = {"name": 40, "tagline_en": 120, "tagline_fr": 140, "domain": 60, "tone": 12, "scope_en": 600,
          "scope_fr": 700, "greeting_en": 240, "greeting_fr": 280, "expert_title": 80}


@anvil.server.callable(require_user=True)
def update_agent(agent_id, fields):
    a, me, role = load_agent(agent_id, need=("owner", "expert"))
    if not isinstance(fields, dict):
        return C.fail("Nothing to save.")
    changes: dict = {}
    for k, limit in FIELDS.items():
        if k in fields:
            changes[k] = C.text(fields[k], limit, multiline=k.startswith("scope"))
    if "name" in changes and len(changes["name"]) < 2:
        return C.fail("Give your agent a name (at least 2 characters).")
    if "tone" in changes and changes["tone"] not in TONES:
        changes["tone"] = "warm"
    if "refuse" in fields:
        items = fields["refuse"] if isinstance(fields["refuse"], list) else []
        changes["refuse"] = [C.text(x, 60) for x in items if C.text(x, 60)][:20]
    changes["updated"] = C.now()
    a.update(**changes)
    return C.ok(agent=agent_full(a, role))


FACE_KEYS = {"skin", "hair", "hairStyle", "eyes", "brows", "glasses", "accessory", "shirt", "bg"}


@anvil.server.callable(require_user=True)
def set_face(agent_id, face):
    a, me, role = load_agent(agent_id, need=("owner", "expert"))
    if not isinstance(face, dict):
        return C.fail("That face didn't come through. Try again.")
    clean: dict = {k: C.text(v, 20) for k, v in face.items() if k in FACE_KEYS and isinstance(v, str)}
    v = face.get("voice")
    if isinstance(v, dict):
        rate = min(1.4, max(0.7, float(v.get("rate") or 1)))
        pitch = min(1.6, max(0.5, float(v.get("pitch") or 1)))
        clean["voice"] = {"rate": round(rate, 2), "pitch": round(pitch, 2)}
    a.update(face=clean, updated=C.now())
    return C.ok(face=clean)


@anvil.server.callable(require_user=True)
def set_expert(agent_id, name, email, title=""):
    """Invite the expert who approves topics. They sign in (or sign up) with this email to review."""
    a, me, role = load_agent(agent_id, need=("owner",))
    name, email = C.text(name, 60), C.text(email, 120).lower()
    if not email:
        a.update(expert_name="", expert_email="", expert_title="", updated=C.now())
        return C.ok(agent=agent_full(a, role))
    if len(name) < 2:
        return C.fail("Add the expert's name (at least 2 characters).")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", email):
        return C.fail("That email doesn't look right. Check it and try again.")
    a.update(expert_name=name, expert_email=email, expert_title=C.text(title, 80), updated=C.now())
    return C.ok(agent=agent_full(a, role))


@anvil.server.callable(require_user=True)
def delete_agent(agent_id):
    a, me, role = load_agent(agent_id, need=("owner",))
    for table in (app_tables.asks, app_tables.versions, app_tables.topics, app_tables.sources):
        for r in table.search(agent=a):
            r.delete()
    a.delete()
    return C.ok()
