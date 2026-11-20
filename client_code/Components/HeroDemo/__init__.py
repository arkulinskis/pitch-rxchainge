from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import HeroDemoTemplate
from ... import router, state


class HeroDemo(HeroDemoTemplate):
    """The landing hero: a guide asks herself a sample question, thinks, answers (lip-synced) with the expert's
    approval stamp, then the next one, alternating English and French; after three, the next guide. Visitors can pick
    a guide. Timers stop when the component leaves the screen."""

    def __init__(self, **properties):
        self._guides: list = []
        self._g, self._i, self._lang = 0, 0, "en"
        self._timers: list = []
        self._running = False
        super().__init__(**properties)
        self.guide_panel.add_event_handler("x-guide", self._pick)

    def setup(self, guides):
        self._guides = [g for g in guides if g.get("samples")]
        if not self._guides:
            return
        self._g, self._i, self._lang = 0, 0, "en"
        self._render(animate=False)

    # ---- drawing one moment
    def _render(self, animate=True):
        g = self._guides[self._g]
        s = g["samples"][self._i % len(g["samples"])]
        lang = self._lang
        self.face.face = g["face"]
        self.q_text.text = s["q_" + lang] or s["q_en"]
        self.a_text.text = s["a_" + lang] or s["a_en"]
        self.who.text = g["name"]
        by = s.get("by") or g.get("expert_name") or ""
        anvil.js.get_dom_node(self.stamp_text).textContent = ("Approuvé par " if lang == "fr" else "Approved by ") + by
        self.stamp.visible = bool(by)
        state.set_attr(self.talk_link, "href", router.href("talk", g["slug"]))
        anvil.js.get_dom_node(self.talk_text).textContent = "Talk to %s yourself" % g["name"]
        self.guide_panel.items = [{"i": n, "name": x["name"], "face": x["face"], "on": n == self._g} for n, x in enumerate(self._guides)]
        for box in (self.q_box, self.a_box):
            box.classes["in"] = not animate
        if not animate:
            return
        self._later(lambda: self.q_box.classes.update({"in": True}), 60)
        self._later(lambda: self.face.think(True), 500)
        self._later(self._answer, 1300)

    def _answer(self):
        self.face.think(False)
        self.a_box.classes["in"] = True
        self.face.say(self.a_text.text, self._lang, False)
        dwell = min(9000, 1800 + 62 * len(self.a_text.text or ""))
        self._later(self._next, dwell)

    def _next(self):
        g = self._guides[self._g]
        self._lang = "fr" if self._lang == "en" else "en"
        self._i += 1
        if self._i >= min(3, len(g["samples"])):
            self._i = 0
            self._g = (self._g + 1) % len(self._guides)
        self._render()

    # ---- timers
    def _later(self, fn, ms):
        self._timers.append(window.setTimeout(anvil.js.report_exceptions(fn), ms))

    def _clear(self):
        for t in self._timers:
            window.clearTimeout(t)
        self._timers = []

    @handle("", "show")
    def form_show(self, **event_args):
        if self._guides and not self._running:
            self._running = True
            self._later(self._answer_first, 1400)

    def _answer_first(self):
        self.face.say(self.a_text.text, self._lang, False)
        self._later(self._next, min(9000, 1800 + 62 * len(self.a_text.text or "")))

    @handle("", "hide")
    def form_hide(self, **event_args):
        self._running = False
        self._clear()

    def _pick(self, i, **event_args):
        self._clear()
        self._g, self._i, self._lang = i, 0, "en"
        self._render()
