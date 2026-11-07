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

1. In Obsidian, run `QuickAdd: New Blog Post` from the command palette and enter the title. This creates the note in `Areas/Blog/` from the `Blog Post` template.
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
| `![[image.png]]` or `![alt](path/to/image.png)` | Image copied to `static/images/posts/<slug>/` with a web-safe name |
| `![[image.png\|description]]` | Same, with that text as the alt text. Without it, the alt text is empty |
| `![[image.png\|300]]` | Same, at full size, because the width is dropped |
| `[[Other Post]]` or `[[Other Post\|text]]` | Link to that post, if it's published |

Code blocks and inline code are left alone. Images are copied unchanged, so resize large ones first.

Anything else that wouldn't render stops the run before anything is written: links to notes that aren't published posts, links to headings, note embeds, images that can't be found, callouts, highlights, and properties other than `title`, `author`, `date`, `tags`, `series`, and `description`.

### Dates

The script sets `date` on the first publish and keeps it after that, unless the note sets its own. It sets `lastmod` when a later run finds the post's text, properties, or images have changed, and leaves it alone if they haven't. Reformatted frontmatter doesn't count as a change.

Both dates exist only in `content/posts/`, because the script doesn't write to the vault. The post sidebar shows `Published`, and `Updated` when `lastmod` falls on a different day. The posts list and RSS keep the published date, so an edit doesn't resurface a post in feed readers.

### Remove a post

Delete the note or set `draft: true`, then run:

```sh
scripts/publish-from-vault --prune    # add --check to see what would be removed
```

This deletes every post and image folder with no published note. Without `--prune`, the script only warns about them. It stops without deleting anything if it finds no published notes at all. Review the deletions in the diff before pushing.

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
| Create in folder | `Areas/Blog` |
| Open | On |
| ⚡ | On |

The template's `{{VALUE:...}}` placeholders only work through QuickAdd, not the core Templates plugin.

Run `git pull` on the Mac before publishing from there. Otherwise, a post with a blank `date` gets a new date and conflicts with the phone's commit.

## Tags

Tags group posts by topic. Add them in the post's front matter:

```yaml
tags: ["updates", "book-club"]
```

A tag is created the first time it's used, so there's nothing else to set up. Each one gets a page at `/tags/<tag>/`, and all of them are listed at `/tags/`.

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
| Posts | `Areas/Blog/` in the Obsidian vault, copied to `content/posts/` |
| Post images | `Resources/Attachments/` in the vault, copied to `static/images/posts/` |
| Author page | `content/authors/josh-maxwell.md` |
| Template for new posts | `Resources/Templates/Blog Post.md` in the vault |
| Scripts for the `Publish Blog` command | `Resources/Scripts/` in the vault: `Publish Blog.md` on iPhone, `Publish Blog Mac.md` on the Mac |
| Template overrides | `layouts/`, using the same path as the theme file |
| CSS, palette, images, favicon | `static/` |
| Content Security Policy | `static/_headers` |
| Syntax highlighting colors | `static/css/syntax.css`, generated with `hugo gen chromastyles --style=monokai` |

Never edit the theme directly. To change a theme template, copy it into `layouts/` at the same path and edit that copy.

## CSP

The CSP in `static/_headers` allows only the Font Awesome stylesheet and fonts from cdnjs and the site's own stylesheets, images, and manifest. Scripts and inline styles are blocked. Anything new from another host, such as a remote image or an embed, needs adding there first.

## Updating

**Theme:** it's pinned to a release in `go.mod`. To update:

```sh
hugo mod get github.com/joeroe/risotto@<version>
```

Check the theme's `NEWS.md` first, then review a preview build. The next release after v0.5.1 is expected to move CSS into `assets/`, so `layouts/partials/head.html` and the files in `static/css/` will need to change with it. If they don't, the build still passes but the site loses its styling.

**Hugo:** Cloudflare builds with the `HUGO_VERSION` and `GO_VERSION` set in the Pages project settings, not with whatever is installed locally. Update those when you upgrade, for both Production and Preview.
