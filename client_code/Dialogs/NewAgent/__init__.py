import anvil.server
from anvil import *

from ._anvil_designer import NewAgentTemplate
from ... import state

BLANK = {"key": "blank", "name": "Blank", "tagline": "Start from nothing", "face": {"hairStyle": "short", "bg": "#EFEBE6", "shirt": "#6D6A75"}}


class NewAgent(NewAgentTemplate):
    """Choose a template (or blank) and a name; closes with the new agent's id, or None."""

    def __init__(self, templates, chosen="", **properties):
        super().__init__(**properties)
        self._templates = list(templates) + [BLANK]
        self._chosen = chosen or self._templates[0]["key"]
        self._named = False
        self.tpl_panel.add_event_handler("x-template", self._pick)
        self._draw()
        self._suggest_name()

    def _draw(self):
        self.tpl_panel.items = [dict(t, on=t["key"] == self._chosen) for t in self._templates]

    def _suggest_name(self):
        if self._named:
            return
        t = [x for x in self._templates if x["key"] == self._chosen]
        self.name_box.text = "" if (not t or self._chosen == "blank") else t[0]["name"]

    def _pick(self, key, **event_args):
        k = state.focus_key()
        self._chosen = key
        self._draw()
        self._suggest_name()
        state.refocus(self.tpl_panel, k)

    @handle("name_box", "change")
    def name_box_change(self, **event_args):
        self._named = bool((self.name_box.text or "").strip())

    @handle("name_box", "pressed_enter")
    def name_box_pressed_enter(self, **event_args):
        self.create_button_click()

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)

    @handle("create_button", "click")
    def create_button_click(self, **event_args):
        name = (self.name_box.text or "").strip()
        if len(name) < 2:
            self.message.text, self.message.visible = "Give your agent a name (at least 2 characters).", True
            state.focus(self.name_box)
            return
        self.create_button.enabled = False
        try:
            r = anvil.server.call("create_agent", "" if self._chosen == "blank" else self._chosen, name)
        finally:
            self.create_button.enabled = True
        if not r.get("ok"):
            self.message.text, self.message.visible = r.get("error") or "That didn't work.", True
            return
        self.raise_event("x-close-alert", value=r["id"])
