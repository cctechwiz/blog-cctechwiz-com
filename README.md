# blog.cctechwiz.com

Source for [blog.cctechwiz.com](https://blog.cctechwiz.com/), built with [Hugo](https://gohugo.io/) and the [Risotto](https://github.com/joeroe/risotto) theme, and hosted on Cloudflare Pages.

## Setup

Install Hugo (extended) and Go. The theme is a Hugo Module, so it downloads automatically on the first build.

```sh
brew install hugo go
hugo server -D    # preview at http://localhost:1313, -D includes drafts
```

## Add a new post

1. Create the post. It starts as a draft, with the author and date filled in:

   ```sh
   hugo new content posts/my-post-title.md
   ```

2. Write it in `content/posts/my-post-title.md`. The file name becomes the URL (`/posts/my-post-title/`).
3. Put `<!--more-->` on its own line where the summary on the posts page should end.
4. Preview it with `hugo server -D`.
5. Delete `draft: true` when it's ready.
6. Publish it:
   - Push to `main` to publish right away.
   - Push to any other branch to get a preview at `https://<branch-name>.blog-cctechwiz-com.pages.dev`. Styles and some links on previews point at the live site.

A post dated in the future won't appear until a build runs after that date.

## Tags

Tags group posts by topic. Add them in the post's front matter:

```yaml
tags: ["updates", "book-club"]
```

A tag is created the first time it's used, so there's nothing else to set up. Each one gets a page at `/tags/<tag>/`, and all of them are listed at `/tags/`.

Each tag also has its own RSS feed at `/tags/<tag>/index.xml`, linked from its page.

Use lowercase with hyphens so tags stay consistent. Tags display exactly as written, and `book-club` and `bookclub` would be two different tags.

## Series and collections

A series groups related posts that belong together, like a multi-part guide or a reading list. New posts start with an empty `series: []`, which you can leave as is for a standalone post. To add a post to a series, set the series name, using exactly the same name on every post in it:

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
| Posts | `content/posts/` |
| Author page | `content/authors/josh-maxwell.md` |
| Template for new posts | `archetypes/default.md` |
| Template overrides | `layouts/`, using the same path as the theme file |
| CSS, palette, images, favicon | `static/` |

Never edit the theme directly. To change a theme template, copy it into `layouts/` at the same path and edit that copy.

## Updating

**Theme:** it's pinned to a release in `go.mod`. To update:

```sh
hugo mod get github.com/joeroe/risotto@<version>
```

Check the theme's `NEWS.md` first, then review a preview build. The next release after v0.5.1 is expected to move CSS into `assets/`, so `layouts/partials/head.html` and the files in `static/css/` will need to change with it. If they don't, the build still passes but the site loses its styling.

**Hugo:** Cloudflare builds with the `HUGO_VERSION` and `GO_VERSION` set in the Pages project settings, not with whatever is installed locally. Update those when you upgrade, for both Production and Preview.
