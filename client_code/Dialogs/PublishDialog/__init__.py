import anvil.server
from anvil import *

from ._anvil_designer import PublishDialogTemplate
from ... import state


class PublishDialog(PublishDialogTemplate):
    """Name the new version and publish it. Closes with the new version number, or None."""

    def __init__(self, agent_id, approved, **properties):
        super().__init__(**properties)
        self.agent_id = agent_id
        self.lead.text = ("The %s approved right now become what visitors hear, in English and French. "
                          "Drafts and topics waiting for review stay behind." % state.plural(approved, "topic"))

    @handle("note_box", "pressed_enter")
    def note_box_pressed_enter(self, **event_args):
        self.publish_button_click()

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)

    @handle("publish_button", "click")
    def publish_button_click(self, **event_args):
        self.publish_button.enabled = False
        try:
            r = anvil.server.call("publish", self.agent_id, self.note_box.text or "")
        finally:
            self.publish_button.enabled = True
        if not r.get("ok"):
            self.message.text, self.message.visible = r.get("error"), True
            return
        self.raise_event("x-close-alert", value=r["number"])
