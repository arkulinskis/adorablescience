# Public: real web addresses for stories and writers, served by the server as light HTML pages in the lab's look,
# so link previews, search engines and AI assistants see the real story (the app itself lives at #article/N).
#
#   /a/<no>[/<slug>]        a published story. Anything else (draft, pending, taken down, unknown) gets a friendly 404
#                           that never names the article. A wrong slug redirects (301) to the right one.
#   /w/<uid>                a writer's public portfolio, once they have a published story (else 404). Never emails.
#   /feed.xml               RSS 2.0: the latest 30 published stories, full text (RSS readers, RSS-to-email newsletters)
#   /sitemap-articles.xml   every /a/ and /w/ address, for search engines
#
# Built from Lab.card / sources_of and Render.markdown (which escapes everything the writer typed); never from
# full_article (that one reads the viewer). Cached for 5 minutes by browsers and proxies.
import html
import json
from datetime import datetime, timezone
from email.utils import format_datetime

import anvil
import anvil.server
import anvil.tables as tables
from anvil.tables import app_tables

from . import lab_config as C
from . import Render
from . import seo_routes
from .Accounts import _badges, _published_by, _stats
from .Lab import card, clean, opt, profile, sources_of

CACHE = {"Cache-Control": "public, max-age=300"}
FEEDBACK = "https://prepsto.com/#f/7uhztrz"
FEED_SIZE = 30
e = html.escape


def origin():
    return seo_routes.origin()


def _iso(d):
    if not d:
        return ""
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).isoformat()


def _rfc822(d):
    d = d or datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return format_datetime(d.astimezone(timezone.utc), usegmt=True)


def _ld(data):
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def article_path(c):
    """'/a/12/why-wombat-poop-comes-out-in-cubes' from a card() dict."""
    return "/a/%d/%s" % (c["no"], c["slug"])


def _published(no):
    """The published article row with this specimen number, or None (drafts, pending, taken down, unknown)."""
    try:
        n = int(str(no or "").strip())
    except ValueError:
        return None
    row = app_tables.articles.get(specimen_no=n)
    return row if row is not None and row["status"] == "published" else None


