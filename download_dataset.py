#!/usr/bin/env python3
"""Download and verify dataset release parts using only Python's standard library."""

import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request


REPOSITORY = "BCXXCDCS/UAV-MultiCamera-Tracking-Dataset"
TAG = "v1.0.0"
BASE_URL = "https://github.com/{}/releases/download/{}".format(REPOSITORY, TAG)
DEFAULT_MANIFEST = "https://raw.githubusercontent.com/{}/main/RELEASE_INFO.json".format(REPOSITORY)
PART_PATTERN = re.compile(r"UAV_Dataset_Public\.7z\.([0-9]{3,})\Z")
SHA_PATTERN = re.compile(r"[0-9a-fA-F]{64}\Z")
BLOCK_SIZE = 1024 * 1024
METADATA_NAMES = ("SHA256SUMS.txt", "ARCHIVE_SHA256.txt", "FILE_MANIFEST.csv", "FILE_SHA256SUMS.txt")


class DownloadError(Exception):
    """An expected download, validation, or local-file conflict."""


def https_url(value):
    if not isinstance(value, str):
        raise DownloadError("A download URL is missing or invalid.")
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise DownloadError("Download URLs must use HTTPS without embedded credentials.")
    return value


def open_url(url, headers=None):
    request = urllib.request.Request(https_url(url), headers=headers or {})
    try:
        response = urllib.request.urlopen(request, timeout=60)
    except urllib.error.HTTPError as error:
        raise DownloadError("HTTPS request failed with status {}.".format(error.code)) from None
    except (urllib.error.URLError, OSError):
        raise DownloadError("HTTPS request failed; check connectivity and retry.") from None
    try:
        https_url(response.geturl())
    except Exception:
        response.close()
        raise
    return response


def fetch_bytes(url, limit=64 * 1024 * 1024):
    try:
        with open_url(url) as response:
            data = response.read(limit + 1)
    except DownloadError:
        raise
    except (OSError, ValueError, http.client.HTTPException):
        raise DownloadError("HTTPS response could not be read; retry the download.") from None
    if len(data) > limit:
        raise DownloadError("The manifest or metadata response exceeds its size limit.")
    return data


def parse_manifest(raw):
    try:
        manifest = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeError, ValueError):
        raise DownloadError("RELEASE_INFO.json is not valid UTF-8 JSON.") from None
    if not isinstance(manifest, dict) or not isinstance(manifest.get("parts"), list) or not manifest["parts"]:
        raise DownloadError("RELEASE_INFO.json must contain a nonempty parts list.")
    for index, part in enumerate(manifest["parts"], 1):
        if not isinstance(part, dict):
            raise DownloadError("Each part entry must be an object.")
        name = part.get("name")
        match = PART_PATTERN.fullmatch(name) if isinstance(name, str) else None
        if not match or name != "UAV_Dataset_Public.7z.{:03d}".format(index):
            raise DownloadError("Part names must be safe, contiguous, and ordered from .001.")
        size = part.get("size_bytes")
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            raise DownloadError("Each part needs a positive integer size_bytes.")
        if not isinstance(part.get("sha256"), str) or not SHA_PATTERN.fullmatch(part["sha256"]):
            raise DownloadError("Each part needs a valid SHA-256 digest.")
        https_url(part.get("url"))
    return manifest


def read_manifest(location):
    if location.startswith("https://"):
        raw = fetch_bytes(location, 8 * 1024 * 1024)
    elif "://" in location:
        raise DownloadError("--manifest accepts a local file or an HTTPS URL.")
    else:
        path = Path(location)
        if path.stat().st_size > 8 * 1024 * 1024:
            raise DownloadError("The local manifest exceeds its size limit.")
        raw = path.read_bytes()
    return parse_manifest(raw), raw


def digest_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(BLOCK_SIZE), b""):
            digest.update(block)
    return digest.hexdigest()


def reject_symlink(path):
    if path.is_symlink():
        raise DownloadError("Refusing to use a symbolic link: {}".format(path.name))


def publish_new(temporary, destination):
    """Publish the complete file atomically without overwriting an existing name."""
    try:
        os.link(str(temporary), str(destination))
    except FileExistsError:
        raise DownloadError("A destination appeared during download; it was left unchanged: {}".format(destination.name)) from None
    except OSError:
        if os.name == "nt":
            # Windows rename refuses an existing destination, including on FAT
            # volumes that do not support hard links.
            try:
                os.rename(str(temporary), str(destination))
                return
            except OSError:
                pass
        raise DownloadError("Cannot publish the verified file without overwriting; check the temporary file: {}".format(temporary.name)) from None
    temporary.unlink()


