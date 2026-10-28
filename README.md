# UAV Multi-Camera Tracking Dataset Files

This repository documents a data-only export of the self-collected UAV surveillance files retained from the research project. Dataset archives are distributed through [GitHub Releases](https://github.com/BCXXCDCS/UAV-MultiCamera-Tracking-Dataset/releases); the Git repository contains documentation, checksums, a file manifest, and download/verification helpers.

The GitHub **Code > Download ZIP** archive contains only the repository files; it does **not** include the dataset videos, images, or labels. Download the dataset from GitHub Releases instead.

The export preserves the source files and their relative directory structure. Original files have not been modified or deleted. It is **not a validated, complete benchmark release**. The annotation and dataset-version limitations below are part of the release description.

Third-party DUT data, research source code, model weights, caches, logs, and experiment outputs are excluded. Directories whose names begin with `output_` contain only retained ground-truth files in this package.

## Release assets and storage

Release: [`v1.0.0`](https://github.com/BCXXCDCS/UAV-MultiCamera-Tracking-Dataset/releases/tag/v1.0.0).

- Source files recorded by the file manifest: **19,853**.
- Source file bytes before compression: **15,698,149,124**.
- Total compressed archive bytes: **12,915,238,189**.
- Split archive parts: **8**.
- Maximum part size: **1,800,000,000 bytes**, or **1.8 decimal GB**; this is not 1.8 GiB. The final part may be smaller.

| Part | Bytes | SHA-256 |
|---|---:|---|
| [UAV_Dataset_Public.7z.001](https://github.com/BCXXCDCS/UAV-MultiCamera-Tracking-Dataset/releases/download/v1.0.0/UAV_Dataset_Public.7z.001) | 1,800,000,000 | `95033750419bc7adc859685d442b0cb6a3d8da1da6708428b7c5a0ec2c81b519` |
| [UAV_Dataset_Public.7z.002](https://github.com/BCXXCDCS/UAV-MultiCamera-Tracking-Dataset/releases/download/v1.0.0/UAV_Dataset_Public.7z.002) | 1,800,000,000 | `36b24235fb5b50117b694fd31c8e33dd375f02cd64af7ab75fd87a4de0e88779` |
| [UAV_Dataset_Public.7z.003](https://github.com/BCXXCDCS/UAV-MultiCamera-Tracking-Dataset/releases/download/v1.0.0/UAV_Dataset_Public.7z.003) | 1,800,000,000 | `f6af03475fdd2f2a61645a83fc672f41b73a2f46fbe3d675fc389ddeddc9960c` |
| [UAV_Dataset_Public.7z.004](https://github.com/BCXXCDCS/UAV-MultiCamera-Tracking-Dataset/releases/download/v1.0.0/UAV_Dataset_Public.7z.004) | 1,800,000,000 | `96bafda4460e1968a9f7cf1aa2e6090ea6e5267258ce5dae77ee6791a043cfe0` |
| [UAV_Dataset_Public.7z.005](https://github.com/BCXXCDCS/UAV-MultiCamera-Tracking-Dataset/releases/download/v1.0.0/UAV_Dataset_Public.7z.005) | 1,800,000,000 | `206f932ec93992281b37ab2684da5c5a8a8bb0220a7c8c2bf89dca7db67938da` |
| [UAV_Dataset_Public.7z.006](https://github.com/BCXXCDCS/UAV-MultiCamera-Tracking-Dataset/releases/download/v1.0.0/UAV_Dataset_Public.7z.006) | 1,800,000,000 | `8b075b4ab3655f5224bd7d22785ed0e1e2700484c8abe67ff442b09eceb1c633` |
| [UAV_Dataset_Public.7z.007](https://github.com/BCXXCDCS/UAV-MultiCamera-Tracking-Dataset/releases/download/v1.0.0/UAV_Dataset_Public.7z.007) | 1,800,000,000 | `ed8483cfbd43ee8bbc03b3803192d9b4f8210bf37de47f0a3c63a2046689e928` |
| [UAV_Dataset_Public.7z.008](https://github.com/BCXXCDCS/UAV-MultiCamera-Tracking-Dataset/releases/download/v1.0.0/UAV_Dataset_Public.7z.008) | 315,238,189 | `f419292cd9c501e5dcf7e52bcd4db4b424b05d723520033f50e8c6305a7a0fa9` |


Download **every** `UAV_Dataset_Public.7z.001`, `.002`, and subsequent numbered part. Keep the names unchanged and all parts in the same directory. They are volumes of one archive, not independent archives.

| Small release asset | Purpose |
|---|---|
| `RELEASE_INFO.json` | Machine-readable release metadata used by `download_dataset.py` to locate the numbered archive parts and verification assets for automatic download. |
| `SHA256SUMS.txt` | SHA-256 checksums for the archive parts and accompanying assets listed in the file. |
| `ARCHIVE_SHA256.txt` | SHA-256 checksum of the single `.7z` file obtained by joining all parts in numerical order. |
| `FILE_MANIFEST.csv` | Relative file paths, byte sizes, and SHA-256 checksums for the source files. |
| `FILE_SHA256SUMS.txt` | File checksum list whose paths are relative to the parent of the extracted `UAV_Dataset_Public` directory. |

Download these small assets as well as the numbered parts. Checksums establish transfer and file integrity; they do not establish annotation correctness or grant reuse rights.

Allow enough disk space for the downloaded parts and the extracted data. If you also create a merged archive, allow roughly **twice the compressed archive size plus the source file size**, with additional filesystem headroom. Direct extraction from `.001` avoids storing a second compressed copy.

## Download, verify, and extract

Install Python 3 and 7-Zip. On Windows, the commands below use the usual `C:\Program Files\7-Zip\7z.exe` installation path; adjust it if needed. On Linux/macOS, the examples use `7zz`; substitute `7z` if that is the command installed on your system.

Clone this lightweight repository, or download its code ZIP and open a terminal in the extracted repository directory:

```text
git clone https://github.com/BCXXCDCS/UAV-MultiCamera-Tracking-Dataset.git
cd UAV-MultiCamera-Tracking-Dataset
```

### Windows PowerShell

Download the archive parts and small verification assets:

```powershell
py -3 .\download_dataset.py --output downloads
```

Alternatively, download all parts and all small assets from the release page into `downloads`. Verify **every entry** in `SHA256SUMS.txt` before extraction:

```powershell
function Test-Sha256List {
    param([string]$ListPath, [string]$Root)
    $basePath = (Resolve-Path -LiteralPath $Root).Path
    foreach ($line in Get-Content -LiteralPath $ListPath) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) { continue }
        if ($line -notmatch '^([0-9a-fA-F]{64})\s+\*?(.+)$') {
            throw "Invalid checksum line: $line"
        }
        $expectedHash = $Matches[1]
        $assetPath = Join-Path $basePath $Matches[2]
        if (-not (Test-Path -LiteralPath $assetPath -PathType Leaf)) {
            throw "Missing file: $assetPath"
        }
        $actualHash = (Get-FileHash -LiteralPath $assetPath -Algorithm SHA256).Hash
        if ($actualHash -ine $expectedHash) { throw "SHA-256 mismatch: $assetPath" }
        Write-Host "OK $assetPath"
    }
}
Test-Sha256List -ListPath .\downloads\SHA256SUMS.txt -Root .\downloads
```

Choose **one** extraction route. Direct extraction uses less disk space and requires all parts to remain beside `.001`:

```powershell
$sevenZip = 'C:\Program Files\7-Zip\7z.exe'
& $sevenZip t .\downloads\UAV_Dataset_Public.7z.001
if ($LASTEXITCODE -ne 0) { throw '7-Zip archive test failed.' }
& $sevenZip x .\downloads\UAV_Dataset_Public.7z.001 -o.\extracted
if ($LASTEXITCODE -ne 0) { throw '7-Zip extraction failed.' }
```

Or merge the parts, check the merged archive hash, and extract that archive:

```powershell
py -3 .\merge_parts.py --input downloads --output UAV_Dataset_Public.7z
$expectedArchiveHash = ((Get-Content .\downloads\ARCHIVE_SHA256.txt | Select-Object -First 1) -split '\s+')[0]
$actualArchiveHash = (Get-FileHash .\UAV_Dataset_Public.7z -Algorithm SHA256).Hash
if ($actualArchiveHash -ine $expectedArchiveHash) { throw 'Merged archive SHA-256 mismatch.' }
$sevenZip = 'C:\Program Files\7-Zip\7z.exe'
& $sevenZip t .\UAV_Dataset_Public.7z
if ($LASTEXITCODE -ne 0) { throw '7-Zip archive test failed.' }
& $sevenZip x .\UAV_Dataset_Public.7z -o.\extracted
if ($LASTEXITCODE -ne 0) { throw '7-Zip extraction failed.' }
```

Verify the extracted files against the path/size/hash manifest:

```powershell
py -3 .\verify_dataset.py --root extracted/UAV_Dataset_Public --manifest downloads/FILE_MANIFEST.csv
```

The native checksum-list alternative uses the **parent** extraction directory as its root:

```powershell
Test-Sha256List -ListPath .\downloads\FILE_SHA256SUMS.txt -Root .\extracted
```

### Linux/macOS

Download the parts and small verification assets:

```bash
python3 download_dataset.py --output downloads
```

Check every archive part and accompanying asset listed in `SHA256SUMS.txt`. Use the command for your operating system:

```bash
# Linux
(cd downloads && sha256sum -c SHA256SUMS.txt)

# macOS
(cd downloads && shasum -a 256 -c SHA256SUMS.txt)
```

Choose **one** extraction route. Direct extraction avoids a second compressed copy:

```bash
7zz t downloads/UAV_Dataset_Public.7z.001 && \
  7zz x downloads/UAV_Dataset_Public.7z.001 -oextracted
```

Or merge the parts and verify the merged archive before extracting it:

```bash
python3 merge_parts.py --input downloads --output UAV_Dataset_Public.7z

# Linux
sha256sum -c downloads/ARCHIVE_SHA256.txt

# macOS
shasum -a 256 -c downloads/ARCHIVE_SHA256.txt

7zz t UAV_Dataset_Public.7z && \
  7zz x UAV_Dataset_Public.7z -oextracted
```

Check the extracted files against the manifest:

```bash
python3 verify_dataset.py --root extracted/UAV_Dataset_Public --manifest downloads/FILE_MANIFEST.csv
```

Alternatively, check the file checksum list from the **parent** extraction directory:

```bash
# Linux
(cd extracted && sha256sum -c ../downloads/FILE_SHA256SUMS.txt)

# macOS
(cd extracted && shasum -a 256 -c ../downloads/FILE_SHA256SUMS.txt)
```

The extracted archive has a single top-level directory, `UAV_Dataset_Public`. Extract into a fresh directory to avoid mixing release files with a previous copy. If a checksum or archive test fails, stop and re-download the affected part before using the data.

## Dataset contents

Paths below are relative to `UAV_Dataset_Public/`:

- `dataset/yolo-dataset/{train,val,test,test1}/{images,labels}/`: project images and YOLO label files; cache files and Python scripts are excluded.
- `track_video/video*.mp4`: 47 single-camera videos.
- `track_video/K1/` through `track_video/K26/`: 92 multi-camera videos across 26 scenes.
- `track_video/output_0114/*_gt.txt`: 47 single-camera ground-truth files.
- `track_video/output_0121_nocuda_noarea_K/*_gt.txt`: 26 scene-level multi-camera ground-truth files.
- `track_video_test/K10/*_gt.txt` and `track_video_test/K2/*_gt.txt`: per-camera ground truth for four and two cameras, respectively.
- `data1.json`: COCO annotations for the project's self-collected test images.

YOLO labels use `class_id center_x center_y width height`, with normalized box coordinates and class `0` denoting UAV. `data1.json` uses category ID `0` and string image IDs.

## Known limitations

The following statements are retained from the source package README. Packaging and checksum verification do not resolve them.

An earlier inventory recorded 8,948 images and 10,685 label files. In `train`, 753 images lacked a same-name label and 241 labels lacked a corresponding image. In `val`, 2,249 labels lacked a same-name image. `test` and `test1` contained 1,125 and 4,218 image-label pairs, respectively. Content overlaps exist among `train`, `val`, and `test`; the intended role of `test1` remains unconfirmed. These directory names should not be assumed to define an independent evaluation protocol.

The first six ground-truth columns represent `frame, id, x1, y1, x2, y2`. The final three columns of nine-column files are not fully documented. Some frame/ID combinations have multiple boxes. Aggregated multi-camera annotations lack a camera identifier. Complete per-camera annotations and global-ID/synchronization mappings for all 92 video streams were not located in the earlier review; only K10 and K2 have per-camera ground truth here.

The earlier single-camera video inventory contained 17,891 frames, whereas the manuscript reports 29,264. The owners must confirm the intended dataset version. The earlier multi-camera frame count was 20,184. This export does not resolve these limitations, repair annotations, or perform new annotation validation.

## License

**Not specified in the supplied materials; to be confirmed by the owners.** No public reuse license is asserted by this package. Availability for download does not establish a CC BY, CC0, or other reuse license.

## Citation

No verified paper-author citation or paper DOI is provided in the supplied materials. Until the owners provide a formal dataset or paper citation, the following template identifies this GitHub release only; replace the access date before use:

```text
UAV-MultiCamera-Tracking-Dataset. GitHub repository and data release v1.0.0.
https://github.com/BCXXCDCS/UAV-MultiCamera-Tracking-Dataset/releases/tag/v1.0.0
Accessed: YYYY-MM-DD.
```

This repository URL is not a DOI. Do not substitute unverified author names, paper details, or licensing claims.