# ------------------------------------------------------------------------------------------------ page frame
CSS = """
:root{--paper:#fff9f0;--grid:rgba(108,79,216,.07);--card:#fff;--ink:#2b2a4c;--soft:#4d4b70;--muted:#67658a;--line:#2b2a4c;
--shadow:#2b2a4c;--hair:#e9e2f5;--accent:#6c4fd8;--lav-deep:#6c4fd8;--lav:#e6dbff;--mint:#c4f3e5;--peach:#ffdccf;
--butter:#fff1b8;--sky:#d6ecff;--pink:#ffd6e8;--ease:cubic-bezier(.23,1,.32,1);--dur:160ms;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#17162a;--grid:rgba(184,166,255,.06);--card:#232140;
--ink:#f3f0ff;--soft:#d6d1f0;--muted:#b3aed3;--line:#a8a1dc;--shadow:#08070f;--hair:#3b3860;--accent:#b9a8ff;--lav:#362d66;
--mint:#1d4a40;--peach:#5b3326;--butter:#4d4120;--sky:#20405e;--pink:#5c2946;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#17162a;--grid:rgba(184,166,255,.06);--card:#232140;--ink:#f3f0ff;--soft:#d6d1f0;
--muted:#b3aed3;--line:#a8a1dc;--shadow:#08070f;--hair:#3b3860;--accent:#b9a8ff;--lav:#362d66;--mint:#1d4a40;--peach:#5b3326;
--butter:#4d4120;--sky:#20405e;--pink:#5c2946;color-scheme:dark}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%;accent-color:var(--lav-deep)}
body{margin:0;background-color:var(--paper);background-image:linear-gradient(var(--grid) 1px,transparent 1px),
linear-gradient(90deg,var(--grid) 1px,transparent 1px);background-size:26px 26px;color:var(--ink);
font:400 17px/1.65 "Nunito",system-ui,-apple-system,"Segoe UI",sans-serif;overflow-wrap:break-word}
a{color:var(--accent)}h1,h2,h3,h4{font-family:"Fredoka","Nunito",system-ui,sans-serif;font-weight:600;line-height:1.2;text-wrap:balance}
:focus-visible{outline:3px solid var(--accent);outline-offset:2px;border-radius:6px}
.wrap{max-width:760px;margin:0 auto;padding:0 16px}
.top{background:var(--card);border-bottom:2.5px solid var(--line)}
.top .wrap{max-width:980px;display:flex;align-items:center;justify-content:space-between;gap:12px;padding-top:10px;padding-bottom:10px}
.brand{display:flex;align-items:center;gap:10px;color:var(--ink);text-decoration:none;font:600 1.15rem "Fredoka",system-ui,sans-serif}
.brand img{width:36px;height:36px;display:block}.brand b{color:var(--accent);font-weight:600}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:44px;padding:10px 18px;border:2.5px solid var(--line);
border-radius:99px;background:var(--card);color:var(--ink);font:800 .95rem/1.2 "Nunito",system-ui,sans-serif;text-decoration:none;
box-shadow:2px 2px 0 var(--shadow);transition:transform var(--dur) var(--ease),box-shadow var(--dur) var(--ease)}
.btn:hover{transform:translate(-1px,-1px);box-shadow:3px 3px 0 var(--shadow)}.btn:active{transform:translate(2px,2px);box-shadow:0 0 0 var(--shadow)}
.btn-primary{background:var(--lav-deep);color:#fff}.btn-soft{background:var(--butter)}.btn-sm{min-height:38px;padding:7px 14px;font-size:.875rem;border-width:2px}
main{padding:24px 0 36px}
.sheet{background:var(--card);border:3px solid var(--line);border-radius:26px;box-shadow:5px 5px 0 var(--shadow);overflow:hidden}
.head{padding:22px 22px 18px;background:var(--t,var(--lav));border-bottom:3px solid var(--line)}
.chips{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.chip{display:inline-flex;align-items:center;gap:4px;font-weight:800;font-size:.8rem;padding:3px 11px;border-radius:99px;background:var(--card);
border:2px solid var(--line);color:var(--ink);text-decoration:none;white-space:nowrap}
.chip-dash{border-style:dashed}.chip-early{background:var(--peach)}.chip-ok{background:var(--mint)}
.spec{font:700 .75rem "Space Mono",ui-monospace,monospace;letter-spacing:.04em;color:var(--soft)}
h1.title{font-size:clamp(1.7rem,5vw,2.5rem);margin:12px 0 8px}
.dek{font-size:1.12rem;color:var(--soft);margin:0 0 14px}
.by{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;font-size:.92rem;color:var(--soft)}
.by a{color:var(--ink);font-weight:800;text-decoration:none}.by a:hover{text-decoration:underline}
.av{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:50%;background:var(--card);border:2px solid var(--line);font-size:18px;flex:none}
.snap{display:flex;flex-wrap:wrap;gap:4px 14px;margin:14px 0 0;padding:9px 14px;background:var(--card);border:2px dashed var(--line);
border-radius:14px;font-weight:700;font-size:.92rem}
.body{padding:6px 22px 4px}
.horses{margin:18px 0 4px;padding:13px 16px;background:var(--butter);border:2.5px solid var(--line);border-radius:18px;box-shadow:2px 2px 0 var(--shadow)}
.horses b{display:block;font:700 .8rem "Space Mono",ui-monospace,monospace;letter-spacing:.04em;margin-bottom:2px}
.prose{font-size:1.05rem}.prose p,.prose li{max-width:65ch}.prose h3{font-size:1.35rem;margin:26px 0 6px}.prose h4{font-size:1.1rem;margin:20px 0 4px}
.prose blockquote{margin:16px 0;padding:6px 16px;border-left:5px solid var(--accent);color:var(--soft)}
.prose code{font-family:"Space Mono",ui-monospace,monospace;font-size:.88em;background:var(--lav);padding:1px 5px;border-radius:6px}
.prose hr{border:0;border-top:2px dashed var(--hair);margin:24px 0}
.as-labnote{display:block;background:var(--mint);border:2.5px solid var(--line);border-radius:18px;padding:13px 17px;margin:16px 0;box-shadow:2px 2px 0 var(--shadow)}
.as-labnote-tag{display:block;font:700 .8rem "Space Mono",ui-monospace,monospace;letter-spacing:.04em;margin-bottom:4px}
.as-cite{font:700 .7rem "Space Mono",ui-monospace,monospace}.as-cite a{text-decoration:none;padding:0 2px}.as-cite-missing{color:var(--muted)}
.refs{margin:12px 22px 22px;padding:16px 18px;background:var(--sky);border:2.5px solid var(--line);border-radius:20px}
.refs h2{font-size:1.25rem;margin:0 0 6px}.refs ol{margin:0;padding-left:24px}.refs li{margin:8px 0}.refs small{display:block;color:var(--soft)}
.refs-none{background:var(--peach)}
.cta{display:flex;flex-wrap:wrap;gap:10px;margin:22px 0 0}
.section{font-size:1.3rem;margin:30px 0 12px}
.cards{display:grid;gap:14px}
.card{display:block;background:var(--card);border:2.5px solid var(--line);border-radius:20px;padding:14px 16px;color:var(--ink);text-decoration:none;
box-shadow:2px 2px 0 var(--shadow);transition:transform var(--dur) var(--ease),box-shadow var(--dur) var(--ease)}
.card:hover{transform:translate(-1px,-1px);box-shadow:4px 4px 0 var(--shadow)}.card h3{margin:8px 0 4px;font-size:1.15rem}
.card p{margin:0;color:var(--soft);font-size:.95rem}.card small{display:block;margin-top:8px;color:var(--muted);font-weight:700}
.profile{display:grid;grid-template-columns:auto minmax(0,1fr);gap:18px;align-items:start;padding:22px}
.dish{display:grid;place-items:center;width:92px;height:92px;border-radius:50%;background:var(--lav);border:3px solid var(--line);font-size:48px;box-shadow:3px 3px 0 var(--shadow)}
.profile h1{font-size:clamp(1.6rem,5vw,2.2rem);margin:6px 0 2px}.profile p{margin:6px 0}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;padding:0 22px 22px}
.stat{background:var(--paper);border:2px solid var(--line);border-radius:16px;padding:10px;text-align:center}
.stat b{display:block;font:700 1.4rem/1.1 "Space Mono",ui-monospace,monospace}.stat span{font-size:.8rem;font-weight:800;color:var(--soft)}
.badges{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.promise{margin:0 22px 22px;padding:11px 15px;background:var(--mint);border:2px solid var(--line);border-radius:14px;font-weight:700}
.lost{text-align:center;padding:34px 22px}.bea{width:110px;height:auto;display:block;margin:0 auto}
footer{border-top:2px dashed var(--hair);padding:22px 0 34px;color:var(--soft);font-size:.92rem}footer p{margin:6px 0}footer a{color:inherit}
@media (prefers-reduced-motion:reduce){.btn,.card{transition:none}}
@media (max-width:560px){.head,.body{padding-left:16px;padding-right:16px}.refs{margin:12px 12px 16px;padding:14px}
.profile{grid-template-columns:minmax(0,1fr);padding:18px 16px}.stats{grid-template-columns:repeat(2,minmax(0,1fr));padding:0 16px 16px}
.promise{margin:0 16px 16px}.top .hide-sm{display:none}}
"""

