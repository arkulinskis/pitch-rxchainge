from anvil import *

from ._anvil_designer import MessageTemplate


class Message(MessageTemplate):
    """One line of a conversation. item = {who: "agent" | "me", text, by (the "Approved by ..." line), kind}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.bubble.classes["me"] = self.item["who"] == "me"
        self.bubble.classes["agent"] = self.item["who"] != "me"
        self.bubble.classes["soft"] = self.item.get("kind") in ("unknown", "refused", "error")
