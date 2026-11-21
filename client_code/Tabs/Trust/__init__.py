from anvil import *
import anvil.js
import anvil.media
import anvil.server

from ._anvil_designer import TrustTemplate
from ... import state

FILTERS = ["all", "review", "content", "publish"]
NAMES = {"all": "All", "review": "Reviews", "content": "Content", "publish": "Publishing"}
VERDICT = {"none": ("No questions yet", "badge"), "good": ("Well covered", "badge-good"),
           "ok": ("Some gaps", "badge-warn"), "gaps": ("Gaps to fill", "badge-bad")}
PAGE = 40


class Trust(TrustTemplate):
    """Trust tab: the coverage report (answer rate, unanswered themes with "Write a topic") and the approval audit
    trail (filter, Show all, Download CSV). One get_trust call; writing a topic for a theme resolves all its questions."""

    def __init__(self, page, **properties):
        super().__init__(**properties)
        self.page = page
        self.filter = state.store_get("as.trail_filter", "all")
        if self.filter not in FILTERS:
            self.filter = "all"
        self.show_all = False
        self.cluster_panel.add_event_handler("x-make", self._make)
        self.data = anvil.server.call("get_trust", page.agent_id)
        self._draw_cover()
        self._draw_trail()

    # ---- coverage
    def _draw_cover(self):
        c = self.data["coverage"]
        asked = c["asked"]
        self.rate.text = ("%d%%" % c["rate"]) if asked else "–"
        if asked:
            self.rate_line.text = "%d of %s on the public page got an approved answer" % (
                c["answered"], state.plural(asked, "question"))
        else:
            self.rate_line.text = "Nobody has asked the public agent anything yet"
        label, role = VERDICT.get(c["verdict"], VERDICT["none"])
        self.verdict.text, self.verdict.role = label, ["badge", role] if role != "badge" else ["badge"]
        self.bar_fill.style["width"] = "%d%%" % (c["rate"] if asked else 0)
        bl = c["by_lang"]
        self.s_en.text = "%d of %d" % (bl["en"]["missed"], bl["en"]["asked"])
        self.s_fr.text = "%d of %d" % (bl["fr"]["missed"], bl["fr"]["asked"])
        self.s_missing_fr.text = str(c["missing_fr"])
        self.s_unpub.text = str(c["unpublished"])
        self.s_wait.text = str(c["waiting"])
        can = self.data["can_edit"]
        self.cluster_panel.items = [dict(x, can_edit=can) for x in c["clusters"]]
        self.no_clusters.visible = not c["clusters"]

    def _make(self, cluster, **event_args):
        from ...Dialogs.TopicEditor import TopicEditor
        changed = alert(TopicEditor(page=self.page, prefill=cluster["example"]), buttons=[], role="app-dialog", large=True)
        if changed:
            r = state.call("resolve_gaps", self.page.agent_id, cluster["ids"])
            if r:
                state.toast("Topic saved. %s in this theme marked as handled." % state.plural(r["resolved"], "question"), "ok")
            self.page.reload("trust")

    # ---- audit trail
    def _shown(self):
        return [e for e in self.data["events"] if self.filter == "all" or e["kind"] == self.filter]

    def _draw_trail(self):
        ev = self.data["events"]
        for f in FILTERS:
            btn = getattr(self, "f_" + f)
            btn.classes["on"] = f == self.filter
            n = len([e for e in ev if f == "all" or e["kind"] == f])
            anvil.js.get_dom_node(btn).textContent = "%s %d" % (NAMES[f], n)
        shown = self._shown()
        self.event_panel.items = shown if self.show_all else shown[:PAGE]
        self.more_button.visible = not self.show_all and len(shown) > PAGE
        self.more_button.text = "Show all %d" % len(shown)
        self.csv_button.enabled = bool(ev)
        self.no_events.visible = not shown
        if not self.data["trail_ready"]:
            self.no_events_h.text = "The audit trail starts soon"
            self.no_events_p.text = "It needs one new table in the database. Once it's added, every review and publish is recorded here."
        elif not ev:
            self.no_events_h.text = "Nothing recorded yet"
            self.no_events_p.text = "Write a topic, send it to the expert or publish a version, and each step shows up here."
        else:
            self.no_events_h.text = "Nothing in %s" % NAMES[self.filter].lower()
            self.no_events_p.text = "Pick another filter to see the other events."

    def filter_click(self, event):
        self.filter = event.currentTarget.getAttribute("data-f")
        state.store_set("as.trail_filter", self.filter)
        self.show_all = False
        self._draw_trail()

    @handle("more_button", "click")
    def more_button_click(self, **event_args):
        self.show_all = True
        self._draw_trail()

    @handle("csv_button", "click")
    def csv_button_click(self, **event_args):
        def cell(v):
            v = str(v if v is not None else "")
            return '"%s"' % v.replace('"', '""') if any(ch in v for ch in ',"\n') else v
        rows = [["When (UTC)", "Event", "Topic", "By", "Details", "Version"]]
        for e in self.data["events"]:
            rows.append([(e["when"] or "")[:19].replace("T", " "), e["label"], e["topic"], e["actor"], e["detail"],
                         e["version"] or ""])
        text = "﻿" + "\r\n".join(",".join(cell(v) for v in r) for r in rows) + "\r\n"
        slug = "".join(ch if ch.isalnum() else "-" for ch in (self.data["name"] or "agent").lower()).strip("-") or "agent"
        anvil.media.download(BlobMedia("text/csv", text.encode("utf-8"), name="%s-audit-trail.csv" % slug))
