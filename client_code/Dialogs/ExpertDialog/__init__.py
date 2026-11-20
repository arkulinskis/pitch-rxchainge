import anvil.server
from anvil import *

from ._anvil_designer import ExpertDialogTemplate
from ... import state


class ExpertDialog(ExpertDialogTemplate):
    """Invite, change or remove the agent's expert. Closes with True when something changed."""

    def __init__(self, agent_id, agent, **properties):
        super().__init__(**properties)
        self.agent_id = agent_id
        self.name_box.text = agent.get("expert_name") or ""
        self.email_box.text = agent.get("expert_email") or ""
        self.title_box.text = agent.get("expert_title") or ""
        self.remove_button.visible = bool(agent.get("has_expert"))
        state.set_control_attr(self.name_box, "autocomplete", "off")
        state.set_control_attr(self.email_box, "autocomplete", "off")

    def _save(self, name, email, title):
        r = anvil.server.call("set_expert", self.agent_id, name, email, title)
        if not r.get("ok"):
            self.message.text, self.message.visible = r.get("error"), True
            return
        self.raise_event("x-close-alert", value=True)

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        if not (self.email_box.text or "").strip():
            self.message.text, self.message.visible = "Add the expert's email.", True
            return
        self._save(self.name_box.text, self.email_box.text, self.title_box.text)

    @handle("remove_button", "click")
    def remove_button_click(self, **event_args):
        self._save("", "", "")

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=False)
