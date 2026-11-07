from anvil import *

from ._anvil_designer import LogEntryTemplate
from ... import bits

LOG_LABELS = {
    "submitted": "📤 Submitted for review",
    "approved": "🚀 Approved & published",
    "sent_back": "🧪 Sent back for more data",
    "withdrawn": "↩️ Moved back to drafts",
    "unpublished": "🛑 Taken off the front page",
    "featured": "⭐ Featured on the front page",
    "unfeatured": "☆ No longer featured",
}


class LogEntry(LogEntryTemplate):
    """One line of the lab notebook. item = {action, note, who, ago} from the server's history_of."""

    def __init__(self, **properties):
        super().__init__(**properties)
        h, d = self.item, self.dom_nodes
        bits.text(d["what"], LOG_LABELS.get(h["action"], h["action"]))
        bits.text(d["who"], "by %s · %s" % (h["who"], h["ago"]))
        bits.text(d["note"], h.get("note") or "")
        bits.show(d["note"], bool(h.get("note")))
