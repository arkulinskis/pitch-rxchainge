from anvil import *
import anvil.server

from ._anvil_designer import OverviewTemplate
from ... import router, state

TONES = [("Warm and welcoming", "warm"), ("Witty", "witty"), ("Precise, no frills", "precise"), ("Calm and reassuring", "calm")]


class Overview(OverviewTemplate):
    """Overview tab: identity (EN | FR side by side), the steps to go live, the expert, and how it's being used."""

    def __init__(self, page, **properties):
        super().__init__(**properties)
        self.page = page
        d = page.data
        a = d["agent"]
        self.name_box.text, self.domain_box.text = a["name"], a["domain"]
        self.tag_en.text, self.tag_fr.text = a["tagline_en"], a["tagline_fr"]
        self.greet_en.text, self.greet_fr.text = a["greeting_en"], a["greeting_fr"]
        self.tone_dd.items = TONES
        self.tone_dd.selected_value = a["tone"]
        state.set_control_attr(self.tone_dd, "aria-label", "Tone of voice")
        for box in (self.name_box, self.domain_box, self.tag_en, self.tag_fr, self.greet_en, self.greet_fr, self.tone_dd):
            box.enabled = d["can_edit"]
        self.save_button.visible = d["can_edit"]
        steps = d["checklist"]
        done = len([s for s in steps if s["done"]])
        self.steps_panel.items = steps
        self.bar.style["width"] = "%d%%" % int(100 * done / max(1, len(steps)))
        state.set_attr(self.bar_box, "aria-valuenow", done)
        state.set_attr(self.bar_box, "aria-valuemax", len(steps))
        self.progress_label.text = "%d of %d done" % (done, len(steps))
        if a["has_expert"]:
            self.expert_name.text = a["expert_name"]
            self.expert_line.text = (a["expert_title"] + " · " if a["expert_title"] else "") + (a["expert_email"] or "invited")
            self.expert_button.text = "Change the expert"
        else:
            self.expert_name.text = "No expert yet"
            self.expert_line.text = "Until you invite one, you approve answers yourself and they're marked as owner-approved."
        self.expert_button.visible = d["is_owner"]
        self.asked_num.text = str(d["asked"])
        self.gaps_num.text = str(d["counts"]["gaps"])
        self.delete_button.visible = d["is_owner"]

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        fields = {"name": self.name_box.text, "domain": self.domain_box.text, "tagline_en": self.tag_en.text,
                  "tagline_fr": self.tag_fr.text, "greeting_en": self.greet_en.text, "greeting_fr": self.greet_fr.text,
                  "tone": self.tone_dd.selected_value}
        self.save_button.enabled = False
        try:
            r = anvil.server.call("update_agent", self.page.agent_id, fields)
        finally:
            self.save_button.enabled = True
        if not r.get("ok"):
            self.message.text, self.message.visible = r.get("error"), True
            return
        self.message.visible = False
        state.toast("Saved", "ok")
        self.page.reload()

    @handle("expert_button", "click")
    def expert_button_click(self, **event_args):
        from ...Dialogs.ExpertDialog import ExpertDialog
        if alert(ExpertDialog(agent_id=self.page.agent_id, agent=self.page.data["agent"]), buttons=[], role="app-dialog"):
            self.page.reload()

    @handle("delete_button", "click")
    def delete_button_click(self, **event_args):
        name = self.page.data["agent"]["name"]
        if confirm("Its topics, sources, versions and the questions people asked go too. This can't be undone.",
                   title="Delete %s?" % name, buttons=[("Cancel", False), ("Delete", True)], role="app-dialog"):
            if state.call("delete_agent", self.page.agent_id):
                state.toast("%s was deleted." % name)
                router.go("studio")
