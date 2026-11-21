from anvil import *

from ._anvil_designer import AuditRowTemplate
from ... import state


class AuditRow(AuditRowTemplate):
    """One event in an audit trail (Trust tab, topic editor history). item = Audit.event_dict(); compact=True hides
    the topic line (the editor already shows the topic)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        e = self.item
        self.row.classes[e["action"]] = True
        self.row.classes["k-" + (e.get("kind") or "content")] = True
        when = e.get("when") or ""
        self.when.text = "%s %s · %s" % (state.short_date(when), when[11:16], state.ago(when)) if when else ""
        self.topic.text = "“%s”" % e["topic"] if e.get("topic") and not e.get("compact") else ""
        self.topic.visible = bool(self.topic.text)
        v = " · version %d" % e["version"] if e.get("version") and e["action"] != "published" else ""
        self.detail.text = (e.get("detail") or "") + v
        self.detail.visible = bool(self.detail.text)
        self.actor.text = "by " + e["actor"] if e.get("actor") else ""
        self.actor.visible = bool(self.actor.text)
