from anvil import *

from ._anvil_designer import AgentCardTemplate
from ... import router, state


class AgentCard(AgentCardTemplate):
    """An agent in the studio grid. item = agent_card() from the server. The whole card links to its editor."""

    def __init__(self, **properties):
        super().__init__(**properties)
        a = self.item
        state.set_attr(self.link, "href", router.href("agent", a["id"]))
        state.set_attr(self.link, "aria-label", "Open %s" % a["name"])
        self.face.face = a["face"]
        live = a["status"] == "live"
        self.status.text = ("Live · v%d" % a["live_version"]) if live else "Draft"
        self.status.role = ["badge", "badge-good" if live else "badge-warn"]
        n = a["counts"]
        bits = ["%d of %d approved" % (n["approved"], n["total"])]
        if n["in_review"]:
            bits.append("%d to review" % n["in_review"])
        if n["gaps"]:
            bits.append(state.plural(n["gaps"], "unanswered question"))
        if a["role"] == "expert":
            bits.insert(0, "You review")
        self.meta.text = " · ".join(bits)
