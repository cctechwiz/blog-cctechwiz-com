# Comments

Comments are **removed** from this site. The code was deleted so that an outdated sanitizer and unused third-party-content handling weren't sitting in the repo. This file explains how to bring them back.

## How they worked

Each post could be tied to a Mastodon toot. A "Load comments" button fetched the public replies to that toot from the fosstodon.org API in the reader's browser and displayed them under the post. There's no server or database involved.

Things to know before deciding to bring them back:

- Only replies known to fosstodon.org appear, so some from other servers may be missing.
- There's no moderation. Anything public in the thread shows up on the blog.
- Replies are written by strangers, so sanitizing them properly is essential.

## Restore the code

The last commit with comments is `3212634`. Restore the partial and styles from it:

```sh
git checkout 3212634 -- layouts/partials/mastodon-comments.html static/css/mastodon.css
```

## Update DOMPurify

Do **not** restore the old `static/js/purify.min.js`. It was DOMPurify 3.0.6 from 2023 and has known security advisories. Download the current release instead:

```sh
VERSION=$(npm view dompurify version)
mkdir -p static/js
curl -fsSL "https://cdn.jsdelivr.net/npm/dompurify@$VERSION/dist/purify.min.js" -o static/js/purify.min.js
head -c 80 static/js/purify.min.js   # confirm the version in the license comment
```

Check for open advisories before shipping: <https://github.com/cure53/DOMPurify/security/advisories>

## Fix the sanitizing

The restored code assigns reply content to `innerHTML` first and only sanitizes when the finished comment is added to the page. Browsers can act on some HTML as soon as it's assigned, so sanitize at the point of assignment. In `layouts/partials/mastodon-comments.html`, change:

```js
display.innerHTML = status.account.display_name;
main.innerHTML = status.content;
```

to:

```js
display.innerHTML = DOMPurify.sanitize(status.account.display_name);
main.innerHTML = DOMPurify.sanitize(status.content);
```

Keep the existing final `DOMPurify.sanitize(comment.outerHTML)` call as well.

Two smaller fixes while you're there:

- When a toot has no replies, the button stays stuck on "Loading". Show a "No comments yet" message instead.
- A failed request isn't handled. Add a `.catch()` with a link to the toot.

## Wire it back in

1. In `layouts/_default/single.html`, add this after the `content__body` div:

   ```go-html-template
   {{ partial "mastodon-comments.html" . }}
   ```

2. In `layouts/partials/head.html`, add this after the `css/custom.css` link:

   ```go-html-template
   <link rel="stylesheet" href="{{ "css/mastodon.css" | absURL }}">
   ```

   If the theme has since moved CSS to `assets/`, this step will differ. Check the theme's `NEWS.md`.

3. Optionally, add this to `archetypes/default.md` so new posts include it, with comments off by default:

   ```yaml
   no-comments:
     host: fosstodon.org
     username: cctechwiz
     id:
   ```

## Enable comments on a post

A post has to be live before you can toot about it, so this happens after publishing:

1. Publish the post and toot a link to it.
2. In the post's front matter, add this, using the toot's ID (the number at the end of its URL). Keep the quotes, because the ID is too long to be treated as a number:

   ```yaml
   comments:
     host: fosstodon.org
     username: cctechwiz
     id: "123456789012345678"
   ```

3. Push to a branch and test "Load comments" on the preview with a real thread that has replies, plus one with none. Then merge to `main`.
