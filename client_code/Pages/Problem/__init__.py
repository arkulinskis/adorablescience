from anvil import *

from ._anvil_designer import ProblemTemplate
from ... import bits


class Problem(ProblemTemplate):
    """The friendly "Oops" page: router.show() opens it when a page can't load (an article that isn't published,
    a writer who doesn't exist ...) or for the review desk when someone isn't a Lab Director.
    cta = (link text, address); the default goes back to the front page."""

    def __init__(self, title="", message="", mood="sad", cta=None, args=(), **properties):
        super().__init__(**properties)
        self.page_title = "Oops"
        d = self.dom_nodes
        if title:
            bits.text(d["title"], title)
        bits.text(d["message"], message)
        self.mascot.mood = mood
        if cta:
            bits.text(d["cta"], cta[0])
            d["cta"].setAttribute("href", cta[1])
            d["cta"].className = "as-btn as-btn-primary"
