# page_home — the front page: published articles only, newest first, with field filters and search.
from . import api
from . import as_ui as ui
from . import lab_config as C
from .as_ui import esc

# Watch section: the app's video on the Addanapp YouTube channel (APP_MAKER/youtube/manifest.json).
# Click to play: nothing loads from YouTube until the play button is pressed (on_action "play-video").
YT_VIDEO = "eoGeoGcAmg8"
WATCH = ('<section class="as-watch ytf" id="watch"><div class="ytf-in"><div class="ytf-copy"><div class="as-eyebrow ytf-kick"><svg viewBox="0 0 28 20" width="20" height="14" aria-hidden="true"><rect width="28" height="20" rx="5" fill="#FF0033"/><path d="M11.2 5.8v8.4l7.3-4.2z" fill="#fff"/></svg>Watch</div><h2>See Adorable Science in about a minute</h2><p>A short video tour of what Adorable Science does and how it works.</p><a class="ytf-link" href="https://www.youtube.com/watch?v=eoGeoGcAmg8" target="_blank" rel="noopener">Watch on YouTube &#8599;</a></div><div><div class="ytf-frame"><button type="button" class="ytf-cover" data-action="play-video" data-yt-film="eoGeoGcAmg8" data-yt-title="Adorable Science video" aria-label="Play the Adorable Science video (1:11)"><img src="_/theme/yt-cover.jpg" alt="" loading="lazy" decoding="async" width="960" height="540"><span class="ytf-play" aria-hidden="true"><svg viewBox="0 0 68 48" width="68" height="48"><path d="M66.5 7.7a8.5 8.5 0 0 0-6-6C55.3.3 34 .3 34 .3s-21.3 0-26.5 1.4a8.5 8.5 0 0 0-6 6C.1 13 .1 24 .1 24s0 11 1.4 16.3a8.5 8.5 0 0 0 6 6c5.2 1.4 26.5 1.4 26.5 1.4s21.3 0 26.5-1.4a8.5 8.5 0 0 0 6-6C67.9 35 67.9 24 67.9 24s0-11-1.4-16.3z" fill="#FF0033"/><path d="M45 24 27 14v20z" fill="#fff"/></svg></span><span class="ytf-len">1:11</span></button></div><p class="ytf-note">The video loads from YouTube when you press play.</p></div></div></section>')


class HomePage(ui.Page):
    nav = "home"
    loading_text = "Pipetting today's discoveries…"

    def __init__(self, app, arg=None):
        super().__init__(app, arg)
        self.category = arg if arg in C.CATEGORY else ""
        self.query = ""
        self.data = None
        if self.category:
            self.title = C.CATEGORY[self.category]["label"]

    def load(self):
        self.data = api.load("get_front_page", self.category or None, self.query or None)

    def html(self):
        d = self.data
        st = d["stats"]
        me = self.me
        write_href = "#write" if me else "#join/write"

        hero_stats = (
            '<span><b>%d</b> discoveries</span><span><b>%d</b> writers</span><span><b>%d</b> sources cited</span>'
            % (st["articles"], st["writers"], st["sources"]))
        mascot = ui.mascot("as-mascot-hero")
        write_btn = ui.btn("✍️ Write a discovery", href=write_href, kind="primary")
        writers_btn = ui.btn("🧑‍🔬 Meet the writers", href="#writers", kind="soft")
        hero = f"""<section class="as-hero">
  <div class="as-hero-copy">
    <div class="as-eyebrow">Vol. 1 · Peer-purr-viewed news</div>
    <h1>The cutest corner of <span class="as-squiggle">serious science</span>.</h1>
    <p>Real discoveries, explained with warmth by our community of writers. Every story is checked by
    a Lab Director before it's published, and every claim links its sources.</p>
    <div class="as-row">{write_btn}{writers_btn}</div>
    <div class="as-hero-stats">{hero_stats}</div>
  </div>
  <div class="as-hero-art">{mascot}<div class="as-hero-bubble">Hi! I'm Bea. I only believe things with citations. 📎</div></div>
</section>"""

        chips = ['<a class="as-filter%s" href="#">✨ Everything <i>%d</i></a>'
                 % (" as-filter-on" if not self.category else "", st["articles"])]
        for key, label, emoji, tone in C.CATEGORIES:
            n = d["counts"].get(key, 0)
            on = " as-filter-on" if key == self.category else ""
            chips.append('<a class="as-filter tone-%s%s" href="#topic/%s">%s %s <i>%d</i></a>'
                         % (tone, on, key, emoji, esc(label), n))
        search = f"""<form class="as-search" data-form="search" role="search">
  <span aria-hidden="true">🔎</span>
  <input type="search" name="q" placeholder="Search titles, summaries and writers…" value="{esc(self.query)}" autocomplete="off">
  <button type="submit" class="as-btn as-btn-sm">Search</button>
</form>"""
        filters = '<div class="as-filters">%s</div>' % "".join(chips)

        if d["lead"] is None and not d["items"]:
            if self.query:
                body = ui.empty("No specimens match “%s”" % esc(self.query),
                                "Try a different word, or browse everything.",
                                ui.btn("Clear search", "clear-search", kind="soft"), mood="wow")
            elif self.category:
                cat = C.CATEGORY[self.category]
                body = ui.empty("Nothing in %s %s yet" % (cat["emoji"], esc(cat["label"])),
                                "Be the first to publish a discovery in this field!",
                                ui.btn("✍️ Write one", href=write_href, kind="primary"))
            else:
                body = ui.empty("The lab is quiet… for now",
                                "No articles have been published yet. Write the very first one! "
                                "Once a Lab Director approves it, it appears right here.",
                                ui.btn("✍️ Write the first discovery", href=write_href, kind="primary"))
        else:
            lead = ui.lead_card(d["lead"]) if d["lead"] else ""
            if self.query:
                heading = "🔎 %s for “%s”" % (ui.plural(len(d["items"]), "result"), esc(self.query))
            elif self.category:
                heading = "%s Latest in %s" % (C.CATEGORY[self.category]["emoji"], esc(C.CATEGORY[self.category]["label"]))
            else:
                heading = "🧫 Fresh from the lab"
            more = ui.grid([ui.article_card(c) for c in d["items"]]) if d["items"] else ""
            section = '<h2 class="as-section">%s</h2>%s' % (heading, more) if d["items"] else ""
            body = lead + section

        show_hero = not self.category and not self.query
        return "%s%s%s%s%s" % (hero if show_hero else "", filters, search, body, WATCH if show_hero else "")

    def on_submit(self, name, form, ev):
        if name == "search":
            self.query = self.val("q").strip()
            self.load()
            self.render()

    def on_action(self, action, arg, el, ev):
        if action == "play-video":
            el.parentNode.innerHTML = (
                '<iframe src="https://www.youtube-nocookie.com/embed/%s?autoplay=1&rel=0&playsinline=1" '
                'title="Adorable Science video" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" '
                'allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>' % YT_VIDEO)
            return
        if action == "clear-search":
            self.query = ""
            self.load()
            self.render()
