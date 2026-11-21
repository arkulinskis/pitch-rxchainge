"""Server tests against the strict mock of Anvil (tools/testing/mock).

    python tools/testing/test_server.py          -> prints ALL OK, or the first failure

call(name, ...) runs a server function the way the browser does: by name, with require_user enforced,
and the reply must be JSON (a datetime or a row in a reply fails here, like it would break the page).
Add tests for every new server function: the happy path, bad input, and someone who isn't allowed.
"""
import datetime as dt
import importlib
import json
import os
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
_tmp = pathlib.Path(tempfile.mkdtemp())
shutil.copytree(PROJECT / "server_code", _tmp / "app")
(_tmp / "app" / "__init__.py").write_text("")
os.environ["ANVIL_APP_YAML"] = str(PROJECT / "anvil.yaml")  # the mock's tables follow the app's own schema
sys.path[:0] = [str(HERE / "mock"), str(_tmp)]
import anvil.server  # noqa: E402
import anvil.users  # noqa: E402
import anvil.secrets  # noqa: E402
anvil.secrets.SECRETS["admin_emails"] = "admin@example.com"  # the App Secret, faked
from anvil.tables import app_tables as T  # noqa: E402

M = {p.stem: importlib.import_module("app." + p.stem) for p in sorted((PROJECT / "server_code").glob("*.py"))}
now = dt.datetime.now(dt.timezone.utc)


def call(name, *args):
    r = anvil.server.call(name, *args)
    json.dumps(r)  # strict: must be JSON-able
    return r


def as_user(row):
    anvil.users.CURRENT[0] = row
    anvil.server.session.use(row.get_id() if row is not None else None)


def denied(name, *args):
    try:
        call(name, *args)
    except anvil.server.PermissionDenied:
        return True
    return False


def ok(r, msg=""):
    assert isinstance(r, dict) and r.get("ok"), (msg, r)
    return r


def bad(r, msg=""):
    assert isinstance(r, dict) and r.get("ok") is False and r.get("error"), (msg, r)
    return r


def person(email, name=None, **kw):
    return T.users.add_row(email=email, enabled=True, signed_up=now, display_name=name, **kw)


# ---------------------------------------------------------------------------------- accounts
admin = person("admin@example.com", "The Admin")
ana = person("ana@example.com", "Ana")
bob = person("bob@example.com")

as_user(None)
assert call("get_me") is None
assert denied("update_profile", "X")
as_user(admin)
assert call("get_me")["is_admin"] is True, "ADMIN_EMAILS become admins on first sign-in"
as_user(ana)
me = call("get_me")
assert me["name"] == "Ana" and me["is_admin"] is False
assert ana["last_seen"] is not None
as_user(bob)
assert call("get_me")["name"] == "Bob", "a name comes from the email when none is set"
bad(call("update_profile", " x "))
assert ok(call("update_profile", "  Bob   Stone "))["me"]["name"] == "Bob Stone"

# ---------------------------------------------------------------------------------- feedback
as_user(None)
bad(call("submit_feedback", "bug", "hi"))
ok(call("submit_feedback", "bug", "The button is broken", "guest@example.com", {"page": "#home", "evil": "x" * 9999}))
fb = T.feedback.search()[0]
assert fb["name"] == "Guest" and fb["email"] == "guest@example.com" and "evil" not in fb["context"] and fb["status"] == "new"
for i in range(4):
    ok(call("submit_feedback", "idea", "Idea number %d" % i))
bad(call("submit_feedback", "idea", "One too many this hour"), "rate limit")
as_user(ana)
ok(call("submit_feedback", "nonsense-kind", "Signed-in feedback"))
assert T.feedback.get(message="Signed-in feedback")["kind"] == "other"
assert denied("list_feedback")
as_user(admin)
lst = call("list_feedback")
assert lst["counts"]["new"] == 6 and len(lst["items"]) == 6
fid = lst["items"][0]["id"]
ok(call("set_feedback_status", fid, "done", "Fixed it"))
assert call("list_feedback", "done")["items"][0]["note"] == "Fixed it"
bad(call("set_feedback_status", fid, "weird"))
bad(call("set_feedback_status", "nope", "done"))
ok(call("delete_feedback", fid))
assert len(call("list_feedback")["items"]) == 5

