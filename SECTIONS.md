# Sections design: Uses and Books

Status: designed, not built. Written 2026-11-06.

Read `CLAUDE.md` and `README.md` first. The repo is public, so keep private vault content out of it.

## Goal

Add two parts of the site that don't behave like posts:

- **Uses:** living pages about the tools Josh uses, connected by links in any structure he likes. Neovim can have its own page and also appear under a Terminal Tools hub.
- **Books:** a page per book, with a generated list that can be sorted by date read, title, or author.

Posts record a moment. Uses and Books describe how things are now, and get edited in place. News about either goes in a post, tagged something like `tool-updates` or `book-updates`, linking to the page.

## Decisions

### Vault layout

```text
Areas/Blog/Posts/   -> content/posts/   /posts/<slug>/
Areas/Blog/Uses/    -> content/uses/    /uses/<slug>/
Areas/Blog/Books/   -> content/books/   /books/<slug>/
```

- The script keeps a short list of sections, each setting its folder, output path, allowed properties, and whether its pages are dated. Adding a later section, such as articles, should be mostly configuration.
- Subfolders inside a section don't affect URLs. Every page is `/<section>/<slug>/`, so notes can be reorganized without breaking links.
- Images go to `static/images/<section>/<slug>/`. Post images keep their current paths.

### Hubs

- `_hub.md` in a section folder becomes that section's `content/<section>/_index.md`.
- Uses has a hand-written hub in the vault. Further hubs, like Terminal Tools, are ordinary Uses notes that link to other notes. There are no categories: links are the structure.
- Tools with no page yet are plain external links in a hub.
- The Posts and Books lists are generated. `_hub.md` is optional there and supplies intro text only.
- A hub needs `title` and `draft: false`, but no `slug`.
- Several notes share the name `_hub`, so the duplicate name check must skip hubs and a bare `[[_hub]]` must stop the run. Linking to a hub by path, like `[[Uses/_hub|my setup]]`, should resolve to `/uses/`.

### Properties

| Section | Allowed, besides `slug` and `draft` |
|---|---|
| Posts | `title`, `date`, `tags`, `series`, `description` |
| Uses | `title`, `tags`, `description` |
| Books | `title`, `author`, `authorSort`, `status`, `dateRead`, `rating`, `tags`, `description` |

- **`author` now means the author of the book.** Josh is no longer an author on posts, because this is a personal blog with no guest posts.
- `status` is required on books and must be `to-be-read`, `reading`, `finished`, or `did-not-finish`.
- `dateRead` is required when `status` is `finished`, and not allowed on any other status.
- `rating` is a whole number of stars from 1 to 5, with no halves. It's optional, and allowed only on `finished` and `did-not-finish`. Anything else stops the run.
- `authorSort` is optional and overrides the default, which is the last word of `author`.
- Tags are optional on Uses and Books, for tying them to topics like security or devops.
- Uses and Books have no `date` and show no `Published` line. They keep `lastmod`, so `Updated` still appears after an edit.
- Every book gets its own page, even a thin one, so backlinks have somewhere to land.

### Removing `author` from posts

These all use it today:

- `layouts/_default/single.html`: the `By` link in the sidebar. Left in place, every book links to a broken `/authors/<name>` page.
- `layouts/posts/list.html`: the author link in the post meta line.
- `content/posts/_index.md`, `archetypes/default.md`, and `content/posts/hello-world.md`.
- In the vault: `Hello World`, `What Is Devx`, and `Resources/Templates/Blog Post.md`. Posts that still have `author` will stop the run once it's disallowed there.

Keep these:

- `params.author` in `hugo.yaml`, because `rss.xml` uses it for feed metadata.
- `content/authors/josh-maxwell.md`, because `layouts/partials/about.html` links to it from the sidebar.

Show the book's author, status, date read, and rating in the sidebar on book pages, without a link.

### Book lists

The CSP blocks JavaScript, so each sort order is its own pre-built page:

- `/books/`: by date read. Reading first, then finished with the newest first, then did not finish, then to be read.
- `/books/by-title/`: all books by title, ignoring a leading "The", "A", or "An".
- `/books/by-author/`: all books by `authorSort`.

A second row of tabs under the main navigation links between them, and appears only on these pages. Build it as a partial called from `layouts/partials/header.html`, so it sits directly under the navigation rather than inside the content box. Show each book's status on the title and author pages, and its rating on all three. Draw stars with Font Awesome's `fa-star` icons, which the CSP already allows. There's no sort by rating.

The script writes `titleSort` and `authorSort` into generated book files. Add both to the keys ignored by `properties()`, or every run will look like an edit and bump `lastmod`.

