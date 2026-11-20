"""Python side of the face engine (theme/assets/as-face.js). Components/Face is the usual way in; this module is for
the few places that need the engine directly (the Look tab's option lists, speech support).

    face.svg(cfg)            static SVG string of a face
    face.mount(el, cfg)      a live face (blinks, glances, talks) in a DOM node; .say(text, lang, speak) .think(on)
                             .set(cfg) .stop() .destroy()
    face.options(key)        the choices the Look tab offers for one part (list of strings)
    face.speech_ok()         True if this browser can read answers aloud
    face.NULL                a typed "nothing" for attributes that will later hold an engine object
"""
from anvil.js import window

NULL = window.Function("return null")()

LABELS = {
    "short": "Short", "bob": "Bob", "curly": "Curly", "bun": "Bun", "long": "Long", "wavy": "Wavy", "shaved": "Shaved",
    "soft": "Soft", "straight": "Straight", "arched": "Arched", "none": "None", "round": "Round", "square": "Square",
    "earrings": "Earrings", "beret": "Beret", "headband": "Headband", "scarf": "Scarf",
}


def _engine():
    return window.AS


def svg(cfg):
    return _engine().faceSVG(cfg or {})


def mount(el, cfg):
    return _engine().Face(el, cfg or {}, {"live": True})


def options(key):
    return [str(x) for x in _engine().OPTIONS[key]]


def speech_ok():
    return bool(_engine().speechOK())


def random_face():
    """A random combination (the Look tab's Shuffle)."""
    rnd = window.Math.random
    out = {}
    for key in ("skin", "hair", "hairStyle", "eyes", "brows", "glasses", "accessory", "shirt", "bg"):
        opts = options(key)
        out[key] = opts[int(rnd() * len(opts)) % len(opts)]
    if rnd() < 0.6:
        out["glasses"] = "none"
    if rnd() < 0.5:
        out["accessory"] = "none"
    return out
