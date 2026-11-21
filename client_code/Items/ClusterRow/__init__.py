from anvil import *
import anvil.js

from ._anvil_designer import ClusterRowTemplate
from ... import state


class ClusterRow(ClusterRowTemplate):
    """An unanswered theme on the Trust tab: questions that share words. item = {theme, count, questions, ids,
    example, langs, can_edit}. Write a topic = x-make(cluster) on the panel."""

    def __init__(self, **properties):
        super().__init__(**properties)
        c = self.item
        anvil.js.get_dom_node(self.count).textContent = "%d×" % c["count"]
        langs = " · ".join({"en": "English", "fr": "French"}.get(x, x) for x in c.get("langs") or [])
        self.theme.text = "%s%s" % (c["theme"].capitalize(), (" · " + langs) if langs else "")
        self.examples.text = "  ".join("“%s”" % q for q in c["questions"][:3])
        self.make_button.visible = bool(c.get("can_edit"))
        state.set_control_attr(self.make_button, "aria-label", "Write a topic for %s" % c["theme"])

    @handle("make_button", "click")
    def make_button_click(self, **event_args):
        self.parent.raise_event("x-make", cluster=self.item)
