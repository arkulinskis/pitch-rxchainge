"""Business pilots, sold by hand through Addanapp (APP_MAKER money round 2, kit `hand`, 2026-11-27).

The Landing page shows "Start a pilot for your business ($1,500 setup + $300/mo)" only when the App Secret
`sales_link` holds a https link (a Stripe Payment Link or a booking page the owner made). Missing or not https =
hidden, so the app looks exactly as before. No tables, nothing in the studio itself.
"""
import anvil.secrets
import anvil.server


def link():
    try:
        v = str(anvil.secrets.get_secret("sales_link") or "").strip()
    except Exception:
        return None
    return v if v.startswith("https://") and len(v) < 500 and not any(c.isspace() for c in v) else None


@anvil.server.callable
def sales_link():
    """The sales link for the Landing page, or None (hidden). Public on purpose: it reads one App Secret, takes no input."""
    return link()
