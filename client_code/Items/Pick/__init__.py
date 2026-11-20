from anvil import *
import anvil.js

from ._anvil_designer import PickTemplate


class Pick(PickTemplate):
    """One choice in the Look tab: a colour swatch or a word chip. item = {group, value, color, label, on, enabled}.
    Raises x-pick(group, value) on its panel."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        node = anvil.js.get_dom_node(self.btn)
        node.setAttribute("aria-pressed", "true" if it["on"] else "false")
        node.setAttribute("data-key", it["group"] + ":" + it["value"])
        setattr(node, "disabled", not it.get("enabled", True))
        self.btn.classes["on"] = bool(it["on"])
        self.btn.classes["swatch"] = bool(it["color"])
        if it["color"]:
            node.setAttribute("aria-label", it["label"])
            node.setAttribute("title", it["label"])
            self.dot.style["background"] = it["color"]
            self.word.visible = False
        else:
            self.dot.visible = False
            anvil.js.get_dom_node(self.word).textContent = it["label"]

    def btn_click(self, event):
        self.parent.raise_event("x-pick", group=self.item["group"], value=self.item["value"])
