from anvil import *

from ._anvil_designer import SourceEditTemplate
from ... import bits, state
from ...lab_config import SOURCE_KIND, SOURCE_KINDS, doi_of


class SourceEdit(SourceEditTemplate):
    """One source row on the writing desk. item = the page's own dict {i, url, title, publisher, kind[, flag,
    flag_note, flag_doi]}: typing updates it in place, so the page always has what's on screen. Tells the page through
    the RepeatingPanel: x-changed (the link changed: redraw the meter), x-cite (insert [n]), x-remove.
    A link holding a DOI shows "✨ Fill from DOI" (server Sources.lookup_doi, Crossref): it fills the title, journal and
    kind, normalises the link to https://doi.org/..., and shows a red note when the paper was retracted."""

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
        state.set_control_attr(self.fill_button, "aria-label", "Fill source %d from its DOI" % n)
        self._doi_ui()

    def focus_url(self):
        node = state.control(self.url_box)
        node.scrollIntoView({"behavior": "smooth", "block": "center"})
        self.url_box.focus()

    def _doi_ui(self):
        """Show the fill button only when the link holds a DOI, and the Crossref note for that same DOI."""
        doi = doi_of(self.url_box.text or "")
        bits.show(self.dom_nodes["doi_row"], bool(doi))
        if self.item.get("flag_doi") and doi.lower() != (self.item.get("flag_doi") or "").lower():
            self.item["flag"], self.item["flag_note"], self.item["flag_doi"] = "", "", ""  # a different paper now
        note, flag = self.item.get("flag_note") or "", self.item.get("flag") or ""
        node = self.dom_nodes["flag"]
        bits.show(node, bool(note))
        bits.text(node, note)
        node.className = "as-src-flag" + (" as-src-flag-soft" if flag == "corrected" else "")

    @handle("url_box", "change")
    def url_box_change(self, **event_args):
        self.item["url"] = self.url_box.text or ""
        self._doi_ui()
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

    @handle("fill_button", "click")
    def fill_button_click(self, **event_args):
        button = self.fill_button
        button.enabled, button.text = False, "🔎 Looking it up…"
        try:
            r = state.call("lookup_doi", self.url_box.text or "")
        finally:
            button.enabled, button.text = True, "✨ Fill from DOI"
        if r is None:
            return
        if r.get("missing"):
            if r.get("not_found"):
                state.toast("Crossref doesn't know that DOI. Check it for typos, or fill in the fields by hand.", "error")
            elif r.get("no_doi"):
                state.toast("That link has no DOI in it. Paste a https://doi.org/… link, or fill in the fields by hand.")
            else:
                state.toast("Couldn't reach Crossref just now. Fill in the title and publisher by hand: it saves fine. 🧪",
                            "error")
            return
        s = self.item
        s["url"] = r["url"] or s.get("url") or ""
        s["title"] = r["title"] or s.get("title") or ""
        s["publisher"] = r["publisher"] or s.get("publisher") or ""
        if r["kind"] in SOURCE_KIND and r["kind"] != "other":
            s["kind"] = r["kind"]
        s["flag"], s["flag_note"], s["flag_doi"] = r["flag"], r["flag_note"], r["doi"]
        self.url_box.text, self.title_box.text, self.pub_box.text = s["url"], s["title"], s["publisher"]
        self.kind_box.selected_value = s.get("kind") or "journal"
        self._doi_ui()
        self.parent.raise_event("x-changed")
        if r["flag"] == "retracted":
            state.toast("Heads up: this paper was retracted. ⚠️", "error")
        else:
            state.toast("Filled from Crossref ✨ Check it's the study you read.", "ok")

    @handle("cite_button", "click")
    def cite_button_click(self, **event_args):
        self.parent.raise_event("x-cite", index=self.item["i"])

    @handle("remove_button", "click")
    def remove_button_click(self, **event_args):
        self.parent.raise_event("x-remove", index=self.item["i"])
