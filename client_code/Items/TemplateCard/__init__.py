from anvil import *
import anvil.js

from ._anvil_designer import TemplateCardTemplate


class TemplateCard(TemplateCardTemplate):
    """A starting point for a new agent (studio empty state, New agent dialog). item = {key, name, tagline, face,
    on?}. Pressing it raises x-template on the panel with the key."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.face.face = self.item.get("face")
        self.btn.classes["on"] = bool(self.item.get("on"))
        node = anvil.js.get_dom_node(self.btn)
        node.setAttribute("aria-pressed", "true" if self.item.get("on") else "false")
        node.setAttribute("data-key", self.item["key"])

    def btn_click(self, event):
        self.parent.raise_event("x-template", key=self.item["key"])
