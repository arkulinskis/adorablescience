# Sources: DOI magic on the writing desk and the review desk, through Crossref's free REST API (no key, no account).
#
#   lookup_doi(text)      a doi.org link / bare DOI -> title, journal (year), kind, retraction flags  (writers)
#   find_study(words)     a few words -> up to 5 papers to pick from                                  (writers)
#   check_retractions(no) the article's DOI sources -> one reviewer-checklist line                     (Lab Directors)
#
# Crossref includes Retraction Watch's data (since 2025): a retracted paper lists {"type": "retraction"} in
# "updated-by". We send only the DOI or the search words, with a polite User-Agent naming the site (no email).
# Every network problem comes back as {"missing": True} so the writer can carry on by hand: never an Oops page.
# Answers are kept for 6 hours in this server process (a small cache; Crossref asks clients to be gentle).
import time
from urllib.parse import quote

import anvil.http

from . import lab_config as C
from .Lab import Oops, api, clean, get_article_row, sources_of

API = "https://api.crossref.org"
UA = "AdorableScience/1.0 (+https://adorablescience.com)"
TIMEOUT = 6
TTL = 6 * 3600
_cache: dict = {}

KINDS = {"journal-article": "journal", "proceedings-article": "journal", "posted-content": "preprint",
         "dataset": "dataset", "report": "agency", "report-series": "agency", "report-component": "agency"}
FLAGS = {  # Crossref update type -> our flag
    "retraction": "retracted", "withdrawal": "retracted", "removal": "retracted",
    "expression_of_concern": "concern", "expression-of-concern": "concern",
    "correction": "corrected", "erratum": "corrected", "corrigendum": "corrected",
}
FLAG_NOTES = {
    "retracted": "⚠️ Retracted (Crossref + Retraction Watch). Only cite it if your story is about the retraction.",
    "concern": "⚠️ The journal published an expression of concern about this paper. Read it before relying on it.",
    "corrected": "📝 This paper has a published correction. Check that the part you cite still holds.",
}


def _fetch(path, timeout=TIMEOUT):
    """GET a Crossref path (cached). Raises on any network or HTTP problem."""
    hit = _cache.get(path)
    if hit and time.time() - hit[0] < TTL:
        return hit[1]
    reply = anvil.http.request(API + path, json=True, timeout=timeout,
                               headers={"User-Agent": UA, "Accept": "application/json"})
    if len(_cache) > 400:
        _cache.clear()
    _cache[path] = (time.time(), reply)
    return reply


def _kind(t):
    t = t or ""
    if t.startswith("book") or t in ("monograph", "edited-book", "reference-book"):
        return "book"
    return KINDS.get(t, "other")


def _year(m):
    for key in ("published-print", "published-online", "published", "issued", "created"):
        parts = ((m.get(key) or {}).get("date-parts") or [[None]])[0]
        if parts and parts[0]:
            return int(parts[0])
    return 0


def _flag(m):
    """The most serious editorial notice on a work: retracted > concern > corrected (or '')."""
    found = set()
    for u in (m.get("updated-by") or []):
        f = FLAGS.get(str(u.get("type") or "").lower())
        if f:
            found.add(f)
    title = " ".join(m.get("title") or [])
    if title.upper().startswith(("RETRACTED", "WITHDRAWN")):
        found.add("retracted")
    for f in ("retracted", "concern", "corrected"):
        if f in found:
            return f
    return ""


def _work(m):
    """A Crossref work -> the plain dict the browser gets."""
    doi = str(m.get("DOI") or "")
    title = " ".join(" ".join(m.get("title") or []).split())
    journal = (m.get("container-title") or [""])[0] or ""
    if not journal and m.get("type") == "posted-content":  # preprints: the server's name (bioRxiv, arXiv...)
        journal = ((m.get("institution") or [{}])[0] or {}).get("name") or ""
    journal = journal or m.get("publisher") or ""
    year = _year(m)
    authors = m.get("author") or []
    first = (authors[0].get("family") or authors[0].get("name") or "") if authors else ""
    flag = _flag(m)
    return {
        "doi": doi,
        "url": "https://doi.org/" + doi if doi else "",
        "title": title[:200],
        "publisher": (("%s (%d)" % (journal, year)) if journal and year else (journal or (str(year) if year else "")))[:100],
        "kind": _kind(m.get("type")),
        "year": year,
        "authors": (first + (" et al." if len(authors) > 1 else "")) if first else "",
        "flag": flag,
        "flag_note": FLAG_NOTES.get(flag, ""),
    }