THEME_JS = ("try{var t=JSON.parse(localStorage.getItem('adorablescience.theme'));"
            "if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t)}catch(e){}")


def _frame(title, desc, canonical, body, head="", robots="index, follow, max-image-preview:large"):
    o = origin()
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<meta name="robots" content="%(robots)s">
%(canonical)s<link rel="icon" href="/_/theme/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="Adorable Science: new discoveries" href="%(o)s/feed.xml">
<meta name="theme-color" content="#6c4fd8">
%(head)s
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@600&family=Nunito:wght@400;700;800&family=Space+Mono:wght@700&display=swap" rel="stylesheet">
<script>%(theme)s</script>
<style>%(css)s</style></head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="/"><img src="/_/theme/favicon.svg" alt="" width="36" height="36"><span>Adorable<b>Science</b></span></a>
<a class="btn btn-primary btn-sm" href="/#write" aria-label="Write a discovery">✍️ <span class="hide-sm">Write a discovery</span></a>
</div></header>
<main><div class="wrap">
%(body)s
</div></main>
<footer><div class="wrap">
<p>🥽 <b>Adorable Science</b>: fuzzy-hearted, well-sourced science news. Every story is reviewed before it's published, and every claim should wear its citations.</p>
<p>📡 <a href="/feed.xml">RSS feed</a> · <a href="%(fb)s" target="_blank" rel="noopener">💬 Submit feedback</a> · <a href="/#legal">Privacy &amp; Terms</a></p>
<p>Contact developer: <a href="https://arkvital.com" target="_blank" rel="noopener">arkvital.com</a> · Parent company: <a href="https://addanapp.com" target="_blank" rel="noopener">addanapp.com</a></p>
</div></footer>
</body></html>
""" % {"title": e(title), "desc": e(desc), "robots": robots, "o": e(o), "head": head, "theme": THEME_JS, "css": CSS,
       "canonical": ('<link rel="canonical" href="%s">\n' % e(canonical)) if canonical else "", "body": body, "fb": FEEDBACK}


def _share_tags(kind, title, desc, url):
    o = origin()
    return "\n".join([
        '<meta property="og:type" content="%s">' % kind,
        '<meta property="og:site_name" content="Adorable Science">',
        '<meta property="og:title" content="%s">' % e(title),
        '<meta property="og:description" content="%s">' % e(desc),
        '<meta property="og:url" content="%s">' % e(url),
        '<meta property="og:image" content="%s/_/theme/og-image.png">' % e(o),
        '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
        '<meta property="og:locale" content="en_CA">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:title" content="%s">' % e(title),
        '<meta name="twitter:description" content="%s">' % e(desc),
        '<meta name="twitter:image" content="%s/_/theme/og-image.png">' % e(o),
    ])


# Bea the Beaker with a sad mouth (the same drawing as client_code/Components/Mascot), for the 404 page
BEA_SAD = """<svg class="bea" viewBox="0 0 120 140" width="110" height="128" aria-hidden="true" focusable="false">
<path d="M60 129 H30 a13 13 0 0 1 -11 -20 L45 63 V36 H75 V63 L101 109 a13 13 0 0 1 -11 20 Z" fill="#c4f3e5"/>
<path d="M60 129 H30 a13 13 0 0 1 -11 -20 L33 84 q7 -5 14 0 t14 0 t14 0 t13 0 L101 109 a13 13 0 0 1 -11 20 Z" fill="#8fe3cb"/>
<path d="M60 129 H30 a13 13 0 0 1 -11 -20 L45 63 V36 H75 V63 L101 109 a13 13 0 0 1 -11 20 Z" fill="none" stroke="#2b2a4c" stroke-width="4.5" stroke-linejoin="round"/>
<rect x="40" y="28" width="40" height="9" rx="4.5" fill="#ffffff" stroke="#2b2a4c" stroke-width="4.5"/>
<ellipse cx="38" cy="106" rx="6" ry="3.5" fill="#d6408a" opacity=".45"/><ellipse cx="82" cy="106" rx="6" ry="3.5" fill="#d6408a" opacity=".45"/>
<circle cx="47" cy="96" r="4.5" fill="#2b2a4c"/><circle cx="73" cy="96" r="4.5" fill="#2b2a4c"/>
<circle cx="48.6" cy="94.4" r="1.5" fill="#fff"/><circle cx="74.6" cy="94.4" r="1.5" fill="#fff"/>
<path d="M53 108 q7 -6 14 0" fill="none" stroke="#2b2a4c" stroke-width="3.5" stroke-linecap="round"/></svg>"""


def not_found_page(what="specimen"):
    """A friendly 404 in the lab's look. Never says what the missing thing was called."""
    if what == "writer":
        h, p = "This scientist's portfolio isn't open yet", ("Writers get a public portfolio once their first story is "
                                                             "approved. Maybe they're still out on fieldwork?")
    else:
        h, p = "This specimen isn't on display", ("It may still be in the lab (drafts and stories under review stay "
                                                  "private), it may have been taken down, or the address has a typo.")
    body = """<section class="sheet lost">
%s
<h1>%s</h1>
<p>%s</p>
<p><b>Bea says:</b> “I only believe things with citations, and I can't find this one.”</p>
<div class="cta" style="justify-content:center"><a class="btn btn-primary" href="/">📰 Front page</a><a class="btn btn-soft" href="/#writers">🧑‍🔬 Meet the writers</a></div>
</section>""" % (BEA_SAD, e(h), e(p))
    return _frame("Not found · Adorable Science", "This page isn't on display at Adorable Science.", "", body,
                  robots="noindex")


