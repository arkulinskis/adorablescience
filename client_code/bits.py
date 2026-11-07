"""The little stickers every page repeats (field chip, evidence badge, sources badge, status pill, specimen number,
critter avatar, byline), filled into plain elements of a form template: <a anvil:dom-node="cat">, then
bits.cat_chip(self.dom_nodes["cat"], item["category"]). Text goes in with textContent (never innerHTML), so writers'
words can't turn into markup.

    bits.plural(3, "source")      '3 sources'
"""
from .lab_config import STATUSES


def plural(n, word, many=None):
    return "%d %s" % (n, word if n == 1 else (many or word + "s"))


def text(node, value):
    node.textContent = "" if value is None else str(value)


def show(node, visible):
    node.hidden = not visible


TONES = ["sky", "mint", "peach", "lav", "butter", "pink"]


def tone(node, name):
    """Give an element one colour tone (tone-sky, tone-mint ...), keeping its other classes."""
    for t in TONES:
        node.classList.remove("tone-" + t)
    node.classList.add("tone-" + (name if name in TONES else "lav"))


def cat_chip(node, cat, link=True):
    """The field chip (🪐 Space). An <a>: a link to #topic/<field>, or plain text when link is False."""
    cat = cat or {}
    show(node, bool(cat))
    if not cat:
        return
    node.className = "as-chip tone-%s" % (cat.get("tone") or "lav")
    text(node, "%s %s" % (cat.get("emoji") or "", cat.get("label") or ""))
    if link and cat.get("key"):
        node.setAttribute("href", "#topic/%s" % cat["key"])
    else:
        node.removeAttribute("href")


def evidence(node, ev):
    show(node, bool(ev))
    if ev:
        node.className = "as-evidence"
        node.setAttribute("title", "Evidence level")
        text(node, "%s %s" % (ev["emoji"], ev["label"]))


def sources_badge(node, n):
    n = int(n or 0)
    if n <= 0:
        node.className = "as-srcbadge as-srcbadge-none"
        node.setAttribute("title", "This article links no sources")
        text(node, "⚠️ Unsourced")
    else:
        node.className = "as-srcbadge" + (" as-srcbadge-gold" if n >= 3 else "")
        node.setAttribute("title", "Sources linked")
        text(node, "📎 " + plural(n, "source"))


def status_pill(node, status, label=None):
    name, emoji, _ = STATUSES.get(status, ("Unknown", "❔", ""))
    node.className = "as-status as-status-%s" % status
    text(node, "%s %s" % (emoji, label or name))


def specimen(node, no, prefix="SPECIMEN #"):
    node.className = "as-specimen"
    text(node, "%s%03d" % (prefix, int(no or 0)))


def avatar(node, person, size="md"):
    node.className = "as-avatar as-avatar-%s" % size
    node.setAttribute("aria-hidden", "true")
    text(node, (person or {}).get("avatar") or "🥼")


def byline(link, av, name, extra, author, extra_text=""):
    """<a class="as-byline"> with the avatar, the name in bold and an optional ' · 2 days ago · 3 min read'."""
    author = author or {}
    if author.get("uid"):
        link.setAttribute("href", "#writer/%s" % author["uid"])
    else:
        link.removeAttribute("href")
    avatar(av, author, "sm")
    text(name, author.get("name") or "A mystery scientist")
    text(extra, extra_text)