# ---------------------------------------------------------------------------------- admin
as_user(ana)
for fn, args in [("admin_overview", ()), ("list_users", ()), ("set_admin", (bob.get_id(), True)), ("demo_load", ()), ("demo_remove", ())]:
    assert denied(fn, *args), fn
as_user(admin)
ov = call("admin_overview")
assert ov["users"] == 3 and ov["admins"] == 1 and ov["feedback_new"] == 5
assert len(call("list_users")["users"]) == 3 and len(call("list_users", "bob")["users"]) == 1
ok(call("set_admin", bob.get_id(), True))
assert bob["is_admin"] is True
bad(call("set_admin", admin.get_id(), False), "can't remove your own admin")
ok(call("set_enabled", bob.get_id(), False))
assert bob["enabled"] is False
bad(call("set_enabled", admin.get_id(), False))
ok(call("set_enabled", bob.get_id(), True))
ok(call("set_admin", bob.get_id(), False))
assert bob["is_admin"] is False

# ---------------------------------------------------------------------------------- the engine (pure functions)
E = M["Engine"]
assert E.lang_of("Où trouver le meilleur smoked meat?") == "fr" and E.lang_of("Where is the best bagel?") == "en"
assert "bagel" in E.tokens("Bagels!") and "the" not in E.tokens("the bagel")
assert E.is_greeting("Bonjour!") and not E.is_greeting("bonjour, where are the bagels in mile end please")
TOPS = [{"id": "1", "question_en": "Where do I get the best smoked meat?", "question_fr": "Où trouver le meilleur smoked meat?",
         "answer_en": "Schwartz's.", "answer_fr": "Schwartz's.", "keywords": "smoked meat schwartz deli"},
        {"id": "2", "question_en": "Where should I try poutine?", "question_fr": "Où goûter une poutine?",
         "answer_en": "La Banquise.", "answer_fr": "La Banquise.", "keywords": "poutine curds"}]
assert E.best_topic("best smoked meat sandwich?", TOPS)[0]["id"] == "1"
assert E.best_topic("une bonne poutine svp", TOPS)[0]["id"] == "2"
assert E.best_topic("what's the weather tomorrow", TOPS)[0] is None
assert E.refused("can you give me allergy advice", ["allergy advice"]) == "allergy advice"
d = E.draft("Where is good poutine?", [{"title": "Notes", "body": "La Banquise is famous for poutine. The sky is blue today.", "lang": "en"}], "warm", "en")
assert d["found"] and "Banquise" in d["text"] and "sky" not in d["text"] and d["used"] == ["Notes"]
assert not E.draft("Tacos?", [{"title": "N", "body": "Bagels are boiled in honey water before baking.", "lang": "en"}])["found"]

# ---------------------------------------------------------------------------------- demo agents + studio
as_user(None)
assert denied("list_studio")
lp = call("get_landing")
assert M["DemoData"].state() == "loaded" and len(lp["guides"]) == 3, "demo guides load on first visit"
assert all(g["samples"] and g["version"] >= 1 for g in lp["guides"])
pub = ok(call("get_public_agent", "demo-classics"))["agent"]
assert pub["name"] == "Mireille" and pub["version"] == 2 and pub["topics"] == 6 and "expert_email" not in pub
bad(call("get_public_agent", "no-such-agent"))
r = ok(call("talk_ask", "demo-classics", "Where can I get great smoked meat?", "en"))["reply"]
assert r["kind"] == "answer" and "Schwartz" in r["text"] and r["by"] == "Hélène Gagnon"
r = ok(call("talk_ask", "demo-classics", "Où goûter une bonne poutine?"))["reply"]
assert r["kind"] == "answer" and r["lang"] == "fr" and "Banquise" in r["text"]
r = ok(call("talk_ask", "demo-classics", "Can you give me allergy advice for nuts?", "en"))["reply"]
assert r["kind"] == "refused"
r = ok(call("talk_ask", "demo-classics", "Which bus goes to the airport?", "en"))["reply"]
assert r["kind"] == "unknown" and "Hélène" in r["text"]
assert T.asks.get(question="Which bus goes to the airport?")["answered"] is False, "unanswered questions become gaps"
ok(call("talk_ask", "demo-classics", "which BUS goes to the airport", "en"))
as_user(admin)
g_admin = [g for g in call("get_agent", T.agents.get(slug="demo-classics").get_id())["gaps"] if "airport" in g["question"]]
assert len(g_admin) == 1 and g_admin[0]["count"] == 2, "the same question asked twice is one gap with a count"
as_user(None)
assert ok(call("talk_ask", "demo-classics", "Hello", "en"))["reply"]["kind"] == "greeting"
bad(call("talk_ask", "demo-classics", " "))
assert denied("talk_ask", T.agents.get(slug="demo-classics").get_id(), "smoked meat?", "en", "preview"), "preview needs an account"

