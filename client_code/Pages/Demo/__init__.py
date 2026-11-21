from anvil import *
import anvil.js
import anvil.server
from anvil.js import window

from ._anvil_designer import DemoTemplate
from ... import router, state

RESULT = {"answer": "Answered from an approved topic", "refused": "Declined: a refused subject",
          "unknown": "No approved answer: logged for the expert", "greeting": "Greeting"}


class Demo(DemoTemplate):
    """#demo/<slug>, presenter mode (anyone): a step card (Say / Do / the scripted question) beside a live chat
    with one of the demo guides. Run this step asks the question in the step's language; Back / Next or the arrow
    keys move along. Steps come from Talk.get_demo_script, checked against the guide's live version."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.slug = args[0] if args else ""
        self.i = 0
        self.steps: list = []
        self.guides: list = []
        self.ran: set = set()
        self._key = None
        state.heading(self.title, 1)
        self.guide_panel.add_event_handler("x-guide", self._pick_guide)
        self.step_panel.add_event_handler("x-step", self._jump)
        self._load()

    def _load(self):
        r = anvil.server.call("get_demo_script", self.slug)
        ok = bool(r.get("ok"))
        self.missing.visible, self.main.visible = not ok, ok
        if not ok:
            self.missing_text.text = r.get("error") or ""
            self.guide_panel.items = []
            return
        self.slug, self.steps, self.guides = r["slug"], r["steps"], r["guides"]
        router.replace("demo", self.slug)
        self.guide_panel.items = [{"i": n, "name": g["name"], "face": g["face"], "on": g["on"]}
                                  for n, g in enumerate(self.guides)]
        self.chat.setup(r["agent"], self.slug, "live", lang="en")
        state.set_attr(self.public_link, "href", router.href("talk", self.slug))
        self.i, self.ran = 0, set()
        self._draw()

    def _draw(self):
        st = self.steps[self.i]
        n = len(self.steps)
        self.progress.text = "Step %d of %d" % (self.i + 1, n)
        self.bar_fill.style["width"] = "%d%%" % round(100 * (self.i + 1) / n)
        self.step_title.text = st["title"]
        state.heading(self.step_title, 2)
        self.say.text, self.do.text = st["say"], st["do"]
        self.q_row.visible = bool(st["ask"])
        self.question.text = ("“%s”" % st["ask"]) if st["ask"] else ""
        self.run_button.visible = bool(st["ask"]) or st["key"] == "meet"
        self.run_button.text = "Voice on" if st["key"] == "meet" else ("Ask again" if self.i in self.ran else "Run this step")
        self.result.visible = False
        self.back_button.enabled = self.i > 0
        self.next_button.enabled = self.i < n - 1
        self.behind_links.visible = st["key"] == "behind"
        self.step_panel.items = [{"n": k, "title": s["title"], "on": k == self.i, "done": k in self.ran}
                                 for k, s in enumerate(self.steps)]

    def _go(self, i):
        self.i = max(0, min(len(self.steps) - 1, i))
        self._draw()

    def _jump(self, n, **event_args):
        self._go(n)

    def _pick_guide(self, i, **event_args):
        if 0 <= i < len(self.guides) and self.guides[i]["slug"] != self.slug:
            self.slug = self.guides[i]["slug"]
            self._load()

    @handle("run_button", "click")
    def run_button_click(self, **event_args):
        st = self.steps[self.i]
        if st["key"] == "meet":
            self.chat.set_voice(True)
            self.ran.add(self.i)
            self._draw()
            return
        self.chat.ask(st["ask"], st["lang"])
        self.ran.add(self.i)
        self._draw()

    @handle("chat", "asked")
    def chat_asked(self, reply, **event_args):
        st = self.steps[self.i]
        kind = reply.get("kind")
        text = RESULT.get(kind, "")
        if st.get("expect") and kind != st["expect"]:
            text += " (the script expected: %s)" % RESULT.get(st["expect"], st["expect"]).lower()
        self.result.text = text
        self.result.visible = bool(text)
        self.result.role = ["dm-result", "ok" if kind == st.get("expect") else "off"]

    @handle("back_button", "click")
    def back_button_click(self, **event_args):
        self._go(self.i - 1)

    @handle("next_button", "click")
    def next_button_click(self, **event_args):
        self._go(self.i + 1)

    # ---- arrow keys move between steps (not while typing in the question box)
    def _on_key(self, event):
        tag = str(getattr(event.target, "tagName", "") or "").lower()
        if tag in ("input", "textarea", "select") or event.altKey or event.ctrlKey or event.metaKey:
            return
        if event.key == "ArrowRight":
            self._go(self.i + 1)
        elif event.key == "ArrowLeft":
            self._go(self.i - 1)

    @handle("", "show")
    def form_show(self, **event_args):
        if self._key is None:
            self._key = anvil.js.report_exceptions(self._on_key)
            window.document.addEventListener("keydown", self._key)

    @handle("", "hide")
    def form_hide(self, **event_args):
        if self._key is not None:
            window.document.removeEventListener("keydown", self._key)
            self._key = None
