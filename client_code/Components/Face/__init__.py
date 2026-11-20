from anvil import *
import anvil.js

from ._anvil_designer import FaceTemplate
from ... import face as engine


class Face(FaceTemplate):
    """An agent's face. Still (a picture, for cards) or live (blinks, glances, lip-syncs, speaks). The live engine
    starts when the component is on screen and stops when it leaves, so pages can't leak timers."""

    def __init__(self, **properties):
        self._face, self._live, self._ready = None, False, False
        self._eng = engine.NULL
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _node(self):
        return anvil.js.get_dom_node(self)

    def _draw(self):
        if not self._ready:
            return
        if self._eng:
            self._eng.set(self._face or {})
        else:
            self._node().innerHTML = engine.svg(self._face)

    def _start(self):
        if self._live and not self._eng:
            self._eng = engine.mount(self._node(), self._face)

    @handle("", "show")
    def form_show(self, **event_args):
        self._start()

    @handle("", "hide")
    def form_hide(self, **event_args):
        if self._eng:
            self._eng.destroy()
            self._eng = engine.NULL

    # ---- for pages and other components
    def say(self, text, lang="en", speak=False):
        """Lip-sync (and, with speak=True, read aloud) a line. Returns at once."""
        self._start()
        if self._eng:
            self._eng.say(text or "", lang or "en", bool(speak))

    def think(self, on=True):
        self._start()
        if self._eng:
            self._eng.think(bool(on))

    def stop(self):
        if self._eng:
            self._eng.stop()

    @property
    def face(self):
        return self._face

    @face.setter
    def face(self, value):
        self._face = value
        self._draw()

    @property
    def live(self):
        return self._live

    @live.setter
    def live(self, value):
        self._live = bool(value)
