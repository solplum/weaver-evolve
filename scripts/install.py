#!/usr/bin/env python3
"""Install the same skill files into an explicitly selected host skill directory."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid


MAIN = "lzl-weaver-evolve"
LEGACY = "weaver-自我迭代"
SKILLS = (MAIN, "memory-keeper", "file-tidy", "debug-architect")


class InstallError(Exception):
    pass


def _nested(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _no_symlink_ancestors(path):
    for entry in (path, *path.parents):
        if entry.is_symlink():
            raise InstallError(f"Symbolic link in path: {entry}")


def _source_ok(source):
    _no_symlink_ancestors(source)
    if not source.is_dir() or not (source / "SKILL.md").is_file():
        raise InstallError(f"Missing skill source: {source}")
    for entry in (source, *source.rglob("*")):
        if entry.is_symlink() or not (entry.is_file() or entry.is_dir()):
            raise InstallError(f"Unsupported source entry: {entry}")


def make_plan(repo, destination, include_all=False, force=False):
    repo = Path(repo).resolve()
    destination = Path(os.path.abspath(Path(destination).expanduser()))
    _no_symlink_ancestors(destination)
    if _nested(destination, repo) or _nested(repo, destination):
        raise InstallError("Source repository and destination must not overlap")
    if destination.exists() and not destination.is_dir():
        raise InstallError(f"Destination is not a directory: {destination}")
    selected = SKILLS if include_all else (MAIN,)
    plan = []
    for name in selected:
        source = repo / "skills" / name
        _source_ok(source)
        target = destination / name
        legacy = destination / LEGACY if name == MAIN else None
        existing = [entry for entry in (target, legacy) if entry is not None and (entry.exists() or entry.is_symlink())]
        for entry in existing:
            if entry.is_symlink() or not entry.is_dir():
                raise InstallError(f"Existing skill is not a regular directory: {entry}")
        action = "skip" if existing and not force else "update" if existing else "install"
        plan.append({"name": name, "source": source, "target": target, "existing": existing, "action": action})
    return destination, plan


def install(repo, destination, include_all=False, force=False, dry_run=False):
    destination, plan = make_plan(repo, destination, include_all, force)
    for item in plan:
        prefix = "DRY-RUN " if dry_run else ""
        print(f"{prefix}{item['action'].upper()} {item['name']} -> {item['target']}")
    active = [item for item in plan if item["action"] != "skip"]
    result = {"installed": [] if dry_run else [item["name"] for item in active], "planned": [item["name"] for item in active], "skipped": [item["name"] for item in plan if item["action"] == "skip"], "backup": None}
    if dry_run or not active:
        if result["skipped"]:
            print("Existing skills kept; use --force to update or migrate the old name.")
        return result

    backup_parent = destination.parent / ".lzl-weaver-evolve-backups"
    _no_symlink_ancestors(backup_parent)
    if backup_parent.exists() and not backup_parent.is_dir():
        raise InstallError(f"Backup parent is not a directory: {backup_parent}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    made_destination = not destination.exists()
    moved = []
    placed = []
    backup = None
    with tempfile.TemporaryDirectory(prefix=".lzl-weaver-install-", dir=destination.parent) as temporary:
        stage = Path(temporary)
        for item in active:
            shutil.copytree(item["source"], stage / item["name"])
        try:
            destination.mkdir(exist_ok=True)
            for item in active:
                for old in item["existing"]:
                    if backup is None:
                        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                        backup = backup_parent / f"{stamp}-{uuid.uuid4().hex[:8]}"
                        backup.mkdir(parents=True)
                    saved = backup / old.name
                    old.rename(saved)
                    moved.append((old, saved))
                target = item["target"]
                (stage / item["name"]).rename(target)
                placed.append(target)
        except BaseException:
            for target in reversed(placed):
                shutil.rmtree(target)
            for old, saved in reversed(moved):
                saved.rename(old)
            if made_destination and destination.exists() and not any(destination.iterdir()):
                destination.rmdir()
            if backup is not None and not any(backup.iterdir()):
                backup.rmdir()
            raise
    if backup is not None:
        result["backup"] = str(backup)
        print(f"BACKUP {backup}")
    print(f"Installed {len(result['installed'])}; skipped {len(result['skipped'])}.")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", required=True, help="Existing host's skill directory; no platform is assumed")
    parser.add_argument("--all", action="store_true", help="Also install the three optional companion skills")
    parser.add_argument("--force", action="store_true", help="Back up and replace existing skills, migrating the old main name")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without creating or changing files")
    args = parser.parse_args()
    try:
        install(Path(__file__).resolve().parents[1], args.dest, args.all, args.force, args.dry_run)
    except (InstallError, OSError, shutil.Error) as error:
        print(f"Installation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
