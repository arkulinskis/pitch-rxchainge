from anvil import *
import anvil.js
import anvil.server
from anvil.js import window

from ._anvil_designer import TalkTemplate


class Talk(TalkTemplate):
    """#talk/<slug>, the public page of a published agent: anyone can talk to it, no account needed."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        slug = args[0] if args else ""
        r = anvil.server.call("get_public_agent", slug)
        ok = bool(r.get("ok"))
        self.missing.visible, self.main.visible = not ok, ok
        if not ok:
            self.missing_text.text = r.get("error") or "The link may be wrong."
            return
        a = r["agent"]
        window.document.title = "Talk to %s · Agent Studio" % a["name"]
        anvil.js.get_dom_node(self.sr_title).textContent = "Talk to %s" % a["name"]
        self.chat.setup(a, slug, "live")
        if a.get("expert_name"):
            self.expert_line.text = "Knowledge from %s%s" % (a["expert_name"], (", " + a["expert_title"]) if a.get("expert_title") else "")
        else:
            self.expert_line.visible = False
