# page_writers — the writer roster (#writers), a writer's profile (#writer/<uid>), and editing
# my own profile (#me).
from . import api
from . import as_ui as ui
from . import lab_config as C
from .as_ui import esc


def badges_html(badges, small=False):
    if not badges:
        return ""
    cls = "as-badges as-badges-sm" if small else "as-badges"
    return '<div class="%s">%s</div>' % (cls, "".join(
        '<span class="as-badge2" title="%s">%s <b>%s</b></span>' % (esc(b["why"]), esc(b["emoji"]), esc(b["label"]))
        for b in badges))


class WritersPage(ui.Page):
    nav = "writers"
    title = "Writers"
    loading_text = "Rounding up the scientists…"

    def load(self):
        self.writers = api.load("list_writers")

    def html(self):
        join = "" if self.me else ui.btn("🥼 Join the lab", href="#join", kind="primary")
        head = ui.page_head("🧑‍🔬 The lab roster", "Meet our writers",
                            "The curious minds behind every published discovery.", join)
        if not self.writers:
            return head + ui.empty("No published writers yet",
                                   "Writers appear here after their first article is approved.",
                                   ui.btn("✍️ Become the first", href="#write" if self.me else "#join/write", kind="primary"))
        cards = []
        for w in self.writers:
            spec = esc(w["specialty"]) or "Community science writer"
            bio = '<p class="as-wcard-bio">%s</p>' % esc(w["bio"]) if w["bio"] else ""
            cards.append(f"""<article class="as-wcard">
  <div class="as-wcard-dish">{ui.avatar(w, 'xl')}</div>
  <h3><a class="as-stretch" href="#writer/{esc(w['uid'])}">{esc(w['name'])}</a></h3>
  <div class="as-wcard-spec">{spec}</div>
  {bio}
  <div class="as-wcard-stats"><span><b>{w['published']}</b> published</span><span><b>{w['sources']}</b> sources</span><span><b>{w['boops']}</b> boops</span></div>
  {badges_html(w['badges'], True)}
  <div class="as-wcard-latest">Latest: <i>{esc(w['latest'])}</i></div>
</article>""")
        return head + ui.grid(cards, "as-grid-writers")


class WriterPage(ui.Page):
    nav = "writers"
    loading_text = "Opening their lab notebook…"

    def load(self):
        self.w = api.load("get_writer", self.arg)
        self.title = self.w["name"]

    def html(self):
        w = self.w
        st = w["stats"]
        site = ""
        if w["website"]:
            site = '<a class="as-linkish" href="%s" target="_blank" rel="noopener nofollow">🔗 %s</a>' % (
                esc(w["website"]), esc(C.domain_of(w["website"])))
        edit = ui.btn("✏️ Edit profile", href="#me", kind="soft sm") if w["is_me"] else ""
        bio = esc(w["bio"]) or ("Tell readers about yourself!" if w["is_me"] else "This scientist prefers to let their articles do the talking.")
        spec = esc(w["specialty"]) or "Community science writer"
        tiles = "".join('<div class="as-stat"><b>%s</b><span>%s</span></div>' % (v, l) for v, l in [
            (st["published"], "discoveries"), (st["sources"], "sources cited"),
            (st["avg_sources"], "sources / article"), (st["boops"], "boops received")])
        director = '<span class="as-chip tone-lav">🥼 Lab Director</span>' if w["is_admin"] else ""
        since = esc(w["since"])
        if w["articles"]:
            arts = '<h2 class="as-section">🔬 Published discoveries</h2>' + ui.grid([ui.article_card(c) for c in w["articles"]])
        elif w["is_me"]:
            arts = ui.empty("No published articles yet",
                            "Your published articles will appear here. Drafts and articles in review stay in your lab.",
                            ui.btn("🧫 Go to my lab", href="#lab", kind="soft") + ui.btn("✍️ Write", href="#write", kind="primary"))
        else:
            arts = ui.empty("Nothing published yet", "Their first discovery is still in the lab. Check back soon!")
        return f"""<div class="as-crumbs"><a href="#writers">← All writers</a>{edit}</div>
<section class="as-profile">
  <div class="as-profile-dish">{ui.avatar(w, 'xxl')}</div>
  <div class="as-profile-main">
    <div class="as-row as-tight"><span class="as-specimen">LAB ID · {esc(w['uid']).upper()}</span>{director}</div>
    <h1>{esc(w['name'])}</h1>
    <div class="as-profile-spec">🔭 {spec}</div>
    <p class="as-profile-bio">{bio}</p>
    <div class="as-row as-muted as-small"><span>🧫 Lab member since {since}</span>{site}</div>
    {badges_html(w['badges'])}
  </div>
</section>
<div class="as-stats">{tiles}</div>
{arts}"""


class ProfileEditPage(ui.Page):
    nav = ""
    needs = "user"
    title = "My profile"

    def load(self):
        self.p = api.load("get_writer", self.me["uid"])
        self.avatar = self.p["avatar"]

    def html(self):
        p = self.p
        avatars = "".join('<button type="button" class="as-cover as-avatar-pick%s" data-action="avatar" data-arg="%s" aria-label="Avatar %s">%s</button>'
                          % (" as-cover-on" if a == self.avatar else "", a, a, a) for a in C.AVATARS)
        head = ui.page_head("🪪 Lab badge", "Edit your profile", "This is what readers see on your writer page.")
        return f"""<div class="as-crumbs"><a href="#writer/{esc(p['uid'])}">← My profile</a></div>
{head}
<form class="as-panel as-form-narrow" data-form="profile">
  <div class="as-field"><span class="as-field-label">Your lab critter</span><div class="as-covers as-covers-lg">{avatars}</div></div>
  <label class="as-field"><span class="as-field-label">Display name</span>
    <input type="text" name="name" maxlength="40" value="{esc(p['name'])}" required></label>
  <label class="as-field"><span class="as-field-label">What do you love writing about?</span>
    <input type="text" name="specialty" maxlength="60" value="{esc(p['specialty'])}" placeholder="Deep-sea squishies, black holes, fungi…"></label>
  <label class="as-field"><span class="as-field-label">Short bio</span>
    <textarea name="bio" rows="4" maxlength="{C.BIO_MAX}" placeholder="Marine biology student. Will talk about octopuses for hours.">{esc(p['bio'])}</textarea></label>
  <label class="as-field"><span class="as-field-label">Website (optional)</span>
    <input type="url" name="website" maxlength="200" value="{esc(p['website'])}" placeholder="https://"></label>
  <div class="as-row as-end"><a class="as-btn as-btn-ghost" href="#writer/{esc(p['uid'])}">Cancel</a><button type="submit" class="as-btn as-btn-primary">💾 Save profile</button></div>
</form>"""

    def on_action(self, action, arg, el, ev):
        if action == "avatar":
            self.avatar = arg
            for b in self.qa(".as-avatar-pick"):
                b.classList.toggle("as-cover-on", b.getAttribute("data-arg") == arg)

    def on_submit(self, name, form, ev):
        if name != "profile":
            return
        api.do("update_profile", self.val("name"), self.avatar, self.val("specialty"),
               self.val("bio"), self.val("website"))
        ui.toast("Profile saved. Looking sharp in that lab coat! 🥼")
        self.app.refresh_me()
        self.app.go("writer/%s" % self.me["uid"])
