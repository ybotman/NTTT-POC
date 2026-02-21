#!/usr/bin/env python3
"""
NTTT v2.0 - Upload Music to Azure Blob Storage

Uses Azure CLI (az) to upload MP3 files with MD5 hash verification.
Storage is publicly readable but only updatable internally.

Usage:
    python uploadToAzure_v2.py --dry-run
    python uploadToAzure_v2.py --sample=10
    python uploadToAzure_v2.py --full
"""

import json
import os
import subprocess
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

# New NTTT storage (not BORIS anymore)
STORAGE_ACCOUNT = "nttt"
CONTAINER_NAME = "v20"  # Version 2.0 container - new version = new container
RESOURCE_GROUP = "tangotiempo"

# Source files
SONGS_FILE = "./djSongs_boris.json"  # Will be renamed to djSongs_nttt.json after migration
MATCHED_FILE = "./djMatchedSongs_boris.json"
SOURCE_FOLDER = "/Volumes/EXTVideo1/djImports/NTTTUpload_v20"

# Azure blob base URL (public read)
BLOB_BASE_URL = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net/{CONTAINER_NAME}"

LOG_FILE = "upload_v2.log"


def parse_args():
    parser = argparse.ArgumentParser(description='Upload NTTT music to Azure')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be uploaded without uploading')
    parser.add_argument('--sample', type=int, default=0,
                        help='Upload only N files (0 = all matched)')
    parser.add_argument('--full', action='store_true',
                        help='Upload all matched files')
    parser.add_argument('--skip-existing', action='store_true', default=True,
                        help='Skip files that already exist in blob (default: True)')
    parser.add_argument('--source-folder', type=str, default=SOURCE_FOLDER,
                        help='Source folder for MP3 files')
    parser.add_argument('--verbose', '-v', action='store_true')
    return parser.parse_args()


def log(message, verbose_only=False, verbose=False):
    """Log message to console and file."""
    if verbose_only and not verbose:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + "\n")


