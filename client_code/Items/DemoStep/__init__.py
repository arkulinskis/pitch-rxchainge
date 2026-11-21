from anvil import *
import anvil.js

from ._anvil_designer import DemoStepTemplate


class DemoStep(DemoStepTemplate):
    """One step in presenter mode's step list. item = {n, title, on, done}. Pressing it = x-step(n) on the panel."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        anvil.js.get_dom_node(self.num).textContent = "✓" if it["done"] and not it["on"] else str(it["n"] + 1)
        anvil.js.get_dom_node(self.title_text).textContent = it["title"]
        node = anvil.js.get_dom_node(self.btn)
        node.setAttribute("aria-current", "step" if it["on"] else "false")
        self.btn.classes["on"] = bool(it["on"])
        self.btn.classes["done"] = bool(it["done"])

    def btn_click(self, event):
        self.parent.raise_event("x-step", n=self.item["n"])
