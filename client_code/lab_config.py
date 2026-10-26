# lab_config — shared constants. Pure Python: imported by client pages AND server modules.
import re

APP_NAME = "Adorable Science"
TAGLINE = "Fuzzy-hearted news from the frontiers of discovery"

# (key, label, emoji, tone) — tone picks the card colour in theme.css (.tone-<tone>)
CATEGORIES = [
    ("space", "Space", "🪐", "sky"),
    ("life", "Life Sciences", "🧬", "mint"),
    ("critters", "Critters", "🐾", "peach"),
    ("chem", "Chemistry", "⚗️", "lav"),
    ("physics", "Physics", "⚛️", "sky"),
    ("earth", "Earth & Climate", "🌋", "mint"),
    ("brain", "Mind & Brain", "🧠", "pink"),
    ("health", "Health", "🩺", "pink"),
    ("tech", "Tech & AI", "🤖", "butter"),
]
CATEGORY = {k: {"key": k, "label": l, "emoji": e, "tone": t} for k, l, e, t in CATEGORIES}

# How solid is the science behind the story?
EVIDENCE = [
    ("established", "Established science", "🧱"),
    ("peer", "Fresh peer-reviewed study", "📄"),
    ("preprint", "Preprint / early results", "🧪"),
    ("speculative", "Speculative & fun", "🦄"),
]
EVIDENCE_LEVEL = {k: {"key": k, "label": l, "emoji": e} for k, l, e in EVIDENCE}

SOURCE_KINDS = [
    ("journal", "Journal article", "📄"),
    ("preprint", "Preprint", "📝"),
    ("dataset", "Dataset", "📊"),
    ("agency", "Agency / institute", "🏛️"),
    ("news", "News report", "📰"),
    ("book", "Book", "📚"),
    ("video", "Video / talk", "🎥"),
    ("other", "Other", "🔗"),
]
SOURCE_KIND = {k: {"key": k, "label": l, "emoji": e} for k, l, e in SOURCE_KINDS}

# key -> (label, emoji, explanation)
STATUSES = {
    "draft": ("In the Petri dish", "🧫", "Draft. Only you can see it."),
    "pending": ("Under the microscope", "🔬", "Waiting for a Lab Director to review it."),
    "rejected": ("Needs more data", "🧪", "Sent back with reviewer notes. Revise and resubmit!"),
    "published": ("Published", "🚀", "Live on the front page."),
}
STATUS_ORDER = ["rejected", "draft", "pending", "published"]

AVATARS = ["🐹", "🐰", "🦊", "🐼", "🐨", "🐸", "🦉", "🐙", "🦔", "🐧", "🦦", "🐝", "🐱", "🐶", "🦄", "🐢", "🦥", "🐳"]
COVERS = ["🔭", "🧪", "🧬", "🪐", "🐙", "🦠", "🌋", "🧲", "🦕", "🐝", "🌱", "⚛️", "🧠", "🛰️", "🐧", "🍄", "💎", "🌊", "🦋", "🌌"]

FUN_ADJECTIVES = ["Curious", "Fluffy", "Quantum", "Sparkly", "Brave", "Gentle", "Fizzy", "Cosmic", "Nimble", "Cozy", "Dapper", "Stellar"]
FUN_ANIMALS = ["Quokka", "Axolotl", "Otter", "Tardigrade", "Pangolin", "Capybara", "Narwhal", "Hedgehog", "Red Panda", "Puffin", "Wombat", "Octopus"]

# True (and delightful) facts for the footer.
LAB_FACTS = [
    "Octopuses have three hearts and blue blood.",
    "Wombats produce cube-shaped poop.",
    "A day on Venus is longer than its year.",
    "Tardigrades have survived exposure to the vacuum of space.",
    "Bananas are slightly radioactive, thanks to potassium-40.",
    "There are more trees on Earth than stars in the Milky Way.",
    "Sea otters often hold paws while they sleep so they don't drift apart.",
    "Honeybees can be trained to recognise human faces.",
    "A teaspoon of neutron star would weigh around a billion tonnes.",
    "Axolotls can regrow limbs, parts of their heart, and even bits of their brain.",
    "Sloths can hold their breath longer than dolphins can.",
    "Your body contains roughly as many bacterial cells as human cells.",
]

TITLE_MAX = 140
DEK_MAX = 280
BODY_MAX = 40000
BODY_MIN_SUBMIT = 80
SOURCES_MAX = 20
NOTE_MAX = 2000
BIO_MAX = 500

_URL_RE = re.compile(r"^https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,}(:[0-9]+)?([/?#][^\s]*)?$")
_CITE_RE = re.compile(r"\[(\d{1,2})\](?!\()")


def is_url(s):
    return bool(s) and bool(_URL_RE.match(s.strip()))


def domain_of(url):
    url = (url or "").strip()
    if "://" in url:
        url = url.split("://", 1)[1]
    host = url.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    if host.lower().startswith("www."):
        host = host[4:]
    return host.lower()


def cited_numbers(body):
    """Which [n] citation markers appear in an article body."""
    return sorted(set(int(n) for n in _CITE_RE.findall(body or "")))


def citation_meter(n_sources, n_cited=0):
    """How well-sourced is this? -> dict(pct, label, emoji, tone, tip)."""
    if n_sources <= 0:
        m = dict(pct=6, label="Pure hypothesis", emoji="😿", tone="peach",
                 tip="No sources yet. Link the original study so readers can check your work.")
    elif n_sources == 1:
        m = dict(pct=38, label="Single specimen", emoji="🙂", tone="butter",
                 tip="A good start! A second, independent source makes a story much stronger.")
    elif n_sources == 2:
        m = dict(pct=70, label="Corroborated", emoji="😺", tone="sky",
                 tip="Nice. One more source unlocks the Peer-purr-viewed gold star.")
    else:
        m = dict(pct=100, label="Peer-purr-viewed", emoji="😻", tone="mint",
                 tip="Beautifully sourced. Reviewers love this.")
    if n_sources > 0 and n_cited < n_sources:
        m["tip"] += " Tip: type [1], [2]… in your text to cite each source inline."
    return m
