"""
Download the H&M Personalized Fashion Recommendations dataset from Kaggle.

By default, downloads only the four CSV files we need for EDA and modeling
through Phase 3 (~700 MB total). The image folder (~24 GB) is gated behind
--with-images, because we only need images in Phase 4 — and image-embedding
work happens in Colab anyway.

Requires:
    - kaggle Python package (installed via environment.yml)
    - Kaggle access token at C:\\Users\\<you>\\.kaggle\\access_token
    - Accepted competition rules: https://www.kaggle.com/c/h-and-m-personalized-fashion-recommendations/rules

Usage:
    python scripts/download_data.py              # CSVs only (default)
    python scripts/download_data.py --with-images  # full ~25 GB download
    python scripts/download_data.py --force      # re-download even if files exist
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

COMPETITION = "h-and-m-personalized-fashion-recommendations"
CSV_FILES = [
    "articles.csv",
    "customers.csv",
    "transactions_train.csv",
    "sample_submission.csv",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def _human(n_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} TB"


def _maybe_unzip(zip_path: Path, out_dir: Path) -> None:
    """Extract a Kaggle-downloaded .zip in place and delete the archive."""
    if not zip_path.exists():
        return
    print(f"  extracting {zip_path.name} ...")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(out_dir)
    zip_path.unlink()


def download_csvs(api, force: bool) -> None:
    for fname in CSV_FILES:
        target = RAW_DIR / fname
        if target.exists() and not force:
            print(f"  {fname:30s}  already present ({_human(target.stat().st_size)})  skipping")
            continue
        print(f"  {fname:30s}  downloading ...")
        # Kaggle CLI downloads each file as <name>.zip
        api.competition_download_file(COMPETITION, fname, path=str(RAW_DIR), force=force)
        _maybe_unzip(RAW_DIR / f"{fname}.zip", RAW_DIR)
        if target.exists():
            print(f"  {fname:30s}  done ({_human(target.stat().st_size)})")


def download_images(api, force: bool) -> None:
    images_dir = RAW_DIR / "images"
    if images_dir.exists() and any(images_dir.iterdir()) and not force:
        print("  images/ already present, skipping")
        return
    print("  downloading full competition zip (~25 GB) — this will take a while ...")
    api.competition_download_files(COMPETITION, path=str(RAW_DIR), quiet=False, force=force)
    full_zip = RAW_DIR / f"{COMPETITION}.zip"
    _maybe_unzip(full_zip, RAW_DIR)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--with-images", action="store_true", help="also download item images (~24 GB)")
    parser.add_argument("--force", action="store_true", help="re-download even if files exist")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Import here so --help works without kaggle installed.
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("ERROR: 'kaggle' package not installed. Run: conda activate truss && pip install kaggle", file=sys.stderr)
        return 1

    api = KaggleApi()
    try:
        api.authenticate()
    except Exception as e:
        print(f"ERROR: Kaggle authentication failed: {e}", file=sys.stderr)
        print("Check that C:\\Users\\<you>\\.kaggle\\access_token exists and contains a valid KGAT_ token.", file=sys.stderr)
        return 1

    print(f"Target directory: {RAW_DIR}")
    print(f"Downloading CSVs from competition: {COMPETITION}")
    download_csvs(api, force=args.force)

    if args.with_images:
        print("\nDownloading images ...")
        download_images(api, force=args.force)
    else:
        print("\nSkipping images. Re-run with --with-images when you reach Phase 4 (image embeddings).")

    print("\nDone. Files in data/raw/:")
    for p in sorted(RAW_DIR.iterdir()):
        if p.is_file():
            print(f"  {p.name:40s}  {_human(p.stat().st_size)}")
        else:
            print(f"  {p.name}/  (dir)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
