import anvil.server
from anvil import *

from ._anvil_designer import ReviewRowTemplate
from ... import router, state


class ReviewRow(ReviewRowTemplate):
    """A topic waiting for approval on the Review page. item = topic_dict() + agent_id, agent_name, face."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        self.face.face = it["face"]
        self.agent_name.text = it["agent_name"]
        state.set_attr(self.agent_link, "href", router.href("agent", it["agent_id"], "topics"))
        self.when.text = "sent " + state.ago(it["updated"])
        self.note_box.visible = False

    def _decide(self, decision, note=""):
        r = anvil.server.call("review_topic", self.item["id"], decision, note)
        if not r.get("ok"):
            self.message.text, self.message.visible = r.get("error"), True
            return
        state.toast("Approved" if decision == "approve" else "Note sent", "ok")
        self.parent.raise_event("x-done")

    @handle("approve_button", "click")
    def approve_button_click(self, **event_args):
        self._decide("approve")

    @handle("changes_button", "click")
    def changes_button_click(self, **event_args):
        if not self.note_box.visible:
            self.note_box.visible = True
            self.changes_button.text = "Send the note"
            state.focus(self.note)
            return
        self._decide("changes", self.note.text or "")