# ------------------------------------------------------------------------------------------------ /a/<no>/<slug>
def _snapshot_strip(c, size):
    s = c.get("subject")
    if not (s or size):
        return ""
    bits = []
    if s:
        bits.append("<span>%s %s</span>" % (s["emoji"], e(s["phrase"])))
    if size:
        bits.append("<span>🔢 %s</span>" % e(size))
    if c.get("evidence"):
        bits.append("<span>%s %s</span>" % (c["evidence"]["emoji"], e(c["evidence"]["label"])))
    return '<p class="snap">%s</p>' % "<span aria-hidden=\"true\">·</span>".join(bits)


def _card_html(c):
    chip = ""
    if c.get("subject") and c["subject"]["early"]:
        chip = ' <span class="chip chip-early">%s</span>' % e(c["subject"]["chip"])
    return """<a class="card" href="%s"><div class="chips"><span class="chip">%s %s</span>%s</div>
<h3>%s %s</h3><p>%s</p><small>%s · 📎 %d source%s · 🐾 %d</small></a>""" % (
        e(article_path(c)), c["category"]["emoji"], e(c["category"]["label"]), chip, e(c["cover"]), e(c["title"]),
        e(c["dek"]), e(c["date"]), c["sources"], "" if c["sources"] == 1 else "s", c["boops"])


