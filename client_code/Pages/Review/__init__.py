from anvil import *

from ._anvil_designer import ReviewTemplate
from ... import state


class Review(ReviewTemplate):
    """#review, the expert's queue: every topic sent for review on agents I approve for (or my own agents with no
    expert yet), English and French side by side, approve or ask for changes right here."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        state.heading(self.title, 1)
        self.queue_panel.add_event_handler("x-done", self._load)
        self._load()

    def _load(self, **event_args):
        items = state.call("review_queue")["items"]
        self.queue_panel.items = items
        self.empty.visible = not items
        self.sub.text = ("%s to look at" % state.plural(len(items), "answer")) if items else "All caught up."
