# blog.cctechwiz.com

Source for [blog.cctechwiz.com](https://blog.cctechwiz.com/), built with [Hugo](https://gohugo.io/) and the [Risotto](https://github.com/joeroe/risotto) theme, and hosted on Cloudflare Pages.

## Setup

Install Hugo (extended) and Go. The theme is a Hugo Module, so it downloads automatically on the first build.

```sh
brew install hugo go
hugo server    # preview at http://localhost:1313
```

## Add a new post

Posts are written in Obsidian and copied here by a script. The vault is the source of truth, so edit posts there. Any edit made directly in `content/posts/` is overwritten by the next run.

1. In Obsidian, run `QuickAdd: New Blog Post` from the command palette and enter the title. This creates the note in `Areas/Blog/Posts/` from the `Blog Post` template.
2. Check `slug`, which QuickAdd generates from the title. It becomes the URL (`/posts/my-post-title/`) and stays put if you rename the note.
3. Write the post. Put `<!--more-->` on its own line where the summary on the posts page should end.
4. Set `draft: false` when it's ready. Leave `date` blank to use the time of the first publish, or set it with a time.
5. Copy it into this repo by running `QuickAdd: Publish Blog` in Obsidian, or from a terminal:

   ```sh
   scripts/publish-from-vault          # add --check to see problems without writing anything
   ```

6. Preview it with `hugo server`, and review the changes with `git status` and `git diff`.
7. Publish it:
   - Push to `main` to publish right away.
   - Push to any other branch to get a preview at `https://<branch-name>.blog-cctechwiz-com.pages.dev`. Styles and some links on previews point at the live site.

A post dated in the future won't appear until a build runs after that date.

### What the script converts

Drafts stay in the vault, because this repo is public. Only notes with `draft: false` are copied.

| In the note | In the post |
|---|---|
| `%%comment%%` | Removed |
| `![[image.png]]` or `![alt](path/to/image.png)` | Image copied to `static/images/<section>/<slug>/` with a web-safe name |
| `![[image.png\|description]]` | Same, with that text as the alt text. Without it, the alt text is empty |
| `![[image.png\|300]]` | Same, at full size, because the width is dropped |
| `[[Other Note]]` or `[[Other Note\|text]]` | Link to that note's page, in any section. See [Links and backlinks](#links-and-backlinks) |
| `![alt](https://example.com/image.png)` | Left as it is, if the CSP allows that host. See [CSP](#csp) |

Code blocks and inline code are left alone. Images are copied unchanged, so resize large ones first.

Anything else that wouldn't render stops the run before anything is written: links to notes outside `Areas/Blog/`, links to headings, note embeds, images that can't be found, reference-style images, remote images the CSP doesn't allow, shortcodes other than `details`, `highlight`, `param`, `ref`, and `relref`, callouts, highlights, published notes outside a section folder, two notes with the same name, and properties a section doesn't allow. Posts allow `title`, `date`, `tags`, `series`, and `description`, besides `slug` and `draft`.

### Dates

The script sets `date` on the first publish and keeps it after that, unless the note sets its own. It sets `lastmod` when a later run finds the page's text, properties, or images have changed, and leaves it alone if they haven't. Reformatted frontmatter doesn't count as a change.

Both dates exist only in `content/posts/`, because the script doesn't write to the vault. The post sidebar shows `Published`, and `Updated` when `lastmod` falls on a different day. The posts list and RSS keep the published date, so an edit doesn't resurface a post in feed readers.

### Remove a page

This works the same for posts, Uses, and Books. Delete the note or set `draft: true`, then run:

```sh
scripts/publish-from-vault --prune    # add --check to see what would be removed
```

This deletes every page and image folder with no published note. Without `--prune`, the script only warns about them. A section with no published notes is skipped with a warning, so it can't lose all its pages to a moved folder or an unfinished sync, and the script stops if it finds no published notes at all. That means the last page in a section has to be deleted by hand. `_index.md` and anything in a subfolder, such as `content/books/by-title/`, are never pruned. Review the deletions in the diff before pushing.

### Publish from iPhone

[Working Copy](https://workingcopy.app/) holds the repo and [a-Shell](https://holzschu.github.io/a-Shell_iOS/) runs the script, so no Mac is needed.

Set up once:

1. Clone this repo in Working Copy. Pushing needs its paid unlock.
2. In a-Shell, run `pickFolder` and choose the vault, then again for the repo in Working Copy. They become `~Exocortex` and `~blog-cctechwiz-com`.
3. Create a Shortcut with Working Copy's Pull action, a-Shell's Execute Command action running the command below in the app, and Open App for Working Copy:

   ```sh
   cd ~blog-cctechwiz-com; python3 scripts/publish-from-vault --vault ~Exocortex
   ```

4. Optionally, add a command to start the Shortcut from Obsidian. In QuickAdd, create a Macro choice called `Publish Blog` with a User Script command set to `Resources/Scripts/Publish Blog.md`, then tap ⚡ to add it to the command palette. The `shortcut` value in that note must match the Shortcut's name.

To publish, run `QuickAdd: Publish Blog` or the Shortcut, then review the diff and commit and push in Working Copy. If the diff is empty, check a-Shell, which shows any problems that stopped the run.

QuickAdd choices don't sync, because Obsidian Sync's community plugin settings are off, so set them up on each device. On the Mac, `Publish Blog` is a Macro choice with a User Script command set to `Resources/Scripts/Publish Blog Mac.md`. It runs the script and shows the result in a notice, without pulling or pushing. `New Blog Post` uses:

| Setting | Value |
|---|---|
| Type | Template |
| Template Path | `Resources/Templates/Blog Post.md` |
| File name | `{{VALUE:title}}` |
| Create in folder | `Areas/Blog/Posts` |
| Open | On |
| ⚡ | On |

`New Uses Page` and `New Book` use the same settings, with these differences:

| Choice | Template Path | Create in folder |
|---|---|---|
| `New Uses Page` | `Resources/Templates/Uses Page.md` | `Areas/Blog/Uses` |
| `New Book` | `Resources/Templates/Book.md` | `Areas/Blog/Books` |

The template's `{{VALUE:...}}` placeholders only work through QuickAdd, not the core Templates plugin.

Run `git pull` on the Mac before publishing from there. Otherwise, a post with a blank `date` gets a new date and conflicts with the phone's commit.

## Sections

Posts record a moment. Uses and Books describe how things are now, and get edited in place. News about either goes in a post, tagged something like `tool-updates` or `book-updates`, linking to the page.

| Vault folder | Site folder | URL |
|---|---|---|
| `Areas/Blog/Posts/` | `content/posts/` | `/posts/<slug>/` |
| `Areas/Blog/Uses/` | `content/uses/` | `/uses/<slug>/` |
| `Areas/Blog/Books/` | `content/books/` | `/books/<slug>/` |

Subfolders inside a section don't affect URLs, so notes can be reorganized without breaking links. Publishing, images, and `--prune` work as they do for posts, with images in `static/images/<section>/<slug>/`.

Uses and Books have no `date` and show no `Published` line, and setting one stops the run. They show `Updated` after an edit. They stay out of RSS, but do appear on tag pages. Their tabs in the top menu appear once they have content.

To add another section, add it to `SECTIONS` in `scripts/publish-from-vault`, which sets its folder, allowed properties, and whether its pages are dated. Then add it to `cascade` in `hugo.yaml` to keep it out of feeds.

### Hubs

`_hub.md` directly in a section folder becomes that section's `content/<section>/_index.md`. It needs `title` and `draft: false`, but no `slug`, and can also have a `description`.

- **Uses:** the hub is the `/uses/` page, written by hand. Further hubs, like Terminal Tools, are ordinary Uses notes that link to other notes. There are no categories: links are the structure. Tools with no page yet are plain external links.
- **Posts and Books:** the lists are generated, so `_hub.md` is optional and supplies intro text only.

Removing a hub leaves its `_index.md` in place, so edit or delete that by hand.

### Uses

Uses notes allow `title`, `tags`, and `description`, besides `slug` and `draft`.

### Books

Every book gets its own page, even a thin one, so backlinks have somewhere to land. Book notes allow these properties, besides `slug` and `draft`:

| Property | Rules |
|---|---|
| `title` | Required |
| `author` | Required. The author of the book, as a single value |
| `authorSort` | Optional. Overrides the default sort name, which is the last word of `author` |
| `status` | Required: `to-be-read`, `reading`, `finished`, or `did-not-finish` |
| `dateRead` | Like `2026-11-06`. Required when `status` is `finished`, and not allowed otherwise |
| `rating` | Optional. A whole number of stars from 1 to 5, only on `finished` and `did-not-finish` |
| `tags`, `description` | Optional |

The CSP blocks JavaScript, so each sort order is its own page, linked by a row of tabs under the main menu:

- `/books/`: reading, then finished with the newest first, then did not finish, then to be read.
- `/books/by-title/`: by title, ignoring a leading "The", "A", or "An".
- `/books/by-author/`: by `authorSort`, then title.

The script writes `titleSort` and `authorSort` into `content/books/`. Book covers go in the vault, because the CSP blocks remote images.

### Links and backlinks

`[[Note]]` resolves across all sections, to the right `/<section>/<slug>/`. A few rules apply:

- **Unpublished notes:** a link to an unpublished note under `Areas/Blog/` is allowed and returns 404 until that note is published. The note still needs a valid `slug`.
- **Hubs:** link to one by path, like `[[Uses/_hub|my setup]]`, which resolves to `/uses/`. A bare `[[_hub]]` stops the run.
- **Same names:** two notes under `Areas/Blog/` with the same name stop the run, even drafts, because a link can't tell them apart. Hubs are the exception.

Every page shows a "Mentioned in" list, from `data/backlinks.json`. The script regenerates that file on each run, so publishing a post doesn't rewrite the pages it links to or change their `lastmod`. Only `[[wikilinks]]` from published notes count, including from hubs. Posts are listed newest first, then everything else by title.

## Tags

Tags group posts by topic. Add them in the post's front matter:

```yaml
tags: ["updates", "book-club"]
```

A tag is created the first time it's used, so there's nothing else to set up. Each one gets a page at `/tags/<tag>/`, and all of them are listed at `/tags/`. Tags are optional on Uses and Books, for tying them to topics like security or devops. Tag pages list every section, but tag feeds only include posts.

Each tag also has its own RSS feed at `/tags/<tag>/index.xml`, linked from its page.

Use lowercase with hyphens so tags stay consistent. Tags display exactly as written, and `book-club` and `bookclub` would be two different tags.

## Series and collections

A series groups related posts that belong together, like a multi-part guide or a reading list. The template starts with an empty `series: []`, which you can leave as is for a standalone post. To add a post to a series, set the series name, using exactly the same name on every post in it:

```yaml
series: ["Book Club 2026"]
```

A series is created the first time its name is used, so there's nothing else to set up.

Each series gets a page at `/series/<series-name>/` (for example `/series/book-club-2026/`), and all of them are listed with their posts at `/series/`. Posts in a series link to it from their sidebar. Each series also has its own RSS feed at `/series/<series-name>/index.xml`, linked from its page.

Posts in a series are listed oldest first, so `date` controls their order. The Series tab in the top menu appears automatically once the first series exists. A post can have tags and a series at the same time.

**Tag or series?** Use a tag for an ongoing topic, and a series for posts meant to be read together.

## Comments

Comments are currently removed from the site. See [COMMENTS.md](COMMENTS.md) for how to restore, update, and enable them.

## Where things go

| What | Where |
|---|---|
| Site settings, menu, social links, tagline | `hugo.yaml` |
| Posts, Uses, and Books | `Areas/Blog/Posts/`, `Uses/`, and `Books/` in the Obsidian vault, copied to `content/<section>/` |
| Images in notes | `Resources/Attachments/` in the vault, copied to `static/images/<section>/` |
| Backlinks | `data/backlinks.json`, generated by the script |
| Book sort pages | `content/books/by-title/`, `content/books/by-author/`, and `layouts/books/` |
| Author page | `content/authors/josh-maxwell.md` |
| Template for new posts | `Resources/Templates/Blog Post.md` in the vault |
| Scripts for the `Publish Blog` command | `Resources/Scripts/` in the vault: `Publish Blog.md` on iPhone, `Publish Blog Mac.md` on the Mac |
| Template overrides | `layouts/`, using the same path as the theme file |
| CSS, palette, images, favicon | `static/` |
| Content Security Policy | `static/_headers` |
| Syntax highlighting colors | `static/css/syntax.css`, generated with `hugo gen chromastyles --style=monokai` |

Never edit the theme directly. To change a theme template, copy it into `layouts/` at the same path and edit that copy.

## CSP

The CSP in `static/_headers` allows only the Font Awesome stylesheet and fonts from cdnjs and the site's own stylesheets, images, and manifest. Scripts and inline styles are blocked. Anything from another host needs adding there first.

`scripts/publish-from-vault` checks notes against the policy:

- **Remote images:** an `https` image from a host not in `img-src` stops the run. Saving the image in the vault is usually better, because a remote host can see readers' IP addresses and can change or remove the image. To allow the host anyway, run this from a terminal, then review the change to `static/_headers` in the diff. The `Publish Blog` command on the Mac doesn't pass this flag.

  ```sh
  scripts/publish-from-vault --update-csp    # add --check to see what would change
  ```

- **Unused hosts:** the script warns about hosts in `img-src` that no published page uses, and leaves them for you to remove.
- **Embeds:** shortcodes such as `youtube` stop the run, and the flag doesn't change that, because they need more than a host added. To show a shortcode as text in a code block, write it as `{{</* name */>}}`.

Tests for the script are in `scripts/test_publish_from_vault.py`. Run them with `python3 scripts/test_publish_from_vault.py`.

## Updating

**Theme:** it's pinned to a release in `go.mod`. To update:

```sh
hugo mod get github.com/joeroe/risotto@<version>
```

Check the theme's `NEWS.md` first, then review a preview build. The next release after v0.5.1 is expected to move CSS into `assets/`, so `layouts/partials/head.html` and the files in `static/css/` will need to change with it. If they don't, the build still passes but the site loses its styling.

**Hugo:** Cloudflare builds with the `HUGO_VERSION` and `GO_VERSION` set in the Pages project settings, not with whatever is installed locally. Update those when you upgrade, for both Production and Preview.
