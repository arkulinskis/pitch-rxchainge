from anvil import *
import anvil.js

from ._anvil_designer import TopicsTemplate
from ... import state

FILTERS = ["all", "draft", "in_review", "changes", "approved"]
NAMES = {"all": "All", "draft": "Drafts", "in_review": "In review", "changes": "Changes asked", "approved": "Approved"}


class Topics(TopicsTemplate):
    """Topics tab: the list (filter by status), New topic, and the questions people asked that nothing answered."""

    def __init__(self, page, **properties):
        super().__init__(**properties)
        self.page = page
        d = page.data
        self.topics = d["topics"]
        self.filter = state.store_get("as.topic_filter", "all")
        if self.filter not in FILTERS:
            self.filter = "all"
        self.new_button.visible = d["can_edit"]
        self.topic_panel.add_event_handler("x-open", self._open)
        self.gap_panel.add_event_handler("x-make", self._make)
        self.gap_panel.add_event_handler("x-dismiss", self._dismiss)
        self.gap_panel.items = [dict(g, can_edit=d["can_edit"]) for g in d["gaps"]]
        self.gaps_sec.visible = bool(d["gaps"])
        self._draw()

    def _draw(self):
        counts = {f: len([t for t in self.topics if f == "all" or t["status"] == f]) for f in FILTERS}
        for f in FILTERS:
            btn = getattr(self, "f_" + f)
            btn.classes["on"] = f == self.filter
            anvil.js.get_dom_node(btn).textContent = "%s %d" % (NAMES[f], counts[f])
        shown = [t for t in self.topics if self.filter == "all" or t["status"] == self.filter]
        self.topic_panel.items = shown
        self.empty.visible = not shown
        anvil.js.get_dom_node(self.empty_h).textContent = "No topics yet" if not self.topics else "Nothing in %s" % NAMES[self.filter].lower()

    def filter_click(self, event):
        self.filter = event.currentTarget.getAttribute("data-f")
        state.store_set("as.topic_filter", self.filter)
        self._draw()

    def _edit(self, topic=None, prefill="", gap_id=None):
        from ...Dialogs.TopicEditor import TopicEditor
        changed = alert(TopicEditor(page=self.page, topic=topic, prefill=prefill), buttons=[], role="app-dialog", large=True)
        if changed:
            if gap_id:
                state.call("resolve_gap", gap_id)
            self.page.reload()

    @handle("new_button", "click")
    def new_button_click(self, **event_args):
        self._edit()

    def _open(self, topic, **event_args):
        self._edit(topic)

    def _make(self, gap, **event_args):
        self._edit(None, gap["question"], gap["id"])

    def _dismiss(self, gap, **event_args):
        if state.call("resolve_gap", gap["id"]):
            self.page.reload()
