from anvil import *

from ._anvil_designer import TryTemplate
from ... import router, state

KIND = {"answer": "Matched an approved topic", "unknown": "No approved topic fits: logged as a gap",
        "refused": "A refused subject: polite no", "greeting": "A greeting"}


class Try(TryTemplate):
    """Try it tab: the chat in preview mode (the topics approved right now) and what happened to the last question."""

    def __init__(self, page, **properties):
        super().__init__(**properties)
        self.page = page
        d = page.data
        a = d["agent"]
        approved = [t for t in d["topics"] if t["status"] == "approved"]
        view = {"name": a["name"], "tagline_en": a["tagline_en"], "tagline_fr": a["tagline_fr"],
                "greeting_en": a["greeting_en"], "greeting_fr": a["greeting_fr"], "face": a["face"],
                "expert_name": a["expert_name"],
                "suggest_en": [t["question_en"] for t in approved if t["question_en"]][:4],
                "suggest_fr": [t["question_fr"] for t in approved if t["question_fr"]][:4]}
        self.chat.setup(view, page.agent_id, "preview")
        self.count_label.text = "%s approved right now" % state.plural(len(approved), "topic")
        self.last_label.visible = False
        self.public_link.visible = a["status"] == "live"
        state.set_attr(self.public_link, "href", router.href("talk", a["slug"]))

    @handle("chat", "asked")
    def chat_asked(self, reply, **event_args):
        text = KIND.get(reply.get("kind"), "")
        if reply.get("kind") == "answer" and reply.get("question"):
            text += ": “%s”" % reply["question"]
        self.last_label.text = text
        self.last_label.visible = bool(text)
