from anvil import *
import anvil.server

from ._anvil_designer import KnowledgeTemplate
from ... import state


class Knowledge(KnowledgeTemplate):
    """Knowledge tab: the sources drafts are built from, the scope (EN | FR) and the subjects it refuses."""

    def __init__(self, page, **properties):
        super().__init__(**properties)
        self.page = page
        d = page.data
        a = d["agent"]
        self.can_edit = d["can_edit"]
        self.refuse: list = list(a["refuse"])
        self.scope_en.text, self.scope_fr.text = a["scope_en"], a["scope_fr"]
        state.set_control_attr(self.refuse_box, "aria-label", "New refused subject")
        self.src_panel.items = [dict(s, can_edit=self.can_edit) for s in d["sources"]]
        self.no_sources.visible = not d["sources"]
        self.src_panel.add_event_handler("x-deleted", self._deleted)
        self.refuse_panel.add_event_handler("x-remove", self._remove)
        for c in (self.scope_en, self.scope_fr):
            c.enabled = self.can_edit
        for c in (self.add_button, self.save_button, self.refuse_add):
            c.visible = self.can_edit
        self._draw_refuse()

    def _draw_refuse(self):
        self.refuse_panel.items = [{"text": t, "can_edit": self.can_edit} for t in self.refuse]

    def _remove(self, text, **event_args):
        self.refuse = [t for t in self.refuse if t != text]
        self._draw_refuse()

    @handle("refuse_box", "pressed_enter")
    def refuse_box_pressed_enter(self, **event_args):
        self.refuse_button_click()

    @handle("refuse_button", "click")
    def refuse_button_click(self, **event_args):
        t = (self.refuse_box.text or "").strip()
        if t and t not in self.refuse:
            self.refuse.append(t)
            self._draw_refuse()
        self.refuse_box.text = ""
        state.focus(self.refuse_box)

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        r = state.call("update_agent", self.page.agent_id,
                       {"scope_en": self.scope_en.text, "scope_fr": self.scope_fr.text, "refuse": self.refuse})
        if r:
            state.toast("Saved", "ok")
            self.page.reload()

    @handle("add_button", "click")
    def add_button_click(self, **event_args):
        from ...Dialogs.AddSource import AddSource
        if alert(AddSource(agent_id=self.page.agent_id), buttons=[], role="app-dialog", large=True):
            state.toast("Source added", "ok")
            self.page.reload()

    def _deleted(self, **event_args):
        self.page.reload()
