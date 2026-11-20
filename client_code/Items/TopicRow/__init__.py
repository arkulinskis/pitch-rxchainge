from anvil import *
import anvil.js

from ._anvil_designer import TopicRowTemplate
from ... import state

STATUS = {"draft": ("Draft", "badge-warn"), "in_review": ("In review", "badge-brand"),
          "changes": ("Changes asked", "badge-bad"), "approved": ("Approved", "badge-good")}


class TopicRow(TopicRowTemplate):
    """A topic in the Topics tab. item = topic_dict(). Pressing it opens the editor (x-open on the panel)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        t = self.item
        self.q_en.text = t["question_en"] or "(no English question yet)"
        self.q_fr.text = t["question_fr"] or ""
        self.q_fr.visible = bool(t["question_fr"])
        label, role = STATUS.get(t["status"], STATUS["draft"])
        self.status.text, self.status.role = label, ["badge", role]
        self.fr_badge.visible = t["missing_fr"]
        if t["status"] == "approved":
            self.meta.text = "Approved by %s · %s" % (t["approved_by"], state.short_date(t["approved_at"]))
        elif t["status"] == "changes":
            self.meta.text = "Note: " + t["review_note"]
        elif not (t["answer_en"] or t["answer_fr"]):
            self.meta.text = "No answer yet"
        else:
            self.meta.text = "Updated " + state.ago(t["updated"])
        anvil.js.get_dom_node(self.btn).setAttribute("data-key", t["id"])

    def btn_click(self, event):
        self.parent.raise_event("x-open", topic=self.item)