### Links

- `[[Note]]` resolves across all sections, to the right `/<section>/<slug>/`.
- `notes_by_name` silently keeps the last note when two share a name, so a duplicate name must stop the run. A book and a post with the same title is the likely case.
- **Links to unpublished notes:** a link to an unpublished note under `Areas/Blog/` is allowed and points at its eventual URL, returning 404 until that note is published. This replaces the current rule, which stops the run. The note still needs a valid `slug`, or there's no URL to link to.
- **Links outside `Areas/Blog/`** stop the run.

### Backlinks

Every page shows a "Mentioned in" list, from the start.

- The script writes `data/backlinks.json`, mapping each target page to the pages linking to it, with keys sorted so diffs stay small. Use the standard library `json` module.
- Keeping this out of front matter means publishing a post doesn't rewrite the pages it links to, and doesn't touch their `lastmod`.
- Store page paths, not titles. The template looks each one up with `site.GetPage` and skips any that don't resolve, so a future-dated or removed page never shows.
- Only `[[wikilinks]]` count, from published notes. Hubs count as sources. Skip self-links.
- Sort posts newest first, then everything else by title.

### Feeds, tags, and navigation

- Uses and Books stay out of RSS. The site and tag feeds already filter to the `posts` section, so this needs no change.
- Set `outputs: [html]` on these sections. Otherwise Hugo generates empty `index.xml` feeds, including under `by-title` and `by-author`.
- Tag pages list every section. They need no change, and pages without a date render fine there.
- Add `Uses` and `Books` to the main menu in `hugo.yaml`, hidden until they have content, using the same approach as Series in `layouts/partials/header.html`.

## Verified in a throwaway build

Tested on Hugo 0.169.0, which matches Production and Preview on Cloudflare.

- **Sort pages:** `content/books/by-title/_index.md` with `layout: by-title` and a matching `layouts/books/by-title.html` renders at the right URL. Same for `by-author`. Each template lists `where site.RegularPages "Section" "books"`, because `.Pages` on the subsection is empty.
- **Don't use custom output formats for this.** Their `path` is a URL prefix, so they render at `/by-title/books/`.
- **Backlinks:** a data file plus `site.GetPage` renders correctly in `single.html`. This was tested with YAML, and JSON should behave the same. The lookup key was the page's `.Path` without the leading slash.
- **Feeds:** books stayed out of the site feed and the tag feed.
- **Confirmed problem:** a book with `author` currently renders `By <a href="/authors/frank-herbert">`.

The tab row, `_hub.md` handling, and a hub as a backlink source are untested.

## Build order

Each step should leave the site working. Don't push to `main` without asking.

1. **Make the script section-aware, with Posts only.** No visible change to the site. Cover paths, per-section properties, the duplicate name check, cross-section links, and per-section `--prune`.
2. **Remove `author` from posts.**
3. **Add Uses, hubs, and backlinks.**
4. **Add Books and the sort pages.**
5. **Update `README.md` and `CLAUDE.md`, then delete this file.** Its decisions should live in those docs once built.

## Constraints

- **a-Shell:** the script must stay standard library only and run on Python 3.10 or later.
- **Script safety:** keep "every note is checked before anything is written". It never commits or pushes.
- **`--prune`:** the check for no published notes must apply per section, so an empty section can't delete that section's pages. Only `*.md` directly in the output folder is eligible, which protects `by-title/` and `by-author/`. Don't prune `_index.md`.
- **CSP:** the policy stays as it is. No JavaScript or inline styles in new templates. Book covers go in the vault, because remote images hit the host check in the script.
- **Tests:** extend `scripts/test_publish_from_vault.py`. Its `publish` helper writes to `Areas/Blog/`, so it needs updating in step 1.
- **Verifying:** follow `CLAUDE.md`. Check rendered HTML and live URLs, and use `--destination` outside the repo.

## Migration

The order matters, because the phone runs its own copy of the repo.

1. Merge the section-aware script, and pull it in Working Copy on the phone.
2. Move the notes in `Areas/Blog/` into `Areas/Blog/Posts/`. URLs stay the same because they come from `slug`.
3. Point the `New Blog Post` QuickAdd choice at `Areas/Blog/Posts/`, and update the `Blog Post` template.
4. Add `New Uses Page` and `New Book` templates and QuickAdd choices. QuickAdd is set up separately on the Mac and iPhone, so this happens on both.
5. Confirm a `--check` run on both devices.

Josh makes the vault and QuickAdd changes, or approves them first. The script otherwise only reads the vault.