def article_page(no, slug=None):
    """(status, html or redirect target) for /a/<no>[/<slug>]."""
    a = _published(no)
    if a is None:
        return 404, not_found_page()
    c = card(a)
    path = article_path(c)
    if slug is not None and slug != c["slug"]:
        return 301, path
    o = origin()
    url = o + path
    sources = sources_of(a)
    size, caveat = opt(a, "study_size"), opt(a, "caveat")
    author = c["author"]
    writer_url = "/w/%s" % author["uid"] if author.get("uid") else ""
    reviewed = "✅ Reviewed by a Lab Director" if a["reviewer"] is not None else "✅ Checked by the Adorable Science team"
    tone = c["category"].get("tone") or "lav"
    chips = ['<a class="chip" href="/#topic/%s">%s %s</a>' % (e(c["category"]["key"]), c["category"]["emoji"],
                                                             e(c["category"]["label"])) if c["category"].get("key")
             else '<span class="chip">%s %s</span>' % (c["category"]["emoji"], e(c["category"]["label"]))]
    if c.get("evidence"):
        chips.append('<span class="chip chip-dash" title="Evidence level">%s %s</span>'
                     % (c["evidence"]["emoji"], e(c["evidence"]["label"])))
    if c.get("subject") and c["subject"]["early"]:
        chips.append('<span class="chip chip-early">%s</span>' % e(c["subject"]["chip"]))
    chips.append('<span class="spec">SPECIMEN #%03d</span>' % c["no"])
    name = e(author["name"])
    byline = ('<a href="%s">%s</a>' % (e(writer_url), name)) if writer_url else "<b>%s</b>" % name
    if sources:
        refs = '<section class="refs" id="sources"><h2>📚 Sources (%d)</h2><ol>%s</ol></section>' % (len(sources), "".join(
            '<li><a href="%s" target="_blank" rel="noopener nofollow">%s</a><small>%s %s%s</small></li>'
            % (e(s["url"]), e(s["title"]), s["kind_emoji"], e(s["kind_label"]),
               (" · " + e(s["publisher"])) if s["publisher"] else "") for s in sources))
    else:
        refs = ('<section class="refs refs-none" id="sources"><h2>📚 Sources</h2><p>⚠️ <b>This story doesn\'t link any '
                'sources.</b> Read it with a skeptical squint, and look for the original research before sharing.</p></section>')
    horses = ('<aside class="horses" aria-label="Hold your horses"><b>🐴 HOLD YOUR HORSES</b>%s</aside>' % e(caveat)
              if caveat else "")
    more = [card(r) for r in _published_by(a["author"]) if r.get_id() != a.get_id()][:3] if a["author"] is not None else []
    more_html = ('<h2 class="section">More from %s %s</h2><div class="cards">%s</div>'
                 % (author["avatar"], name, "".join(_card_html(m) for m in more))) if more else ""
    body = """<article class="sheet">
<header class="head" style="--t:var(--%(tone)s)">
<div class="chips">%(chips)s</div>
<h1 class="title">%(cover)s %(title)s</h1>
<p class="dek">%(dek)s</p>
<div class="by"><span class="av" aria-hidden="true">%(avatar)s</span><span>By %(byline)s</span><span>· %(date)s · %(minutes)d min read</span>
<span class="chip chip-ok">%(reviewed)s</span></div>
%(snap)s
</header>
<div class="body">%(horses)s<div class="prose">%(prose)s</div></div>
%(refs)s
</article>
<div class="cta"><a class="btn btn-primary" href="/#article/%(no)d">🐾 Boop it in the lab</a><a class="btn btn-soft" href="/#write">✍️ Write your own discovery</a>%(writer)s</div>
%(more)s""" % {
        "tone": tone, "chips": "".join(chips), "cover": e(c["cover"]), "title": e(c["title"]), "dek": e(c["dek"]),
        "avatar": e(author["avatar"]), "byline": byline, "date": e(c["date"]), "minutes": c["minutes"],
        "reviewed": reviewed, "snap": _snapshot_strip(c, size), "horses": horses,
        "prose": Render.markdown(a["body"] or "", sources), "refs": refs, "no": c["no"],
        "writer": ('<a class="btn" href="%s">%s See %s\'s portfolio</a>' % (e(writer_url), e(author["avatar"]), name))
        if writer_url else "", "more": more_html}
    desc = c["dek"] or c["title"]
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": c["title"][:110], "description": desc,
          "url": url, "mainEntityOfPage": {"@type": "WebPage", "@id": url}, "inLanguage": "en", "isAccessibleForFree": True,
          "datePublished": _iso(a["published_at"]), "dateModified": _iso(a["updated"] or a["published_at"]),
          "image": [o + "/_/theme/og-image.png"], "articleSection": c["category"]["label"],
          "wordCount": len((a["body"] or "").split()),
          "author": {"@type": "Person", "name": author["name"], **({"url": o + writer_url} if writer_url else {})},
          "publisher": {"@type": "Organization", "name": "Adorable Science", "url": o + "/",
                        "logo": {"@type": "ImageObject", "url": o + "/_/theme/favicon.png"}},
          "citation": [{"@type": "CreativeWork", "name": s["title"], "url": s["url"]} for s in sources]}
    head = "\n".join([
        _share_tags("article", c["title"], desc, url),
        '<meta property="article:published_time" content="%s">' % _iso(a["published_at"]),
        '<meta property="article:section" content="%s">' % e(c["category"]["label"]),
        ('<meta property="article:author" content="%s">' % e(o + writer_url)) if writer_url else "",
        '<script type="application/ld+json">%s</script>' % _ld(ld),
    ])
    return 200, _frame("%s · Adorable Science" % c["title"], desc, url, body, head)


