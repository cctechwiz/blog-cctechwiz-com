# CLAUDE.md

Hugo blog using the Risotto theme, hosted on Cloudflare Pages.

Read `README.md` when adding posts, tags, or series, or updating the theme or Hugo. Read `COMMENTS.md` before any work on comments, which are intentionally removed.

## Posts

- Posts, Uses, and Books live in the Obsidian vault at `~/Vaults/exocortex/Areas/Blog/`, in `Posts/`, `Uses/`, and `Books/`. `scripts/publish-from-vault` generates `content/<section>/`, `static/images/<section>/`, and `data/backlinks.json` from them, so make those edits in the vault. `_index.md`, `by-title/`, and `by-author/` in `content/` are the exceptions: without a `_hub.md`, they're edited here.
- The repo is public, so drafts stay in the vault.

## Deploying

- Pushing to `main` publishes to production. Any other branch gets a preview at `https://<branch>.blog-cctechwiz-com.pages.dev`.
- Build settings live in Cloudflare, not this repo: `HUGO_VERSION`, `GO_VERSION`, and build image v3, for both Production and Preview. Cloudflare has no repo file for pinning Hugo. Read them with `cf pages projects get blog-cctechwiz-com`.
- `cf` needs `CLOUDFLARE_ACCOUNT_ID` set. Its deployment commands take `--project-name`, not a positional name.

## Verifying changes

- A passing build proves little here. Check the rendered HTML, then the live URLs after a deploy.
- A deployment is done when `latest_stage` is `deploy` with status `success`.
- Previews load CSS and some links from the production domain because `baseURL` and `absURL` are baked in, so a preview can't confirm CSS changes.
- Run test builds with `--destination` pointing outside the repo, and use throwaway copies for sample content.
- Josh usually has his own `hugo server` running on port 1313, so use another port.

## Theme

- The theme is a Hugo Module pinned to a release in `go.mod`. Josh chose a tagged release over upstream `main` for stability.
- All customizations are overrides in `layouts/`.
- The release after v0.5.1 is expected to move CSS to `assets/`. The `head.html` override then links to files that no longer exist: the build passes and the site silently loses its styling. Follow the upgrade note in `README.md`.

## Behavior spread across files

- `{year}` in the `copyright` setting is replaced in both `layouts/partials/footer.html` and `layouts/_default/rss.xml`. Change them together.
- `params.about.description` must stay plain text because it's also the meta description. `layouts/partials/about.html` adds the author link at render time.
- `capitalizeListTitles: false` keeps tags lowercase, which is why `content/tags/_index.md` and `content/series/_index.md` set their titles.
- `layouts/partials/header.html` hides the Series, Uses, and Books tabs until they have content.
- `author` means the author of a book. Posts have none. `params.author` in `hugo.yaml` stays for `rss.xml`, and `content/authors/josh-maxwell.md` stays for `layouts/partials/about.html`.
- `frontmatter.date` in `hugo.yaml` drops Hugo's fallback to `lastmod`. Without it, Uses and Books get a `Published` line after their first edit, and `.Params.date` can't detect that because Hugo fills it in too.
- `cascade` in `hugo.yaml` keeps Uses and Books out of feeds. A new section needs adding there and to `SECTIONS` in the script.
- The book sort pages use `layout:` with `layouts/books/by-*.html`. Custom output formats don't work, because their `path` is a URL prefix. `.Pages` is empty on those subsections, so they list `where site.RegularPages "Section" "books"`.
- `.page__header` is a flex row, so `static/css/custom.css` wraps it to put the book tabs on their own row.
- `content/posts/_index.md` has `aliases` that notes can't set, so `hub_lines` in the script adds them if a `Posts/_hub.md` replaces that file.
- Keys in `data/backlinks.json` are Hugo's `.Path` without the leading slash. `layouts/partials/backlinks.html` skips any that `site.GetPage` can't resolve, such as future-dated posts.
- The CSP in `static/_headers` blocks inline styles. That's why `markup.highlight.noClasses` is false and `layouts/_default/_markup/render-table.html` exists. Previews load CSS from production, so `style-src` must keep `https://blog.cctechwiz.com`. `scripts/publish-from-vault` reads and updates `img-src`, so keep that directive on the `Content-Security-Policy` line.
- Give post dates a time. A date alone means midnight UTC, which feed readers in US time zones show as the previous day.

