# as_ui — client Module. Small HTML building blocks shared by every page, plus toasts and dialogs.
# Pages build HTML strings with these helpers; Main puts them on screen and routes clicks back
# to the page via data-action="..." attributes. Always pass user text through esc().
from anvil.js import window

from . import lab_config as C


def esc(s):
    s = "" if s is None else str(s)
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&#39;"))


def plural(n, word, many=None):
    return "%d %s" % (n, word if n == 1 else (many or word + "s"))


def opts(items, selected, placeholder=None):
    """<option> list from (value, label) pairs."""
    out = []
    if placeholder:
        out.append('<option value="">%s</option>' % esc(placeholder))
    for v, label in items:
        out.append('<option value="%s"%s>%s</option>' % (esc(v), " selected" if v == selected else "", esc(label)))
    return "".join(out)


# ---------- the mascot: Bea the Beaker ----------

def mascot(cls="", mood="happy"):
    mouth = {"happy": "M53 104 q7 7 14 0", "sad": "M53 108 q7 -6 14 0",
             "wow": "M57 104 a3 4 0 1 0 6 0 a3 4 0 1 0 -6 0"}.get(mood, "M53 104 q7 7 14 0")
    return f"""<svg class="as-mascot {cls}" viewBox="0 0 120 140" aria-hidden="true">
  <circle class="as-bub as-bub1" cx="50" cy="16" r="5"/>
  <circle class="as-bub as-bub2" cx="66" cy="7" r="3.5"/>
  <circle class="as-bub as-bub3" cx="72" cy="20" r="2.5"/>
  <path d="M60 129 H30 a13 13 0 0 1 -11 -20 L45 63 V36 H75 V63 L101 109 a13 13 0 0 1 -11 20 Z" fill="var(--as-mint)"/>
  <path d="M60 129 H30 a13 13 0 0 1 -11 -20 L33 84 q7 -5 14 0 t14 0 t14 0 t13 0 L101 109 a13 13 0 0 1 -11 20 Z" fill="var(--as-mint-mid)"/>
  <path d="M60 129 H30 a13 13 0 0 1 -11 -20 L45 63 V36 H75 V63 L101 109 a13 13 0 0 1 -11 20 Z" fill="none" stroke="var(--as-ink)" stroke-width="4.5" stroke-linejoin="round"/>
  <rect x="40" y="28" width="40" height="9" rx="4.5" fill="var(--as-card)" stroke="var(--as-ink)" stroke-width="4.5"/>
  <ellipse cx="38" cy="106" rx="6" ry="3.5" fill="var(--as-pink-deep)" opacity=".45"/>
  <ellipse cx="82" cy="106" rx="6" ry="3.5" fill="var(--as-pink-deep)" opacity=".45"/>
  <g class="as-eyes"><circle cx="47" cy="96" r="4.5" fill="var(--as-ink)"/><circle cx="73" cy="96" r="4.5" fill="var(--as-ink)"/>
  <circle cx="48.6" cy="94.4" r="1.5" fill="#fff"/><circle cx="74.6" cy="94.4" r="1.5" fill="#fff"/></g>
  <path d="{mouth}" fill="none" stroke="var(--as-ink)" stroke-width="3.5" stroke-linecap="round"/>
</svg>"""


# ---------- small pieces ----------

def avatar(p, size="md"):
    return '<span class="as-avatar as-avatar-%s" aria-hidden="true">%s</span>' % (size, esc((p or {}).get("avatar") or "🥼"))


def byline(author, extra=""):
    return ('<a class="as-byline" href="#writer/%s">%s<span><b>%s</b>%s</span></a>'
            % (esc(author.get("uid")), avatar(author, "sm"), esc(author.get("name")), extra))


def cat_chip(cat, link=True):
    if not cat:
        return ""
    inner = "%s %s" % (esc(cat.get("emoji")), esc(cat.get("label")))
    if link and cat.get("key"):
        return '<a class="as-chip tone-%s" href="#topic/%s">%s</a>' % (esc(cat.get("tone")), esc(cat["key"]), inner)
    return '<span class="as-chip tone-%s">%s</span>' % (esc(cat.get("tone")), inner)


