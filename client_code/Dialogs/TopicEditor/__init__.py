import anvil.js
import anvil.server
from anvil import *

from ._anvil_designer import TopicEditorTemplate
from ... import state

STATUS = {"draft": ("Draft", "badge-warn"), "in_review": ("In review", "badge-brand"),
          "changes": ("Changes asked", "badge-bad"), "approved": ("Approved", "badge-good")}


class TopicEditor(TopicEditorTemplate):
    """One topic, English and French side by side: draft each answer from the sources, save, send to the expert,
    approve or ask for changes. Closes with True when anything was saved (the tab reloads)."""

    def __init__(self, page, topic=None, prefill="", **properties):
        super().__init__(**properties)
        self.page = page
        d = page.data
        self.topic: dict = dict(topic or {})
        self.used: list = list(self.topic.get("used") or [])
        self.changed = False
        a = d["agent"]
        self.can_edit = d["can_edit"]
        self.can_approve = d["role"] == "expert" or (d["role"] == "owner" and not a["has_expert"])
        self.expert = a["expert_name"] if a["has_expert"] else ""
        t = self.topic
        self.q_en.text = t.get("question_en") or ""
        self.q_fr.text = t.get("question_fr") or ""
        self.a_en.text = t.get("answer_en") or ""
        self.a_fr.text = t.get("answer_fr") or ""
        self.kw_box.text = t.get("keywords") or ""
        if prefill:
            if prefill and any(ch in prefill for ch in "éèàçùêâîô") or prefill.lower().startswith(("où", "ou ", "quel", "est-ce")):
                self.q_fr.text = prefill
            else:
                self.q_en.text = prefill
        for box in (self.q_en, self.q_fr, self.a_en, self.a_fr, self.kw_box, self.review_note):
            box.enabled = self.can_edit
        state.set_control_attr(self.kw_box, "aria-label", "Keywords")
        self._draw()

    def _draw(self):
        t = self.topic
        st = t.get("status") or "draft"
        anvil.js.get_dom_node(self.heading).textContent = "Edit topic" if t.get("id") else "New topic"
        label, role = STATUS.get(st, STATUS["draft"])
        self.status.text, self.status.role = label, ["badge", role]
        self.status.visible = bool(t.get("id"))
        if st == "changes" and t.get("review_note"):
            self.note.text, self.note.visible = "Changes asked: " + t["review_note"], True
        elif st == "approved":
            self.note.text, self.note.visible = "Approved by %s. Editing the words sends it back to draft." % t.get("approved_by"), True
        elif st == "in_review":
            self.note.text, self.note.visible = "Waiting for %s to approve." % (self.expert or "approval"), True
        else:
            self.note.visible = False
        self.used_label.text = ("Drafted from: " + ", ".join(self.used)) if self.used else ""
        self.used_label.visible = bool(self.used)
        e = self.can_edit
        self.draft_en.visible = self.draft_fr.visible = e
        self.save_button.visible = e
        self.delete_button.visible = e and bool(t.get("id"))
        self.submit_button.visible = e and st in ("draft", "changes") and bool(self.expert)
        self.approve_button.visible = e and self.can_approve and st != "approved"
        self.changes_button.visible = e and self.can_approve and bool(self.expert) and st in ("in_review", "approved")
        self.review_box.visible = False
        if not self.expert and self.can_approve:
            self.approve_button.text = "Approve (as owner)"

    def _fields(self):
        return {"question_en": self.q_en.text, "question_fr": self.q_fr.text, "answer_en": self.a_en.text,
                "answer_fr": self.a_fr.text, "keywords": self.kw_box.text, "used": self.used}

    def _error(self, text):
        self.message.text, self.message.visible = text, bool(text)

    def _save(self):
        r = anvil.server.call("save_topic", self.page.agent_id, self.topic.get("id"), self._fields())
        if not r.get("ok"):
            self._error(r.get("error"))
            return False
        self._error("")
        self.topic = r["topic"]
        self.changed = True
        return True

    # ---- drafting
    def _draft(self, lang):
        q = (self.q_en.text if lang == "en" else self.q_fr.text) or self.q_en.text or self.q_fr.text
        r = anvil.server.call("draft_answer", self.page.agent_id, q or "", lang)
        if not r.get("ok"):
            self._error(r.get("error"))
            return
        self._error("" if r["found"] else "")
        box = self.a_en if lang == "en" else self.a_fr
        box.text = r["text"]
        for u in r["used"]:
            if u not in self.used:
                self.used.append(u)
        if not r["found"]:
            state.toast("Nothing in the sources fits that question yet.", "error")
        self._draw()

    @handle("draft_en", "click")
    def draft_en_click(self, **event_args):
        self._draft("en")

    @handle("draft_fr", "click")
    def draft_fr_click(self, **event_args):
        self._draft("fr")

    # ---- actions
    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        if self._save():
            state.toast("Saved", "ok")
            self.raise_event("x-close-alert", value=True)

    @handle("submit_button", "click")
    def submit_button_click(self, **event_args):
        if not self._save():
            return
        r = anvil.server.call("submit_topic", self.topic["id"])
        if not r.get("ok"):
            self._error(r.get("error"))
            return
        state.toast("Sent to %s for review" % self.expert, "ok")
        self.raise_event("x-close-alert", value=True)

    @handle("approve_button", "click")
    def approve_button_click(self, **event_args):
        if not self._save():
            return
        r = anvil.server.call("review_topic", self.topic["id"], "approve", "")
        if not r.get("ok"):
            self._error(r.get("error"))
            return
        state.toast("Approved. It goes live with the next published version.", "ok")
        self.raise_event("x-close-alert", value=True)

    @handle("changes_button", "click")
    def changes_button_click(self, **event_args):
        if not self.review_box.visible:
            self.review_box.visible = True
            state.focus(self.review_note)
            self.changes_button.text = "Send the note"
            return
        r = anvil.server.call("review_topic", self.topic["id"], "changes", self.review_note.text or "")
        if not r.get("ok"):
            self._error(r.get("error"))
            return
        state.toast("Note sent", "ok")
        self.raise_event("x-close-alert", value=True)

    @handle("delete_button", "click")
    def delete_button_click(self, **event_args):
        if confirm("The live agent keeps answering it until you publish again.", title="Delete this topic?",
                   buttons=[("Cancel", False), ("Delete", True)], role="app-dialog"):
            if state.call("delete_topic", self.topic["id"]):
                self.raise_event("x-close-alert", value=True)

    @handle("close_button", "click")
    def close_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=self.changed)