def save_metadata(raw, destination):
    reject_symlink(destination)
    if destination.exists():
        if not destination.is_file() or destination.read_bytes() != raw:
            raise DownloadError("Existing metadata differs; move it aside explicitly before retrying: {}".format(destination.name))
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=destination.name + ".", suffix=".metadata.partial", dir=str(destination.parent), delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        publish_new(temporary, destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def metadata_urls(manifest):
    """Optional metadata URL overrides; the four named checksum files are fixed."""
    overrides = manifest.get("metadata", {})
    if not isinstance(overrides, dict):
        raise DownloadError("Optional metadata must be an object mapping filenames to HTTPS URLs.")
    urls = {}
    for name in ("RELEASE_INFO.json",) + METADATA_NAMES:
        value = overrides.get(name, BASE_URL + "/" + urllib.parse.quote(name))
        if isinstance(value, dict):
            value = value.get("url")
        urls[name] = https_url(value)
    return urls


def download_metadata(manifest, raw_manifest, output):
    # A repository manifest discovers the parts; require the release copy to agree.
    urls = metadata_urls(manifest)
    release_raw = fetch_bytes(urls["RELEASE_INFO.json"], 8 * 1024 * 1024)
    if parse_manifest(release_raw) != manifest:
        raise DownloadError("The repository/local manifest differs from the release manifest.")
    save_metadata(release_raw, output / "RELEASE_INFO.json")
    for name in METADATA_NAMES:
        save_metadata(fetch_bytes(urls[name]), output / name)


def download_part(part, output):
    destination = output / part["name"]
    partial = output / (part["name"] + ".partial")
    reject_symlink(destination)
    reject_symlink(partial)
    expected_size = part["size_bytes"]
    expected_hash = part["sha256"].lower()
    if destination.exists():
        if not destination.is_file() or destination.stat().st_size != expected_size or digest_file(destination) != expected_hash:
            raise DownloadError("An existing final part failed verification and was left unchanged: {}".format(destination.name))
        print("Verified existing part: {}".format(destination.name))
        return
    if partial.exists() and not partial.is_file():
        raise DownloadError("The partial download path is not a file: {}".format(partial.name))
    offset = partial.stat().st_size if partial.exists() else 0
    if offset > expected_size:
        raise DownloadError("The partial download is oversized; move it aside before retrying: {}".format(partial.name))
    if offset < expected_size:
        headers = {"Range": "bytes={}-".format(offset)} if offset else {}
        try:
            with open_url(part["url"], headers) as response:
                status = response.status
                if status == 206:
                    content_range = response.headers.get("Content-Range", "")
                    match = re.fullmatch(r"bytes ([0-9]+)-([0-9]+)/([0-9]+)", content_range.strip())
                    if not match or int(match[1]) != offset or int(match[3]) != expected_size or int(match[2]) != expected_size - 1:
                        raise DownloadError("The server returned an invalid resume range: {}".format(partial.name))
                elif status == 200:
                    # The server ignored Range. Restart only our own .partial file.
                    offset = 0
                else:
                    raise DownloadError("Unexpected HTTP status {} for {}.".format(status, partial.name))
                length = response.headers.get("Content-Length")
                if length is not None:
                    try:
                        valid_length = int(length) == expected_size - offset
                    except ValueError:
                        valid_length = False
                    if not valid_length:
                        raise DownloadError("The server returned an unexpected response size: {}".format(partial.name))
                mode = "ab" if offset else "wb"
                with partial.open(mode) as stream:
                    received = offset
                    for block in iter(lambda: response.read(BLOCK_SIZE), b""):
                        if received + len(block) > expected_size:
                            raise DownloadError("The response exceeds the expected part size: {}".format(partial.name))
                        stream.write(block)
                        received += len(block)
                    stream.flush()
                    os.fsync(stream.fileno())
        except DownloadError:
            raise
        except (OSError, ValueError, http.client.HTTPException):
            raise DownloadError("Part download was interrupted; its partial file was retained: {}".format(partial.name)) from None
    if partial.stat().st_size != expected_size:
        raise DownloadError("Incomplete download; retry to resume: {}".format(partial.name))
    if digest_file(partial) != expected_hash:
        raise DownloadError("SHA-256 mismatch; no final file was published. Move the damaged partial aside before retrying: {}".format(partial.name))
    publish_new(partial, destination)
    print("Downloaded and verified: {}".format(destination.name))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="downloads", help="Destination directory (default: downloads)")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help="RELEASE_INFO.json local path or HTTPS URL")
    args = parser.parse_args(argv)
    try:
        manifest, raw = read_manifest(args.manifest)
        output = Path(args.output).resolve()
        output.mkdir(parents=True, exist_ok=True)
        download_metadata(manifest, raw, output)
        for part in manifest["parts"]:
            download_part(part, output)
        print("All {} release parts passed size and SHA-256 checks.".format(len(manifest["parts"])))
        print("Extract UAV_Dataset_Public.7z.001 with 7-Zip, or run merge_parts.py.")
        return 0
    except (DownloadError, OSError, ValueError) as error:
        # Expected messages contain filenames/statuses, never request URLs or headers.
        message = str(error) if isinstance(error, DownloadError) else "A local file could not be read or written."
        print("ERROR: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
