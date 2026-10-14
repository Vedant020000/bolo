import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from bolo import render  # noqa: E402


class RenderTests(unittest.TestCase):
    def test_code_fences_dropped(self):
        s = render.to_speech("Fixed it.\n```py\nprint('hi')\n```\nAll good.")
        self.assertIn("Fixed it.", s)
        self.assertNotIn("print", s)

    def test_links_keep_labels(self):
        s = render.to_speech("See [the docs](https://example.com/x) for more.")
        self.assertIn("the docs", s)
        self.assertNotIn("http", s)

    def test_urls_dropped(self):
        s = render.to_speech("Go to https://example.com now.")
        self.assertNotIn("example.com", s)

    def test_paths_spoken(self):
        s = render.to_speech("Edited ~/workspace/openletta/src/App.tsx today.")
        self.assertNotIn("/", s)
        self.assertNotIn(".tsx", s)
        self.assertIn("App", s)

    def test_numbers(self):
        s = render.to_speech("Total 1234567 credits.")
        self.assertIn("1,234,567", s)

    def test_emoji_stripped(self):
        s = render.to_speech("Done 🎉✅")
        self.assertNotIn("🎉", s)
        self.assertNotIn("✅", s)

    def test_max_chars(self):
        s = render.to_speech("word " * 500, max_chars=100)
        self.assertLessEqual(len(s), 140)
        self.assertTrue(s.endswith("more on screen."))

    def test_language_detect(self):
        self.assertEqual(render.lang_for("नमस्ते दोस्त"), "hi-IN")
        self.assertEqual(render.lang_for("hello there"), "en-IN")

    def test_split_sentences(self):
        out = render.split_sentences("One. Two! Three? Ok")
        self.assertEqual(out, ["One. Two! Three? Ok"])
        out2 = render.split_sentences("Done. The build passed and everything is verified.")
        self.assertEqual(out2, ["Done.", "The build passed and everything is verified."])


if __name__ == "__main__":
    unittest.main()
