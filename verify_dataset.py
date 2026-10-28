#!/usr/bin/env python3
"""Read-only size and SHA-256 verification of an extracted dataset."""

import argparse
import csv
import hashlib
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys


SHA_PATTERN = re.compile(r"[0-9a-fA-F]{64}\Z")
BLOCK_SIZE = 1024 * 1024


def safe_member(root, member):
    """Reject traversal, Windows drives/streams, and symlinks escaping the root."""
    if not isinstance(member, str) or not member or "\\" in member or ":" in member or any(ord(char) < 32 for char in member):
        raise ValueError("invalid path characters")
    posix = PurePosixPath(member)
    windows = PureWindowsPath(member)
    if posix.is_absolute() or windows.drive or any(part in ("", ".", "..") for part in member.split("/")):
        raise ValueError("absolute or noncanonical path")
    candidate = root.joinpath(*posix.parts)
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ValueError("path escapes the dataset root") from None
    return candidate


def digest_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(BLOCK_SIZE), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(root, manifest):
    if not root.is_dir():
        raise ValueError("--root must identify an existing extracted dataset directory")
    root = root.resolve()
    checked = 0
    passed = 0
    issues = []
    seen = set()
    with manifest.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)) or not {"path", "size_bytes", "sha256"}.issubset(reader.fieldnames):
            raise ValueError("CSV requires unique headers including path,size_bytes,sha256")
        for line_number, row in enumerate(reader, 2):
            checked += 1
            member = row.get("path")
            try:
                path = safe_member(root, member)
                identity = os.path.normcase(member)
                if identity in seen:
                    raise ValueError("duplicate manifest path")
                seen.add(identity)
                size = int(row["size_bytes"])
                expected_hash = row["sha256"]
                if size < 0 or not isinstance(expected_hash, str) or not SHA_PATTERN.fullmatch(expected_hash):
                    raise ValueError("invalid size or SHA-256")
            except (ValueError, TypeError, OSError, RuntimeError):
                issues.append("CSV line {}: invalid/unsafe entry".format(line_number))
                continue
            if not path.is_file():
                issues.append("Missing or non-file: {}".format(member))
                continue
            try:
                actual_size = path.stat().st_size
                actual_hash = digest_file(path)
            except OSError:
                issues.append("Unreadable file: {}".format(member))
                continue
            if actual_size != size:
                issues.append("Size mismatch: {} (expected {}, found {})".format(member, size, actual_size))
            elif actual_hash != expected_hash.lower():
                issues.append("SHA-256 mismatch: {}".format(member))
            else:
                passed += 1
    if checked == 0:
        raise ValueError("the file manifest has no entries")
    print("Manifest entries: {}; verified: {}; differing/invalid entries: {}".format(checked, passed, checked - passed))
    for issue in issues[:50]:
        print("ERROR: " + issue)
    if len(issues) > 50:
        print("... {} further issues omitted.".format(len(issues) - 50))
    if not issues:
        print("All listed files passed size and SHA-256 checks. Dataset files were not changed.")
    return 1 if issues else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="extracted/UAV_Dataset_Public", help="Extracted dataset root directory")
    parser.add_argument("--manifest", type=Path, default=Path("FILE_MANIFEST.csv"), help="CSV containing path,size_bytes,sha256")
    args = parser.parse_args(argv)
    try:
        return verify(Path(args.root), args.manifest)
    except (ValueError, OSError, csv.Error) as error:
        message = str(error) if isinstance(error, ValueError) else "The manifest or a local file could not be read."
        print("ERROR: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