def _lookup(doi, timeout=TIMEOUT):
    """-> work dict, {"missing": True, "not_found": True} (Crossref doesn't know it) or {"missing": True} (offline)."""
    try:
        reply = _fetch("/works/" + quote(doi, safe="/:;()._-"), timeout)
    except anvil.http.HttpError as e:
        if getattr(e, "status", 0) == 404:
            return {"missing": True, "not_found": True}
        return {"missing": True}
    except Exception:
        return {"missing": True}
    m = reply.get("message") if isinstance(reply, dict) else None
    if not isinstance(m, dict):
        return {"missing": True}
    return _work(m)


@api(user=True)
def lookup_doi(text):
    """Fill a source row from a DOI. Never raises: {"missing": True[, "not_found"/"no_doi"]} when it can't."""
    doi = C.doi_of(clean(text, 600))
    if not doi:
        return {"missing": True, "no_doi": True}
    return _lookup(doi)


@api(user=True)
def find_study(words):
    """Search Crossref for the original study: up to 5 papers, or {"missing": True} when Crossref can't be reached."""
    words = " ".join(clean(words, 200).split())
    if len(words.replace(" ", "")) < 8:
        raise Oops("Type a few more words (the paper's title, a lead author, the journal…) so Bea can sniff it out. 🔎")
    try:
        reply = _fetch("/works?rows=5&query.bibliographic=" + quote(words, safe=""))
    except Exception:
        return {"missing": True}
    items = ((reply or {}).get("message") or {}).get("items") or [] if isinstance(reply, dict) else []
    out = [_work(m) for m in items[:5] if isinstance(m, dict) and m.get("DOI")]
    return {"items": out}


@api(admin=True)
def check_retractions(no):
    """The reviewer checklist line "No retracted or flagged papers": every DOI source (at most 10, ~12 s budget).
    ok = True (all clear), False (something is flagged) or None (couldn't check: no DOIs, or Crossref offline)."""
    a = get_article_row(no)
    todo = []
    for s in sources_of(a):
        doi = C.doi_of(s["url"])
        if doi and doi.lower() not in [d.lower() for _, d in todo]:
            todo.append((s["n"], doi))
    label = "No retracted or flagged papers"
    if not todo:
        return {"ok": None, "label": label, "detail": "No DOI links to check. Only doi.org sources can be checked."}
    start, flagged, checked, missed = time.time(), [], 0, 0
    for n, doi in todo[:10]:
        left = 12 - (time.time() - start)
        if left < 1:
            missed += 1
            continue
        w = _lookup(doi, min(TIMEOUT, left))
        if w.get("missing"):  # offline, or a DOI Crossref doesn't hold (DataCite datasets, Zenodo...)
            missed += 1
            continue
        checked += 1
        if w["flag"]:
            flagged.append("#%d %s" % (n, {"retracted": "retracted", "concern": "expression of concern",
                                           "corrected": "corrected"}[w["flag"]]))
    serious = [f for f in flagged if not f.endswith("corrected")]
    if serious:
        return {"ok": False, "label": label, "detail": "⚠️ " + ", ".join(flagged) + " (Crossref + Retraction Watch)"}
    if not checked:
        return {"ok": None, "label": label, "detail": "Couldn't reach Crossref just now. Check the DOI links by hand."}
    detail = "%d DOI%s checked with Crossref + Retraction Watch" % (checked, "" if checked == 1 else "s")
    if flagged:
        detail += " · " + ", ".join(flagged) + " (fine to cite)"
    if missed or len(todo) > 10:
        detail += " · %d not checked" % (missed + max(0, len(todo) - 10))
    return {"ok": True, "label": label, "detail": detail}
