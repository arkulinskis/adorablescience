# 🧪 Adorable Science

Fuzzy-hearted, well-sourced science news. Anyone can sign up and write articles; **nothing is published
until a Lab Director (admin) reviews and approves it**. Approved articles appear on the front page.

Built with [Anvil](https://anvil.works). Clone it into Anvil with **"Clone from GitHub"** and press **Run**.

## How it works

| Stage | Name in the app | Who sees it |
|---|---|---|
| `draft` | 🧫 In the Petri dish | The writer only |
| `pending` | 🔬 Under the microscope | The writer + Lab Directors (review queue) |
| `rejected` | 🧪 Needs more data | The writer, with the reviewer's note |
| `published` | 🚀 Published | Everyone, on the front page |

- **Editing a published article** takes it off the front page until it's approved again.
- **Sources are strongly encouraged:** a live citation meter, one-click `[1]` inline citations that link
  straight to the source, a "no sources?" warning on submit, an "Unsourced" badge on published articles,
  and an automatic checklist for reviewers (source count, inline citations, https, news-only sources…).
- **Writer profiles** (`#writer/<id>`) show a writer's published articles, stats and badges.
  The **Writers** page lists everyone with at least one published article.
- **Boops** 🐾 are likes. Lab Directors can feature an article at the top of the front page.
- **Real addresses** (server_code/Public.py): every published story lives at `/a/<no>/<slug>` (a light page with its
  own link preview, NewsArticle JSON-LD, sources and "Boop it in the lab"); writers with a published story get a public
  portfolio at `/w/<uid>`; `/feed.xml` (RSS 2.0, latest 30, full text) and `/sitemap-articles.xml`. Drafts, pending
  and taken-down stories answer a friendly 404 that never names them. "Copy link" / "🔗 Share" copy the `/a/` address.
- **Study snapshot:** writers say who or what was studied (people, animals, cells, a model…), how many, and a
  "🐴 Hold your horses" caveat. Readers see the strip under the byline; animal, cell and model studies carry a chip
  ("🐭 In animals") on their cards; reviewers get two checklist lines for it.
- **DOI magic** (server_code/Sources.py, Crossref's free API, no key): "✨ Fill from DOI" fills a source's title,
  journal and type; "🔎 Find the original study" lists 5 papers to pick from; retracted papers (Retraction Watch data)
  get a red note, and the review desk checks every DOI source ("No retracted or flagged papers").

## First run: becoming a Lab Director

The **first person to sign in becomes the first Lab Director**, so sign up yourself right after
publishing. After that, Directors can promote others from **Review desk → Lab members**. You can also tick
`is_admin` for a user in the Data Tables editor.

**Empty front page?** While nothing is published, **Review desk → Published** offers *Publish the starter articles*:
five short, sourced articles (wombat cubes, puppy-dog eyes, tardigrades in space, ticklish rats, bumblebees at play) by
the "Adorable Science team" account, which nobody can sign in to. Each ends with a note saying it's a starter; take any
of them down like any other article.

Sign-up uses email + password and asks new users to confirm their email address (Users service settings).

## Code map

Native Anvil Forms (Python + HTML templates, a layout, custom components, RepeatingPanels), since Nov 2026.

```
client_code/
  startup.py       get_me, Privacy & Terms kit, router.start()
  router.py        #addresses -> page Forms (#, #topic/x, #article/12, #writer/abc, #write, #lab, #join, #review/12 ...)
  state.py         signed-in person, server calls ({"__oops__"} -> toast), toasts, theme, accessibility helpers
  api.py           api.load: server calls for pages; friendly server errors become LabError (the "Oops" page)
  auth.py          sign in / sign up / reset / Continue with Google / sign out
  bits.py          the little stickers: field chip, evidence, sources badge, status pill, specimen, avatar, byline
  lab_config.py    shared constants (fields, evidence levels, statuses); also used by the server
  Layouts/Shell    header (Bea, tabs, the signed-in writer), footer (lab fact, feedback, Privacy & Terms, light/dark)
  Pages/           Front, Article, Editor (writing desk), Lab (my articles), Writers, Writer, MyProfile, Join,
                   Review (Lab Director desk + one review), Problem (friendly "Oops")
  Components/      Mascot (Bea the Beaker), Meter (citation meter), ArticleView (reader + review), Notebook
  Items/           RepeatingPanel rows: ArticleCard, FilterChip, SourceRef, SourceEdit, Pick, LabTile, LabGroup,
                   LabRow, DeskRow, MemberRow, WriterCard, Badge, Check, LogEntry, NavLink
  Dialogs/         NoSources (submit without sources?), TakeDown (note for the writer)
server_code/
  Lab.py           @api decorator, permissions, row -> dict helpers
  Render.py        safe Markdown-style renderer for article bodies (escapes everything first)
  Accounts.py      me, profiles, writers, admin roles
  Articles.py      front page, read, save/submit, withdraw, delete, boops
  Review.py        review queue, approve / send back, feature, take down
  Starters.py      five sourced starter articles for an empty front page
theme/assets/      app.css (the whole look, light + dark), app-kit.js, icons.css, theme.css (Bea spinner), legal-kit.js
tools/             check.py (Anvil validator, server tests), ui_test.py (real App Server in Docker + headless Chrome)
```

All server functions return plain dicts, so writer emails and unpublished drafts never reach other people's
browsers. Checks: `python tools/check.py` and `python -I tools/ui_test.py`.

### Article formatting

`## Heading` · `**bold**` · `*italic*` · `- bullet` · `1. numbered` · `> quote` ·
`!! lab note` (callout) · `[text](https://link)` · `[1]` cites source #1

<!-- libraries:start -->
## Libraries and outside services

What this project uses besides its own code. Generated by `APP_MAKER/tools/libraries.py`; to change it, edit `APP_MAKER/libraries/catalog.py` and re-run the script.

| Name | How it gets in | Used here for |
|---|---|---|
| [YouTube embeds](https://developers.google.com/youtube/player_parameters) | Outside web service | Plays a YouTube video inside the page (the privacy-friendlier youtube-nocookie address). |
| [Google Fonts](https://fonts.google.com) | Loaded from a CDN | Fredoka, Nunito, Space Mono |

**Built into the browser:** localStorage, Clipboard.

**Anvil platform:** Anvil, Anvil Data Tables, Anvil Email, Anvil JS bridge (anvil.js), Anvil Secrets, Anvil Users, Anvil Google service, Anvil HTTP, Anvil timezones (anvil.tz).

**Build and test tools (not shipped):** axe-core, Node.js, Headless Chrome (DevTools Protocol), PyYAML.

<!-- libraries:end -->
