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

## First run: becoming a Lab Director

The **first person to sign in becomes the first Lab Director**, so sign up yourself right after
publishing. After that, Directors can promote others from **Review desk → Lab members**. You can also tick
`is_admin` for a user in the Data Tables editor.

Sign-up uses email + password and asks new users to confirm their email address (Users service settings).

## Code map

```
client_code/
  Main/            startup form: header, footer, routing (#article/12, #writer/abc, #write, #review…)
  as_ui.py         HTML building blocks, the Bea-the-Beaker mascot, toasts and dialogs
  api.py           server calls; friendly server errors become LabError
  lab_config.py    shared constants (fields, evidence levels, statuses); also used by the server
  page_home.py     front page          page_article.py  reading an article
  page_editor.py   writing desk        page_lab.py      "My lab": my articles by status
  page_writers.py  roster, profile, edit profile
  page_auth.py     sign in / sign up   page_review.py   Lab Director review desk
server_code/
  Lab.py           @api decorator, permissions, row → dict helpers
  Render.py        safe Markdown-style renderer for article bodies (escapes everything first)
  Accounts.py      me, profiles, writers, admin roles
  Articles.py      front page, read, save/submit, withdraw, delete, boops
  Review.py        review queue, approve / send back, feature, take down
theme/assets/theme.css   the whole look
```

Pages build HTML in Python; `Main` sends clicks on elements with `data-action="…"` back to the
current page's `on_action()`. All server functions return plain dicts, so writer emails and unpublished
drafts never reach other people's browsers.

### Article formatting

`## Heading` · `**bold**` · `*italic*` · `- bullet` · `1. numbered` · `> quote` ·
`!! lab note` (callout) · `[text](https://link)` · `[1]` cites source #1
