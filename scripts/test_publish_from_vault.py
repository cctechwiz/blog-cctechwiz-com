#!/usr/bin/env python3
"""Tests for publish-from-vault, run against a throwaway vault and site."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "publish-from-vault"
HEADERS = """/*
  Content-Security-Policy: default-src 'none'; img-src 'self' https://allowed.example; base-uri 'none'
"""


class PublishTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.vault = root / "vault"
        self.site = root / "site"
        (self.vault / "Areas/Blog/Posts").mkdir(parents=True)
        (self.site / "content/posts").mkdir(parents=True)
        (self.site / "static/images/posts").mkdir(parents=True)
        self.headers = self.site / "static/_headers"
        self.headers.write_text(HEADERS)
        self.post = self.site / "content/posts/post.md"

    def publish(self, body, *flags):
        note = f"---\ntitle: Post\nslug: post\ndraft: false\ndate: 2026-11-06T12:00:00-07:00\n---\n{body}\n"
        (self.vault / "Areas/Blog/Posts/Post.md").write_text(note)
        return self.run_script(*flags)

    def run_script(self, *flags):
        command = [sys.executable, str(SCRIPT), "--vault", str(self.vault), "--site", str(self.site), *flags]
        return subprocess.run(command, capture_output=True, text=True)

    def assert_stopped(self, result, message):
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(message, result.stderr)
        self.assertFalse(self.post.exists())
        self.assertEqual(self.headers.read_text(), HEADERS)

    def assert_published(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.post.exists())

    def test_allowed_host_publishes_without_the_flag(self):
        self.assert_published(self.publish("![a](https://allowed.example/a.png)"))
        self.assertEqual(self.headers.read_text(), HEADERS)

    def test_new_host_stops_the_run(self):
        self.assert_stopped(self.publish("![a](https://new.example/a.png)"), "the CSP blocks images from new.example")

    def test_update_csp_adds_only_the_new_host(self):
        result = self.publish("![a](https://New.Example/a.png)\n![b](https://allowed.example/b.png)", "--update-csp")
        self.assert_published(result)
        self.assertEqual(
            self.headers.read_text(),
            HEADERS.replace("https://allowed.example;", "https://allowed.example https://new.example;"),
        )
        self.assertEqual(self.publish("![a](https://new.example/a.png)").returncode, 0)

    def test_check_with_update_csp_writes_nothing(self):
        result = self.publish("![a](https://new.example/a.png)", "--check", "--update-csp")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("would add https://new.example", result.stdout)
        self.assertFalse(self.post.exists())
        self.assertEqual(self.headers.read_text(), HEADERS)

    def test_unsafe_urls_stop_the_run_even_with_the_flag(self):
        for url in (
            "http://new.example/a.png",
            "//new.example/a.png",
            "https://user@new.example/a.png",
            "https://new.example;script-src/a.png",
            "https://*.example/a.png",
        ):
            with self.subTest(url):
                self.assert_stopped(self.publish(f"![a]({url})", "--update-csp"), "need an https URL")

    def test_reference_image_stops_the_run(self):
        body = "![a][pic]\n\n[pic]: https://new.example/a.png"
        self.assert_stopped(self.publish(body, "--update-csp"), "reference-style images")

    def test_image_in_code_or_comment_is_ignored(self):
        self.assert_published(self.publish("`![a](https://new.example/a.png)`\n\n%% ![a](https://new.example/a.png) %%"))

    def test_embed_shortcodes_stop_the_run_even_with_the_flag(self):
        for body in ("{{< youtube abc >}}", '{{% figure src="https://new.example/a.png" %}}', "```\n{{< vimeo 1 >}}\n```"):
            with self.subTest(body):
                self.assert_stopped(self.publish(body, "--update-csp"), "can't be published with the site's CSP")

    def test_safe_and_escaped_shortcodes_publish(self):
        body = '{{< details summary="x" >}}y{{< /details >}}\n\n```\n{{</* youtube abc */>}}\n```'
        self.assert_published(self.publish(body))

    def test_unused_host_warns_and_stays(self):
        result = self.publish("No images.")
        self.assert_published(result)
        self.assertIn("no published page uses https://allowed.example", result.stdout)
        self.assertEqual(self.headers.read_text(), HEADERS)

    def test_missing_img_src(self):
        self.headers.write_text("/*\n  X-Frame-Options: DENY\n")
        result = self.publish("![a](https://new.example/a.png)", "--update-csp")
        self.assertEqual(result.returncode, 1)
        self.assertIn("has no img-src", result.stderr)
        self.assertFalse(self.post.exists())

    def test_no_headers_file_is_fine_without_remote_images(self):
        self.headers.unlink()
        self.assert_published(self.publish("No images."))

    def test_line_limit_stops_the_run(self):
        long_host = "a" * 2000 + ".example"
        self.assert_stopped(self.publish(f"![a](https://{long_host}/a.png)", "--update-csp"), "character line limit")


class SectionsTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.vault = root / "vault"
        self.site = root / "site"
        self.blog = self.vault / "Areas/Blog"
        self.blog.mkdir(parents=True)
        (self.site / "static").mkdir(parents=True)
        (self.site / "static/_headers").write_text(HEADERS)

    def note(self, path, properties, body=""):
        target = self.blog / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"---\n{properties}\n---\n{body}\n")

    def post(self, name="Post", slug="post", body="", extra=""):
        date = "date: 2026-11-06T12:00:00-07:00"
        self.note(f"Posts/{name}.md", f"title: {name}\nslug: {slug}\ndraft: false\n{date}{extra}", body)

    def use(self, name="Neovim", slug="neovim", body="", draft="false"):
        self.note(f"Uses/{name}.md", f"title: {name}\nslug: {slug}\ndraft: {draft}", body)

    def book(self, properties="status: reading", name="Dune", author="Frank Herbert"):
        self.note(f"Books/{name}.md", f"title: {name}\nslug: {name.lower().replace(' ', '-')}\nauthor: {author}\ndraft: false\n{properties}")

    def run_script(self, *flags):
        command = [sys.executable, str(SCRIPT), "--vault", str(self.vault), "--site", str(self.site), *flags]
        return subprocess.run(command, capture_output=True, text=True)

    def assert_ok(self, *flags):
        result = self.run_script(*flags)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def assert_stopped(self, message):
        result = self.run_script()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(message, result.stderr)
        self.assertFalse((self.site / "content").exists())

    def page(self, path):
        return (self.site / "content" / path).read_text()

    def backlinks(self):
        return json.loads((self.site / "data/backlinks.json").read_text())

    def test_sections_get_their_own_paths(self):
        (self.vault / "Resources/Attachments").mkdir(parents=True)
        (self.vault / "Resources/Attachments/shot.png").write_bytes(b"png")
        self.post(body="![[shot.png]]")
        self.use(body="![[shot.png]]")
        self.assert_ok()
        self.assertIn("(/images/posts/post/shot.png)", self.page("posts/post.md"))
        self.assertIn("(/images/uses/neovim/shot.png)", self.page("uses/neovim.md"))
        self.assertTrue((self.site / "static/images/uses/neovim/shot.png").is_file())

    def test_subfolders_do_not_change_urls(self):
        self.note("Uses/Terminal/Deep/Neovim.md", "title: Neovim\nslug: neovim\ndraft: false")
        self.assert_ok()
        self.assertTrue((self.site / "content/uses/neovim.md").is_file())

    def test_same_slug_is_fine_in_different_sections(self):
        self.post("A Post", "dune")
        self.book()
        self.assert_ok()

    def test_same_slug_in_a_section_stops_the_run(self):
        self.use("One", "same")
        self.use("Two", "same")
        self.assert_stopped("is also used by")

    def test_published_note_outside_a_section_stops_the_run(self):
        self.note("Loose.md", "title: Loose\nslug: loose\ndraft: false")
        self.assert_stopped("published notes must be in a section folder")

    def test_properties_are_per_section(self):
        for write, message in (
            (lambda: self.post(extra="\nauthor: Josh"), "'author' isn't allowed in Posts"),
            (lambda: self.note("Uses/A.md", "title: A\nslug: a\ndraft: false\nseries: []"), "'series' isn't allowed in Uses"),
            (lambda: self.note("Uses/A.md", "title: A\nslug: a\ndraft: false\ndate: 2026-11-06T12:00:00-07:00"), "'date' isn't allowed in Uses"),
        ):
            with self.subTest(message):
                write()
                self.assert_stopped(message)
                for path in self.blog.rglob("*.md"):
                    path.unlink()

    def test_undated_pages_get_lastmod_but_no_date(self):
        self.use(body="One.")
        self.assert_ok()
        self.assertNotIn("date:", self.page("uses/neovim.md"))
        self.assertNotIn("lastmod:", self.page("uses/neovim.md"))
        self.use(body="Two.")
        self.assert_ok()
        self.assertIn("lastmod:", self.page("uses/neovim.md"))
        self.assertNotIn("\ndate:", self.page("uses/neovim.md"))

    def test_hub_becomes_the_section_index(self):
        self.note("Uses/_hub.md", "title: Uses\ndescription: My setup\ndraft: false", "Links.")
        self.assert_ok()
        self.assertEqual(self.page("uses/_index.md"), "---\ntitle: Uses\ndescription: My setup\n---\nLinks.\n")

    def test_posts_hub_keeps_the_aliases(self):
        self.post()
        self.note("Posts/_hub.md", "title: Posts\ndraft: false", "Intro.")
        self.assert_ok()
        self.assertIn('aliases: ["articles", "blog"]', self.page("posts/_index.md"))
        before = self.page("posts/_index.md")
        self.assert_ok()
        self.assertEqual(self.page("posts/_index.md"), before)

    def test_hubs_share_a_name_without_stopping_the_run(self):
        self.note("Uses/_hub.md", "title: Uses\ndraft: false")
        self.note("Books/_hub.md", "title: Books\ndraft: false")
        self.assert_ok()

    def test_hub_rules(self):
        for path, properties, message in (
            ("Uses/_hub.md", "draft: false", "title is required"),
            ("Uses/_hub.md", "title: Uses\ndraft: false\ntags: []", "'tags' isn't allowed in a hub"),
            ("Uses/Tools/_hub.md", "title: Uses\ndraft: false", "must be directly in a section folder"),
        ):
            with self.subTest(message):
                self.note(path, properties)
                self.assert_stopped(message)
                (self.blog / path).unlink()

    def test_draft_hub_is_not_published(self):
        self.note("Uses/_hub.md", "title: Uses\ndraft: true")
        self.assert_ok()
        self.assertFalse((self.site / "content/uses/_index.md").exists())

    def test_links_resolve_across_sections(self):
        self.book()
        self.post(body="[[Dune]] and [[Books/Dune|the book]] and [[Uses/_hub|my setup]] and [[Uses/_hub]]")
        self.note("Uses/_hub.md", "title: My Uses\ndraft: false")
        self.assert_ok()
        body = self.page("posts/post.md")
        self.assertIn("[Dune](/books/dune/)", body)
        self.assertIn("[the book](/books/dune/)", body)
        self.assertIn("[my setup](/uses/)", body)
        self.assertIn("[My Uses](/uses/)", body)

    def test_bare_hub_link_stops_the_run(self):
        self.note("Uses/_hub.md", "title: Uses\ndraft: false")
        self.post(body="[[_hub]]")
        self.assert_stopped("a link to a hub needs its section")

    def test_duplicate_names_stop_the_run(self):
        self.post("Dune", "dune-post")
        self.book()
        self.assert_stopped("share a name")

    def test_duplicate_names_count_drafts(self):
        self.post("Dune", "dune-post")
        self.note("Books/dune.md", "title: Dune\nslug: dune\ndraft: true")
        self.assert_stopped("share a name")

    def test_link_to_unpublished_note_points_at_its_url(self):
        self.use("Tmux", "tmux", draft="true")
        self.post(body="[[Tmux]]")
        self.assert_ok()
        self.assertIn("[Tmux](/uses/tmux/)", self.page("posts/post.md"))
        self.assertEqual(self.backlinks(), {})

    def test_link_to_unpublished_note_needs_a_valid_slug(self):
        self.use("Tmux", "Not A Slug", draft="true")
        self.post(body="[[Tmux]]")
        self.assert_stopped("without a valid slug")

    def test_links_outside_the_blog_stop_the_run(self):
        (self.vault / "Areas/Private").mkdir(parents=True)
        (self.vault / "Areas/Private/Secret.md").write_text("---\ntitle: Secret\nslug: secret\n---\n")
        self.post(body="[[Secret]]")
        self.assert_stopped("link to a note outside Areas/Blog/")

    def test_path_to_a_note_elsewhere_does_not_match_a_blog_note(self):
        self.book()
        self.post(body="[[Areas/Private/Dune]]")
        self.assert_stopped("link to a note outside Areas/Blog/")

    def test_link_to_a_note_outside_the_sections_stops_the_run(self):
        self.note("Loose.md", "title: Loose\nslug: loose\ndraft: true")
        self.post(body="[[Loose]]")
        self.assert_stopped("outside the section folders")

    def test_backlinks(self):
        self.use(body="[[Neovim]] links to itself")
        self.post("A Post", "a-post", "[[Neovim]] [[Neovim|twice]] `[[Code]]` %% [[Comment]] %%")
        self.note("Uses/_hub.md", "title: Uses\ndraft: false", "[[Neovim]]")
        self.note("Uses/Draft.md", "title: Draft\nslug: draft\ndraft: true", "[[Neovim]]")
        self.assert_ok()
        self.assertEqual(self.backlinks(), {"uses/neovim": ["posts/a-post", "uses"]})

    def test_publishing_a_link_does_not_touch_the_target(self):
        self.use()
        self.assert_ok()
        before = self.page("uses/neovim.md")
        self.post(body="[[Neovim]]")
        self.assert_ok()
        self.assertEqual(self.page("uses/neovim.md"), before)

    def test_check_does_not_write_backlinks(self):
        self.post()
        self.assert_ok("--check")
        self.assertFalse((self.site / "data").exists())

    def test_book_sort_properties(self):
        self.book("status: finished\ndateRead: '2026-01-02'\nrating: 5", "The Left Hand", "Ursula K. Le Guin")
        self.assert_ok()
        page = self.page("books/the-left-hand.md")
        self.assertIn('titleSort: "left hand"', page)
        self.assertIn('authorSort: "guin"', page)
        self.assertIn("dateRead: 2026-01-02\n", page)

    def test_author_sort_overrides_the_default_once(self):
        self.book("status: reading\nauthorSort: Le Guin", "A Book", "Ursula K. Le Guin")
        self.assert_ok()
        page = self.page("books/a-book.md")
        self.assertEqual(page.count("authorSort:"), 1)
        self.assertIn('authorSort: "le guin"', page)
        self.assertIn('titleSort: "book"', page)

    def test_generated_properties_do_not_bump_lastmod(self):
        self.book("status: reading\nauthorSort: Herbert")
        self.assert_ok()
        self.assert_ok()
        self.assertNotIn("lastmod:", self.page("books/dune.md"))

    def test_blank_template_properties_count_as_unset(self):
        self.book("status: reading\ndateRead:\nrating:\nauthorSort:")
        self.assert_ok()
        self.assertIn('authorSort: "herbert"', self.page("books/dune.md"))

    def test_book_rules(self):
        for properties, message in (
            ("rating: 3", "status must be one of"),
            ("status: abandoned", "status must be one of"),
            ("status: finished", "dateRead is required"),
            ("status: reading\ndateRead: 2026-01-02", "dateRead is only allowed"),
            ("status: did-not-finish\ndateRead: 2026-01-02", "dateRead is only allowed"),
            ("status: finished\ndateRead: 2026-02-30", "dateRead must be a date"),
            ("status: finished\ndateRead: 2026-01-02T12:00:00", "dateRead must be a date"),
            ("status: finished\ndateRead: 2026-01-02\nrating: 4.5", "rating must be a whole number"),
            ("status: finished\ndateRead: 2026-01-02\nrating: 0", "rating must be a whole number"),
            ("status: finished\ndateRead: 2026-01-02\nrating: 6", "rating must be a whole number"),
            ("status: finished\ndateRead: 2026-01-02\nrating:\n  - 4", "rating must be a single value"),
            ("status: reading\nrating: 4", "rating is only allowed"),
            ("status: to-be-read\nrating: 4", "rating is only allowed"),
        ):
            with self.subTest(properties):
                self.book(properties)
                self.assert_stopped(message)

    def test_book_needs_an_author(self):
        self.note("Books/Dune.md", "title: Dune\nslug: dune\ndraft: false\nstatus: reading")
        self.assert_stopped("author is required")

    def test_valid_book_statuses(self):
        for properties in (
            "status: to-be-read",
            "status: reading",
            "status: finished\ndateRead: 2026-01-02\nrating: 1",
            "status: did-not-finish\nrating: 2",
            "status: did-not-finish",
        ):
            with self.subTest(properties):
                self.book(properties)
                self.assert_ok()

    def test_prune_is_per_section(self):
        self.post()
        self.post("Old", "old")
        self.use()
        self.assert_ok()
        (self.blog / "Posts/Old.md").unlink()
        (self.blog / "Uses/Neovim.md").unlink()
        result = self.assert_ok("--prune")
        self.assertFalse((self.site / "content/posts/old.md").exists())
        self.assertTrue((self.site / "content/uses/neovim.md").exists())
        self.assertIn("no published notes in Uses", result.stdout)

    def test_prune_with_no_published_notes_at_all_stops(self):
        self.use(draft="true")
        result = self.run_script("--prune")
        self.assertEqual(result.returncode, 1)
        self.assertIn("nothing was pruned", result.stderr)

    def test_prune_leaves_indexes_and_subsections(self):
        self.book()
        self.book("status: reading", "Stale")
        self.assert_ok()
        (self.blog / "Books/Stale.md").unlink()
        (self.site / "content/books/by-title").mkdir()
        keep = [self.site / "content/books/by-title/_index.md", self.site / "content/books/_index.md"]
        for path in keep:
            path.write_text("---\ntitle: Books\n---\n")
        self.assert_ok("--prune")
        self.assertFalse((self.site / "content/books/stale.md").exists())
        for path in keep:
            self.assertTrue(path.exists())

    def test_prune_keeps_hub_images(self):
        (self.vault / "Resources/Attachments").mkdir(parents=True)
        (self.vault / "Resources/Attachments/desk.png").write_bytes(b"png")
        self.use()
        self.note("Uses/_hub.md", "title: Uses\ndraft: false", "![[desk.png]]")
        self.assert_ok()
        self.assert_ok("--prune")
        self.assertTrue((self.site / "static/images/uses/_hub/desk.png").is_file())
        self.assertIn("(/images/uses/_hub/desk.png)", self.page("uses/_index.md"))


if __name__ == "__main__":
    unittest.main()
