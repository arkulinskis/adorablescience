# page_review — the Lab Director's review desk (#review) and reviewing one article (#review/<no>).
# Tabs: the queue of articles waiting for review, what's published (feature / take down), and members.
from . import api
from . import as_ui as ui
from . import lab_config as C
from .as_ui import esc
from .page_article import article_html, history_html

TABS = [("queue", "🔬 Waiting for review"), ("published", "🚀 Published"), ("members", "🥼 Lab members")]


class ReviewPage(ui.Page):
    nav = "review"
    needs = "admin"
    title = "Review desk"
    loading_text = "Polishing the microscope lenses…"

    def __init__(self, app, arg=None):
        super().__init__(app, arg)
        self.tab = "queue"
        self.no = int(arg) if arg and arg.isdigit() else None

    def load(self):
        if self.no:
            self.a = api.load("get_review", self.no)
            self.title = "Review: %s" % self.a["title"]
        elif self.tab == "queue":
            self.items = api.load("review_queue")
        elif self.tab == "published":
            self.items = api.load("published_list")
        else:
            self.items = api.load("list_members")

    # ---------- the desk ----------

    def html(self):
        if self.no:
            return self.review_html()
        tabs = "".join('<button type="button" class="as-tab2%s" data-action="tab" data-arg="%s">%s</button>'
                       % (" as-tab2-on" if k == self.tab else "", k, label) for k, label in TABS)
        head = ui.page_head("🔬 Lab Directors only", "Review desk",
                            "Nothing reaches the front page until it's approved here. Check the sources, "
                            "then approve it or send it back with friendly notes.")
        body = {"queue": self.queue_html, "published": self.published_html, "members": self.members_html}[self.tab]()
        return '%s<div class="as-tabs2 as-tabs2-lg">%s</div>%s' % (head, tabs, body)

    def queue_html(self):
        if not self.items:
            return ui.empty("All caught up! ✨", "No articles are waiting for review. Time for a coffee (or a beaker of tea).")
        rows = []
        for c in self.items:
            rows.append(f"""<div class="as-labrow">
  <span class="as-labrow-cover">{esc(c['cover'])}</span>
  <div class="as-labrow-main">
    <div class="as-row as-tight">{ui.specimen(c['no'])}{ui.cat_chip(c['category'], link=False)}{ui.sources_badge(c['sources'])}</div>
    <h3>{esc(c['title'])}</h3>
    <div class="as-muted as-small">by {esc(c['author']['avatar'])} {esc(c['author']['name'])} · submitted {esc(c['submitted_ago'])} · {c['minutes']} min read</div>
  </div>
  <div class="as-labrow-actions">{ui.btn('🔬 Review', href='#review/%d' % c['no'], kind='primary sm')}</div>
</div>""")
        return '<p class="as-muted">Oldest first. %s waiting.</p>%s' % (ui.plural(len(self.items), "article"), "".join(rows))

    def published_html(self):
        if not self.items:
            return ui.empty("Nothing published yet", "Approved articles show up here.")
        rows = []
        for c in self.items:
            star = "⭐ Featured" if c["featured"] else "☆ Feature"
            feature = ui.btn(star, "feature", c["no"], kind="soft sm" if c["featured"] else "ghost sm",
                             attrs='data-on="%s"' % ("1" if c["featured"] else "0"))
            rows.append(f"""<div class="as-labrow">
  <span class="as-labrow-cover">{esc(c['cover'])}</span>
  <div class="as-labrow-main">
    <div class="as-row as-tight">{ui.specimen(c['no'])}{ui.cat_chip(c['category'], link=False)}{ui.sources_badge(c['sources'])}</div>
    <h3><a href="#article/{c['no']}">{esc(c['title'])}</a></h3>
    <div class="as-muted as-small">by {esc(c['author']['name'])} · published {esc(c['ago'])} · 🐾 {c['boops']}</div>
  </div>
  <div class="as-labrow-actions">{feature}{ui.btn('🛑 Take down', 'unpublish', c['no'], kind='ghost sm')}</div>
</div>""")
        return '<p class="as-muted">The featured article leads the front page.</p>' + "".join(rows)

    def members_html(self):
        rows = []
        for m in self.items:
            if m["is_admin"]:
                role = '<span class="as-chip tone-lav">🥼 Lab Director</span>'
                act = ui.btn("Remove Director", "set-admin", m["uid"], kind="ghost sm", attrs='data-on="0"')
            else:
                role = '<span class="as-chip tone-mint">✍️ Writer</span>'
                act = ui.btn("Make Lab Director", "set-admin", m["uid"], kind="soft sm", attrs='data-on="1"')
            you = ' <span class="as-muted">(you)</span>' if m["is_me"] else ""
            rows.append(f"""<div class="as-labrow">
  {ui.avatar(m, 'lg')}
  <div class="as-labrow-main">
    <h3><a href="#writer/{esc(m['uid'])}">{esc(m['name'])}</a>{you}</h3>
    <div class="as-muted as-small">{esc(m['email'])} · joined {esc(m['since'])} · {m['published']} published / {m['total']} written</div>
  </div>
  <div class="as-labrow-actions">{role}{act}</div>
</div>""")
        return ('<p class="as-muted">Lab Directors can review, approve and take down articles. '
                'Emails are only shown to Directors.</p>' + "".join(rows))

    # ---------- reviewing one article ----------

    def review_html(self):
        a = self.a
        checks = "".join('<li class="%s"><span>%s</span><div><b>%s</b><small>%s</small></div></li>'
                         % ("as-ok" if c["ok"] else "as-warn", "✅" if c["ok"] else "⚠️", esc(c["label"]), esc(c["detail"]))
                         for c in a["checks"])
        passed = sum(1 for c in a["checks"] if c["ok"])
        if a["status"] == "pending":
            decision = f"""<div class="as-panel as-decide">
  <h4>Your decision</h4>
  <label class="as-field"><span class="as-field-label">Note to the writer</span>
    <textarea name="note" rows="5" maxlength="{C.NOTE_MAX}" placeholder="Lovely piece! Could you link the original paper for the second claim?"></textarea></label>
  <label class="as-check"><input type="checkbox" name="feature"> ⭐ Feature it at the top of the front page</label>
  {ui.btn('🚀 Approve &amp; publish', 'approve', kind='good block')}
  {ui.btn('🧪 Send back: needs more data', 'send-back', kind='soft block')}
  <p class="as-muted as-small">Sending back needs a note, so the writer knows what to fix.</p>
</div>"""
        else:
            decision = ('<div class="as-panel"><h4>Not in the queue</h4><p>This article is <b>%s</b>, so there’s nothing to decide right now.</p>%s</div>'
                        % (esc(C.STATUSES.get(a["status"], ("?",))[0]), ui.btn("← Back to the queue", href="#review", kind="soft block")))
        meter = ui.meter(a["sources"], a["cited"])
        return f"""<div class="as-crumbs"><a href="#review">← Review desk</a><a class="as-linkish" href="#article/{a['no']}">Open the reader view →</a></div>
<div class="as-editor">
  <div class="as-editor-main"><article class="as-article as-article-review">{article_html(a)}{history_html(a.get('history'))}</article></div>
  <aside class="as-editor-side">
    <div class="as-panel"><h4>Reviewer checklist <span class="as-muted">{passed}/{len(a['checks'])}</span></h4><ul class="as-checks">{checks}</ul></div>
    <div class="as-panel"><h4>Citation meter</h4>{meter}</div>
    {decision}
  </aside>
</div>"""

    # ---------- actions ----------

    def on_action(self, action, arg, el, ev):
        if action == "tab":
            self.tab = arg
            self.app.view.innerHTML = ui.loading()
            self.load()
            self.render()
        elif action == "approve":
            feature = self.q('[name="feature"]')
            api.do("decide", self.no, "approve", self.val("note"), bool(feature is not None and feature.checked))
            ui.toast("Published! It's on the front page now 🚀")
            self.app.refresh_me()
            self.app.go("review")
        elif action == "send-back":
            note = self.val("note").strip()
            if len(note) < 5:
                ui.toast("Add a note telling the writer what to fix. 🙏", "bad")
                el_note = self.q('[name="note"]')
                if el_note is not None:
                    el_note.focus()
                return
            api.do("decide", self.no, "send_back", note)
            ui.toast("Sent back with your notes 🧪")
            self.app.refresh_me()
            self.app.go("review")
        elif action == "feature":
            on = el.getAttribute("data-on") != "1"
            api.do("set_featured", int(arg), on)
            ui.toast("Featured on the front page ⭐" if on else "No longer featured")
            self.load()
            self.render()
        elif action == "unpublish":
            ui.modal("Take this article down?",
                     '<p>It leaves the front page and goes back to the writer as “needs more data”.</p>'
                     '<label class="as-field"><span class="as-field-label">Note to the writer (required)</span>'
                     '<textarea name="unpublish_note" rows="4" placeholder="What needs fixing?"></textarea></label>',
                     ui.btn("Cancel", "modal-close", kind="ghost") + ui.btn("🛑 Take down", "unpublish-yes", arg, kind="danger"),
                     mood="wow")
        elif action == "unpublish-yes":
            api.do("unpublish", int(arg), self.val("unpublish_note"))
            ui.close_modal()
            ui.toast("Taken down. The writer can see your note.")
            self.load()
            self.render()
        elif action == "set-admin":
            on = el.getAttribute("data-on") == "1"
            api.do("set_admin", arg, on)
            ui.toast("Promoted to Lab Director 🥼" if on else "Director role removed")
            if not on and arg == (self.me or {}).get("uid"):
                self.app.refresh_me()
                self.app.go("")
                return
            self.load()
            self.render()
