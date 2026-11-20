import anvil.server
from anvil import *

from ._anvil_designer import AddSourceTemplate
from ... import state

KINDS = [("Notes", "notes"), ("Guide", "guide"), ("FAQ", "faq"), ("Leaflet", "leaflet"), ("Review", "review")]


class AddSource(AddSourceTemplate):
    """Paste or upload a source. Closes with True when one was added."""

    def __init__(self, agent_id, **properties):
        super().__init__(**properties)
        self.agent_id = agent_id
        self.kind_dd.items = KINDS
        self.kind_dd.selected_value = "notes"
        state.set_control_attr(self.kind_dd, "aria-label", "Kind of source")
        self._count()

    def _count(self):
        n = len((self.body_box.text or "").split())
        self.count_label.text = state.plural(n, "word")

    @handle("body_box", "change")
    def body_box_change(self, **event_args):
        self._count()

    @handle("file_loader", "change")
    def file_loader_change(self, file, **event_args):
        if file is None:
            return
        try:
            text = file.get_bytes().decode("utf-8")
        except Exception:
            self.message.text, self.message.visible = "That file isn't plain text. Save it as .txt and try again.", True
            return
        self.body_box.text = text[:40000]
        if not (self.title_box.text or "").strip():
            self.title_box.text = (file.name or "Source").rsplit(".", 1)[0][:80]
        self.message.visible = False
        self._count()

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=False)

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        self.save_button.enabled = False
        try:
            r = anvil.server.call("add_source", self.agent_id, self.title_box.text, self.kind_dd.selected_value,
                                  self.body_box.text)
        finally:
            self.save_button.enabled = True
        if not r.get("ok"):
            self.message.text, self.message.visible = r.get("error"), True
            return
        self.raise_event("x-close-alert", value=True)
