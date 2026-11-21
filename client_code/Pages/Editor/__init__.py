from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import EditorTemplate
from ... import api, bits, router, state
from ...Dialogs.NoSources import NoSources
from ...lab_config import (BODY_MAX, CATEGORIES, CAVEAT_MAX, COVERS, DEK_MAX, EVIDENCE, SIZE_MAX, SOURCES_MAX,
                           STATUSES, STUDY_SUBJECTS, TITLE_MAX, cited_numbers, needs_caveat)

BLANK_SOURCE = {"url": "", "title": "", "publisher": "", "kind": "journal"}

FORMATS = {
    # key: (before, after, placeholder, starts a line)
    "bold": ("**", "**", "important words", False),
    "italic": ("*", "*", "emphasis", False),
    "h": ("## ", "", "A new section", True),
    "ul": ("- ", "", "a point", True),
    "quote": ("> ", "", "A quote from a scientist", True),
    "note": ("!! ", "", "A fun fact or important caveat", True),
    "link": ("[", "](https://)", "link text", False),
}

_js: dict = {}


def _sel(ta):
    """The selected text of a textarea, by JavaScript string offsets (so emoji don't confuse the positions)."""
    if "sel" not in _js:
        _js["sel"] = window.Function("ta", "return ta.value.substring(ta.selectionStart, ta.selectionEnd);")
        _js["before"] = window.Function("ta", "s", "return ta.value.charAt(s - 1);")
    return _js["sel"](ta) or ""


