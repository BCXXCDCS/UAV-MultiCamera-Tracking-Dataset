# Data release v1.0.0

This release packages the existing `UAV_Dataset_Public` data-only project export for download through GitHub Releases. It preserves the source files and relative directory structure, including the original package README. Original source files have not been modified or deleted.

It is **not a validated, complete benchmark release**. Publication, archive testing, and checksum generation establish packaging and transfer integrity; they do not resolve annotation or dataset-version limitations.

## Download inventory

| Item | Value |
|---|---|
| Source files recorded in the manifest | 19,853 |
| Source file bytes before compression | 15,698,149,124 |
| Compressed archive bytes | 12,915,238,189 |
| Numbered archive parts | 8 |
| Maximum volume size | 1,800,000,000 bytes (1.8 decimal GB, not GiB) |
| Archive root directory | `UAV_Dataset_Public/` |

The numbered files `UAV_Dataset_Public.7z.001`, `.002`, and subsequent parts form one split 7-Zip archive. Every part is required. The last part may be smaller than the maximum volume size. Large archive parts are release assets and are not stored in Git history.

Download the parts together with `SHA256SUMS.txt`, `ARCHIVE_SHA256.txt`, `FILE_MANIFEST.csv`, and `FILE_SHA256SUMS.txt`. Verify each part against `SHA256SUMS.txt`. Either open `.001` directly in 7-Zip while all parts are in the same directory, or join the parts in numerical order and verify the merged `.7z` file against `ARCHIVE_SHA256.txt`. Extract to an empty destination, then use the file manifest to check extracted paths, byte sizes, and SHA-256 hashes.

The [repository README](https://github.com/BCXXCDCS/UAV-MultiCamera-Tracking-Dataset/blob/main/README.md) provides complete Windows PowerShell and Linux/macOS commands, both extraction routes, storage guidance, and Python helper usage. Direct extraction from `.001` avoids storing an additional merged archive.

## Included data

- Project YOLO images and labels under `dataset/yolo-dataset/{train,val,test,test1}/`.
- 47 single-camera videos and 92 multi-camera videos across 26 scenes under `track_video/`.
- 47 single-camera and 26 scene-level multi-camera ground-truth files in the retained `output_` directories. These directories contain ground truth only, not experiment results.
- Per-camera ground truth for the four K10 cameras and two K2 cameras under `track_video_test/`.
- `data1.json`, containing COCO annotations for the project's self-collected test images.

Third-party DUT data, research code, model weights, caches, logs, and experiment outputs are excluded. Repository helper scripts are provided for downloading, joining archive parts, and checking file integrity; they are not the research/tracking implementation.

## Known limitations retained from the source README

An earlier inventory recorded 8,948 images and 10,685 label files. In `train`, 753 images lacked a same-name label and 241 labels lacked a corresponding image. In `val`, 2,249 labels lacked a same-name image. `test` and `test1` contained 1,125 and 4,218 image-label pairs, respectively. There is content overlap among `train`, `val`, and `test`, and the role of `test1` remains unconfirmed. Directory names alone do not define an independent evaluation protocol.

The first six ground-truth columns are `frame, id, x1, y1, x2, y2`; the final three columns of nine-column files are not fully documented. Some frame/ID combinations have multiple boxes. Aggregated multi-camera annotations do not contain camera identifiers. Complete per-camera ground truth and global-ID/synchronization mappings for all 92 streams were not located in the earlier review. Only K10 and K2 have per-camera ground truth in the supplied export.

The earlier single-camera video inventory contained 17,891 frames, compared with 29,264 reported in the manuscript. The intended version must be confirmed by the owners. The earlier multi-camera frame count was 20,184. This publication does not relabel, deduplicate, repair splits, create global identities, reconstruct synchronization, or perform new annotation validation.

## License and citation

License: **Not specified in the supplied materials; to be confirmed by the owners.** This release does not assert CC BY, CC0, or another public reuse license.

No verified paper author list or DOI is supplied. See the repository README for a release-URL citation template. The GitHub repository/release URL is not presented as a DOI or a substitute for a verified paper citation.
