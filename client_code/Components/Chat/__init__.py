from anvil import *
import anvil.js
import anvil.server
from anvil.js import window

from ._anvil_designer import ChatTemplate
from ... import face as engine
from ... import state

UI_TEXT = {
    "en": {"ph": "Ask {n} a question", "ask": "Ask", "approved": "Approved by {b}", "foot": "Answers approved by {e}",
           "foot_none": "Every answer was approved before it went live", "ver": "version {v}", "preview": "Preview: approved topics, not yet published"},
    "fr": {"ph": "Posez une question à {n}", "ask": "Demander", "approved": "Approuvé par {b}", "foot": "Réponses approuvées par {e}",
           "foot_none": "Chaque réponse a été approuvée avant sa mise en ligne", "ver": "version {v}", "preview": "Aperçu : sujets approuvés, pas encore publiés"},
}


class Chat(ChatTemplate):
    """Talking to an agent (public page, the editor's Try tab). setup() with the agent's view, then people type or
    tap a suggested question; the face thinks, answers aloud if Voice is on, and the reply joins the conversation."""

    def __init__(self, **properties):
        self._view: dict = {}
        self._ref, self._mode, self._lang, self._voice = "", "live", "en", False
        self._msgs: list = []
        super().__init__(**properties)
        self.typing.visible = False
        self.voice_btn.visible = engine.speech_ok()
        self._voice = bool(state.store_get("as.voice", False)) and engine.speech_ok()
        self.suggest_panel.add_event_handler("x-ask", self._suggested)
        self._show_tools()

    def setup(self, view, ref, mode="live", lang=None):
        self._view, self._ref, self._mode = view or {}, ref, mode
        nav = str(window.navigator.language or "en")[:2]
        self._lang = lang or (state.store_get("as.lang", None) or ("fr" if nav == "fr" else "en"))
        self.face.face = self._view.get("face") or {}
        self.name_label.text = self._view.get("name") or "Agent"
        self._msgs = []
        greet = self._view.get("greeting_" + self._lang) or self._view.get("greeting_en") or ""
        if greet:
            self._msgs.append({"who": "agent", "text": greet, "by": ""})
        self._redraw()

    # ---- language and voice
    def lang_click(self, event):
        self._lang = event.currentTarget.getAttribute("data-lang")
        state.store_set("as.lang", self._lang)
        self._redraw(keep=True)

    def voice_click(self, event):
        self._voice = not self._voice
        state.store_set("as.voice", self._voice)
        if not self._voice:
            self.face.stop()
        self._show_tools()

    def _show_tools(self):
        self.lang_en.classes["on"] = self._lang == "en"
        self.lang_fr.classes["on"] = self._lang == "fr"
        anvil.js.get_dom_node(self.voice_text).textContent = "Voice on" if self._voice else "Voice off"
        anvil.js.get_dom_node(self.voice_btn).setAttribute("aria-pressed", "true" if self._voice else "false")
        self.voice_btn.classes["on"] = self._voice

    def _redraw(self, keep=False):
        v, L = self._view, UI_TEXT[self._lang]
        self.tagline_label.text = v.get("tagline_" + self._lang) or v.get("tagline_en") or ""
        self.ask_box.placeholder = L["ph"].format(n=v.get("name") or "the agent")
        self.ask_button.text = L["ask"]
        self.suggest_panel.items = [{"text": q} for q in (v.get("suggest_" + self._lang) or [])[:4]]
        if self._mode == "preview":
            self.foot.text = L["preview"]
        else:
            e = v.get("expert_name")
            line = L["foot"].format(e=e) if e else L["foot_none"]
            if v.get("version"):
                line += " · " + L["ver"].format(v=v.get("version"))
            self.foot.text = line
        if keep and len(self._msgs) == 1 and self._msgs[0]["who"] == "agent":  # only the greeting so far: re-greet
            self._msgs[0]["text"] = v.get("greeting_" + self._lang) or self._msgs[0]["text"]
        self.msg_panel.items = self._msgs
        self._show_tools()

    # ---- asking
    def _suggested(self, text, **event_args):
        self.ask_box.text = text
        self._ask()

    @handle("ask_box", "pressed_enter")
    def ask_box_pressed_enter(self, **event_args):
        self._ask()

    @handle("ask_button", "click")
    def ask_button_click(self, **event_args):
        self._ask()

    def ask(self, text, lang=None):
        """Ask from code (the landing page, presenter mode, tests); lang switches the language first."""
        if lang in ("en", "fr") and lang != self._lang:
            self.set_lang(lang)
        self.ask_box.text = text
        self._ask()

    def set_lang(self, lang):
        self._lang = lang if lang in ("en", "fr") else "en"
        state.store_set("as.lang", self._lang)
        self._redraw(keep=True)

    def voice_on(self):
        return self._voice

    def set_voice(self, on):
        if bool(on) != self._voice and engine.speech_ok():
            self.voice_click(None)

    def _ask(self):
        q = (self.ask_box.text or "").strip()
        if len(q) < 2:
            state.focus(self.ask_box)
            return
        self.ask_box.text = ""
        self._msgs.append({"who": "me", "text": q, "by": ""})
        self.msg_panel.items = self._msgs
        self.typing.visible = True
        self.ask_button.enabled = False
        self.face.think(True)
        self._scroll()
        try:
            r = anvil.server.call_s("talk_ask", self._ref, q, self._lang, self._mode)
        finally:
            self.typing.visible = False
            self.ask_button.enabled = True
            self.face.think(False)
        if not r.get("ok"):
            self._msgs.append({"who": "agent", "text": r.get("error") or "Something went wrong.", "by": "", "kind": "error"})
        else:
            rep = r["reply"]
            by = UI_TEXT[self._lang]["approved"].format(b=rep["by"]) if rep.get("by") else ""
            self._msgs.append({"who": "agent", "text": rep["text"], "by": by, "kind": rep.get("kind", ""),
                               "why": rep.get("why"), "lang": rep.get("lang") or self._lang})
            self.face.say(rep["text"], rep.get("lang") or self._lang, self._voice)
            self.raise_event("asked", reply=rep)
        self.msg_panel.items = self._msgs
        self._scroll()

    def _scroll(self):
        node = anvil.js.get_dom_node(self.log)
        node.scrollTop = node.scrollHeight
