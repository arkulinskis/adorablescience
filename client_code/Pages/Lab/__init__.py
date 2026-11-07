from anvil import *

from ._anvil_designer import LabTemplate
from ... import api, bits, router, state
from ...lab_config import STATUS_ORDER, STATUSES

SECTION_HELP = {
    "rejected": "A Lab Director sent these back with notes. Revise and resubmit!",
    "draft": "Only you can see these. Submit when they're ready.",
    "pending": "Waiting for a Lab Director. You can withdraw one to keep editing.",
    "published": "Live on the front page. Editing one sends it back for review.",
}


class Lab(LabTemplate):
    """My lab bench (#lab): every article I've written, grouped by where it is in review, with tiles counting each
    group. Rows withdraw / delete themselves (Items/LabRow) and raise x-reload."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        me = state.me() or {}
        bits.text(self.dom_nodes["heading"], "Hi, %s %s" % (me.get("name", "scientist"), me.get("avatar", "")))
        self.group_panel.add_event_handler("x-reload", self._reload)
        self.items = api.load("my_articles")
        self._draw()

    def _draw(self):
        groups = {k: [c for c in self.items if c["status"] == k] for k in STATUSES}
        self.empty_box.visible = not self.items
        self.bench.visible = bool(self.items)
        self.tile_panel.items = [{"status": k, "emoji": STATUSES[k][1], "label": STATUSES[k][0], "n": len(groups[k])}
                                 for k in STATUS_ORDER]
        self.group_panel.items = [{"status": k, "emoji": STATUSES[k][1], "label": STATUSES[k][0],
                                   "help": SECTION_HELP[k], "rows": groups[k]} for k in STATUS_ORDER if groups[k]]

    def _reload(self, **event_args):
        state.set_me(state.call("get_me"))
        router.refresh_shell()
        self.items = state.call("my_articles") or []
        self._draw()
