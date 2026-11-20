"""Demo content, so the studio never looks empty: three live Montréal restaurant guides (DemoContent.py) owned by a
demo producer, with their (invented) experts, sources, topics in every state, published versions and a few
unanswered questions. Loaded the first time anyone opens the app (ensure_loaded), removed or reloaded from
Admin -> Demo data. Removing it is remembered: it doesn't come back.

Demo users have is_demo=True and @example.com emails; they can't sign in (no password). Every demo row is flagged
is_demo=True, so remove() deletes exactly what load() added. fill_from_template() also seeds a user's new agent.
"""
import datetime as dt
from typing import Any

from anvil.tables import app_tables

from . import common as C
from . import DemoContent, Engine

PRODUCER = ("Lina Moreau", "lina.demo@example.com")
# Tables that hold demo rows (each has an is_demo column). Children before parents.
DEMO_TABLES = ["asks", "versions", "topics", "sources", "agents"]


def state():
    return C.get_setting("demo", "never")  # "never" | "loaded" | "removed"


def ensure_loaded():
    """Call from the app's main data callables: loads the demo once, unless an admin removed it."""
    if state() == "never":
        load()


def _user(name, email):
    u = app_tables.users.get(email=email) or app_tables.users.add_row(email=email, enabled=False)
    u.update(display_name=name, is_demo=True, signed_up=C.now() - dt.timedelta(days=40))
    return u


def fill_from_template(a, t, as_drafts=False, demo=False):
    """Copy a template's identity, face, sources and topics into agent a. as_drafts: every topic starts as a draft
    (a new owner's expert approves them again)."""
    a.update(tagline_en=t["tagline_en"], tagline_fr=t["tagline_fr"], domain=t["domain"], tone=t["tone"],
             scope_en=t["scope_en"], scope_fr=t["scope_fr"], refuse=list(t["refuse"]), greeting_en=t["greeting_en"],
             greeting_fr=t["greeting_fr"], face=dict(t["face"]))
    for i, (title, kind, body) in enumerate(t["sources"]):
        app_tables.sources.add_row(agent=a, title=title, kind=kind, lang=Engine.lang_of(body), body=body,
                                   words=len(body.split()), created=C.now() - dt.timedelta(days=20 - i), is_demo=demo)
    rows = []
    for i, (q_en, q_fr, a_en, a_fr, kw, status, note) in enumerate(t["topics"]):
        st = "draft" if as_drafts else status
        approved = st == "approved"
        rows.append(app_tables.topics.add_row(
            agent=a, question_en=q_en, question_fr=q_fr, answer_en=a_en, answer_fr=a_fr, keywords=kw, status=st,
            review_note="" if as_drafts else note, approved_by=t["expert"][0] if approved else "",
            approved_at=C.now() - dt.timedelta(days=12 - i) if approved else None,
            used=[t["sources"][0][0]] if a_en else [], position=i, updated=C.now() - dt.timedelta(days=10 - i),
            is_demo=demo))
    return rows


def load():
    remove(remember=False)
    from . import Versions
    owner = _user(*PRODUCER)
    for n, key in enumerate(DemoContent.ORDER):
        t: Any = DemoContent.TEMPLATES[key]
        exp_name, exp_title, exp_email = t["expert"]
        _user(exp_name, exp_email)
        a = app_tables.agents.add_row(owner=owner, slug="demo-" + key, name=t["name"], expert_name=exp_name,
                                      expert_title=exp_title, expert_email=exp_email, status="draft", live_version=0,
                                      template=key, created=C.now() - dt.timedelta(days=30 - n),
                                      updated=C.now() - dt.timedelta(hours=6 * (n + 1)), is_demo=True)
        rows = fill_from_template(a, t, demo=True)
        approved = [r for r in rows if r["status"] == "approved"]
        for vi, (note, k) in enumerate(t["versions"]):
            keep = set(r.get_id() for r in approved[:k])  # each version holds the first k approved topics
            snap = Versions.snapshot(a)
            snap["topics"] = [x for x in snap["topics"] if x["id"] in keep]
            app_tables.versions.add_row(agent=a, number=vi + 1, note=note, snapshot=snap, published_by=PRODUCER[0],
                                        published_at=C.now() - dt.timedelta(days=8 - 3 * vi), is_demo=True)
        a.update(live_version=len(t["versions"]), status="live")
        for gi, q in enumerate(t["gaps"]):
            app_tables.asks.add_row(agent=a, question=q, lang=Engine.lang_of(q), topic_id="", answered=False,
                                    version=a["live_version"], mode="live", resolved=False,
                                    created=C.now() - dt.timedelta(hours=5 + 9 * gi), is_demo=True)
        for gi, r in enumerate(approved[:4]):  # a few answered questions, so "people asked" isn't zero
            for k in range(3 - gi % 3):
                app_tables.asks.add_row(agent=a, question=r["question_en"], lang="en", topic_id=r.get_id(),
                                        answered=True, version=a["live_version"], mode="live", resolved=False,
                                        created=C.now() - dt.timedelta(hours=3 + 7 * k + gi), is_demo=True)
    C.set_setting("demo", "loaded")
    return counts()


def remove(remember=True):
    for name in DEMO_TABLES:
        for r in getattr(app_tables, name).search(is_demo=True):
            r.delete()
    for u in app_tables.users.search(is_demo=True):
        u.delete()
    if remember:
        C.set_setting("demo", "removed")
    return counts()


def counts():
    out = {"users": len(app_tables.users.search(is_demo=True))}
    for name in DEMO_TABLES:
        out[name] = len(getattr(app_tables, name).search(is_demo=True))
    return out
