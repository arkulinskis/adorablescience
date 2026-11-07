from anvil import *

from ._anvil_designer import SourceEditTemplate
from ... import bits, state
from ...lab_config import SOURCE_KINDS


class SourceEdit(SourceEditTemplate):
    """One source row on the writing desk. item = the page's own dict {i, url, title, publisher, kind}: typing
    updates it in place, so the page always has what's on screen. Tells the page through the RepeatingPanel:
    x-changed (the link changed: redraw the meter), x-cite (insert [n]), x-remove."""

    def __init__(self, **properties):
        super().__init__(**properties)
        s = self.item
        n = s["i"] + 1
        bits.text(self.dom_nodes["n"], n)
        self.url_box.text, self.title_box.text, self.pub_box.text = s.get("url"), s.get("title"), s.get("publisher")
        state.maxlength(self.title_box, 200)
        state.maxlength(self.pub_box, 100)
        self.kind_box.items = [("%s %s" % (e, l), k) for k, l, e in SOURCE_KINDS]
        self.kind_box.selected_value = s.get("kind") or "journal"
        self.cite_button.text = "❝ Cite [%d]" % n
        self.cite_button.tooltip = "Insert [%d] where your cursor is" % n
        self.remove_button.tooltip = "Remove this source"
        for box, what in ((self.url_box, "link"), (self.title_box, "title"), (self.pub_box, "publisher"),
                          (self.kind_box, "type")):
            state.set_control_attr(box, "aria-label", "Source %d %s" % (n, what))
        state.set_control_attr(self.url_box, "inputmode", "url")
        state.set_control_attr(self.url_box, "autocomplete", "off")
        state.set_control_attr(self.remove_button, "aria-label", "Remove source %d" % n)

    def focus_url(self):
        node = state.control(self.url_box)
        node.scrollIntoView({"behavior": "smooth", "block": "center"})
        self.url_box.focus()

    @handle("url_box", "change")
    def url_box_change(self, **event_args):
        self.item["url"] = self.url_box.text or ""
        self.parent.raise_event("x-changed")

    @handle("title_box", "change")
    def title_box_change(self, **event_args):
        self.item["title"] = self.title_box.text or ""

    @handle("pub_box", "change")
    def pub_box_change(self, **event_args):
        self.item["publisher"] = self.pub_box.text or ""

    @handle("kind_box", "change")
    def kind_box_change(self, **event_args):
        self.item["kind"] = self.kind_box.selected_value or "other"

    @handle("cite_button", "click")
    def cite_button_click(self, **event_args):
        self.parent.raise_event("x-cite", index=self.item["i"])

    @handle("remove_button", "click")
    def remove_button_click(self, **event_args):
        self.parent.raise_event("x-remove", index=self.item["i"])
