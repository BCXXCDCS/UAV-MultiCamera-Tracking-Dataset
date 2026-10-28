#!/usr/bin/env python3
"""Verify and join a dataset's split 7z archive without shell commands."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile


PART_PATTERN = re.compile(r"UAV_Dataset_Public\.7z\.([0-9]{3,})\Z")
SHA_PATTERN = re.compile(r"[0-9a-fA-F]{64}\Z")
ARCHIVE_NAME = "UAV_Dataset_Public.7z"
BLOCK_SIZE = 1024 * 1024


class MergeError(Exception):
    """Invalid input, checksum failure, or an output conflict."""


def read_checksums(path):
    checksums = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([0-9a-fA-F]{64})[ \t]+\*?(.+)", line.strip())
        if not match:
            raise MergeError("Invalid checksum line {} in {}.".format(line_number, path.name))
        name = match[2]
        if "/" in name or "\\" in name or ":" in name or name in (".", ".."):
            raise MergeError("Unsafe filename in {}.".format(path.name))
        if name in checksums:
            raise MergeError("Duplicate filename in {}.".format(path.name))
        checksums[name] = match[1].lower()
    return checksums


def validate_part_order(parts):
    if not parts:
        raise MergeError("No archive parts were listed.")
    for index, part in enumerate(parts, 1):
        name = part.get("name")
        if not isinstance(name, str) or not PART_PATTERN.fullmatch(name) or name != ARCHIVE_NAME + ".{:03d}".format(index):
            raise MergeError("Part names must be safe, contiguous, and ordered from .001.")
        size = part.get("size_bytes")
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            raise MergeError("A part has an invalid size_bytes.")
        if not isinstance(part.get("sha256"), str) or not SHA_PATTERN.fullmatch(part["sha256"]):
            raise MergeError("A part has an invalid SHA-256 digest.")


def load_parts(input_directory, manifest_path=None):
    manifest_file = Path(manifest_path) if manifest_path else input_directory / "RELEASE_INFO.json"
    manifest = None
    if manifest_file.exists():
        try:
            if manifest_file.stat().st_size > 8 * 1024 * 1024:
                raise MergeError("The release manifest is unexpectedly large.")
            manifest = json.loads(manifest_file.read_text(encoding="utf-8-sig"))
        except (UnicodeError, ValueError):
            raise MergeError("The release manifest is invalid JSON.") from None
        if not isinstance(manifest, dict) or not isinstance(manifest.get("parts"), list):
            raise MergeError("The release manifest must contain a parts list.")
        parts = manifest["parts"]
        if not all(isinstance(part, dict) for part in parts):
            raise MergeError("Each part entry must be an object.")
        validate_part_order(parts)
    else:
        if manifest_path:
            raise MergeError("The explicit --manifest file does not exist.")
        checksums = read_checksums(input_directory / "SHA256SUMS.txt")
        names = [name for name in checksums if PART_PATTERN.fullmatch(name)]
        names.sort(key=lambda name: int(PART_PATTERN.fullmatch(name)[1]))
        # The checksum list defines the final part number, so a missing last volume
        # cannot be mistaken for a complete shorter archive.
        parts = []
        for name in names:
            part_file = input_directory / name
            if not part_file.is_file() or part_file.is_symlink():
                raise MergeError("A checksum-listed part is missing or is a link: {}".format(name))
            parts.append({"name": name, "size_bytes": part_file.stat().st_size, "sha256": checksums[name]})
        validate_part_order(parts)
    return parts, manifest


def expected_archive_hash(input_directory, manifest):
    declared = None
    if manifest:
        declared = manifest.get("archive_sha256")
        if declared is None and isinstance(manifest.get("archive"), dict):
            declared = manifest["archive"].get("sha256")
        if declared is not None and (not isinstance(declared, str) or not SHA_PATTERN.fullmatch(declared)):
            raise MergeError("The manifest archive SHA-256 digest is invalid.")
        if declared is not None:
            declared = declared.lower()
    recorded = None
    checksum_file = input_directory / "ARCHIVE_SHA256.txt"
    if checksum_file.exists():
        text = checksum_file.read_text(encoding="utf-8-sig").strip()
        if SHA_PATTERN.fullmatch(text):
            recorded = text.lower()
        else:
            recorded = read_checksums(checksum_file).get(ARCHIVE_NAME)
            if recorded is None:
                raise MergeError("ARCHIVE_SHA256.txt does not identify {}.".format(ARCHIVE_NAME))
    if declared and recorded and declared != recorded:
        raise MergeError("The archive hashes in the manifest and checksum file disagree.")
    if not (declared or recorded):
        raise MergeError("An archive SHA-256 is required in the manifest or ARCHIVE_SHA256.txt.")
    return declared or recorded


def merge_parts(input_directory, output, manifest_path=None):
    if output.exists() or output.is_symlink():
        raise MergeError("The output already exists and will not be overwritten: {}".format(output.name))
    parts, manifest = load_parts(input_directory, manifest_path)
    expected_hash = expected_archive_hash(input_directory, manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    digest = hashlib.sha256()
    total = 0
    try:
        with tempfile.NamedTemporaryFile(prefix=output.name + ".", suffix=".merge.partial", dir=str(output.parent), delete=False) as destination:
            temporary = Path(destination.name)
            for part in parts:
                path = input_directory / part["name"]
                if path.is_symlink() or not path.is_file():
                    raise MergeError("A part is missing, not a file, or is a link: {}".format(part["name"]))
                if path.stat().st_size != part["size_bytes"]:
                    raise MergeError("Part size mismatch: {}".format(part["name"]))
                part_digest = hashlib.sha256()
                part_size = 0
                with path.open("rb") as source:
                    for block in iter(lambda: source.read(BLOCK_SIZE), b""):
                        part_size += len(block)
                        part_digest.update(block)
                        digest.update(block)
                        destination.write(block)
                if part_size != part["size_bytes"] or part_digest.hexdigest() != part["sha256"].lower():
                    raise MergeError("Part verification failed: {}".format(part["name"]))
                total += part_size
                print("Verified part: {}".format(part["name"]))
            destination.flush()
            os.fsync(destination.fileno())
        if digest.hexdigest() != expected_hash:
            raise MergeError("The merged archive SHA-256 does not match; no final archive was published.")
        try:
            os.link(str(temporary), str(output))
        except FileExistsError:
            raise MergeError("An output appeared during merging and was left unchanged.") from None
        except OSError:
            if os.name != "nt":
                raise MergeError("Cannot publish the merged archive without overwriting an existing file.") from None
            try:
                os.rename(str(temporary), str(output))
            except OSError:
                raise MergeError("Cannot publish the merged archive without overwriting an existing file.") from None
        print("Merged and verified: {} ({} bytes)".format(output.name, total))
        print("SHA-256: " + digest.hexdigest())
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="downloads", help="Directory containing all parts and metadata")
    parser.add_argument("--output", default=ARCHIVE_NAME, help="New archive path; existing paths are never overwritten")
    parser.add_argument("--manifest", help="Explicit local RELEASE_INFO.json (default: INPUT/RELEASE_INFO.json)")
    args = parser.parse_args(argv)
    try:
        merge_parts(Path(args.input).resolve(), Path(args.output).absolute(), args.manifest)
        return 0
    except (MergeError, OSError) as error:
        message = str(error) if isinstance(error, MergeError) else "An input or output file could not be read or written."
        print("ERROR: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
