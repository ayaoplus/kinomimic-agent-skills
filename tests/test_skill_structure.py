from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SkillStructureTest(unittest.TestCase):
    def test_skills_have_valid_minimum_frontmatter(self):
        for name in ("kinomimic-recreate", "kinomimic-render"):
            path = ROOT / "skills" / name / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"))
            frontmatter = text.split("---", 2)[1]
            self.assertRegex(frontmatter, rf"(?m)^name: {re.escape(name)}$")
            self.assertRegex(frontmatter, r"(?m)^description: .+")

    def test_no_absolute_home_paths(self):
        for path in (ROOT / "skills").rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="ignore")
                self.assertNotIn("/Users/", text, path)
                self.assertNotIn("/home/", text, path)


if __name__ == "__main__":
    unittest.main()
