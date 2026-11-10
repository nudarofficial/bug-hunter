"""Unit tests for the repository's validation and packaging scripts.

Run with:  python -m unittest discover -s tests -v
"""

import importlib.util
import json
import pathlib
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_script("validate_skill")
builder = load_script("build_release")

GOOD_DESCRIPTION = "Finds bugs. Use when the user reports a crash or asks to debug code."


def make_skill(tmp, name="demo-skill", frontmatter=None, body="# Demo\n", files=None):
    skill_dir = pathlib.Path(tmp) / name
    skill_dir.mkdir()
    if frontmatter is None:
        frontmatter = f"name: {name}\ndescription: {GOOD_DESCRIPTION}\n"
    (skill_dir / "SKILL.md").write_text(f"---\n{frontmatter}---\n{body}", encoding="utf-8")
    for rel, content in (files or {}).items():
        path = skill_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return skill_dir


class RealRepositoryTest(unittest.TestCase):
    def test_bug_hunter_skill_is_valid(self):
        self.assertEqual(validator.validate_skill(ROOT / "bug-hunter"), [])

    def test_repository_links_resolve(self):
        self.assertEqual(validator.validate_repo_links(ROOT), [])

    def test_skill_description_mentions_when_to_use(self):
        text = (ROOT / "bug-hunter" / "SKILL.md").read_text(encoding="utf-8")
        frontmatter, _ = validator.split_frontmatter(text)
        meta = validator.parse_frontmatter(frontmatter)
        self.assertIn("Use when", meta["description"])

    def test_evals_file_is_well_formed(self):
        data = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data), 3)
        for case in data:
            self.assertEqual(case["skills"], ["bug-hunter"])
            self.assertTrue(case["query"].strip())
            self.assertGreaterEqual(len(case["expected_behavior"]), 2)
            for rel in case.get("files", []):
                self.assertTrue((ROOT / rel).is_file(), rel)


class ValidatorRulesTest(unittest.TestCase):
    def check(self, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            return validator.validate_skill(make_skill(tmp, **kwargs))

    def test_minimal_valid_skill(self):
        self.assertEqual(self.check(), [])

    def test_missing_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = pathlib.Path(tmp) / "x"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# no frontmatter\n", encoding="utf-8")
            errors = validator.validate_skill(skill_dir)
        self.assertTrue(any("frontmatter" in e for e in errors))

    def test_uppercase_name_rejected(self):
        errors = self.check(name="Demo", frontmatter=f"name: Demo\ndescription: {GOOD_DESCRIPTION}\n")
        self.assertTrue(any("lowercase" in e for e in errors))

    def test_reserved_word_rejected(self):
        errors = self.check(name="claude-helper",
                            frontmatter=f"name: claude-helper\ndescription: {GOOD_DESCRIPTION}\n")
        self.assertTrue(any("reserved word 'claude'" in e for e in errors))

    def test_long_name_rejected(self):
        name = "a" * 65
        errors = self.check(name=name, frontmatter=f"name: {name}\ndescription: {GOOD_DESCRIPTION}\n")
        self.assertTrue(any("max 64" in e for e in errors))

    def test_name_must_match_directory(self):
        errors = self.check(frontmatter=f"name: other-name\ndescription: {GOOD_DESCRIPTION}\n")
        self.assertTrue(any("should match" in e for e in errors))

    def test_empty_description_rejected(self):
        errors = self.check(frontmatter="name: demo-skill\ndescription: \"\"\n")
        self.assertTrue(any("'description' is required" in e for e in errors))

    def test_long_description_rejected(self):
        errors = self.check(frontmatter=f"name: demo-skill\ndescription: {'x' * 1025}\n")
        self.assertTrue(any("max 1024" in e for e in errors))

    def test_xml_in_description_rejected(self):
        errors = self.check(frontmatter="name: demo-skill\ndescription: Debugs <b>code</b>\n")
        self.assertTrue(any("XML" in e for e in errors))

    def test_body_line_limit(self):
        errors = self.check(body="line\n" * 500)
        self.assertTrue(any("under 500" in e for e in errors))

    def test_broken_link_in_skill(self):
        errors = self.check(body="See [missing](reference/missing.md)\n")
        self.assertTrue(any("does not resolve" in e for e in errors))

    def test_unlinked_reference_file(self):
        errors = self.check(files={"reference/orphan.md": "# Orphan\n"})
        self.assertTrue(any("not linked directly" in e for e in errors))

    def test_nested_reference_rejected(self):
        errors = self.check(
            body="See [a](reference/a.md) and [b](reference/b.md)\n",
            files={"reference/a.md": "See [b](b.md)\n", "reference/b.md": "# B\n"})
        self.assertTrue(any("should not link onward" in e for e in errors))

    def test_long_reference_needs_contents(self):
        errors = self.check(body="See [a](reference/a.md)\n",
                            files={"reference/a.md": "# A\n" + "text\n" * 120})
        self.assertTrue(any("Contents" in e for e in errors))

    def test_backslash_link_rejected(self):
        errors = self.check(body="See [a](reference\\a.md)\n", files={"reference/a.md": "# A\n"})
        self.assertTrue(any("backslash" in e for e in errors))

    def test_links_inside_code_blocks_are_ignored(self):
        body = "```markdown\nSee [x](not-a-real-file.md)\n```\nInline `[y](nope.md)` too.\n"
        self.assertEqual(self.check(body=body), [])


class BuildReleaseTest(unittest.TestCase):
    def test_archive_layout_and_checksum(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, checksum = builder.build("9.9.9", pathlib.Path(tmp))
            self.assertEqual(archive.name, "bug-hunter-v9.9.9.zip")
            with zipfile.ZipFile(archive) as zf:
                names = zf.namelist()
            self.assertIn("bug-hunter/SKILL.md", names)
            self.assertIn("bug-hunter/LICENSE", names)
            self.assertTrue(all(n.startswith("bug-hunter/") for n in names))
            self.assertTrue(builder.verify(archive))
            digest, _, name = checksum.read_text(encoding="utf-8").strip().partition("  ")
            self.assertEqual(name, archive.name)
            self.assertEqual(len(digest), 64)

    def test_build_is_reproducible(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            first, _ = builder.build("1.0.0", pathlib.Path(a))
            second, _ = builder.build("1.0.0", pathlib.Path(b))
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_tampered_archive_fails_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, _ = builder.build("1.0.0", pathlib.Path(tmp))
            with archive.open("ab") as handle:
                handle.write(b"tampered")
            self.assertFalse(builder.verify(archive))


if __name__ == "__main__":
    unittest.main()
