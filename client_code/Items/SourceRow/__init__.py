from anvil import *

from ._anvil_designer import SourceRowTemplate
from ... import state

KINDS = {"guide": "Guide", "notes": "Notes", "faq": "FAQ", "leaflet": "Leaflet", "review": "Review"}


class SourceRow(SourceRowTemplate):
    """A source on the Knowledge tab. item = {id, title, kind, lang, words, preview, created, can_edit}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        self.kind.text = KINDS.get(it["kind"], "Notes")
        self.lang.text = "Français" if it["lang"] == "fr" else "English"
        self.preview.text = it["preview"] + ("..." if len(it["preview"]) >= 180 else "")
        self.meta.text = "%s · added %s" % (state.plural(it["words"], "word"), state.short_date(it["created"]))
        self.delete_button.visible = bool(it.get("can_edit"))

    @handle("delete_button", "click")
    def delete_button_click(self, **event_args):
        if confirm("Drafts already written from it stay as they are.", title="Delete \"%s\"?" % self.item["title"],
                   buttons=[("Cancel", False), ("Delete", True)], role="app-dialog"):
            if state.call("delete_source", self.item["id"]):
                self.parent.raise_event("x-deleted")
