import contextlib
import importlib.util
import io
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock


spec = importlib.util.spec_from_file_location("weaver_install", Path(__file__).resolve().parents[1] / "scripts/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve())
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.dest = self.root / "host" / "skills"
        for name in installer.SKILLS:
            path = self.repo / "skills" / name
            (path / "references").mkdir(parents=True)
            (path / "SKILL.md").write_text("---\nname: " + name + "\n---\nnew content\n")
            (path / "references" / "guide.md").write_text("source guide")
        self.output = io.StringIO()
        self.redirect = contextlib.redirect_stdout(self.output)
        self.redirect.__enter__()

    def tearDown(self):
        self.redirect.__exit__(None, None, None)
        self.temp.cleanup()

    def add_old(self, name):
        path = self.dest / name
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text("old " + name)
        (path / "custom.md").write_text("user modification")
        return path

    def run_install(self, **kwargs):
        return installer.install(self.repo, self.dest, **kwargs)

    def test_default_installs_only_main_with_resources(self):
        result = self.run_install()
        self.assertEqual([installer.MAIN], result["installed"])
        self.assertEqual([installer.MAIN], sorted(p.name for p in self.dest.iterdir()))
        self.assertEqual("source guide", (self.dest / installer.MAIN / "references/guide.md").read_text())

    def test_all_installs_four_skills(self):
        result = self.run_install(include_all=True)
        self.assertEqual(set(installer.SKILLS), set(result["installed"]))
        self.assertEqual(set(installer.SKILLS), {p.name for p in self.dest.iterdir()})

    def test_dry_run_does_not_create_target_or_parent(self):
        result = self.run_install(dry_run=True)
        self.assertEqual([], result["installed"])
        self.assertEqual([installer.MAIN], result["planned"])
        self.assertFalse(self.dest.parent.exists())

    def test_dry_run_update_keeps_existing_bytes(self):
        old = self.add_old(installer.LEGACY)
        self.run_install(force=True, dry_run=True)
        self.assertEqual("user modification", (old / "custom.md").read_text())
        self.assertFalse((self.dest / installer.MAIN).exists())
        self.assertFalse((self.dest.parent / ".lzl-weaver-evolve-backups").exists())

    def test_existing_skips_without_force(self):
        old = self.add_old(installer.MAIN)
        result = self.run_install()
        self.assertEqual([installer.MAIN], result["skipped"])
        self.assertEqual("old " + installer.MAIN, (old / "SKILL.md").read_text())
        self.assertIsNone(result["backup"])

    def test_legacy_requires_force_before_migration(self):
        self.add_old(installer.LEGACY)
        result = self.run_install()
        self.assertEqual([installer.MAIN], result["skipped"])
        self.assertTrue((self.dest / installer.LEGACY).exists())
        self.assertFalse((self.dest / installer.MAIN).exists())

    def test_force_migrates_and_backs_up_legacy_outside_skill_directory(self):
        self.add_old(installer.LEGACY)
        result = self.run_install(force=True)
        backup = Path(result["backup"])
        self.assertEqual("user modification", (backup / installer.LEGACY / "custom.md").read_text())
        self.assertEqual(self.dest.parent, backup.parent.parent)
        self.assertFalse((self.dest / installer.LEGACY).exists())
        self.assertTrue((self.dest / installer.MAIN / "SKILL.md").is_file())

    def test_force_preserves_both_preexisting_names(self):
        self.add_old(installer.LEGACY)
        self.add_old(installer.MAIN)
        result = self.run_install(force=True)
        backup = Path(result["backup"])
        for name in (installer.LEGACY, installer.MAIN):
            self.assertEqual("old " + name, (backup / name / "SKILL.md").read_text())
        self.assertFalse((self.dest / installer.LEGACY).exists())

    def test_missing_companion_rejects_entire_install_before_writes(self):
        shutil.rmtree(self.repo / "skills" / "file-tidy")
        with self.assertRaises(installer.InstallError):
            self.run_install(include_all=True)
        self.assertFalse(self.dest.parent.exists())

    def test_replacement_failure_rolls_back_all_previous_changes(self):
        old_contents = {}
        for name in installer.SKILLS:
            old = self.add_old(name)
            old_contents[name] = (old / "SKILL.md").read_bytes()
        legacy = self.add_old(installer.LEGACY)
        original_rename = Path.rename

        def fail_on_second_place(path, target):
            if path.name == "memory-keeper" and path.parent.name.startswith(".lzl-weaver-install-"):
                raise OSError("simulated placement failure")
            return original_rename(path, target)

        with mock.patch.object(Path, "rename", fail_on_second_place):
            with self.assertRaisesRegex(OSError, "simulated placement failure"):
                self.run_install(include_all=True, force=True)
        for name, data in old_contents.items():
            self.assertEqual(data, (self.dest / name / "SKILL.md").read_bytes())
            self.assertEqual("user modification", (self.dest / name / "custom.md").read_text())
        self.assertEqual("old " + installer.LEGACY, (legacy / "SKILL.md").read_text())

    def test_staging_failure_preserves_existing_install(self):
        old = self.add_old(installer.MAIN)
        with mock.patch.object(shutil, "copytree", side_effect=OSError("simulated copy failure")):
            with self.assertRaises(OSError):
                self.run_install(force=True)
        self.assertEqual("user modification", (old / "custom.md").read_text())

    def test_overlapping_destination_rejected(self):
        for target in (self.repo, self.repo / "skills", self.root):
            with self.subTest(target=target):
                with self.assertRaises(installer.InstallError):
                    installer.install(self.repo, target)

    def test_symlink_target_and_source_rejected(self):
        self.dest.mkdir(parents=True)
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        (self.dest / installer.MAIN).symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaises(installer.InstallError):
            self.run_install(force=True)
        (self.dest / installer.MAIN).unlink()
        (self.repo / "skills" / installer.MAIN / "references/escape").symlink_to(elsewhere)
        with self.assertRaises(installer.InstallError):
            self.run_install()
        self.assertEqual([], list(elsewhere.iterdir()))

    def test_symlink_source_ancestor_rejected(self):
        sources = self.repo / "skills"
        sources.rename(self.repo / "real-skills")
        sources.symlink_to(self.repo / "real-skills", target_is_directory=True)
        with self.assertRaises(installer.InstallError):
            self.run_install()
        self.assertFalse(self.dest.parent.exists())


if __name__ == "__main__":
    unittest.main()
