# CLAUDE.md

Hugo blog using the Risotto theme, hosted on Cloudflare Pages.

Read `README.md` when adding posts, tags, or series, or updating the theme or Hugo. Read `COMMENTS.md` before any work on comments, which are intentionally removed.

## Posts

- Posts live in the Obsidian vault at `~/Vaults/exocortex/Areas/Blog/`. `scripts/publish-from-vault` generates `content/posts/` and `static/images/posts/` from them, so make post edits in the vault.
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
- `layouts/partials/header.html` hides the Series tab until a series exists.
- The CSP in `static/_headers` blocks inline styles. That's why `markup.highlight.noClasses` is false and `layouts/_default/_markup/render-table.html` exists. Previews load CSS from production, so `style-src` must keep `https://blog.cctechwiz.com`.
- Give post dates a time. A date alone means midnight UTC, which feed readers in US time zones show as the previous day.