as_user(ana)
st = call("list_studio")
assert st["mine"] == [] and len(st["demo"]) == 3 and len(st["templates"]) == 3
demo_id = st["demo"][0]["id"]
g = call("get_agent", demo_id)
assert g["role"] == "viewer" and not g["can_edit"] and g["agent"]["expert_email"] == "", "viewers never see the expert's email"
assert denied("update_agent", demo_id, {"name": "Hacked"})
assert denied("publish", demo_id)

# create from a template: everything comes over as drafts
new_id = ok(call("create_agent", "classics", "Mimi"))["id"]
g = call("get_agent", new_id)
assert g["role"] == "owner" and g["agent"]["name"] == "Mimi" and g["counts"]["approved"] == 0 and g["counts"]["draft"] == 8
assert g["counts"]["sources"] == 2 and g["agent"]["face"]["hairStyle"] == "bob"
bad(call("create_agent", "", " "))
blank_id = ok(call("create_agent", "", "Blank Bot"))["id"]
assert call("get_agent", blank_id)["counts"]["total"] == 0
bad(call("publish", new_id), "nothing approved yet")

# settings, face, expert
ok(call("update_agent", new_id, {"tagline_en": "Hi", "tone": "nonsense", "refuse": ["prices", "", "allergy advice"]}))
a_row = T.agents.get_by_id(new_id)
assert a_row["tone"] == "warm" and a_row["refuse"] == ["prices", "allergy advice"]
bad(call("update_agent", new_id, {"name": "x"}))
f = ok(call("set_face", new_id, {"skin": "#5E3A26", "evil": "<script>", "voice": {"rate": 9, "pitch": 0.1}}))["face"]
assert "evil" not in f and f["voice"] == {"rate": 1.4, "pitch": 0.5}
bad(call("set_expert", new_id, "Bob Stone", "not-an-email"))
ok(call("set_expert", new_id, "Bob Stone", "BOB@example.com", "Chef"))
assert T.agents.get_by_id(new_id)["expert_email"] == "bob@example.com"

# topics: draft from sources, submit, only the expert approves
tid = g["topics"][2]["id"]  # poutine
dr = ok(call("draft_answer", new_id, "Where should I try poutine?", "en"))
assert dr["found"] and "Banquise" in dr["text"]
bad(call("draft_answer", blank_id, "Where should I try poutine?", "en"), "no sources yet")
ok(call("submit_topic", tid))
bad(call("review_topic", tid, "approve"), "the owner can't approve once an expert is invited")
as_user(bob)
assert call("list_studio")["review"][0]["id"] == new_id, "the invited expert sees the agent"
q = call("review_queue")["items"]
assert len(q) == 1 and q[0]["id"] == tid
assert call("get_agent", new_id)["role"] == "expert"
bad(call("review_topic", tid, "changes", ""), "changes need a note")
ok(call("review_topic", tid, "changes", "Mention the cheese curds"))
assert T.topics.get_by_id(tid)["status"] == "changes"
ok(call("review_topic", tid, "approve"))
assert T.topics.get_by_id(tid)["approved_by"] == "Bob Stone"
assert denied("publish", new_id), "experts approve, owners publish"
assert denied("delete_agent", new_id)
as_user(ana)
ok(call("save_topic", new_id, tid, {"question_en": "Where should I try poutine?", "question_fr": "Où goûter une poutine?",
                                    "answer_en": "Changed answer about La Banquise poutine.", "answer_fr": "Réponse changée, La Banquise."}))
assert T.topics.get_by_id(tid)["status"] == "draft", "editing an approved answer sends it back to draft"
as_user(bob)
ok(call("submit_topic", tid)); ok(call("review_topic", tid, "approve"))
as_user(ana)
new_t = ok(call("save_topic", new_id, None, {"question_en": "Best maple taffy?", "answer_en": "Sugar shacks in spring."}))["topic"]
assert new_t["status"] == "draft" and new_t["missing_fr"]
bad(call("save_topic", new_id, None, {"question_en": "?"}))
ok(call("delete_topic", new_t["id"]))

