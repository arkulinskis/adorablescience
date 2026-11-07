from anvil import *

from ._anvil_designer import LabRowTemplate
from ... import bits, state


class LabRow(LabRowTemplate):
    """One of my articles on My lab. item = the server's card() dict. Withdraw (pending) and delete (draft, sent back)
    ask first, call the server, then raise x-reload so the page redraws."""

    def __init__(self, **properties):
        super().__init__(**properties)
        c, d = self.item, self.dom_nodes
        st = c["status"]
        bits.text(d["cover"], c["cover"])
        bits.specimen(d["spec"], c["no"])
        bits.cat_chip(d["cat"], c["category"] if c["category"].get("key") else None, link=False)
        bits.sources_badge(d["src"], c["sources"])
        bits.text(d["title"], c["title"])
        when = "published %s" % c["ago"] if st == "published" else "edited %s" % c["ago"]
        if st == "pending" and c["submitted_ago"]:
            when = "submitted %s" % c["submitted_ago"]
        bits.text(d["when"], when + (" · 🐾 %d" % c["boops"] if st == "published" else ""))
        note = c["review_note"] if st == "rejected" else ""
        bits.show(d["note"], bool(note))
        bits.text(d["note_text"], note)
        bits.show(d["edit_link"], st != "pending")
        d["edit_link"].setAttribute("href", "#write/%d" % c["no"])
        d["view_link"].setAttribute("href", "#article/%d" % c["no"])
        self.withdraw_button.visible = st == "pending"
        self.delete_button.visible = st in ("draft", "rejected")
        state.set_control_attr(self.delete_button, "aria-label", "Delete “%s”" % c["title"])

    def _done(self, message):
        state.toast(message, "ok")
        if self.parent is not None:
            self.parent.raise_event("x-reload")

    @handle("withdraw_button", "click")
    def withdraw_button_click(self, **event_args):
        if confirm("It goes back to your drafts so you can keep editing. You'll need to submit it again later.",
                   title="Withdraw from review?", buttons=[("Cancel", False), ("↩️ Withdraw", True)], role="app-dialog"):
            if state.call("withdraw_article", self.item["no"]) is not None:
                self._done("Back in the Petri dish 🧫")

    @handle("delete_button", "click")
    def delete_button_click(self, **event_args):
        if confirm("This can't be undone. The article and its sources will be gone for good.",
                   title="Delete this article?", buttons=[("Cancel", False), ("🗑️ Delete forever", True)],
                   role="app-dialog"):
            if state.call("delete_article", self.item["no"]) is not None:
                self._done("Deleted. Poof! 💨")
