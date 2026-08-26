from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SidebarCollapseTest(unittest.TestCase):
    def test_desktop_sidebar_collapse_is_wired_end_to_end(self):
        template = (ROOT / "templates/_sidebar.html").read_text()
        css = (ROOT / "static/css/style.css").read_text()
        javascript = (ROOT / "static/js/main.js").read_text()

        self.assertIn('id="sidebar-close" aria-controls="sidebar"', template)
        self.assertIn("body.sidebar-collapsed .sidebar", css)
        self.assertIn("kb-sidebar-collapsed", javascript)
        self.assertIn("body.classList.toggle('sidebar-collapsed', collapsed)", javascript)
        self.assertNotIn("transition: margin-left", css)
        self.assertIn("main.animate(", javascript)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertIn("prefers-reduced-motion: reduce", javascript)


if __name__ == "__main__":
    unittest.main()
