from anvil import *
import anvil.js
import anvil.server

from ._anvil_designer import LandingTemplate
from ... import face, state


class Landing(LandingTemplate):
    """#landing, the front page for visitors: the live demo face, how it works, the demo guides, features, FAQ.
    Static copy lives in the template; the guides come from get_landing (the live demo agents)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        me = state.me()
        self.guest_cta.visible = not me
        self.member_cta.visible = bool(me)
        if me:
            state.set_attr(self.band_link, "href", "#studio")
        guides = anvil.server.call("get_landing")["guides"]
        pilot = anvil.server.call("sales_link")   # pilots are sold by hand: shown only with the App Secret sales_link
        self.pilot_line.visible = bool(pilot)
        if pilot:
            state.set_attr(self.pilot_link, "href", pilot)
        self.guides_panel.items = guides
        self.hero_demo.setup(guides)
        self.hero_demo.visible = bool(guides)
        self.fallback.visible = not guides
        if not guides:
            anvil.js.get_dom_node(self.fallback_face).innerHTML = face.svg({"hairStyle": "bob", "glasses": "round", "shirt": "#B0007A"})
