# page_editor — the writing desk (#write and #write/<no>). Writers draft, cite sources, and submit
# for review. Sources are encouraged everywhere: a live citation meter, one-click [n] citations,
# and a "are you sure?" dialog when submitting without any.
import anvil.js
from anvil.js import window

from . import api
from . import as_ui as ui
from . import lab_config as C
from .as_ui import esc

BLANK_SOURCE = {"url": "", "title": "", "publisher": "", "kind": "journal"}

# JS helper: the selected text of a textarea (JS string offsets, so emoji don't confuse it).
_selected_text = None


def selected_text(ta):
    global _selected_text
    if _selected_text is None:
        _selected_text = window.Function("ta", "return ta.value.substring(ta.selectionStart, ta.selectionEnd);")
    return _selected_text(ta) or ""


FORMATS = {
    # key: (button label, title, before, after, placeholder, line_start)
    "bold": ("<b>B</b>", "Bold", "**", "**", "important words", False),
    "italic": ("<i>I</i>", "Italic", "*", "*", "emphasis", False),
    "h": ("H", "Section heading", "## ", "", "A new section", True),
    "ul": ("•", "Bullet list", "- ", "", "a point", True),
    "quote": ("❝", "Quote", "> ", "", "A quote from a scientist", True),
    "note": ("🧪", "Lab note callout", "!! ", "", "A fun fact or important caveat", True),
    "link": ("🔗", "Link", "[", "](https://)", "link text", False),
}