def evidence_badge(ev):
    if not ev:
        return ""
    return '<span class="as-evidence" title="Evidence level">%s %s</span>' % (esc(ev["emoji"]), esc(ev["label"]))


def sources_badge(n):
    if n <= 0:
        return '<span class="as-srcbadge as-srcbadge-none" title="This article links no sources">⚠️ Unsourced</span>'
    gold = " as-srcbadge-gold" if n >= 3 else ""
    return '<span class="as-srcbadge%s" title="Sources linked">📎 %s</span>' % (gold, plural(n, "source"))


def status_pill(status):
    label, emoji, _ = C.STATUSES.get(status, ("Unknown", "❔", ""))
    return '<span class="as-status as-status-%s">%s %s</span>' % (esc(status), emoji, esc(label))


def specimen(no):
    return '<span class="as-specimen">SPECIMEN #%03d</span>' % int(no or 0)


def btn(label, action=None, arg=None, kind="", href=None, attrs=""):
    cls = "as-btn" + ("" if not kind else " as-btn-" + " as-btn-".join(kind.split()))
    if href is not None:
        return '<a class="%s" href="%s" %s>%s</a>' % (cls, esc(href), attrs, label)
    a = ' data-action="%s"' % esc(action) if action else ""
    a += ' data-arg="%s"' % esc(arg) if arg is not None else ""
    return '<button type="button" class="%s"%s %s>%s</button>' % (cls, a, attrs, label)


def page_head(eyebrow, title, sub="", actions=""):
    sub = '<p class="as-sub">%s</p>' % sub if sub else ""
    actions = '<div class="as-row">%s</div>' % actions if actions else ""
    return f"""<header class="as-pagehead">
  <div><div class="as-eyebrow">{eyebrow}</div><h1>{title}</h1>{sub}</div>
  {actions}
</header>"""


def empty(title, text="", cta="", mood="happy"):
    face = mascot("as-mascot-md", mood)
    text = "<p>%s</p>" % text if text else ""
    cta = '<div class="as-row as-center">%s</div>' % cta if cta else ""
    return f"""<div class="as-empty">{face}<h3>{title}</h3>{text}{cta}</div>"""


def loading(text="Calibrating the microscopes…"):
    return f"""<div class="as-loading" role="status"><div class="as-loader-art" aria-hidden="true"></div><p>{esc(text)}</p></div>"""


def error_block(msg):
    return empty("Oops, something fizzled 💥", esc(msg), btn("← Back to the front page", href="#"), mood="sad")


def meter(n_sources, n_cited=0):
    m = C.citation_meter(n_sources, n_cited)
    count = plural(n_sources, "source") + (" · %d cited inline" % n_cited if n_sources else "")
    label = esc(m["label"])
    tip = esc(m["tip"])
    return f"""<div class="as-meter tone-{m['tone']}">
  <div class="as-meter-top"><span class="as-meter-face">{m['emoji']}</span>
    <div><div class="as-meter-label">{label}</div>
    <div class="as-meter-count">{count}</div></div></div>
  <div class="as-meter-track"><div class="as-meter-fill" style="width:{m['pct']}%"></div>
    <span class="as-meter-tick" style="left:38%"></span><span class="as-meter-tick" style="left:70%"></span></div>
  <p class="as-meter-tip">{tip}</p>
</div>"""


# ---------- article cards ----------

def article_card(c, show_status=False, href=None):
    href = href or "#article/%d" % c["no"]
    tone = c["category"].get("tone", "lav")
    status = status_pill(c["status"]) if show_status else ""
    return f"""<article class="as-card tone-{esc(tone)}">
  <div class="as-card-band"><span class="as-card-cover">{esc(c['cover'])}</span>{specimen(c['no'])}</div>
  <div class="as-card-body">
    <div class="as-row as-tight">{cat_chip(c['category'])}{status}</div>
    <h3 class="as-card-title"><a class="as-stretch" href="{esc(href)}">{esc(c['title'])}</a></h3>
    <p class="as-card-dek">{esc(c['dek'])}</p>
  </div>
  <footer class="as-card-foot">
    {byline(c['author'])}
    <span class="as-meta">{sources_badge(c['sources'])}<span title="Boops">🐾 {c['boops']}</span></span>
  </footer>
</article>"""