# ------------------------------------------------------------------------------------------------ /w/<uid>
def writer_page(uid):
    """(status, html) for /w/<uid>: only writers with at least one published story."""
    uid = clean(uid, 20).lower()
    user = app_tables.users.get(uid=uid) if uid else None
    arts = _published_by(user) if user is not None else []
    if not arts:
        return 404, not_found_page("writer")
    o = origin()
    url = "%s/w/%s" % (o, uid)
    p = profile(user)
    st = _stats(arts)
    badges = _badges(user, st)
    cards = [card(r) for r in arts]
    all_reviewed = all(r["reviewer"] is not None for r in arts)
    site = ""
    if p["website"] and C.is_url(p["website"]):
        site = ' · <a href="%s" target="_blank" rel="nofollow ugc noopener">🔗 %s</a>' % (e(p["website"]), e(C.domain_of(p["website"])))
    bio = p["bio"] or "This scientist prefers to let their stories do the talking."
    body = """<section class="sheet">
<div class="profile"><div class="dish" aria-hidden="true">%(avatar)s</div><div>
<span class="spec">LAB ID · %(uid)s</span>%(director)s
<h1>%(name)s</h1>
<p><b>🔭 %(spec)s</b></p>
<p>%(bio)s</p>
<p class="spec" style="letter-spacing:0">🧫 Lab member since %(since)s%(site)s</p>
<div class="badges">%(badges)s</div>
</div></div>
<div class="stats"><div class="stat"><b>%(n)d</b><span>discoveries</span></div><div class="stat"><b>%(src)d</b><span>sources cited</span></div>
<div class="stat"><b>%(avg)s</b><span>sources / story</span></div><div class="stat"><b>%(boops)d</b><span>boops</span></div></div>
<p class="promise">%(promise)s</p>
</section>
<h2 class="section">🔬 Published discoveries</h2>
<div class="cards">%(cards)s</div>""" % {
        "avatar": e(p["avatar"]), "uid": e(uid.upper()), "name": e(p["name"]),
        "director": ' <span class="chip">🥼 Lab Director</span>' if p.get("is_admin") else "",
        "spec": e(p["specialty"] or "Community science writer"), "bio": e(bio), "since": e(p["since"] or "the beginning"),
        "site": site, "badges": "".join('<span class="chip" title="%s">%s %s</span>' % (e(b["why"]), b["emoji"], e(b["label"]))
                                        for b in badges),
        "n": st["published"], "src": st["sources"], "avg": st["avg_sources"], "boops": st["boops"],
        "promise": "✅ Every story here was approved by a Lab Director before it went live." if all_reviewed
        else "✅ Every story here was checked against its sources before it went live.",
        "cards": "".join(_card_html(c) for c in cards)}
    title = "%s: science writer on Adorable Science" % p["name"]
    desc = ("%s writes fuzzy-hearted, well-sourced science stories on Adorable Science: %d published discover%s."
            % (p["name"], st["published"], "y" if st["published"] == 1 else "ies"))
    person = {"@type": "Person", "@id": url + "#person", "name": p["name"], "url": url,
              "description": p["bio"] or p["specialty"] or "Community science writer"}
    if site:
        person["sameAs"] = [p["website"]]
    ld = {"@context": "https://schema.org", "@type": "ProfilePage", "url": url, "name": title, "mainEntity": person,
          "hasPart": [{"@type": "NewsArticle", "headline": c["title"][:110], "url": o + article_path(c)} for c in cards[:20]]}
    head = _share_tags("profile", title, desc, url) + '\n<script type="application/ld+json">%s</script>' % _ld(ld)
    return 200, _frame(title, desc, url, body, head)


