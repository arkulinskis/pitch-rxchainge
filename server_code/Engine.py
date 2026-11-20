"""The agent's brain, in plain Python (no AI service, no key): it only ever says what an expert approved.

    lang_of(text)                      "fr" or "en" (a guess from common words and accents)
    tokens(text)                       lower-case words without accents or stop words (English + French)
    best_topic(question, topics)       (topic, score) of the approved topic that fits best, or (None, 0)
    refused(question, refuse_list)     the refused subject the question touches, or ""
    draft(question, sources, tone, lang)  a first answer built from the agent's sources (sentences that fit the
                                       question, in their order) + the titles used; the expert edits and approves it
    keywords_for(question_en, question_fr, answer_en)  a short keyword string for matching
Everything here is pure (no tables) so tools/testing/test_server.py can test it directly.
"""
import re
import unicodedata

STOP = set("""
a an and are as at be but by can could do does for from had has have how i if in into is it its me my of on or our
should so than that the their them then there these they this to was we were what when where which who why will with
would you your about any some get go going want need tell please best good great place places spot spots
le la les un une des du de d l et ou est sont a au aux en dans pour par sur avec ce cet cette ces qui que quoi quel
quelle quels quelles ou comment pourquoi quand je tu il elle on nous vous ils elles mon ma mes ton ta tes son sa ses
notre votre leur leurs me te se y ne pas plus bien tres faire veux voudrais peux peut-on meilleur meilleure meilleurs
meilleures endroit endroits bon bonne bons bonnes lieu lieux s qu c j n m t
""".split())
FR_HINTS = set("le la les une des est sont pour avec dans quel quelle quels quelles ou pourquoi comment je vous nous "
               "meilleur meilleure bonjour merci ce cette qui que du au aux sur".split())
EN_HINTS = set("the is are for with where what which how why you we best hello thanks this that who of to in".split())
GREET = set("hi hello hey bonjour salut allo hola coucou".split())


def strip_accents(s):
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))


def words(text):
    t = strip_accents((text or "").lower()).replace("’", "'")
    return re.findall(r"[a-z0-9]+", t)


def stem(w):
    """A very small stemmer: plural s/x and a few English/French endings, so bagel ~ bagels, cheap ~ cheaper."""
    for end in ("ements", "ement", "ations", "ation", "eries", "erie", "ings", "ing", "ers", "er", "es", "s", "x"):
        if len(w) > len(end) + 3 and w.endswith(end):
            return w[: -len(end)]
    return w


def tokens(text):
    return [stem(w) for w in words(text) if w not in STOP and len(w) > 1]


def lang_of(text):
    raw = (text or "").lower()
    ws = words(text)
    fr = sum(1 for w in ws if w in FR_HINTS) + (2 if re.search(r"[éèêàçùâîôû]", raw) else 0)
    en = sum(1 for w in ws if w in EN_HINTS)
    return "fr" if fr > en else "en"


def is_greeting(text):
    ws = words(text)
    return 0 < len(ws) <= 4 and ws[0] in GREET


def _bag(*parts):
    out = {}
    for weight, text in parts:
        for t in tokens(text):
            out[t] = max(out.get(t, 0), weight)
    return out


def score(question, topic):
    """How well an approved topic fits the question: question words found in the topic's questions and keywords
    count most, words found in the answers a little. Normalised by the question's length (0..~1)."""
    q = set(tokens(question))
    if not q:
        return 0.0
    bag = _bag((1.0, topic.get("question_en", "")), (1.0, topic.get("question_fr", "")),
               (1.0, topic.get("keywords", "")), (0.35, topic.get("answer_en", "")), (0.35, topic.get("answer_fr", "")))
    hit = sum(bag.get(t, 0) for t in q)
    return hit / (len(q) ** 0.85)


def best_topic(question, topics, threshold=0.42):
    best, best_s = None, 0.0
    for t in topics:
        s = score(question, t)
        if s > best_s:
            best, best_s = t, s
    if best is None or best_s < threshold:
        return None, best_s
    return best, best_s


def refused(question, refuse_list):
    q = set(tokens(question))
    for item in refuse_list or []:
        subject = (item or "").strip()
        if subject and q & set(tokens(subject)):
            return subject
    return ""


def sentences(text):
    text = re.sub(r"\s+", " ", text or "").strip()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Ý0-9«\"])", text) if len(s.strip()) > 12]


OPENERS = {
    "en": {"warm": "Happy to help! ", "witty": "Ah, an excellent question. ", "precise": "", "calm": "Here is what I can tell you. "},
    "fr": {"warm": "Avec plaisir! ", "witty": "Ah, excellente question. ", "precise": "", "calm": "Voici ce que je peux vous dire. "},
}


def draft(question, sources, tone="warm", lang="en", limit=3):
    """A first answer from the sources: the sentences that share the most words with the question (in the source's
    order), with an opener in the agent's tone. Sources in the other language are only used if nothing else fits.
    Returns {"text", "used": [source titles], "found": bool}."""
    q = set(tokens(question))
    picked = []
    for pass_lang in (lang, None):
        for si, src in enumerate(sources or []):
            if pass_lang and (src.get("lang") or lang_of(src.get("body", ""))) != pass_lang:
                continue
            for pi, s in enumerate(sentences(src.get("body", ""))):
                hit = len(q & set(tokens(s)))
                if hit:
                    picked.append((hit, si, pi, s, src.get("title", "Source")))
        if picked:
            break
    if not picked:
        empty = {"en": "I don't have anything on this in my sources yet. Add a source, or write the answer yourself.",
                 "fr": "Je n'ai rien là-dessus dans mes sources pour l'instant. Ajoutez une source, ou écrivez la réponse vous-même."}
        return {"text": empty.get(lang, empty["en"]), "used": [], "found": False}
    top = sorted(picked, key=lambda p: (-p[0], p[1], p[2]))[:limit]
    top.sort(key=lambda p: (p[1], p[2]))
    used = []
    for p in top:
        if p[4] not in used:
            used.append(p[4])
    opener = OPENERS.get(lang, OPENERS["en"]).get(tone, "")
    return {"text": opener + " ".join(p[3] for p in top), "used": used, "found": True}


def keywords_for(question_en, question_fr="", answer_en=""):
    seen, out = set(), []
    for t in tokens(question_en) + tokens(question_fr):
        if t not in seen:
            seen.add(t)
            out.append(t)
    return " ".join(out[:14])
