from anvil import *

from ._anvil_designer import ReviewTemplate
from ... import api, bits, router, state
from ...lab_config import NOTE_MAX, STATUSES

TABS = ("queue", "published", "members")


class Review(ReviewTemplate):
    """The Lab Director's desk (#review): the queue waiting for review (oldest first), what's published (feature /
    take down) and the members (promote to Lab Director). #review/<no> reviews one article: the article exactly as
    readers will see it, the automatic checklist, the citation meter and the decision. Nothing reaches the front
    page without passing through here."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.no = int(args[0]) if args and str(args[0]).isdigit() else None
        self.desk.visible = self.no is None
        self.one.visible = self.no is not None
        if self.no:
            self._load_one()
        else:
            self.tab = "queue"
            self.desk_panel.add_event_handler("x-reload", self._reload)
            self.member_panel.add_event_handler("x-reload", self._reload)
            self._load_tab()

    # ---------------------------------------------------------------- the desk
    def tab_click(self, event):
        self.tab = event.currentTarget.getAttribute("data-tab")
        self._reload()

    def _reload(self, **event_args):
        try:
            self._load_tab()
        except api.LabError as e:
            state.toast(str(e), "error")

    def _load_tab(self):
        for t in TABS:
            self.dom_nodes["tab_" + t].classList.toggle("on", t == self.tab)
        name = {"queue": "review_queue", "published": "published_list", "members": "list_members"}[self.tab]
        items = api.load(name)
        d = self.dom_nodes
        self.starters_button.visible = False
        self.desk_empty.visible = not items
        self.desk_panel.visible = self.tab != "members"
        self.member_panel.visible = self.tab == "members"
        if self.tab == "queue":
            bits.text(d["desk_note"], "Oldest first. %s waiting." % bits.plural(len(items), "article"))
            bits.text(d["empty_title"], "All caught up! ✨")
            bits.text(d["empty_text"], "No articles are waiting for review. Time for a coffee (or a beaker of tea).")
            self.desk_panel.items = [dict(c, mode="queue") for c in items]
        elif self.tab == "published":
            bits.text(d["desk_note"], "The featured article leads the front page.")
            bits.text(d["empty_title"], "Nothing published yet")
            bits.text(d["empty_text"], "Approved articles show up here. Empty front page on launch day? Publish five short "
                                       "starter articles (wombat cubes, puppy-dog eyes, tardigrades in space, ticklish "
                                       "rats, bumblebees at play), each linked to its studies and bylined \"Adorable "
                                       "Science team\". You can take any of them down later.")
            self.starters_button.visible = True
            self.desk_panel.items = [dict(c, mode="published") for c in items]
        else:
            bits.text(d["desk_note"], "Lab Directors can review, approve and take down articles. "
                                      "Emails are only shown to Directors.")
            self.member_panel.items = items
        bits.show(d["desk_note"], bool(items))

    @handle("starters_button", "click")
    def starters_button_click(self, **event_args):
        r = state.call("load_starter_articles")
        if r is not None:
            state.toast("%d starter articles are on the front page 🚀" % r["made"], "ok")
            self._reload()

    # ---------------------------------------------------------------- one article
    def _load_one(self):
        a = api.load("get_review", self.no)
        self.a = a
        self.page_title = "Review: %s" % a["title"]
        self.dom_nodes["reader_link"].setAttribute("href", "#article/%d" % a["no"])
        self.view.show(a)
        self.notebook.show(a.get("history"))
        passed = sum(1 for c in a["checks"] if c["ok"])
        bits.text(self.dom_nodes["passed"], "%d/%d" % (passed, len(a["checks"])))
        self.check_panel.items = a["checks"]
        self.meter.show(a["sources"], a["cited"])
        pending = a["status"] == "pending"
        self.decide_box.visible = pending
        self.closed_box.visible = not pending
        bits.text(self.dom_nodes["closed_status"], STATUSES.get(a["status"], ("?",))[0])
        state.maxlength(self.note_box, NOTE_MAX)

    def _decided(self, message):
        state.toast(message, "ok")
        state.set_me(state.call("get_me"))
        router.go("review")

    @handle("approve_button", "click")
    def approve_button_click(self, **event_args):
        self.approve_button.enabled = False
        try:
            r = state.call("decide", self.no, "approve", self.note_box.text or "", bool(self.feature_box.checked))
        finally:
            self.approve_button.enabled = True
        if r is not None:
            self._decided("Published! It's on the front page now 🚀")

    @handle("send_back_button", "click")
    def send_back_button_click(self, **event_args):
        note = (self.note_box.text or "").strip()
        if len(note) < 5:
            state.toast("Add a note telling the writer what to fix. 🙏", "error")
            self.note_box.focus()
            return
        if state.call("decide", self.no, "send_back", note) is not None:
            self._decided("Sent back with your notes 🧪")
