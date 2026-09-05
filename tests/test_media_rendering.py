from pathlib import Path
import unittest

from app import (
    app,
    build_cat_tree,
    process_obsidian_image_embeds,
    rewrite_content_image_sources,
)


ROOT = Path(__file__).resolve().parents[1]
EXISTING_SVG = "AI/LLM/llm-inference-pipeline.svg"
EXISTING_PNG = "AI/ai-agent-book/images/attention-visualization.png"


class MediaRenderingTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_sidebar_tree_includes_media_only_directories(self):
        tree = build_cat_tree([], [{
            "path": "diagrams/example.svg",
            "name": "example.svg",
            "title": "example",
            "extension": "SVG",
            "category": "diagrams",
        }])

        self.assertEqual(tree["diagrams"]["total"], 1)
        self.assertEqual(tree["diagrams"]["media"][0]["name"], "example.svg")

    def test_obsidian_image_embed_is_converted_and_rewritten(self):
        source = process_obsidian_image_embeds("![[diagram.svg|架构图]]")
        rendered = rewrite_content_image_sources(source, "notes/article.md")

        self.assertIn('alt="架构图"', rendered)
        self.assertIn('src="/content-assets/notes/diagram.svg"', rendered)

    def test_relative_image_path_is_normalized_and_url_encoded(self):
        rendered = rewrite_content_image_sources(
            '<img src="../../svg/中文 图.svg" alt="图">',
            "AI/interview/article.md",
        )

        self.assertIn(
            'src="/content-assets/svg/%E4%B8%AD%E6%96%87%20%E5%9B%BE.svg"',
            rendered,
        )

    def test_media_preview_and_raw_asset_are_served(self):
        for path, mimetype in (
            (EXISTING_SVG, "image/svg+xml"),
            (EXISTING_PNG, "image/png"),
        ):
            with self.subTest(path=path):
                preview = self.client.get(f"/media/{path}")
                asset = self.client.get(f"/content-assets/{path}")
                self.addCleanup(preview.close)
                self.addCleanup(asset.close)

                self.assertEqual(preview.status_code, 200)
                self.assertIn(
                    f'src="/content-assets/{path}"'.encode(),
                    preview.data,
                )
                self.assertEqual(asset.status_code, 200)
                self.assertEqual(asset.mimetype, mimetype)

    def test_sidebar_renders_media_link(self):
        response = self.client.get("/articles")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            f'href="/media/{EXISTING_SVG}"'.encode(),
            response.data,
        )

    def test_markdown_article_renders_svg_and_png(self):
        response = self.client.get("/article/JVM")
        self.addCleanup(response.close)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b'src="/content-assets/'
            b'%E6%8A%80%E6%9C%AF%E7%AC%94%E8%AE%B0/03-JVM/jvm-memory-model.svg"',
            response.data,
        )
        self.assertIn(
            b'src="/content-assets/'
            b'%E6%8A%80%E6%9C%AF%E7%AC%94%E8%AE%B0/03-JVM/JVM-%E5%9E%83%E5%9C%BE'
            b'%E5%9B%9E%E6%94%B6.png"',
            response.data,
        )

    def test_non_image_asset_has_no_preview_page(self):
        response = self.client.get("/media/AI/Agent/react.md")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
