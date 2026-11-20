from anvil import *
import anvil.js
import anvil.server

from ._anvil_designer import LookTemplate
from ... import face as engine
from ... import state

GROUPS = [("skin", "Skin tone", True), ("hairStyle", "Hair style", False), ("hair", "Hair colour", True),
          ("eyes", "Eye colour", True), ("brows", "Brows", False), ("glasses", "Glasses", False),
          ("accessory", "Accessory", False), ("shirt", "Top colour", True), ("bg", "Background", True)]
DEFAULTS = {"skin": "#EBB897", "hair": "#4A2E1F", "hairStyle": "bob", "eyes": "#3B2A20", "brows": "soft",
            "glasses": "none", "accessory": "none", "shirt": "#2E6F6A", "bg": "#F8E3F0"}


class Look(LookTemplate):
    """Face & voice tab, the avatar studio: a live preview, a picker per part, Shuffle, voice speed and pitch, and
    "Say hello" in both languages. Nothing is saved until Save."""

    def __init__(self, page, **properties):
        super().__init__(**properties)
        self.page = page
        self.can_edit = page.data["can_edit"]
        self._saved = dict(DEFAULTS, **(page.data["agent"]["face"] or {}))
        self.cfg: dict = dict(self._saved)
        for key, label, color in GROUPS:
            getattr(self, "p_" + key).add_event_handler("x-pick", self._pick)
        if not engine.speech_ok():
            anvil.js.get_dom_node(self.voice_note).textContent = "This browser can't read aloud; visitors whose browsers can will hear the voice."
        setattr(anvil.js.get_dom_node(self.hear), "checked", engine.speech_ok())
        for btn in (self.shuffle_button, self.save_button, self.reset_button):
            btn.visible = self.can_edit
        for el in (self.rate, self.pitch):
            setattr(anvil.js.get_dom_node(el), "disabled", not self.can_edit)
        self._draw()

    def _voice(self):
        v = self.cfg.get("voice") or {}
        return float(v.get("rate") or 1), float(v.get("pitch") or 1)

    def _draw(self):
        for key, label, color in GROUPS:
            items = []
            for i, value in enumerate(engine.options(key)):
                items.append({"group": key, "value": value, "color": value if color else "",
                              "label": ("%s %d" % (label, i + 1)) if color else engine.LABELS.get(value, value),
                              "on": self.cfg.get(key) == value, "enabled": self.can_edit})
            getattr(self, "p_" + key).items = items
        rate, pitch = self._voice()
        r, p = anvil.js.get_dom_node(self.rate), anvil.js.get_dom_node(self.pitch)
        setattr(r, "value", str(rate))
        setattr(p, "value", str(pitch))
        anvil.js.get_dom_node(self.rate_out).textContent = "%.2fx" % rate
        anvil.js.get_dom_node(self.pitch_out).textContent = "%.2f" % pitch
        r.setAttribute("aria-label", "Voice speed")
        p.setAttribute("aria-label", "Voice pitch")
        self.face.face = self.cfg
        dirty = self.cfg != self._saved
        self.dirty_label.text = "Unsaved changes" if dirty else ("Saved" if self.can_edit else "Make your own copy to change the face")
        self.save_button.enabled = dirty
        self.reset_button.visible = dirty and self.can_edit

    def _pick(self, group, value, **event_args):
        if not self.can_edit:
            return
        k = state.focus_key()
        self.cfg[group] = value
        self._draw()
        panel = getattr(self, "p_" + group)
        state.refocus(panel, k)

    def voice_input(self, event):
        rate = float(getattr(anvil.js.get_dom_node(self.rate), "value"))
        pitch = float(getattr(anvil.js.get_dom_node(self.pitch), "value"))
        self.cfg["voice"] = {"rate": round(rate, 2), "pitch": round(pitch, 2)}
        self._draw()

    def _hello(self, lang):
        a = self.page.data["agent"]
        line = a.get("greeting_" + lang) or ("Hello! I'm %s." % a["name"] if lang == "en" else "Bonjour! Je suis %s." % a["name"])
        self.face.say(line, lang, bool(getattr(anvil.js.get_dom_node(self.hear), "checked")))

    @handle("hello_en", "click")
    def hello_en_click(self, **event_args):
        self._hello("en")

    @handle("hello_fr", "click")
    def hello_fr_click(self, **event_args):
        self._hello("fr")

    @handle("shuffle_button", "click")
    def shuffle_button_click(self, **event_args):
        voice = self.cfg.get("voice")
        self.cfg = engine.random_face()
        if voice:
            self.cfg["voice"] = voice
        self._draw()

    @handle("reset_button", "click")
    def reset_button_click(self, **event_args):
        self.cfg = dict(self._saved)
        self._draw()

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        self.save_button.enabled = False
        r = anvil.server.call("set_face", self.page.agent_id, self.cfg)
        if not r.get("ok"):
            state.toast(r.get("error"), "error")
            self.save_button.enabled = True
            return
        self._saved = dict(DEFAULTS, **r["face"])
        self.cfg = dict(self._saved)
        self.page.data["agent"]["face"] = r["face"]
        self.page.draw_head()
        state.toast("Face and voice saved", "ok")
        self._draw()
