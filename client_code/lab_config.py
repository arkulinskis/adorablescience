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

# Study snapshot: who or what was studied? (key, choice label, emoji, reader phrase, early-stage, card chip)
# Early-stage results (animals, cells, models) are where hype lives: their cards get a chip and reviewers look for a
# "Hold your horses" caveat.
STUDY_SUBJECTS = [
    ("people", "People", "🧑", "Studied in people", False, ""),
    ("animals", "Animals", "🐭", "Studied in animals", True, "🐭 In animals"),
    ("cells", "Cells in a dish", "🧫", "Studied in cells in a dish", True, "🧫 In cells"),
    ("model", "Computer model", "💻", "A computer model", True, "💻 Model only"),
    ("space", "Space & sky", "🔭", "Observed in space & sky", False, ""),
    ("earth", "Earth & fossils", "🪨", "Studied in rocks, ice & fossils", False, ""),
    ("review", "Many studies combined", "📚", "Many studies combined", False, ""),
    ("other", "Something else", "🔍", "Something else was studied", False, ""),
]
STUDY_SUBJECT = {k: {"key": k, "label": l, "emoji": e, "phrase": p, "early": early, "chip": chip}
                 for k, l, e, p, early, chip in STUDY_SUBJECTS}
SIZE_MAX = 40
CAVEAT_MAX = 180
EARLY_EVIDENCE = ("preprint", "speculative")

TITLE_MAX = 140
DEK_MAX = 280
BODY_MAX = 40000
BODY_MIN_SUBMIT = 80
SOURCES_MAX = 20
NOTE_MAX = 2000
BIO_MAX = 500

_URL_RE = re.compile(r"^https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,}(:[0-9]+)?([/?#][^\s]*)?$")
_CITE_RE = re.compile(r"\[(\d{1,2})\](?!\()")
_DOI_RE = re.compile(r"10\.[0-9]{4,9}/[^\s\"<>?#&]+")
_SLUG_FROM = "àáâãäåāăąçćčďđèéêëēėęěìíîïīįıłñńňòóôõöøōőřśšşťùúûüūůűųýÿžźż"
_SLUG_TO = "a" * 9 + "c" * 3 + "d" * 2 + "e" * 8 + "i" * 7 + "l" + "n" * 3 + "o" * 8 + "r" + "s" * 3 + "t" + "u" * 8 + "y" * 2 + "z" * 3


def needs_caveat(subject, evidence):
    """Early-stage results (animals, cells, models, preprints, speculation) should say what they don't mean yet."""
    s = STUDY_SUBJECT.get(subject or "")
    return bool(s and s["early"]) or (evidence or "") in EARLY_EVIDENCE


def doi_of(text):
    """The DOI inside a doi.org link, a publisher link or a bare 'doi:10.xxxx/...' (or '' when there is none)."""
    m = _DOI_RE.search((text or "").strip())
    if not m:
        return ""
    doi = m.group(0)
    while doi and doi[-1] in ".,;:)]}'":
        doi = doi[:-1]
    return doi if len(doi) > 8 else ""


def slugify(title, limit=60):
    """'Why wombat poop comes out in cubes!' -> 'why-wombat-poop-comes-out-in-cubes' (ASCII, at most 60 characters)."""
    out = []
    for ch in (title or "").lower():
        i = _SLUG_FROM.find(ch)
        if i >= 0:
            ch = _SLUG_TO[i]
        elif ch == "ß":
            ch = "ss"
        elif ch == "æ":
            ch = "ae"
        elif ch == "œ":
            ch = "oe"
        if len(ch) > 1 or ("a" <= ch <= "z") or ("0" <= ch <= "9"):
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    slug = "".join(out).strip("-")
    if len(slug) > limit:
        cut = slug[:limit]
        slug = cut.rsplit("-", 1)[0] if "-" in cut[limit // 2:] else cut
        slug = slug.strip("-")
    return slug or "story"


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
    m: dict
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