# ------------------------------------------------------------------------------------------------ feed + sitemap
def _latest(limit):
    out = []
    for r in app_tables.articles.search(tables.order_by("published_at", ascending=False), status="published"):
        out.append(r)
        if limit and len(out) >= limit:
            break
    return out


def _cdata(s):
    return "<![CDATA[%s]]>" % (s or "").replace("]]>", "]]]]><![CDATA[>")


def feed_xml():
    o = origin()
    rows = _latest(FEED_SIZE)
    items = []
    for a in rows:
        c = card(a)
        url = o + article_path(c)
        sources = sources_of(a)
        size, caveat = opt(a, "study_size"), opt(a, "caveat")
        snap = []
        if c.get("subject"):
            snap.append("%s %s" % (c["subject"]["emoji"], c["subject"]["phrase"]))
        if size:
            snap.append(size)
        full = "".join([
            "<p><em>%s</em></p>" % e(" · ".join(snap)) if snap else "",
            "<p><b>🐴 Hold your horses:</b> %s</p>" % e(caveat) if caveat else "",
            Render.markdown(a["body"] or "", sources),
            ("<h3>Sources</h3><ol>%s</ol>" % "".join('<li><a href="%s">%s</a></li>' % (e(s["url"]), e(s["title"]))
                                                     for s in sources)) if sources else "",
            '<p><a href="%s">Read it with its sources on Adorable Science</a></p>' % e(url),
        ])
        items.append("""<item>
<title>%s</title>
<link>%s</link>
<guid isPermaLink="true">%s/a/%d</guid>
<pubDate>%s</pubDate>
<dc:creator>%s</dc:creator>
<category>%s</category>
<description>%s</description>
<content:encoded>%s</content:encoded>
</item>""" % (e(c["title"]), e(url), e(o), c["no"], _rfc822(a["published_at"]), e(c["author"]["name"]),
              e(c["category"]["label"]), e(c["dek"]), _cdata(full)))
    built = _rfc822(rows[0]["published_at"] if rows else None)
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
<title>Adorable Science</title>
<link>%(o)s/</link>
<description>Fuzzy-hearted, well-sourced science news written by the community. Every story is reviewed by a Lab Director before it's published.</description>
<language>en</language>
<lastBuildDate>%(built)s</lastBuildDate>
<ttl>60</ttl>
<atom:link href="%(o)s/feed.xml" rel="self" type="application/rss+xml"/>
<image><url>%(o)s/_/theme/favicon.png</url><title>Adorable Science</title><link>%(o)s/</link></image>
%(items)s
</channel>
</rss>
""" % {"o": e(o), "built": built, "items": "\n".join(items)}


def sitemap_articles_xml():
    o = origin()
    urls, writers = [], {}
    for a in _latest(0):
        c = card(a)
        day = (_iso(a["updated"] or a["published_at"]) or "")[:10]
        urls.append((o + article_path(c), day))
        uid = c["author"].get("uid")
        if uid and (uid not in writers or day > writers[uid]):
            writers[uid] = day
    urls += [("%s/w/%s" % (o, uid), day) for uid, day in sorted(writers.items())]
    rows = ["<url><loc>%s</loc>%s</url>" % (e(u), ("<lastmod>%s</lastmod>" % d) if d else "") for u, d in urls]
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(rows) + "\n</urlset>\n")


# ------------------------------------------------------------------------------------------------ routes
def _respond(status, content, ctype="text/html; charset=utf-8"):
    if status in (301, 302):
        return anvil.server.HttpResponse(status, "", headers={"Location": content, "Cache-Control": CACHE["Cache-Control"]})
    headers = dict(CACHE) if status == 200 else {"Cache-Control": "public, max-age=60"}
    return anvil.server.HttpResponse(status, anvil.BlobMedia(ctype, content.encode("utf-8")), headers=headers)


ROUTE = getattr(anvil.server, "route", None)
if ROUTE:  # the Python 3.10+ server runtimes have it (this app runs python314)
    @ROUTE("/a/:no")
    def public_article(no, **params):
        return _respond(*article_page(no))

    @ROUTE("/a/:no/:slug")
    def public_article_slug(no, slug, **params):
        return _respond(*article_page(no, slug))

    @ROUTE("/w/:uid")
    def public_writer(uid, **params):
        return _respond(*writer_page(uid))

    @ROUTE("/feed.xml")
    def public_feed(**params):
        return _respond(200, feed_xml(), "application/rss+xml; charset=utf-8")

    @ROUTE("/sitemap-articles.xml")
    def public_sitemap(**params):
        return _respond(200, sitemap_articles_xml(), "application/xml; charset=utf-8")
