from anvil import *
import anvil.js
import anvil.server
from anvil.js import window

from ._anvil_designer import AgentTemplate
from ... import router, state

TABS = ["overview", "look", "knowledge", "topics", "try", "publish"]
ROLE_TEXT = {"expert": "You're the expert", "viewer": "Demo: look only", "admin": "Admin view"}


class Agent(AgentTemplate):
    """#agent/<id>/<tab>, the editor. One server call (get_agent) feeds the header and every tab; tabs are Forms in
    client_code/Tabs, built when opened. A tab that changes something calls page.reload() (fresh data, same tab)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.agent_id = args[0] if args else ""
        self.tab = args[1] if len(args) > 1 and args[1] in TABS else "overview"
        self.data: dict = {}
        self.missing.visible = False
        self.reload()

    # ---- data
    def reload(self, tab=None):
        try:
            self.data = anvil.server.call("get_agent", self.agent_id)
        except Exception as e:
            if type(e).__name__ != "PermissionDenied":
                raise
            self.missing.visible, self.main.visible = True, False
            return
        self.missing.visible, self.main.visible = False, True
        self.draw_head()
        self.show_tab(tab or self.tab)

    def draw_head(self):
        d = self.data
        a = d["agent"]
        self.face.face = a["face"]
        self.title.text = a["name"] or "Untitled agent"
        state.heading(self.title, 1)
        window.document.title = (a["name"] or "Agent") + " · Agent Studio"
        live = a["status"] == "live"
        self.status.text = ("Live · v%d" % a["live_version"]) if live else "Draft"
        self.status.role = ["badge", "badge-good" if live else "badge-warn"]
        self.role_badge.text = ROLE_TEXT.get(d["role"], "")
        self.role_badge.visible = d["role"] in ROLE_TEXT
        self.tagline.text = a["tagline_en"] or "Add a tagline on the Overview tab"
        self.public_link.visible = live
        state.set_attr(self.public_link, "href", router.href("talk", a["slug"]))
        self.viewer_note.visible = d["role"] == "viewer"
        n = d["counts"]
        anvil.js.get_dom_node(self.topics_count).textContent = "%d/%d" % (n["approved"], n["total"])

    # ---- tabs
    def tab_click(self, event):
        self.show_tab(event.currentTarget.getAttribute("data-tab"))

    def show_tab(self, name):
        self.tab = name if name in TABS else "overview"
        router.replace("agent", self.agent_id, self.tab)
        for t in TABS:
            getattr(self, "t_" + t).classes["on"] = t == self.tab
            anvil.js.get_dom_node(getattr(self, "t_" + t)).setAttribute("aria-pressed", "true" if t == self.tab else "false")
        active = anvil.js.get_dom_node(getattr(self, "t_" + self.tab))
        bar = active.parentElement
        if bar and getattr(bar, "scrollWidth") > getattr(bar, "clientWidth"):  # phones: keep the open tab in view
            setattr(bar, "scrollLeft", max(0, getattr(active, "offsetLeft") - 16))
        self.tab_panel.clear()
        self.tab_panel.add_component(self._make(self.tab))

    def _make(self, name):
        if name == "look":
            from ...Tabs.Look import Look
            return Look(page=self)
        if name == "knowledge":
            from ...Tabs.Knowledge import Knowledge
            return Knowledge(page=self)
        if name == "topics":
            from ...Tabs.Topics import Topics
            return Topics(page=self)
        if name == "try":
            from ...Tabs.Try import Try
            return Try(page=self)
        if name == "publish":
            from ...Tabs.Publish import Publish
            return Publish(page=self)
        from ...Tabs.Overview import Overview
        return Overview(page=self)

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        r = state.call("copy_agent", self.agent_id)
        if r:
            state.toast("Your copy is ready. Its topics are drafts until your expert approves them.", "ok")
            router.go("agent", r["id"])
