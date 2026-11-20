from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import PublishTemplate
from ... import router, state


class Publish(PublishTemplate):
    """Publish tab: what's live and its link, publishing the approved topics as a new version, the version history
    with one-click rollback, and taking the agent offline."""

    def __init__(self, page, **properties):
        super().__init__(**properties)
        self.page = page
        d = page.data
        a = d["agent"]
        owner = d["is_owner"]
        versions = d["versions"]
        live = a["status"] == "live"
        url = window.location.origin + window.location.pathname + router.href("talk", a["slug"])
        self.live_title.text = ("Live: version %d" % a["live_version"]) if live else "Not live"
        lv = [v for v in versions if v["live"]]
        if live and lv:
            self.live_line.text = "%s · answers from %s approved by %s" % (
                lv[0]["note"], state.plural(lv[0]["topics"], "topic"), a["expert_name"] or "the owner")
        else:
            self.live_line.text = "Nobody can talk to it yet."
        self.link_row.visible = live
        self.link_box.text = url
        state.set_control_attr(self.link_box, "aria-label", "Public link")
        state.set_control_attr(self.link_box, "readonly", "readonly")
        state.set_attr(self.open_link, "href", router.href("talk", a["slug"]))
        approved = d["counts"]["approved"]
        live_n = lv[0]["topics"] if lv else 0
        if approved == 0:
            self.next_line.text = "No approved topics yet. Approve at least one on the Topics tab."
        elif live and approved == live_n:
            self.next_line.text = "%s approved, the same number as the live version. Publish again after new approvals." % state.plural(approved, "topic")
        else:
            self.next_line.text = "%s approved right now (live version: %d). Publishing makes them what visitors hear." % (
                state.plural(approved, "topic"), live_n)
        self.next_card.visible = owner
        self.publish_button.enabled = approved > 0
        self.ver_panel.items = [dict(v, owner=owner) for v in versions]
        self.ver_panel.add_event_handler("x-rollback", self._rollback)
        self.no_versions.visible = not versions
        self.unpublish_button.visible = owner and live

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        try:
            window.navigator.clipboard.writeText(self.link_box.text)
            state.toast("Link copied", "ok")
        except Exception:
            state.control(self.link_box).select()
            state.toast("Press Ctrl+C to copy the selected link.")

    @handle("publish_button", "click")
    def publish_button_click(self, **event_args):
        from ...Dialogs.PublishDialog import PublishDialog
        r = alert(PublishDialog(agent_id=self.page.agent_id, approved=self.page.data["counts"]["approved"]),
                  buttons=[], role="app-dialog")
        if r:
            state.toast("Version %d is live" % r, "ok")
            self.page.reload("publish")

    def _rollback(self, number, **event_args):
        if confirm("Visitors will hear version %d's answers from now on. You can switch back any time." % number,
                   title="Make version %d live?" % number, buttons=[("Cancel", False), ("Make it live", True)],
                   role="app-dialog"):
            if state.call("rollback", self.page.agent_id, number):
                state.toast("Version %d is live again" % number, "ok")
                self.page.reload("publish")

    @handle("unpublish_button", "click")
    def unpublish_button_click(self, **event_args):
        if confirm("The public page stops answering until you publish or make a version live again.",
                   title="Take it offline?", buttons=[("Cancel", False), ("Take offline", True)], role="app-dialog"):
            if state.call("unpublish", self.page.agent_id):
                self.page.reload("publish")