class EditorPage(ui.Page):
    nav = "write"
    needs = "user"
    loading_text = "Warming up the Bunsen burner…"

    def __init__(self, app, arg=None):
        super().__init__(app, arg)
        self.no = None
        self.status = "draft"
        self.review_note = ""
        self.f = {"title": "", "dek": "", "body": "", "category": "", "evidence": "", "cover": ""}
        self.sources = [dict(BLANK_SOURCE)]
        self.confirmed_live_edit = False

    @property
    def title(self):
        return "Editing #%03d" % self.no if self.no else "Write a discovery"

    def load(self):
        if not self.arg:
            return
        d = api.load("get_article_for_edit", self.arg)
        self.no = d["no"]
        self.status = d["status"]
        self.review_note = d["review_note"]
        for k in self.f:
            self.f[k] = d.get(k) or ""
        self.sources = d["sources"] or [dict(BLANK_SOURCE)]

    # ---------- HTML ----------

    def source_rows(self):
        rows = []
        for i, s in enumerate(self.sources):
            kinds = ui.opts([(k, "%s %s" % (e, l)) for k, l, e in C.SOURCE_KINDS], s.get("kind") or "journal")
            rows.append(f"""<div class="as-src" data-idx="{i}">
  <span class="as-src-n" title="Cite this as [{i + 1}]">{i + 1}</span>
  <div class="as-src-fields">
    <input type="url" name="src_url_{i}" value="{esc(s.get('url'))}" placeholder="https://doi.org/…  (link to the study, dataset or page)" inputmode="url" autocomplete="off">
    <div class="as-src-row2">
      <input type="text" name="src_title_{i}" value="{esc(s.get('title'))}" placeholder="Title (e.g. the paper's name)" maxlength="200">
      <input type="text" name="src_pub_{i}" value="{esc(s.get('publisher'))}" placeholder="Publisher (Nature, NASA…)" maxlength="100">
      <select name="src_kind_{i}" aria-label="Type of source">{kinds}</select>
    </div>
  </div>
  <div class="as-src-tools">
    <button type="button" class="as-btn as-btn-soft as-btn-sm" data-action="cite" data-arg="{i}" title="Insert [{i + 1}] where your cursor is">❝ Cite [{i + 1}]</button>
    <button type="button" class="as-iconbtn" data-action="remove-source" data-arg="{i}" title="Remove this source" aria-label="Remove source {i + 1}">✕</button>
  </div>
</div>""")
        return "".join(rows)

    def live_counts(self):
        """(sources with a link, how many of them are cited in the text) — from what's on screen."""
        n = sum(1 for s in self.sources if (s.get("url") or "").strip())
        cited = [x for x in C.cited_numbers(self.f["body"]) if 1 <= x <= n]
        return n, len(cited)

    def html(self):
        f = self.f
        n, cited = self.live_counts()
        banners = []
        if self.status == "published":
            banners.append('<div class="as-banner as-banner-published">🚀 <span><b>This article is live.</b> '
                           'Saving or submitting changes takes it off the front page until a Lab Director approves it again.</span></div>')
        elif self.status == "pending":
            banners.append('<div class="as-banner as-banner-pending">🔬 <span><b>Under the microscope.</b> '
                           'It’s waiting for review. Saving as a draft withdraws it from the queue.</span></div>')
        if self.review_note and self.status in ("rejected", "draft"):
            banners.append('<div class="as-reviewnote"><b>🧪 Reviewer’s note:</b> %s</div>' % esc(self.review_note))

        tools = "".join('<button type="button" class="as-fmt" data-action="fmt" data-arg="%s" title="%s">%s</button>'
                        % (k, v[1], v[0]) for k, v in FORMATS.items())
        cats = ui.opts([(k, "%s %s" % (e, l)) for k, l, e, t in C.CATEGORIES], f["category"], "Pick a field…")
        evs = ui.opts([(k, "%s %s" % (e, l)) for k, l, e in C.EVIDENCE], f["evidence"], "How solid is the science?")
        covers = "".join('<button type="button" class="as-cover%s" data-action="cover" data-arg="%s" aria-label="Cover %s">%s</button>'
                         % (" as-cover-on" if e == f["cover"] else "", e, e, e) for e in C.COVERS)
        status = ui.status_pill(self.status) if self.no else '<span class="as-status as-status-draft">🧫 New draft</span>'
        head = ui.page_head("✍️ Writing desk",
                            ("Editing specimen #%03d" % self.no) if self.no else "Write a new discovery",
                            "Write it warmly, check it carefully, and link where every fact came from.",
                            status)
        meter = ui.meter(n, cited)
        rows = self.source_rows()
        tl, dl = len(f["title"]), len(f["dek"])
        submit_label = "🔬 Resubmit for review" if self.status in ("rejected", "published") else "🔬 Submit for review"
        submit_btn = ui.btn(submit_label, "submit", kind="primary block")
        save_btn = ui.btn("🧫 Save draft", "save", kind="soft block")
        banners = "".join(banners)
        return f"""<div class="as-crumbs"><a href="#lab">← My lab</a></div>
{head}
{banners}
<div class="as-editor">
  <div class="as-editor-main">
    <label class="as-field"><span class="as-field-label">Headline <i data-count="title">{tl}/{C.TITLE_MAX}</i></span>
      <input type="text" class="as-input-title" name="title" maxlength="{C.TITLE_MAX}" value="{esc(f['title'])}" placeholder="Tiny tardigrades survive the impossible"></label>
    <label class="as-field"><span class="as-field-label">One-line summary <i data-count="dek">{dl}/{C.DEK_MAX}</i></span>
      <textarea name="dek" rows="2" maxlength="{C.DEK_MAX}" placeholder="What did scientists find, and why is it delightful? This shows on the front page.">{esc(f['dek'])}</textarea></label>

    <div class="as-field">
      <div class="as-bodybar">
        <div class="as-tabs2"><button type="button" class="as-tab2 as-tab2-on" data-action="mode" data-arg="write">✏️ Write</button><button type="button" class="as-tab2" data-action="mode" data-arg="preview">👀 Preview</button></div>
        <div class="as-fmts" data-ref="fmts">{tools}</div>
      </div>
      <textarea name="body" class="as-body" rows="18" placeholder="Start with the discovery. Who found it, how, and why it matters. Cite sources like this [1].">{esc(f['body'])}</textarea>
      <div class="as-prose as-preview" data-ref="preview" hidden></div>
      <details class="as-help"><summary>Formatting cheat-sheet</summary>
        <code>## Heading</code> · <code>**bold**</code> · <code>*italic*</code> · <code>- bullet</code> · <code>1. numbered</code> ·
        <code>&gt; quote</code> · <code>!! lab note</code> · <code>[text](https://link)</code> · <code>[1]</code> cites source 1</details>
    </div>

    <section class="as-sources" id="sources-editor">
      <div class="as-sources-head">
        <h2>📚 Sources <span class="as-pill-soft">the secret ingredient</span></h2>
        <p>Link the <b>original</b> study, dataset or expert page, not only news coverage of it. A DOI link
        (https://doi.org/…) is perfect. Well-sourced articles are much more likely to be approved, and readers trust them more.</p>
      </div>
      <div data-ref="sources">{rows}</div>
      <button type="button" class="as-btn as-btn-dashed" data-action="add-source">＋ Add another source</button>
    </section>
  </div>

  <aside class="as-editor-side">
    <div class="as-panel"><h4>Citation meter</h4><div data-ref="meter">{meter}</div></div>
    <div class="as-panel">
      <label class="as-field"><span class="as-field-label">Field</span><select name="category">{cats}</select></label>
      <label class="as-field"><span class="as-field-label">Evidence level</span><select name="evidence">{evs}</select></label>
      <div class="as-field"><span class="as-field-label">Cover critter</span><div class="as-covers">{covers}</div></div>
    </div>
    <div class="as-panel as-panel-actions">
      {submit_btn}
      {save_btn}
      <p class="as-muted as-small">Nothing is published until a Lab Director reviews and approves it.</p>
    </div>
    <details class="as-panel as-guide" open><summary><h4>🥼 Lab style guide</h4></summary>
      <ul>
        <li><b>Cute is great, misleading is not.</b> Don't exaggerate what was found.</li>
        <li><b>“In mice” matters.</b> Say who or what was studied, and how many.</li>
        <li><b>Say how sure scientists are.</b> That's what the evidence level is for.</li>
        <li><b>Credit the researchers</b> and link their work.</li>
      </ul>
    </details>
  </aside>
</div>"""

    def mounted(self):
        if not self.no:
            el = self.q('[name="title"]')
            if el is not None:
                el.focus()

    # ---------- reading the form ----------

    def collect(self):
        for k in ("title", "dek", "body", "category", "evidence"):
            el = self.q('[name="%s"]' % k)
            if el is not None:
                self.f[k] = el.value or ""
        out = []
        for i in range(len(self.sources)):
            out.append({
                "url": self.val("src_url_%d" % i).strip(),
                "title": self.val("src_title_%d" % i).strip(),
                "publisher": self.val("src_pub_%d" % i).strip(),
                "kind": self.val("src_kind_%d" % i) or "other",
            })
        self.sources = out

    def update_meter(self):
        box = self.q('[data-ref="meter"]')
        if box is not None:
            n, cited = self.live_counts()
            box.innerHTML = ui.meter(n, cited)

    def redraw_sources(self):
        box = self.q('[data-ref="sources"]')
        if box is not None:
            box.innerHTML = self.source_rows()
        self.update_meter()

    def on_input(self, el, ev):
        name = el.getAttribute("name") or ""
        if name in ("title", "dek"):
            counter = self.q('[data-count="%s"]' % name)
            limit = C.TITLE_MAX if name == "title" else C.DEK_MAX
            if counter is not None:
                counter.textContent = "%d/%d" % (len(el.value or ""), limit)
        if name == "body" or name.startswith("src_url_"):
            self.collect()
            self.update_meter()

    # ---------- actions ----------

    def on_action(self, action, arg, el, ev):
        if action == "add-source" or action == "add-source-modal":
            ui.close_modal()
            self.collect()
            if len(self.sources) >= C.SOURCES_MAX:
                ui.toast("That's the maximum of %d sources. Impressive! 📚" % C.SOURCES_MAX, "info")
                return
            self.sources.append(dict(BLANK_SOURCE))
            self.redraw_sources()
            new = self.q('[name="src_url_%d"]' % (len(self.sources) - 1))
            if new is not None:
                new.scrollIntoView({"behavior": "smooth", "block": "center"})
                new.focus()
        elif action == "remove-source":
            self.collect()
            i = int(arg)
            if 0 <= i < len(self.sources):
                self.sources.pop(i)
            if not self.sources:
                self.sources = [dict(BLANK_SOURCE)]
            self.redraw_sources()
        elif action == "cite":
            self.insert_at_cursor("[%d]" % (int(arg) + 1))
        elif action == "fmt":
            self.apply_format(arg)
        elif action == "cover":
            self.f["cover"] = "" if self.f["cover"] == arg else arg
            for b in self.qa(".as-cover"):
                b.classList.toggle("as-cover-on", b.getAttribute("data-arg") == self.f["cover"])
        elif action == "mode":
            self.set_mode(arg)
        elif action in ("save", "submit"):
            if self.status == "published" and not self.confirmed_live_edit:
                ui.ask("Take it off the front page?",
                       "This article is published. Saving or resubmitting changes hides it from readers until a "
                       "Lab Director approves the new version.",
                       "Yes, continue", action + "-confirmed")
                return
            self.save(submit=(action == "submit"))
        elif action in ("save-confirmed", "submit-confirmed"):
            ui.close_modal()
            self.confirmed_live_edit = True
            self.save(submit=(action == "submit-confirmed"))
        elif action == "submit-unsourced":
            ui.close_modal()
            self.save(submit=True, acknowledge_unsourced=True)

    def body_el(self):
        return self.q('[name="body"]')

    def insert_at_cursor(self, text):
        ta = self.body_el()
        if ta is None:
            return
        self.set_mode("write")
        end = ta.selectionEnd
        ta.setRangeText(text, end, end, "end")
        ta.focus()
        self.collect()
        self.update_meter()

    def apply_format(self, key):
        label, _, before, after, placeholder, line_start = FORMATS[key]
        ta = self.body_el()
        if ta is None:
            return
        self.set_mode("write")
        start, end = ta.selectionStart, ta.selectionEnd
        sel = selected_text(ta) or placeholder
        prefix = ""
        if line_start and start > 0:
            before_char = window.Function("ta", "s", "return ta.value.charAt(s - 1);")(ta, start)
            if before_char != "\n":
                prefix = "\n"
        ta.setRangeText(prefix + before + sel + after, start, end, "end")
        # select the inner text so it can be typed over
        inner_start = start + len(prefix + before)
        ta.setSelectionRange(inner_start, ta.selectionEnd - len(after))
        ta.focus()
        self.collect()
        self.update_meter()

    def set_mode(self, mode):
        ta = self.body_el()
        pv = self.q('[data-ref="preview"]')
        if ta is None or pv is None:
            return
        for b in self.qa(".as-tab2"):
            b.classList.toggle("as-tab2-on", b.getAttribute("data-arg") == mode)
        fmts = self.q('[data-ref="fmts"]')
        if mode == "preview":
            self.collect()
            html = api.do("preview_body", self.f["body"], self.sources)
            pv.innerHTML = html or '<p class="as-muted">Nothing to preview yet. Write something delightful!</p>'
            ta.hidden = True
            pv.hidden = False
            if fmts is not None:
                fmts.classList.add("as-dim")
        else:
            ta.hidden = False
            pv.hidden = True
            if fmts is not None:
                fmts.classList.remove("as-dim")

    def save(self, submit, acknowledge_unsourced=False):
        self.collect()
        fields = dict(self.f)
        r = api.do("save_article", self.no, fields, self.sources,
                   submit=submit, acknowledge_unsourced=acknowledge_unsourced)
        if r.get("needs_ack"):
            ui.modal("No sources yet!",
                     "<p>Bea the Beaker is worried. 😿 Articles without sources are much harder to approve, "
                     "and readers can't check what they read.</p>"
                     "<ul><li>Link the original study (look for a <b>DOI</b> or the journal page)</li>"
                     "<li>Agency or university pages count too: NASA, NOAA, WHO…</li>"
                     "<li>Then type <code>[1]</code> in your text where you use it</li></ul>",
                     ui.btn("Submit without sources", "submit-unsourced", kind="ghost")
                     + ui.btn("📎 Add a source", "add-source-modal", kind="primary"),
                     mood="sad")
            return
        self.no = r["no"]
        self.status = r["status"]
        if submit:
            ui.toast("Submitted! A Lab Director will put it under the microscope 🔬")
            self.app.refresh_me()
            self.app.go("lab")
        else:
            self.app.replace_hash("write/%d" % self.no)
            ui.toast("Saved to your Petri dish 🧫")
            self.review_note = self.review_note if self.status == "draft" else ""
            self.render()
            self.app.refresh_me()