class Editor(EditorTemplate):
    """The writing desk (#write, #write/<no>). Writers draft, cite sources and submit for review. Sources are
    encouraged everywhere: a live citation meter, one-click [n] citations, "✨ Fill from DOI" on each source row
    (Items/SourceEdit), "🔎 Find the original study" (Crossref, Items/StudyPick) and a "no sources?" dialog on submit.
    The "🔍 Study snapshot" panel says who or what was studied, how many, and a "Hold your horses" caveat."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.no = None
        self.status = "draft"
        self.review_note = ""
        self.cover = ""
        self.confirmed_live_edit = False
        self.sources: list = [dict(BLANK_SOURCE)]
        state.maxlength(self.title_box, TITLE_MAX)
        state.maxlength(self.dek_box, DEK_MAX)
        state.maxlength(self.body_box, BODY_MAX)
        self.cat_box.items = [("%s %s" % (e, l), k) for k, l, e, t in CATEGORIES]
        self.ev_box.items = [("%s %s" % (e, l), k) for k, l, e in EVIDENCE]
        self.subject_box.items = [("%s %s" % (subj[2], subj[1]), subj[0]) for subj in STUDY_SUBJECTS]
        state.maxlength(self.size_box, SIZE_MAX)
        state.maxlength(self.caveat_box, CAVEAT_MAX)
        state.maxlength(self.find_box, 200)
        state.set_control_attr(self.find_box, "aria-label", "Words to find the original study")
        self.picks: list = []
        self.study_panel.add_event_handler("x-use", self._use_study)
        state.set_control_attr(self.body_box, "aria-label", "Article text")
        self.source_panel.add_event_handler("x-changed", self._sources_changed)
        self.source_panel.add_event_handler("x-cite", self._cite)
        self.source_panel.add_event_handler("x-remove", self._remove_source)
        self.cover_panel.add_event_handler("x-pick", self._pick_cover)
        if args:
            d = api.load("get_article_for_edit", args[0])
            self.no = d["no"]
            self.status = d["status"]
            self.review_note = d["review_note"]
            self.title_box.text, self.dek_box.text, self.body_box.text = d["title"], d["dek"], d["body"]
            self.cat_box.selected_value = d["category"] or None
            self.ev_box.selected_value = d["evidence"] or None
            self.cover = d["cover"]
            self.sources = d["sources"] or [dict(BLANK_SOURCE)]
            self.subject_box.selected_value = d.get("study_subject") or None
            self.size_box.text, self.caveat_box.text = d.get("study_size") or "", d.get("caveat") or ""
        self.page_title = "Editing #%03d" % self.no if self.no else "Write a discovery"
        self._draw()

    # ---------------------------------------------------------------- drawing
    def _draw(self):
        d = self.dom_nodes
        bits.text(d["heading"], ("✍️ Editing specimen #%03d" % self.no) if self.no else "✍️ Write a new discovery")
        if self.no:
            bits.status_pill(d["status_pill"], self.status)
        bits.show(d["live_banner"], self.status == "published")
        bits.show(d["pending_banner"], self.status == "pending")
        bits.show(d["note_banner"], bool(self.review_note) and self.status in ("rejected", "draft"))
        bits.text(d["note_text"], self.review_note)
        self.submit_button.text = ("🔬 Resubmit for review" if self.status in ("rejected", "published")
                                   else "🔬 Submit for review")
        self._counts()
        self._draw_sources()
        self._draw_covers()

    def _counts(self):
        bits.text(self.dom_nodes["title_count"], "%d/%d" % (len(self.title_box.text or ""), TITLE_MAX))
        bits.text(self.dom_nodes["dek_count"], "%d/%d" % (len(self.dek_box.text or ""), DEK_MAX))
        bits.text(self.dom_nodes["size_count"], "%d/%d" % (len(self.size_box.text or ""), SIZE_MAX))
        bits.text(self.dom_nodes["caveat_count"], "%d/%d" % (len(self.caveat_box.text or ""), CAVEAT_MAX))
        self._caveat_hint()

    def _caveat_hint(self):
        """Animals, cells, models, preprints and speculation: nudge for a "Hold your horses" line until there is one."""
        need = needs_caveat(self.subject_box.selected_value, self.ev_box.selected_value)
        bits.show(self.dom_nodes["caveat_hint"], need and not (self.caveat_box.text or "").strip())

    def _draw_sources(self):
        for i, s in enumerate(self.sources):
            s["i"] = i
        self.source_panel.items = self.sources
        self._meter()

    def _draw_covers(self):
        key = state.focus_key()
        self.cover_panel.items = [{"value": e, "on": e == self.cover, "label": "Cover " + e} for e in COVERS]
        state.refocus(self.cover_panel, key)

    def _live_counts(self):
        """(sources with a link, how many of them are cited in the text) - from what's on screen."""
        n = sum(1 for s in self.sources if (s.get("url") or "").strip())
        cited = [x for x in cited_numbers(self.body_box.text or "") if 1 <= x <= n]
        return n, len(cited)

    def _meter(self):
        n, cited = self._live_counts()
        self.meter.show(n, cited)

    # ---------------------------------------------------------------- typing
    @handle("title_box", "change")
    def title_box_change(self, **event_args):
        self._counts()

    @handle("dek_box", "change")
    def dek_box_change(self, **event_args):
        self._counts()

    @handle("body_box", "change")
    def body_box_change(self, **event_args):
        self._meter()

    @handle("subject_box", "change")
    def subject_box_change(self, **event_args):
        self._caveat_hint()

    @handle("ev_box", "change")
    def ev_box_change(self, **event_args):
        self._caveat_hint()

    @handle("size_box", "change")
    def size_box_change(self, **event_args):
        self._counts()

    @handle("caveat_box", "change")
    def caveat_box_change(self, **event_args):
        self._counts()

    def _sources_changed(self, **event_args):
        self._meter()

    # ---------------------------------------------------------------- sources
    @handle("add_source_button", "click")
    def add_source_button_click(self, **event_args):
        self._add_source()

    def _add_source(self):
        if len(self.sources) >= SOURCES_MAX:
            state.toast("That's the maximum of %d sources. Impressive! 📚" % SOURCES_MAX)
            return
        self.sources.append(dict(BLANK_SOURCE))
        self._draw_sources()
        rows = self.source_panel.get_components()
        if rows:
            getattr(rows[-1], "focus_url")()

    def _remove_source(self, index, **event_args):
        if 0 <= index < len(self.sources):
            self.sources.pop(index)
        if not self.sources:
            self.sources = [dict(BLANK_SOURCE)]
        self._draw_sources()
        state.focus(self.add_source_button)

    def _cite(self, index, **event_args):
        self._insert("[%d]" % (index + 1))

    # ---------------------------------------------------------------- find the original study (Crossref)
    @handle("find_button", "click")
    def find_button_click(self, **event_args):
        self._find()

    @handle("find_box", "pressed_enter")
    def find_box_pressed_enter(self, **event_args):
        self._find()

    def _find_msg(self, text):
        bits.show(self.dom_nodes["find_msg"], bool(text))
        bits.text(self.dom_nodes["find_msg"], text)

    def _find(self):
        words = " ".join((self.find_box.text or "").split())
        if len(words.replace(" ", "")) < 8:
            self._find_msg("Type a few more words: the paper's title, a lead author or the journal. 🔎")
            self.find_box.focus()
            return
        self.find_button.enabled, self.find_button.text = False, "Sniffing…"
        self._find_msg("Bea is sniffing through Crossref…")
        try:
            r = state.call("find_study", words)
        finally:
            self.find_button.enabled, self.find_button.text = True, "🔎 Find it"
        if r is None:
            self._find_msg("")
            return
        if r.get("missing"):
            self.picks = []
            self.study_panel.items = []
            self._find_msg("Couldn't reach Crossref just now. Paste the study's link by hand: it saves fine.")
            state.toast("Couldn't reach Crossref just now. Paste the link by hand and carry on 🧪", "error")
            return
        self.picks = [dict(w, used=False) for w in r["items"]]
        self.study_panel.items = self.picks
        self._find_msg("Pick the paper your story is about:" if self.picks
                       else "No matches. Try the paper's exact title, or the lead author's surname plus a key word.")

    def _use_study(self, work, **event_args):
        """Add a found paper as a source: into the first empty row, else a new one."""
        src = {"url": work["url"], "title": work["title"], "publisher": work["publisher"],
               "kind": work["kind"] if work["kind"] != "other" else "journal",
               "flag": work.get("flag") or "", "flag_note": work.get("flag_note") or "", "flag_doi": work["doi"]}
        index = -1
        for i, row in enumerate(self.sources):
            if not any((row.get(key) or "").strip() for key in ("url", "title", "publisher")):
                index = i
                break
        if index < 0:
            if len(self.sources) >= SOURCES_MAX:
                state.toast("That's the maximum of %d sources. Impressive! 📚" % SOURCES_MAX)
                return
            self.sources.append(dict(BLANK_SOURCE))
            index = len(self.sources) - 1
        self.sources[index].update(src)
        self._draw_sources()
        work["used"] = True
        self.study_panel.items = self.picks
        n = index + 1
        if work.get("flag") == "retracted":
            state.toast("Added as source #%d, but it was retracted. Only cite it if your story is about that. ⚠️" % n,
                        "error")
        else:
            state.toast("Added as source #%d. Type [%d] in your text to cite it 📎" % (n, n), "ok")

    # ---------------------------------------------------------------- cover critter
    def _pick_cover(self, value, **event_args):
        self.cover = "" if self.cover == value else value
        self._draw_covers()

    # ---------------------------------------------------------------- write / preview, formatting
    def mode_click(self, event):
        self._mode(event.currentTarget.getAttribute("data-mode"))

    def _mode(self, mode):
        d = self.dom_nodes
        d["mode_write"].classList.toggle("on", mode == "write")
        d["mode_preview"].classList.toggle("on", mode == "preview")
        d["fmts"].classList.toggle("as-dim", mode == "preview")
        if mode == "preview":
            html = state.call("preview_body", self.body_box.text or "", self._clean_sources())
            d["preview"].innerHTML = html or '<p class="as-muted">Nothing to preview yet. Write something delightful!</p>'
            self.body_box.visible = False
            bits.show(d["preview"], True)
        else:
            self.body_box.visible = True
            bits.show(d["preview"], False)

    def fmt_click(self, event):
        before, after, placeholder, line_start = FORMATS[event.currentTarget.getAttribute("data-fmt")]
        ta = state.control(self.body_box)
        self._mode("write")
        start, end = ta.selectionStart, ta.selectionEnd
        sel = _sel(ta) or placeholder
        prefix = "\n" if line_start and start > 0 and _js["before"](ta, start) != "\n" else ""
        ta.setRangeText(prefix + before + sel + after, start, end, "end")
        inner = start + len(prefix + before)
        ta.setSelectionRange(inner, ta.selectionEnd - len(after))  # the inner words stay selected to type over
        ta.focus()
        self._sync_body(ta)

    def _insert(self, text):
        ta = state.control(self.body_box)
        self._mode("write")
        end = ta.selectionEnd
        ta.setRangeText(text, end, end, "end")
        ta.focus()
        self._sync_body(ta)

    def _sync_body(self, ta):
        self.body_box.text = ta.value
        ta.dispatchEvent(anvil.js.new(window.Event, "input", {"bubbles": True}))
        self._meter()

    # ---------------------------------------------------------------- saving
    def _clean_sources(self):
        return [{k: (s.get(k) or "").strip() if k != "kind" else (s.get("kind") or "other")
                 for k in ("url", "title", "publisher", "kind")} for s in self.sources]

    def _fields(self):
        return {"title": self.title_box.text or "", "dek": self.dek_box.text or "", "body": self.body_box.text or "",
                "category": self.cat_box.selected_value or "", "evidence": self.ev_box.selected_value or "",
                "cover": self.cover, "study_subject": self.subject_box.selected_value or "",
                "study_size": self.size_box.text or "", "caveat": self.caveat_box.text or ""}

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        self._save_or_submit(False)

    @handle("submit_button", "click")
    def submit_button_click(self, **event_args):
        self._save_or_submit(True)

    def _save_or_submit(self, submit):
        if self.status == "published" and not self.confirmed_live_edit:
            if not confirm("This article is published. Saving or resubmitting changes hides it from readers until a "
                           "Lab Director approves the new version.", title="Take it off the front page?",
                           buttons=[("Cancel", False), ("Yes, continue", True)], role="app-dialog"):
                return
            self.confirmed_live_edit = True
        self._save(submit)

    def _save(self, submit, acknowledge_unsourced=False):
        button = self.submit_button if submit else self.save_button
        button.enabled = False
        try:
            r = state.call("save_article", self.no, self._fields(), self._clean_sources(),
                           submit=submit, acknowledge_unsourced=acknowledge_unsourced)
        finally:
            button.enabled = True
        if r is None:
            return
        if r.get("needs_ack"):
            choice = alert(NoSources(), buttons=[], role="app-dialog", dismissible=True)
            if choice == "submit":
                self._save(True, acknowledge_unsourced=True)
            elif choice == "add":
                self._add_source()
            return
        self.no, self.status = r["no"], r["status"]
        state.set_me(state.call("get_me"))
        if submit:
            state.toast("Submitted! A Lab Director will put it under the microscope 🔬", "ok")
            router.go("lab")
        else:
            router.replace("write", self.no)
            state.toast("Saved to your Petri dish 🧫", "ok")
            if self.status != "draft":
                self.review_note = ""
            self.page_title = "Editing #%03d" % self.no
            self._draw()
            router.refresh_shell()