def calculate_md5(file_path):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def check_az_cli():
    """Check if Azure CLI is available and logged in."""
    try:
        result = subprocess.run(
            ["az", "account", "show", "--query", "name", "-o", "tsv"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, "Not logged in"
    except FileNotFoundError:
        return False, "Azure CLI not installed"
    except Exception as e:
        return False, str(e)


def ensure_container_exists():
    """Create container if it doesn't exist, with public blob access."""
    log(f"Ensuring container '{CONTAINER_NAME}' exists with public blob access...")

    result = subprocess.run([
        "az", "storage", "container", "create",
        "--name", CONTAINER_NAME,
        "--account-name", STORAGE_ACCOUNT,
        "--public-access", "blob",
        "--auth-mode", "login"
    ], capture_output=True, text=True)

    if result.returncode == 0:
        log(f"Container ready: {CONTAINER_NAME}")
        return True
    else:
        log(f"Container creation result: {result.stderr}")
        return True  # May already exist


def blob_exists(blob_name):
    """Check if blob already exists."""
    result = subprocess.run([
        "az", "storage", "blob", "exists",
        "--name", blob_name,
        "--container-name", CONTAINER_NAME,
        "--account-name", STORAGE_ACCOUNT,
        "--auth-mode", "login",
        "--query", "exists",
        "-o", "tsv"
    ], capture_output=True, text=True, timeout=30)

    return result.stdout.strip().lower() == "true"


def upload_blob(local_path, blob_name, content_md5=None, dry_run=False):
    """
    Upload a single file to Azure Blob Storage using az CLI.

    Args:
        local_path: Path to local file
        blob_name: Name in blob storage (e.g., "abc123.mp3")
        content_md5: MD5 hash for verification
        dry_run: If True, just log what would happen

    Returns:
        bool: Success or failure
    """
    if dry_run:
        log(f"[DRY RUN] Would upload: {blob_name}")
        return True

    cmd = [
        "az", "storage", "blob", "upload",
        "--file", str(local_path),
        "--name", blob_name,
        "--container-name", CONTAINER_NAME,
        "--account-name", STORAGE_ACCOUNT,
        "--auth-mode", "login",
        "--content-type", "audio/mpeg",
        "--overwrite", "false"
    ]

    # Add MD5 hash if provided
    if content_md5:
        cmd.extend(["--content-md5", content_md5])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            return True
        else:
            log(f"Upload failed for {blob_name}: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        log(f"Upload timeout for {blob_name}")
        return False
    except Exception as e:
        log(f"Upload error for {blob_name}: {e}")
        return False


def load_songs():
    """Load songs that need to be uploaded."""
    if os.path.exists(MATCHED_FILE):
        with open(MATCHED_FILE, 'r', encoding='utf-8') as f:
            matched = json.load(f)
        return matched
    elif os.path.exists(SONGS_FILE):
        with open(SONGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        songs = data.get('songs', data)
        return [{'songID': s['SongID'], 'sourceFile': None} for s in songs]
    else:
        return []


def main():
    args = parse_args()

    print(f"\n{'='*60}")
    print(f"NTTT v2.0 - Upload to Azure Blob Storage")
    print(f"{'='*60}")
    print(f"Storage Account: {STORAGE_ACCOUNT}")
    print(f"Container: {CONTAINER_NAME}")
    print(f"Public URL: {BLOB_BASE_URL}/")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"{'='*60}\n")

    # Check Azure CLI
    az_ok, az_msg = check_az_cli()
    if not az_ok:
        log(f"ERROR: Azure CLI issue: {az_msg}")
        log("Run 'az login' first")
        return 1
    log(f"Azure CLI OK: {az_msg}")

    # Ensure container exists with public access
    if not args.dry_run:
        ensure_container_exists()

    # Load songs to upload
    songs = load_songs()
    if not songs:
        log("ERROR: No songs found. Run djSongsRawMatch_v2.py first.")
        return 1

    log(f"Found {len(songs)} songs to upload")

    # Apply sample limit
    if args.sample > 0:
        songs = songs[:args.sample]
        log(f"Processing sample of {len(songs)} songs")
    elif not args.full and not args.dry_run:
        log("Use --sample=N or --full to upload. Use --dry-run to preview.")
        return 0

    # Source folder check
    source_folder = Path(args.source_folder)
    if not source_folder.exists():
        log(f"ERROR: Source folder not found: {source_folder}")
        log("Run djSongsRawMatch_v2.py to copy files first.")
        return 1

    # Upload files
    stats = {
        'total': len(songs),
        'uploaded': 0,
        'skipped': 0,
        'failed': 0,
        'not_found': 0
    }

    log(f"\nStarting upload...")

    for i, song in enumerate(songs):
        song_id = song.get('songID') or song.get('SongID')
        blob_name = f"{song_id}.mp3"
        local_path = source_folder / blob_name

        # Progress
        if (i + 1) % 50 == 0:
            log(f"Progress: {i+1}/{len(songs)} ({100*(i+1)/len(songs):.1f}%)")

        # Check local file exists
        if not local_path.exists():
            stats['not_found'] += 1
            log(f"Not found: {blob_name}", verbose_only=True, verbose=args.verbose)
            continue

        # Check if already in blob (skip if exists)
        if args.skip_existing and not args.dry_run:
            if blob_exists(blob_name):
                stats['skipped'] += 1
                log(f"Skipped (exists): {blob_name}", verbose_only=True, verbose=args.verbose)
                continue

        # Calculate MD5
        md5_hash = calculate_md5(local_path) if not args.dry_run else "dry-run"

        # Upload
        success = upload_blob(local_path, blob_name, content_md5=md5_hash, dry_run=args.dry_run)

        if success:
            stats['uploaded'] += 1
        else:
            stats['failed'] += 1

    # Summary
    print(f"\n{'='*60}")
    print("UPLOAD SUMMARY")
    print(f"{'='*60}")
    print(f"Total songs: {stats['total']}")
    print(f"Uploaded: {stats['uploaded']}")
    print(f"Skipped (exists): {stats['skipped']}")
    print(f"Not found locally: {stats['not_found']}")
    print(f"Failed: {stats['failed']}")
    print(f"\nBlob URL pattern: {BLOB_BASE_URL}/{{songID}}.mp3")

    if args.dry_run:
        print(f"\n{'='*60}")
        print("DRY RUN COMPLETE - No files were uploaded")
        print(f"Run without --dry-run to upload")
        print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    exit(main())
