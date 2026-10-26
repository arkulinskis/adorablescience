# page_article — reading one article (#article/<no>), with its sources, boops and more by the writer.
from anvil.js import window

from . import api
from . import as_ui as ui
from . import lab_config as C
from .as_ui import esc

LOG_LABELS = {
    "submitted": "📤 Submitted for review",
    "approved": "🚀 Approved & published",
    "sent_back": "🧪 Sent back for more data",
    "withdrawn": "↩️ Moved back to drafts",
    "unpublished": "🛑 Taken off the front page",
    "featured": "⭐ Featured on the front page",
    "unfeatured": "☆ No longer featured",
}


def sources_html(sources):
    if not sources:
        return """<section class="as-refs as-refs-none" id="sources">
  <h3>📚 Sources</h3>
  <p>⚠️ <b>This article doesn't link any sources.</b> Read it with a skeptical squint, and look for the original research before sharing.</p>
</section>"""
    items = []
    for s in sources:
        pub = " · %s" % esc(s["publisher"]) if s["publisher"] else ""
        items.append(f"""<li><span class="as-ref-n">{s['n']}</span>
  <div><a href="{esc(s['url'])}" target="_blank" rel="noopener nofollow">{esc(s['title'])}</a>
  <div class="as-ref-meta">{esc(s['kind_emoji'])} {esc(s['kind_label'])} · {esc(s['domain'])}{pub}</div></div></li>""")
    gold = '<span class="as-srcbadge as-srcbadge-gold">😻 Peer-purr-viewed</span>' if len(sources) >= 3 else ""
    return f"""<section class="as-refs" id="sources">
  <div class="as-row"><h3>📚 Sources ({len(sources)})</h3>{gold}</div>
  <ol>{''.join(items)}</ol>
</section>"""


def history_html(history):
    if not history:
        return ""
    rows = []
    for h in history:
        note = '<blockquote>%s</blockquote>' % esc(h["note"]) if h["note"] else ""
        rows.append('<li><b>%s</b> <span class="as-muted">by %s · %s</span>%s</li>'
                    % (LOG_LABELS.get(h["action"], esc(h["action"])), esc(h["who"]), esc(h["ago"]), note))
    return '<section class="as-notebook"><h3>📓 Lab notebook</h3><p class="as-muted">Only you and Lab Directors see this.</p><ul>%s</ul></section>' % "".join(rows)


def article_html(a, preview_note=""):
    """The article itself. Also used by the review desk, so reviewers see exactly what readers will."""
    status_banner = ""
    if a["status"] != "published":
        _, emoji, explain = C.STATUSES.get(a["status"], ("", "", ""))
        note = ""
        if a.get("review_note") and a["status"] == "rejected":
            note = '<div class="as-reviewnote"><b>Reviewer’s note:</b> %s</div>' % esc(a["review_note"])
        status_banner = ('<div class="as-banner as-banner-%s">%s <span><b>%s</b> %s %s</span></div>%s'
                         % (a["status"], emoji, esc(C.STATUSES[a["status"]][0]), esc(explain),
                            esc(preview_note), note))
    ev = ui.evidence_badge(a["evidence"])
    cat = ui.cat_chip(a["category"])
    when = "Published %s" % esc(a["date"]) if a["status"] == "published" else "Last edited %s" % esc(a["ago"])
    meta = " · %s · %d min read" % (when, a["minutes"])
    src_link = ('<button type="button" class="as-srcbadge as-srcbadge-btn%s" data-action="jump-sources">📎 %s ↓</button>'
                % (" as-srcbadge-gold" if a["sources"] >= 3 else "", ui.plural(a["sources"], "source"))
                if a["sources"] else ui.sources_badge(0))
    return f"""{status_banner}
<div class="as-article-head tone-{esc(a['category'].get('tone', 'lav'))}">
  <div class="as-article-cover">{esc(a['cover'])}</div>
  <div class="as-row as-tight">{cat}{ev}{ui.specimen(a['no'])}</div>
  <h1 class="as-article-title">{esc(a['title'])}</h1>
  <p class="as-article-dek">{esc(a['dek'])}</p>
  <div class="as-article-meta">{ui.byline(a['author'], meta)}{src_link}</div>
</div>
<div class="as-prose">{a['body_html']}</div>
{sources_html(a['sources_list'])}"""


class ArticlePage(ui.Page):
    nav = "home"
    loading_text = "Fetching the specimen…"

    def load(self):
        self.a = api.load("get_article", self.arg)
        self.title = self.a["title"]

    def html(self):
        a = self.a
        me = self.me
        tools = []
        if a["can_edit"]:
            tools.append(ui.btn("✏️ Edit", href="#write/%d" % a["no"], kind="soft sm"))
        if a["viewer_is_admin"] and a["status"] == "pending":
            tools.append(ui.btn("🔬 Review this", href="#review/%d" % a["no"], kind="primary sm"))
        tools.append(ui.btn("🔗 Copy link", "copy-link", kind="ghost sm"))
        boop = ""
        if a["status"] == "published":
            on = " as-boop-on" if a["booped"] else ""
            boop = (f'<button type="button" class="as-boop{on}" data-action="boop" aria-pressed="{"true" if a["booped"] else "false"}">'
                    f'<span class="as-boop-paw">🐾</span><span><b data-ref="boops">{a["boops"]}</b> boops</span></button>')
            boop = ('<div class="as-boopbox">%s<p>Did this article make you go “aww, science!”? Give it a boop.%s</p></div>'
                    % (boop, "" if me else " (Sign in first.)"))
        author = a["author"]
        more = ""
        if a.get("more"):
            more = ('<section><h2 class="as-section">More from %s %s</h2>%s</section>'
                    % (esc(author["avatar"]), esc(author["name"]), ui.grid([ui.article_card(c) for c in a["more"]], "as-grid-3")))
        about = f"""<a class="as-authorbox" href="#writer/{esc(author['uid'])}">{ui.avatar(author, 'lg')}
  <div><div class="as-eyebrow">Written by</div><b>{esc(author['name'])}</b>
  <p>{esc(author.get('specialty') or 'Community science writer')}</p><span class="as-linkish">See their lab profile →</span></div></a>"""
        history = history_html(a.get("history"))
        return f"""<div class="as-crumbs"><a href="#">← Front page</a><div class="as-row as-tight">{''.join(tools)}</div></div>
<article class="as-article">
{article_html(a)}
{boop}
{about}
{history}
</article>
{more}"""

    def on_action(self, action, arg, el, ev):
        if action == "boop":
            if self.me is None:
                ui.toast("Sign in to boop articles 🐾", "info")
                self.app.go("join/article/%d" % self.a["no"])
                return
            r = api.do("toggle_boop", self.a["no"])
            self.a["booped"], self.a["boops"] = r["booped"], r["boops"]
            el.classList.toggle("as-boop-on", r["booped"])
            el.setAttribute("aria-pressed", "true" if r["booped"] else "false")
            count = el.querySelector('[data-ref="boops"]')
            if count is not None:
                count.textContent = str(r["boops"])
            if r["booped"]:
                el.classList.remove("as-boop-pop")
                el.offsetWidth  # restart the animation
                el.classList.add("as-boop-pop")
        elif action == "jump-sources":
            target = self.q("#sources")
            if target is not None:
                target.scrollIntoView({"behavior": "smooth", "block": "start"})
        elif action == "copy-link":
            try:
                window.navigator.clipboard.writeText(window.location.href)
                ui.toast("Link copied! Share the science 🔗")
            except Exception:
                ui.toast("Couldn't copy. You can copy the address from your browser bar.", "info")
