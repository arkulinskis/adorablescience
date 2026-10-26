# Render — turns an article body (a small, safe Markdown dialect) into HTML on the server.
# Everything the writer typed is escaped first; only the formatting below becomes markup.
#
#   ## Heading        ### Smaller heading
#   **bold**  *italic*  `code`  [link text](https://...)
#   - bullet          1. numbered
#   > quote           !! Lab note (a highlighted callout)
#   ---               (a divider)
#   [1] [2] ...       inline citation to source #1, #2 ...
import re

_CODE = re.compile(r"`([^`\n]+)`")
_LINK = re.compile(r"\[([^\]\n]+)\]\((https?://[^\s)]+)\)")
_CITE = re.compile(r"\[(\d{1,2})\](?!\()")
_BOLD = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
_ITAL = re.compile(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])")
_ITAL2 = re.compile(r"(?<![\w])_(?=\S)(.+?)(?<=\S)_(?![\w])")
_OL = re.compile(r"^\d{1,3}[.)]\s+")


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&#39;"))


def inline(text, sources):
    s = esc(text)
    stash = []

    def keep(html):
        stash.append(html)
        return "\x00%d\x00" % (len(stash) - 1)

    s = _CODE.sub(lambda m: keep("<code>%s</code>" % m.group(1)), s)
    s = _LINK.sub(lambda m: keep('<a href="%s" target="_blank" rel="noopener nofollow">%s</a>'
                                 % (m.group(2), m.group(1))), s)

    def cite(m):
        n = int(m.group(1))
        if 1 <= n <= len(sources) and sources[n - 1].get("url"):
            src = sources[n - 1]
            return keep('<sup class="as-cite"><a href="%s" target="_blank" rel="noopener nofollow" '
                        'title="%s">%d</a></sup>' % (esc(src["url"]), esc(src["title"]), n))
        return keep('<sup class="as-cite as-cite-missing" title="No source #%d yet">%d?</sup>' % (n, n))

    s = _CITE.sub(cite, s)
    s = _BOLD.sub(r"<strong>\1</strong>", s)
    s = _ITAL.sub(r"<em>\1</em>", s)
    s = _ITAL2.sub(r"<em>\1</em>", s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], s)
    return s


def markdown(body, sources=()):
    sources = list(sources or [])
    lines = (body or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out = []
    para = []
    lst = None  # ("ul"|"ol", [items])

    def flush_para():
        if para:
            out.append("<p>%s</p>" % "<br>".join(inline(l, sources) for l in para))
            del para[:]

    def flush_list():
        nonlocal lst
        if lst:
            tag, items = lst
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(i, sources) for i in items), tag))
            lst = None

    quote = []

    def flush_quote():
        if quote:
            out.append("<blockquote>%s</blockquote>" % "<br>".join(inline(l, sources) for l in quote))
            del quote[:]

    def flush_all():
        flush_para()
        flush_list()
        flush_quote()

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_all()
            continue
        if line in ("---", "***", "___"):
            flush_all()
            out.append("<hr>")
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            text = line.lstrip("#").strip()
            if text:
                flush_all()
                tag = "h3" if level <= 2 else "h4"
                out.append("<%s>%s</%s>" % (tag, inline(text, sources), tag))
                continue
        if line.startswith("!!"):
            flush_all()
            out.append('<aside class="as-labnote"><span class="as-labnote-tag">🧪 Lab note</span>%s</aside>'
                       % inline(line[2:].strip(), sources))
            continue
        if line.startswith(">"):
            flush_para()
            flush_list()
            quote.append(line[1:].strip())
            continue
        if line[:2] in ("- ", "* ", "• "):
            flush_para()
            flush_quote()
            if not lst or lst[0] != "ul":
                flush_list()
                lst = ("ul", [])
            lst[1].append(line[2:].strip())
            continue
        if _OL.match(line):
            flush_para()
            flush_quote()
            if not lst or lst[0] != "ol":
                flush_list()
                lst = ("ol", [])
            lst[1].append(_OL.sub("", line, count=1))
            continue
        flush_list()
        flush_quote()
        para.append(line)
    flush_all()
    return "\n".join(out)
