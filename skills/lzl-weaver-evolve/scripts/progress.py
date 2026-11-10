#!/usr/bin/env python3
"""Track Weaver source coverage and unresolved candidates in an explicit JSON file."""

import argparse
from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile


COVERAGES = {"complete", "partial", "unavailable"}
STATUSES = {"pending", "applied", "excluded"}


class ProgressError(Exception):
    pass


def empty_state():
    return {"schema_version": 1, "revision": 0, "sources": {}, "candidates": {}}


def fields(value, required, optional, label):
    if not isinstance(value, dict):
        raise ProgressError(f"{label} must be an object")
    missing = set(required) - value.keys()
    unknown = value.keys() - set(required) - set(optional)
    if missing or unknown:
        raise ProgressError(
            f"{label}: missing fields {sorted(missing)}, unknown fields {sorted(unknown)}"
        )


def reference(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ProgressError(f"{label} must be a nonempty reference string")


def same_json(left, right):
    # JSON booleans and numbers must remain distinct in an opaque cursor.
    options = {"sort_keys": True, "allow_nan": False}
    return json.dumps(left, **options) == json.dumps(right, **options)


def candidate_fields(candidate, label):
    reference(candidate["evidence"], f"{label}.evidence")
    if not isinstance(candidate["status"], str) or candidate["status"] not in STATUSES:
        raise ProgressError(f"{label}.status must be pending, applied, or excluded")
    for key in ("target", "reason"):
        if key in candidate and not isinstance(candidate[key], str):
            raise ProgressError(f"{label}.{key} must be a string")


def validate_state(state):
    fields(state, {"schema_version", "revision", "sources", "candidates"}, set(), "state")
    if type(state["schema_version"]) is not int or state["schema_version"] != 1:
        raise ProgressError("unsupported state schema_version")
    if type(state["revision"]) is not int or state["revision"] < 0:
        raise ProgressError("state.revision must be a nonnegative integer")
    if not isinstance(state["sources"], dict) or not isinstance(state["candidates"], dict):
        raise ProgressError("state sources and candidates must be objects")
    for source_id, source in state["sources"].items():
        reference(source_id, "source id")
        fields(source, {"coverage", "cursor"}, set(), f"source {source_id}")
        if not isinstance(source["coverage"], str) or source["coverage"] not in COVERAGES:
            raise ProgressError(f"source {source_id}: invalid coverage")
    for candidate_id, candidate in state["candidates"].items():
        reference(candidate_id, "candidate id")
        fields(candidate, {"source", "evidence", "status"}, {"target", "reason"},
               f"candidate {candidate_id}")
        reference(candidate["source"], f"candidate {candidate_id}.source")
        if candidate["source"] not in state["sources"]:
            raise ProgressError(f"candidate {candidate_id}: unknown source")
        candidate_fields(candidate, f"candidate {candidate_id}")
    return state


def read_json(path):
    def reject_constant(value):
        raise ProgressError(f"invalid JSON constant {value}")

    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
    except (OSError, ValueError) as error:
        raise ProgressError(f"cannot read JSON {path}: {error}") from error


def read_state(path):
    if not path.exists() and not path.is_symlink():
        return empty_state()
    return validate_state(read_json(path))


def apply_batch(state, batch):
    fields(batch, {"expected_revision", "sources"}, set(), "batch")
    if type(batch["expected_revision"]) is not int or batch["expected_revision"] < 0:
        raise ProgressError("expected_revision must be a nonnegative integer")
    if batch["expected_revision"] != state["revision"]:
        raise ProgressError(
            f"revision conflict: expected {batch['expected_revision']}, "
            f"current {state['revision']}; run show and rebuild the batch"
        )
    if not isinstance(batch["sources"], list):
        raise ProgressError("batch.sources must be an array")
    updated = deepcopy(state)
    seen_sources = set()
    for source in batch["sources"]:
        fields(source, {"id", "coverage"}, {"cursor", "candidates"}, "batch source")
        source_id = source["id"]
        reference(source_id, "source id")
        if source_id in seen_sources:
            raise ProgressError(f"duplicate source id in batch: {source_id}")
        seen_sources.add(source_id)
        coverage = source["coverage"]
        if not isinstance(coverage, str) or coverage not in COVERAGES:
            raise ProgressError(f"source {source_id}: invalid coverage")
        old_cursor = updated["sources"].get(source_id, {}).get("cursor")
        cursor = source.get("cursor", old_cursor)
        if coverage != "complete" and not same_json(cursor, old_cursor):
            raise ProgressError(
                f"source {source_id}: {coverage} coverage cannot change cursor"
            )
        updated["sources"][source_id] = {"coverage": coverage, "cursor": cursor}
        candidates = source.get("candidates", [])
        if not isinstance(candidates, list):
            raise ProgressError(f"source {source_id}.candidates must be an array")
        for candidate in candidates:
            fields(candidate, {"id", "status", "evidence"}, {"target", "reason"},
                   "batch candidate")
            candidate_id = candidate["id"]
            reference(candidate_id, "candidate id")
            candidate_fields(candidate, f"candidate {candidate_id}")
            previous = updated["candidates"].get(candidate_id)
            if previous:
                if previous["source"] != source_id or previous["evidence"] != candidate["evidence"]:
                    raise ProgressError(f"candidate {candidate_id}: source/evidence identity conflict")
                if previous["status"] != "pending" and candidate["status"] == "pending":
                    raise ProgressError(
                        f"candidate {candidate_id}: cannot reopen a completed candidate; use a new id"
                    )
            record = dict(previous or {})
            record.update({key: value for key, value in candidate.items() if key != "id"})
            record["source"] = source_id
            updated["candidates"][candidate_id] = record
    if not same_json(updated, state):
        updated["revision"] += 1
    return updated


@contextmanager
def exclusive_lock(path):
    lock_path = path.with_name(path.name + ".lock")
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ProgressError(
            f"state is locked: {lock_path}; after confirming no update process is running, "
            "remove the lock file and retry"
        ) from error
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as lock:
            json.dump({"pid": os.getpid()}, lock)
        yield
    finally:
        lock_path.unlink()


def write_atomic(path, state):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as output:
            temporary = Path(output.name)
            json.dump(state, output, ensure_ascii=False, indent=2, allow_nan=False)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        if path.is_symlink():
            raise ProgressError(f"refusing to write symlink state: {path}")
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def update_state(path, batch):
    if path.is_symlink():
        raise ProgressError(f"refusing to write symlink state: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(path):
        if path.is_symlink():
            raise ProgressError(f"refusing to write symlink state: {path}")
        state = read_state(path)
        updated = apply_batch(state, batch)
        if not same_json(updated, state):
            write_atomic(path, updated)
        return updated


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("show", "update"):
        command = commands.add_parser(name)
        command.add_argument("--state", type=Path, required=True)
        if name == "update":
            command.add_argument("--batch", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        state = (read_state(args.state) if args.command == "show"
                 else update_state(args.state, read_json(args.batch)))
        print(json.dumps(state, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ProgressError, OSError, ValueError) as error:
        print(f"progress: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
