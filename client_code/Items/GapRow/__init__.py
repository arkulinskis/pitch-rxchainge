from anvil import *

from ._anvil_designer import GapRowTemplate
from ... import state


class GapRow(GapRowTemplate):
    """A question nobody answered. item = {id, question, lang, when, mode, can_edit}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        where = "in Try it" if it["mode"] == "preview" else "on the public page"
        times = ("asked %d times · " % it["count"]) if it.get("count", 1) > 1 else ""
        self.meta.text = "%s%s, %s · last %s" % (times.capitalize(), "French" if it["lang"] == "fr" else "English", where,
                                                 state.ago(it["when"]))
        self.actions.visible = bool(it.get("can_edit"))

    @handle("make_button", "click")
    def make_button_click(self, **event_args):
        self.parent.raise_event("x-make", gap=self.item)

    @handle("dismiss_button", "click")
    def dismiss_button_click(self, **event_args):
        self.parent.raise_event("x-dismiss", gap=self.item)
