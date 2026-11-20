from anvil import *

from ._anvil_designer import CheckStepTemplate


class CheckStep(CheckStepTemplate):
    """One step on the Overview's "Getting it live" list. item = {key, label, done}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.row.classes["done"] = bool(self.item["done"])
        self.state_sr.text = "done" if self.item["done"] else "to do"
