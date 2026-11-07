#!/usr/bin/env python3
"""Tests for publish-from-vault's CSP checks, run against a throwaway vault and site."""

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
        (self.vault / "Areas/Blog").mkdir(parents=True)
        (self.site / "content/posts").mkdir(parents=True)
        (self.site / "static/images/posts").mkdir(parents=True)
        self.headers = self.site / "static/_headers"
        self.headers.write_text(HEADERS)
        self.post = self.site / "content/posts/post.md"

    def publish(self, body, *flags):
        note = f"---\ntitle: Post\nslug: post\ndraft: false\ndate: 2026-11-06T12:00:00-07:00\n---\n{body}\n"
        (self.vault / "Areas/Blog/Post.md").write_text(note)
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
        self.assertIn("no published post uses https://allowed.example", result.stdout)
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


if __name__ == "__main__":
    unittest.main()
