from anvil import *

from ._anvil_designer import SuggestTemplate


class Suggest(SuggestTemplate):
    """A suggested question under the chat. item = {text}. Tapping it asks it (x-ask on the panel)."""

    def __init__(self, **properties):
        super().__init__(**properties)

    @handle("chip", "click")
    def chip_click(self, **event_args):
        self.parent.raise_event("x-ask", text=self.item["text"])
