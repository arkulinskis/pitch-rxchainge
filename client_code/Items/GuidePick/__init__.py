from anvil import *
import anvil.js

from ._anvil_designer import GuidePickTemplate


class GuidePick(GuidePickTemplate):
    """A small face to choose which guide the landing hero shows. item = {i, name, face, on}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.face.face = self.item["face"]
        node = anvil.js.get_dom_node(self.btn)
        node.setAttribute("aria-pressed", "true" if self.item["on"] else "false")
        node.setAttribute("aria-label", "Show %s" % self.item["name"])
        self.btn.classes["on"] = bool(self.item["on"])
        anvil.js.get_dom_node(self.name_text).textContent = self.item["name"]

    def btn_click(self, event):
        self.parent.raise_event("x-guide", i=self.item["i"])
