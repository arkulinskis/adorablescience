---
name: adorablescience
description: Context, workflow and recipes for Adorable Science, the user's Anvil community science-news app ("adorable meets science"): anyone writes articles with sources, Lab Directors (admins) review and publish them, writer profiles, boops. Load this before any feature request, bug fix, restyle or deploy for Adorable Science.
---

# Adorable Science: working on the app

**What it is:** fuzzy-hearted, well-sourced science news. Anyone signs up and writes articles; **nothing is published until a Lab Director (admin) approves it**; approved articles appear on the front page.
- Stages: `draft` (🧫 In the Petri dish) → `pending` (🔬 Under the microscope) → `published` (🚀) or `rejected` (🧪 Needs more data, with the reviewer's note). Editing a published article takes it off the front page until approved again.
- Sources are strongly encouraged: live citation meter, one-click `[1]` inline citations, a "no sources?" warning on submit, an "Unsourced" badge, an automatic reviewer checklist.
- Writer profiles (`#writer/<id>`) with stats and badges; Writers page; **boops** 🐾 (likes); Directors can feature an article.
- The **first person to sign in becomes the first Lab Director**; Directors promote others (Review desk → Lab members).

**Where it lives:**
- App repo **github.com/arkulinskis/adorablescience**, branch `master`; Anvil pulls master. Live: https://adorablescience.com (per apps.json).
- This folder **is** the Anvil repo ("git" layout). README.md has the full feature list and formatting syntax.

**What the user wants:** the interface should feel like a mix of adorable and science (Fredoka headings, Nunito text, Space Mono labels; Bea-the-Beaker mascot and spinner). Creative, assumed details welcome. Claude deploys.

## Workflow

1. `python -I C:\Users\arkvi\Documents\CLAUDE\APP_MAKER\tools\apps_status.py adorablescience -v`; pull Anvil's commits; never touch someone else's uncommitted work.
2. Edit the files here.
3. `python C:\Users\arkvi\Documents\CLAUDE\APP_MAKER\tools\gitapp_check.py adorablescience` → `ALL CHECKS PASSED` (it understands the `@api` decorator).
   Server logic: `python ...\APP_MAKER\tools\gitapp_test.py adorablescience <script>`; `from app import Articles, Review, Lab, lab_config` works (lab_config lives in client_code and is shared, like on Anvil).
4. Commit only your files as arkulinskis with the Co-Authored-By line; `git push origin master`.
5. Schema changes: `anvil.yaml → db_schema`; the user accepts the Schema Mismatch alert.

## Architecture

```
client_code/Main/          header, footer, router (ROUTES: "" topic article writers writer me write lab join review); sends clicks on [data-action] to page.on_action()
client_code/as_ui.py       HTML building blocks: mascot, avatar, byline, chips, badges, meter, cards, toast, modal, ask, loading/error blocks; class Page
client_code/api.py         load(name, ...) quiet call / do(name, ...) with spinner; {"__oops__": msg} replies become api.LabError
client_code/lab_config.py  shared constants (fields, evidence levels, statuses) + citation helpers; used by the server too
client_code/page_*.py      home, article, editor (writing desk), lab (my articles), writers, auth, review (Lab Director desk)
server_code/Lab.py         @api(user=..., admin=...) decorator (registers the callable, turns Oops into {"__oops__"}), permissions, row → dict helpers
server_code/Render.py      safe Markdown-style renderer (escapes everything first)
server_code/Accounts.py    get_me, update_profile, list_writers, get_writer, list_members, set_admin
server_code/Articles.py    get_front_page, get_article, get_article_for_edit, save_article, withdraw_article, delete_article, my_articles, toggle_boop, preview_body
server_code/Review.py      review_queue, get_review, decide, published_list, set_featured, unpublish
theme/assets/theme.css     the whole look; beaker-spinner.svg; favicon
```

**Page pattern:** a page is a `ui.Page` subclass with `needs` (None / "user" / "admin"), `load()` (fetch with `api.load`), a paint method returning HTML, and `on_action(action, arg, el, ev)` for `data-action` clicks. Server functions are `@api(...)` in server modules and raise `Oops("friendly message")` for expected problems.

**Tables:** `users` (+ uid, display_name, avatar, specialty, bio, website, is_admin, legal_*), `articles` (specimen_no, dek, body, category, evidence, status, reviewer, review_note, featured, boops, source counts…), `sources`, `boops`, `lab_log`.

## Recipes

- **New server function:** `@api(user=True)` (or `admin=True`) in the right module; use Lab helpers (`me()`, `get_article_row`, `card`, `full_article`); raise `Oops` for user errors; log important actions with `log(...)`.
- **New page:** `client_code/page_x.py` with a `ui.Page` subclass, add it to `ROUTES` in Main.
- **Article formatting:** extend Render.py (escape first) and the README's formatting line.

## Gotchas

- No Email service in this app (unlike MonShop/CityCrossers): adding notifications by email means adding the service + legal kit facts.
- `python -I` hides PyYAML: run gitapp_check/gitapp_test without `-I`.

## Privacy & Terms (legal kit)

From `C:/Users/arkvi/Documents/CLAUDE/APP_MAKER/legal-kit`. Don't edit `theme/assets/legal-kit.js`, `client_code/legal.py` or `server_code/legal_server.py` here: change `apps/adorablescience.json` there, run `python -I build.py adorablescience && python -I install.py adorablescience`, then commit and push here.
- Sign-up keeps the consent tick box (page_auth.py); `legal.refresh_soon()` after sign-in, `legal.signed_out()` after sign-out.
