from anvil import *
import anvil.js

from ._anvil_designer import VersionRowTemplate
from ... import state


class VersionRow(VersionRowTemplate):
    """A published version. item = {number, note, by, when, topics, live, owner}. Make live = x-rollback(number)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        v = self.item
        anvil.js.get_dom_node(self.num).textContent = "v%d" % v["number"]
        self.meta.text = "%s · by %s · %s" % (state.plural(v["topics"], "topic"), v["by"], state.short_date(v["when"]))
        self.live_badge.visible = v["live"]
        self.row.classes["live"] = v["live"]
        self.rollback_button.visible = v["owner"] and not v["live"]
        state.set_control_attr(self.rollback_button, "aria-label", "Make version %d live" % v["number"])

    @handle("rollback_button", "click")
    def rollback_button_click(self, **event_args):
        self.parent.raise_event("x-rollback", number=self.item["number"])
