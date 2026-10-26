# page_lab — "My lab bench" (#lab): every article I've written, grouped by where it is in review.
from . import api
from . import as_ui as ui
from . import lab_config as C
from .as_ui import esc

SECTION_HELP = {
    "rejected": "A Lab Director sent these back with notes. Revise and resubmit!",
    "draft": "Only you can see these. Submit when they're ready.",
    "pending": "Waiting for a Lab Director. You can withdraw one to keep editing.",
    "published": "Live on the front page. Editing one sends it back for review.",
}


class LabPage(ui.Page):
    nav = "lab"
    needs = "user"
    title = "My lab"
    loading_text = "Tidying your lab bench…"

    def load(self):
        self.items = api.load("my_articles")

    def row(self, c):
        st = c["status"]
        actions = []
        if st != "pending":
            actions.append(ui.btn("✏️ Edit", href="#write/%d" % c["no"], kind="soft sm"))
        actions.append(ui.btn("👀 View", href="#article/%d" % c["no"], kind="ghost sm"))
        if st == "pending":
            actions.append(ui.btn("↩️ Withdraw", "withdraw", c["no"], kind="ghost sm"))
        if st in ("draft", "rejected"):
            actions.append(ui.btn("🗑️", "delete", c["no"], kind="ghost sm", attrs='title="Delete" aria-label="Delete"'))
        note = ""
        if st == "rejected" and c["review_note"]:
            note = '<div class="as-reviewnote"><b>Reviewer’s note:</b> %s</div>' % esc(c["review_note"])
        when = "published %s" % c["ago"] if st == "published" else "edited %s" % c["ago"]
        if st == "pending" and c["submitted_ago"]:
            when = "submitted %s" % c["submitted_ago"]
        cat = ui.cat_chip(c["category"], link=False) if c["category"].get("key") else ""
        boops = " · 🐾 %d" % c["boops"] if st == "published" else ""
        return f"""<div class="as-labrow">
  <span class="as-labrow-cover">{esc(c['cover'])}</span>
  <div class="as-labrow-main">
    <div class="as-row as-tight">{ui.specimen(c['no'])}{cat}{ui.sources_badge(c['sources'])}</div>
    <h3>{esc(c['title'])}</h3>
    <div class="as-muted as-small">{esc(when)}{boops}</div>
    {note}
  </div>
  <div class="as-labrow-actions">{''.join(actions)}</div>
</div>"""

    def html(self):
        me = self.me
        groups = {k: [c for c in self.items if c["status"] == k] for k in C.STATUSES}
        tiles = "".join(
            '<div class="as-tile as-status-%s"><span>%s</span><b>%d</b><small>%s</small></div>'
            % (k, C.STATUSES[k][1], len(groups[k]), esc(C.STATUSES[k][0])) for k in C.STATUS_ORDER)
        head = ui.page_head("🧫 My lab bench", "Hi, %s %s" % (esc(me["name"]), esc(me["avatar"])),
                            "Every article starts in the Petri dish and goes under the microscope before it's published.",
                            ui.btn("✍️ New article", href="#write", kind="primary")
                            + ui.btn("Edit my profile", href="#me", kind="soft"))
        if not self.items:
            return head + ui.empty("Your bench is spotless",
                                   "Write your first article. Save it as a draft as often as you like, "
                                   "then submit it for review when it's ready.",
                                   ui.btn("✍️ Start writing", href="#write", kind="primary"))
        sections = []
        for k in C.STATUS_ORDER:
            if not groups[k]:
                continue
            label, emoji, _ = C.STATUSES[k]
            sections.append('<section class="as-labgroup"><h2 class="as-section">%s %s <i>%d</i></h2><p class="as-muted">%s</p>%s</section>'
                            % (emoji, esc(label), len(groups[k]), esc(SECTION_HELP[k]),
                               "".join(self.row(c) for c in groups[k])))
        return '%s<div class="as-tiles">%s</div>%s' % (head, tiles, "".join(sections))

    def on_action(self, action, arg, el, ev):
        if action == "withdraw":
            ui.ask("Withdraw from review?", "It goes back to your drafts so you can keep editing. "
                   "You'll need to submit it again later.", "↩️ Withdraw", "withdraw-yes", arg)
        elif action == "withdraw-yes":
            ui.close_modal()
            api.do("withdraw_article", int(arg))
            ui.toast("Back in the Petri dish 🧫")
            self.app.refresh_me()
            self.load()
            self.render()
        elif action == "delete":
            ui.ask("Delete this article?", "This can't be undone. The article and its sources will be gone for good.",
                   "🗑️ Delete forever", "delete-yes", arg, danger=True, mood="sad")
        elif action == "delete-yes":
            ui.close_modal()
            api.do("delete_article", int(arg))
            ui.toast("Deleted. Poof! 💨")
            self.load()
            self.render()
