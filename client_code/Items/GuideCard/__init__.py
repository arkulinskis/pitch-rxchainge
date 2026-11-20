from anvil import *
import anvil.js

from ._anvil_designer import GuideCardTemplate
from ... import router, state


class GuideCard(GuideCardTemplate):
    """A demo guide on the landing page. item = public_view() + samples. Links to its public page."""

    def __init__(self, **properties):
        super().__init__(**properties)
        g = self.item
        self.face.face = g["face"]
        state.set_attr(self.link, "href", router.href("talk", g["slug"]))
        who = g["expert_name"] + ((", " + g["expert_title"].lower()) if g.get("expert_title") else "")
        self.expert.text = "%s approved by %s" % (state.plural(g["topics"], "answer"), who)
        anvil.js.get_dom_node(self.go_name).textContent = g["name"]
