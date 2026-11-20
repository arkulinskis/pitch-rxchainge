from anvil import *

from ._anvil_designer import RefuseChipTemplate
from ... import state


class RefuseChip(RefuseChipTemplate):
    """A refused subject on the Knowledge tab. item = {text, can_edit}. Remove raises x-remove(text)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.remove_button.visible = bool(self.item.get("can_edit"))
        state.set_control_attr(self.remove_button, "aria-label", "Remove %s" % self.item["text"])

    @handle("remove_button", "click")
    def remove_button_click(self, **event_args):
        self.parent.raise_event("x-remove", text=self.item["text"])
