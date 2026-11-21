from anvil import *
import anvil.js

from ._anvil_designer import MessageTemplate
from ... import state

MONTHS_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
T: dict = {
    "en": {"btn": "Why this answer?", "hide": "Hide the details", "topic": "Matched topic", "by": "Approved by",
           "ver": "Answering from", "vnum": "Published version %d", "preview": "Preview: approved, not yet published",
           "src": "Drafted from", "src_none": "Written by the team, then approved", "match": "Match",
           "strength": {"strong": "Strong", "good": "Good", "close": "Close"}, "on": "on the words",
           "rule": "Rule", "rule_v": "“%s” is a subject this agent must not discuss, so it declines",
           "why_none": "Why no answer", "why_none_v": "No approved topic fits closely enough, and nothing is guessed",
           "next": "What happens next", "next_v": "The question is logged for %s to review",
           "next_team": "the team", "never": "It only ever repeats answers an expert approved word for word."},
    "fr": {"btn": "Pourquoi cette réponse?", "hide": "Masquer les détails", "topic": "Sujet reconnu",
           "by": "Approuvé par", "ver": "Répond à partir de", "vnum": "Version publiée %d",
           "preview": "Aperçu : approuvé, pas encore publié", "src": "Rédigé à partir de",
           "src_none": "Rédigé par l'équipe, puis approuvé", "match": "Correspondance",
           "strength": {"strong": "Forte", "good": "Bonne", "close": "Proche"}, "on": "sur les mots",
           "rule": "Règle", "rule_v": "« %s » est un sujet dont cet agent ne doit pas parler : il décline",
           "why_none": "Pourquoi pas de réponse",
           "why_none_v": "Aucun sujet approuvé ne correspond assez, et rien n'est deviné",
           "next": "Et ensuite", "next_v": "La question est transmise à %s pour examen", "next_team": "l'équipe",
           "never": "Il ne répète que des réponses approuvées mot pour mot par un expert."},
}


def _date(iso, lang):
    if not iso:
        return ""
    if lang == "fr":
        y, m, d = iso[:10].split("-")
        return "%d %s %s" % (int(d), MONTHS_FR[int(m) - 1], y)
    return "%s %s" % (state.short_date(iso), iso[:4])


def receipt(why, lang):
    """The facts behind one reply, as [{term, value}] in the reply's language."""
    fr = lang == "fr"
    L: dict = T["fr" if fr else "en"]
    k = why.get("kind")
    version = why.get("version") or 0
    ver = L["vnum"] % version if version else L["preview"]
    if k == "answer":
        q = why.get("question_" + lang) or why.get("question_en") or why.get("question_fr") or ""
        by = why.get("approved_by") or ""
        if by and why.get("approved_at"):
            by += ", " + _date(why["approved_at"], lang)
        used = why.get("used") or []
        match = L["strength"].get(why.get("strength") or "", "")
        if why.get("words"):
            match += (" %s : %s" if fr else " %s: %s") % (L["on"], ", ".join(why["words"]))
        lines = [(L["topic"], ("« %s »" if fr else "“%s”") % q), (L["by"], by), (L["ver"], ver),
                 (L["src"], ", ".join(used) if used else L["src_none"]), (L["match"], match)]
    elif k == "refused":
        lines = [(L["rule"], L["rule_v"] % (why.get("subject") or "")), (L["ver"], ver)]
    elif k == "unknown":
        lines = [(L["why_none"], L["why_none_v"]), (L["next"], L["next_v"] % (why.get("expert") or L["next_team"])),
                 (L["ver"], ver)]
    else:
        return []
    return [{"term": t, "value": v} for t, v in lines if v]


class Message(MessageTemplate):
    """One line of a conversation. item = {who: "agent" | "me", text, by (the "Approved by ..." line), kind,
    why (the server's receipt facts, or None), lang}. Agent replies with a receipt get a "Why this answer?" toggle."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        self.bubble.classes["me"] = it["who"] == "me"
        self.bubble.classes["agent"] = it["who"] != "me"
        self.bubble.classes["soft"] = it.get("kind") in ("unknown", "refused", "error")
        self.lang = it.get("lang") or "en"
        lines = receipt(it.get("why") or {}, self.lang) if it.get("why") else []
        if lines:
            lines.append({"term": "", "value": T["fr" if self.lang == "fr" else "en"]["never"]})
        self.why_panel.items = lines
        self.why_btn.visible = bool(lines)
        self._open(bool(it.get("why_open")))

    def _open(self, on):
        self.why_box.visible = on
        L: dict = T["fr" if self.lang == "fr" else "en"]
        anvil.js.get_dom_node(self.why_text).textContent = L["hide"] if on else L["btn"]
        anvil.js.get_dom_node(self.why_btn).setAttribute("aria-expanded", "true" if on else "false")
        self.why_btn.classes["on"] = on

    def why_click(self, event):
        on = not self.why_box.visible
        self.item["why_open"] = on  # the chat redraws its list on every message: keep the receipt open
        self._open(on)