def lead_card(c):
    tone = c["category"].get("tone", "lav")
    flag = "⭐ Featured discovery" if c["featured"] else "🆕 Latest discovery"
    extra = " · %s · %d min read" % (esc(c["ago"]), c["minutes"])
    return f"""<article class="as-lead tone-{esc(tone)}">
  <div class="as-lead-art"><span class="as-lead-cover">{esc(c['cover'])}</span>
    <span class="as-lead-flag">{flag}</span></div>
  <div class="as-lead-body">
    <div class="as-row as-tight">{cat_chip(c['category'])}{evidence_badge(c['evidence'])}</div>
    <h2><a class="as-stretch" href="#article/{c['no']}">{esc(c['title'])}</a></h2>
    <p class="as-lead-dek">{esc(c['dek'])}</p>
    <div class="as-lead-foot">{byline(c['author'], extra)}
      <span class="as-meta">{sources_badge(c['sources'])}<span>🐾 {c['boops']}</span></span></div>
  </div>
</article>"""


def grid(cards_html, cls=""):
    return '<div class="as-grid %s">%s</div>' % (cls, "".join(cards_html))


# ---------- toasts & dialogs (live DOM) ----------

def _layer(name):
    return window.document.querySelector('[data-as="%s"]' % name)


def toast(msg, tone="good"):
    layer = _layer("toasts")
    if layer is None:
        return
    el = window.document.createElement("div")
    el.className = "as-toast as-toast-%s" % tone
    el.textContent = msg
    layer.appendChild(el)

    def gone(*a):
        el.classList.add("as-toast-out")
        window.setTimeout(lambda *b: el.remove(), 400)
    window.setTimeout(gone, 3800)


def modal(title, body_html, actions_html, mood=None):
    layer = _layer("modal")
    if layer is None:
        return
    face = mascot("as-mascot-sm", mood) if mood else ""
    layer.innerHTML = f"""<div class="as-modal-back" data-action="modal-close"></div>
<div class="as-modal" role="dialog" aria-modal="true">{face}<h3>{title}</h3>
  <div class="as-modal-body">{body_html}</div><div class="as-row as-end">{actions_html}</div></div>"""
    layer.classList.add("as-open")
    first = layer.querySelector("textarea, input")
    if first is not None:
        first.focus()


def close_modal():
    layer = _layer("modal")
    if layer is not None:
        layer.classList.remove("as-open")
        layer.innerHTML = ""


def ask(title, text, yes_label, yes_action, arg=None, danger=False, mood="wow"):
    """A confirm dialog. Clicking yes fires yes_action (with arg) on the current page."""
    modal(title, "<p>%s</p>" % text,
          btn("Cancel", "modal-close", kind="ghost") + btn(yes_label, yes_action, arg, kind="danger" if danger else "primary"),
          mood=mood)


# ---------- base class for pages ----------

class Page:
    title = C.APP_NAME
    nav = ""          # which header tab to highlight
    needs = None      # None | "user" | "admin"

    def __init__(self, app, arg=None):
        self.app = app
        self.arg = arg

    def load(self):
        """Fetch data from the server (runs while the loading mascot wobbles)."""

    def html(self):
        return ""

    def mounted(self):
        """Called after html() is on screen."""

    def on_action(self, action, arg, el, ev):
        pass

    def on_input(self, el, ev):
        pass

    def on_submit(self, name, form, ev):
        pass

    # helpers
    def render(self):
        self.app.paint(self)

    def q(self, selector):
        return self.app.root.querySelector(selector)

    def qa(self, selector):
        return list(self.app.root.querySelectorAll(selector))

    def val(self, name):
        el = self.q('[name="%s"]' % name)
        return (el.value or "") if el is not None else ""

    @property
    def me(self):
        return self.app.me