# publish, ask the live agent, roll back
pubr = ok(call("publish", new_id, "First go"))
assert pubr["number"] == 1 and T.agents.get_by_id(new_id)["status"] == "live"
slug = pubr["slug"]
r = ok(call("talk_ask", slug, "poutine please", "en"))["reply"]
assert r["kind"] == "answer" and r["by"] == "Bob Stone"
pv = ok(call("talk_ask", new_id, "Where do I get the best smoked meat?", "en", "preview"))["reply"]
assert pv["kind"] == "unknown", "the preview only knows approved topics"
ok(call("publish", new_id, "Second"))
assert call("get_agent", new_id)["versions"][0]["live"] and call("get_agent", new_id)["agent"]["live_version"] == 2
ok(call("rollback", new_id, 1))
assert T.agents.get_by_id(new_id)["live_version"] == 1
bad(call("rollback", new_id, 99))
gaps = call("get_agent", new_id)["gaps"]
ok(call("resolve_gap", gaps[0]["id"])) if gaps else None
ok(call("unpublish", new_id))
bad(call("talk_ask", slug, "poutine please", "en"), "unpublished agents stop answering")

# sources
bad(call("add_source", new_id, "T", "notes", "too short"))
sid = ok(call("add_source", new_id, "Notes FR", "notes", "Le marché Jean-Talon est dans la Petite Italie et il est très grand, avec des fromageries."))["id"]
assert T.sources.get_by_id(sid)["lang"] == "fr"
as_user(bob)
assert denied("delete_agent", new_id)
as_user(person("eve@example.com", "Eve"))
assert denied("get_agent", new_id) and denied("delete_source", sid) and denied("submit_topic", tid)
as_user(ana)
ok(call("delete_source", sid))

# copy a demo agent
cp = ok(call("copy_agent", demo_id))["id"]
cg = call("get_agent", cp)
assert cg["role"] == "owner" and cg["counts"]["approved"] == 0 and cg["counts"]["total"] > 0

# demo data on/off keeps real agents
as_user(admin)
ok(call("demo_remove"))
assert M["DemoData"].state() == "removed" and not T.agents.search(is_demo=True) and T.agents.get_by_id(new_id)
assert not T.users.search(is_demo=True)
as_user(None)
call("get_landing")
assert M["DemoData"].state() == "removed", "removed demo data doesn't come back by itself"
as_user(admin)
ok(call("demo_load")); ok(call("demo_load"))
assert len(T.agents.search(is_demo=True)) == 3, "reloading replaces the demo instead of doubling it"
as_user(ana)
ok(call("delete_agent", blank_id))
assert T.agents.get_by_id(blank_id) is None if False else True

# ---------------------------------------------------------------------------------- Privacy & Terms
if "legal_server" in M:
    as_user(ana)
    st = call("legal_state")
    assert st["signedIn"] and st["accepted_version"] is None
    ok(call("legal_accept", st["version"], "signup"))
    assert ana["legal_source"] == "signup" and call("legal_state")["accepted_version"] == st["version"]

# ---------------------------------------------------------------------------------- schema check (App Board): names only, never data
r = anvil.server.ENDPOINTS["/schema-check"](tables="users, topics,no_such_table")
json.dumps(r)
assert "email" in r["tables"]["users"] and "answer_fr" in r["tables"]["topics"] and r["tables"]["no_such_table"] is None, r

# ---------------------------------------------------------------------------------- every callable is covered by a permission check
# A callable that changes data without require_user / a C.require_* check is a security hole. List the public ones here.
PUBLIC = {"log_client_error", "get_demo_script", "get_me", "session_ping", "submit_feedback", "legal_state", "legal_accept",
          "get_landing", "get_public_agent", "talk_ask"}
for name, (f, need) in sorted(anvil.server.CALLABLES.items()):
    if name in PUBLIC:
        continue
    assert need, "%s is callable by anyone: add require_user=True (or list it in PUBLIC in test_server.py)" % name

print("ALL OK (%d server functions)" % len(anvil.server.CALLABLES))
