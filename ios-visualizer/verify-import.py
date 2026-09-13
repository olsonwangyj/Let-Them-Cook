"""Verify the sanitized import baseline, not later intentional app changes."""

import hashlib
import json
import os
from pathlib import Path
import sys


def verify(root):
    root = root.resolve()
    manifest = json.loads((root / "import-manifest.json").read_text(encoding="utf-8"))
    failures = []
    for entry in manifest["files"]:
        relative = entry["path"]
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            failures.append(f"Unsafe manifest path: {relative}")
            continue
        if not path.is_file():
            failures.append(f"Missing: {relative}")
            continue
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            first = stream.read(1024 * 1024)
            pointer = first.startswith(b"version https://git-lfs.github.com/spec/v1\n")
            digest.update(first)
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if pointer:
            failures.append(f"Git LFS pointer; run git lfs pull: {relative}")
        elif path.stat().st_size != entry["bytes"] or digest.hexdigest() != entry["sha256"]:
            failures.append(f"Changed or incomplete: {relative}")
    if os.name == "posix":
        for relative in manifest["executable_files"]:
            path = (root / relative).resolve()
            if not path.is_relative_to(root) or not os.access(path, os.X_OK):
                failures.append(f"Missing executable permission: {relative}")
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        print(f"IMPORT_CHECK_FAILED: {len(failures)} issue(s)", file=sys.stderr)
        return 1
    print(f"IMPORT_OK: {len(manifest['files'])} baseline files; {manifest['total_bytes']} bytes")
    print("This verifies download integrity only; iOS build and app integration remain separate.")
    return 0


if __name__ == "__main__":
    sys.exit(verify(Path(__file__).parent))
