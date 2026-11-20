from anvil import *

from ._anvil_designer import StudioTemplate
from ... import router, state


class Studio(StudioTemplate):
    """#studio, the signed-in home: my agents, agents I review as the expert, the demo agents, and New agent."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.empty_panel.add_event_handler("x-template", self._from_template)
        state.heading(self.title, 1)
        self._load()

    def _load(self):
        d = state.call("list_studio")
        self._templates = d["templates"]
        self.mine_panel.items = d["mine"]
        self.mine_sec.visible = bool(d["mine"])
        self.empty.visible = not d["mine"]
        self.empty_panel.items = d["templates"]
        self.review_panel.items = d["review"]
        self.review_sec.visible = bool(d["review"])
        self.demo_panel.items = d["demo"]
        self.demo_sec.visible = bool(d["demo"])
        n = len(d["mine"])
        live = len([a for a in d["mine"] if a["status"] == "live"])
        self.sub.text = ("%s, %d live" % (state.plural(n, "agent"), live)) if n else "Turn what an expert knows into a face people can talk to."

    def _new(self, template_key=""):
        from ...Dialogs.NewAgent import NewAgent
        r = alert(NewAgent(templates=self._templates, chosen=template_key), buttons=[], role="app-dialog", large=True)
        if r:
            router.go("agent", r)

    def _from_template(self, key, **event_args):
        self._new(key)

    @handle("new_button", "click")
    def new_button_click(self, **event_args):
        self._new()

    @handle("blank_button", "click")
    def blank_button_click(self, **event_args):
        self._new("blank")
