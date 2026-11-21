from anvil import *

from ._anvil_designer import StudyPickTemplate
from ... import bits, state
from ...lab_config import SOURCE_KIND


class StudyPick(StudyPickTemplate):
    """One paper found by "🔎 Find the original study" on the writing desk. item = a server Sources work dict
    {doi, url, title, publisher, kind, year, authors, flag, flag_note} + used. "Use this" raises x-use on the
    RepeatingPanel; the page adds it as a filled source row."""

    def __init__(self, **properties):
        super().__init__(**properties)
        w, d = self.item, self.dom_nodes
        kind = SOURCE_KIND.get(w.get("kind") or "other", SOURCE_KIND["other"])
        name = w.get("title") or w.get("doi") or "Untitled"
        bits.text(d["title"], name)
        parts = ["%s %s" % (kind["emoji"], kind["label"]), w.get("publisher") or "", w.get("authors") or "",
                 "doi:" + (w.get("doi") or "")]
        bits.text(d["meta"], " · ".join([p for p in parts if p]))
        bits.show(d["flag"], bool(w.get("flag_note")))
        bits.text(d["flag"], w.get("flag_note") or "")
        used = bool(w.get("used"))
        self.use_button.text = "✓ Added" if used else "Use this"
        self.use_button.enabled = not used
        state.set_control_attr(self.use_button, "aria-label", ("Added: %s" if used else "Use %s as a source") % name[:90])

    @handle("use_button", "click")
    def use_button_click(self, **event_args):
        self.parent.raise_event("x-use", work=self.item)
