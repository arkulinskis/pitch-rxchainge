from anvil import *

from ._anvil_designer import WhyLineTemplate


class WhyLine(WhyLineTemplate):
    """One fact on a "Why this answer?" receipt. item = {term, value}."""

    def __init__(self, **properties):
        super().__init__(**properties)
