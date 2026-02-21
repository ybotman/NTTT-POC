#!/usr/bin/env python3
"""
NTTT v2.0 - Step 3: Match MP3 Files & Build Song Metadata

Matches tango songs to MP3 files on disk, copies/renames them,
updates ID3 tags, and generates final djSongs.json.

Usage:
    python djSongsRawMatch_v2.py --source=boris --dry-run
    python djSongsRawMatch_v2.py --source=boris --sample=50 --dry-run
    python djSongsRawMatch_v2.py --source=boris --sample=100  # Copy 100 files
    python djSongsRawMatch_v2.py --source=boris               # Full run
"""

import json
import os
import argparse
import logging
from pathlib import Path
import unicodedata
import shutil
from datetime import datetime

# Try to import mutagen for ID3 tagging (optional in dry-run)
try:
    from mutagen.id3 import ID3, TIT2, TALB, TPE1, TCON, COMM, error as ID3Error
    from mutagen.mp3 import MP3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

# =============================================================================
# CONFIGURATION
# =============================================================================

SOURCES = {
    'boris': {
        'source_folder': '/Volumes/EXTVideo1/djImports/boris/Music',
        'target_folder': '/Volumes/EXTVideo1/djImports/NTTTUpload_v20',
        'track_locations_file': './djTrack_locations_boris.json',
        'tango_songs_file': './djTangoSongs_boris.json',
        'output_file': './djSongs_boris.json',
        'matched_file': './djMatchedSongs_boris.json',
        'unmatched_file': './djUnMatchedSongs_boris.json',
        'description': 'BORIS Music Library',
        'azure_container': 'djsongs'
    },
    'toshi': {
        'source_folder': '/Volumes/External SSD 1T/Mixxx',
        'target_folder': '/Volumes/External SSD 1T/NTTTUpload',
        'track_locations_file': './djTrack_locations.json',
        'tango_songs_file': './djTangoSongs.json',
        'output_file': './djSongs.json',
        'matched_file': './djMatchedSongs.json',
        'unmatched_file': './djUnMatchedSongs.json',
        'description': 'TOSHI Music Library',
        'azure_container': 'djsongs'
    }
}

AZURE_BLOB_BASE = "https://namethattangotune.blob.core.windows.net"

LOG_FILE = "djMatch_v2.log"


def parse_args():
    parser = argparse.ArgumentParser(description='Match MP3 files to tango songs')
    parser.add_argument('--source', choices=['boris', 'toshi'], default='boris',
                        help='Source library to process (default: boris)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would happen without copying files')
    parser.add_argument('--sample', type=int, default=0,
                        help='Process only N songs (0 = all)')
    parser.add_argument('--skip-copy', action='store_true',
                        help='Skip file copy, just generate metadata')
    parser.add_argument('--local-url', action='store_true',
                        help='Use local file:// URLs instead of Azure blob URLs')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    return parser.parse_args()


def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def normalize_filename(name):
    """Normalize filename by removing diacritics."""
    if not name:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', name)
                   if unicodedata.category(c) != 'Mn')


def load_json(file_path):
    """Load JSON from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data, file_path, dry_run=False):
    """Save JSON to file."""
    if dry_run:
        logging.info(f"[DRY RUN] Would save {len(data) if isinstance(data, list) else 'dict'} to {file_path}")
        return
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logging.info(f"Saved to {file_path}")


def find_mp3_files(folder):
    """Recursively find all MP3 files."""
    folder = Path(folder)
    if not folder.exists():
        logging.error(f"Source folder not found: {folder}")
        return []
    return list(folder.rglob("*.mp3"))


def get_subpath_after_marker(path_str, markers=['mixxx/', 'music/']):
    """Extract subpath after known folder markers."""
    norm_path = path_str.replace('\\', '/').lower()
    for marker in markers:
        idx = norm_path.find(marker)
        if idx != -1:
            return path_str[idx + len(marker):].strip("/")
    return path_str


# =============================================================================
# ID3 TAGGING
# =============================================================================

def update_mp3_metadata(mp3_file, song_metadata, dry_run=False):
    """Update MP3 ID3 tags."""
    if dry_run:
        logging.debug(f"[DRY RUN] Would update metadata for {mp3_file}")
        return True

    if not MUTAGEN_AVAILABLE:
        logging.warning("Mutagen not installed, skipping ID3 updates")
        return False

    try:
        audio = MP3(mp3_file, ID3=ID3)
        try:
            audio.add_tags()
        except ID3Error:
            pass

        audio.tags["TIT2"] = TIT2(encoding=3, text=song_metadata.get('Title', ''))
        audio.tags["TALB"] = TALB(encoding=3, text=song_metadata.get('Album', ''))
        audio.tags["TPE1"] = TPE1(encoding=3, text=song_metadata.get('ArtistMaster', ''))
        audio.tags["TCON"] = TCON(encoding=3, text=song_metadata.get('Style', ''))
        audio.tags["COMM"] = COMM(encoding=3, lang="eng", desc="SongID",
                                   text=f"SongID: {song_metadata.get('SongID', '')}")
        audio.save()
        return True
    except Exception as e:
        logging.error(f"Failed to update metadata for {mp3_file}: {e}")
        return False


# =============================================================================
# FILE MATCHING
# =============================================================================

def build_file_index(mp3_files):
    """Build index of MP3 files by normalized path."""
    index = {}
    for mp3 in mp3_files:
        subpath = get_subpath_after_marker(str(mp3.resolve()))
        normalized = normalize_filename(subpath).lower()
        index[normalized] = mp3
    return index


def match_song_to_file(song, file_index):
    """
    Try to match a song record to an MP3 file.

    Returns:
        Path or None
    """
    file_path = song.get('filePath', '')
    if not file_path:
        return None

    # Try direct match
    subpath = get_subpath_after_marker(file_path)
    normalized = normalize_filename(subpath).lower()

    if normalized in file_index:
        return file_index[normalized]

    # Try filename-only match
    filename = Path(file_path).name
    normalized_name = normalize_filename(filename).lower()

    for key, mp3 in file_index.items():
        if key.endswith(normalized_name):
            return mp3

    return None


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_songs(source_config, args):
    """
    Main processing function.

    Returns:
        tuple: (all_songs_metadata, matched, unmatched, stats)
    """
    print(f"\n{'='*60}")
    print(f"NTTT v2.0 - Match MP3 Files")
    print(f"{'='*60}")
    print(f"Source: {source_config['description']}")
    print(f"Source folder: {source_config['source_folder']}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    if args.sample > 0:
        print(f"Sample: {args.sample} songs")
    print(f"{'='*60}\n")

    # Load tango songs
    tango_songs_file = Path(source_config['tango_songs_file'])
    if not tango_songs_file.exists():
        logging.error(f"Tango songs file not found: {tango_songs_file}")
        logging.error("Run djLibrary2Json_v2.py first")
        return None, None, None, None

    tango_songs = load_json(tango_songs_file)
    logging.info(f"Loaded {len(tango_songs):,} tango songs")

    # Apply sample limit
    if args.sample > 0:
        tango_songs = tango_songs[:args.sample]
        logging.info(f"Processing sample of {len(tango_songs)} songs")

    # Find MP3 files
    source_folder = Path(source_config['source_folder'])
    if not source_folder.exists():
        logging.error(f"Source folder not found: {source_folder}")
        logging.error("Is the external drive mounted?")
        return None, None, None, None

    logging.info(f"Scanning for MP3 files in {source_folder}...")
    mp3_files = find_mp3_files(source_folder)
    logging.info(f"Found {len(mp3_files):,} MP3 files")

    # Build file index
    logging.info("Building file index...")
    file_index = build_file_index(mp3_files)

    # Ensure target folder exists
    target_folder = Path(source_config['target_folder'])
    if not args.dry_run and not args.skip_copy:
        target_folder.mkdir(parents=True, exist_ok=True)
        logging.info(f"Target folder: {target_folder}")

    # Process songs
    all_songs_metadata = []
    matched = []
    unmatched = []
    stats = {
        'total': len(tango_songs),
        'matched': 0,
        'unmatched': 0,
        'copied': 0,
        'by_tier': {'A': 0, 'B': 0, 'C': 0, 'D': 0}
    }

    for i, song in enumerate(tango_songs):
        if (i + 1) % 500 == 0:
            logging.info(f"Progress: {i+1}/{len(tango_songs)}")

        song_id = song['songID']
        mp3_file = match_song_to_file(song, file_index)

        if not mp3_file:
            unmatched.append({
                'songID': song_id,
                'title': song.get('songTitleOriginal', ''),
                'artist': song.get('artistOriginal', ''),
                'filePath': song.get('filePath', ''),
                'reason': 'no_match'
            })
            stats['unmatched'] += 1
            continue

        stats['matched'] += 1
        tier = song.get('priorityTier', 'D')
        stats['by_tier'][tier] = stats['by_tier'].get(tier, 0) + 1

        matched.append({
            'songID': song_id,
            'sourceFile': str(mp3_file),
            'tier': tier
        })

        # Build audio URL
        if args.local_url:
            target_path = target_folder / f"{song_id}.mp3"
            audio_url = f"file://{target_path}"
        else:
            container = source_config['azure_container']
            audio_url = f"{AZURE_BLOB_BASE}/{container}/{song_id}.mp3"

        # Build song metadata for final output
        song_metadata = {
            "SongID": song_id,
            "Title": song.get('songTitleClean', song.get('songTitleOriginal', '')),
            "Orchestra": song.get('artistClean', song.get('artistOriginal', '')),
            "Album": song.get('albumTitleCleanL2', song.get('albumTitleOriginal', '')),
            "ArtistMaster": song.get('artistMaster', ''),
            "AudioUrl": audio_url,
            "Year": song.get('year', ''),
            "Style": song.get('style', 'Tango'),
            "Alternative": song.get('alternative', 'N'),
            "Candombe": song.get('candombe', 'N'),
            "Cancion": song.get('cancion', 'N'),
            "Singer": "",

            # v2.0 fields
            "rating": song.get('rating', 0),
            "timesplayed": song.get('timesplayed', 0),
            "priorityTier": tier,
            "priorityScore": song.get('priorityScore', 0)
        }

        # Copy file (unless dry-run or skip-copy)
        if not args.dry_run and not args.skip_copy:
            target_path = target_folder / f"{song_id}.mp3"
            try:
                shutil.copy2(mp3_file, target_path)
                update_mp3_metadata(target_path, song_metadata)
                stats['copied'] += 1
            except Exception as e:
                logging.error(f"Failed to copy {mp3_file}: {e}")
                unmatched.append({
                    'songID': song_id,
                    'sourceFile': str(mp3_file),
                    'reason': f'copy_error: {e}'
                })
                continue

        all_songs_metadata.append(song_metadata)

    return all_songs_metadata, matched, unmatched, stats


def print_stats(stats, matched, unmatched):
    """Print processing statistics."""
    print(f"\n{'='*60}")
    print("PROCESSING STATISTICS")
    print(f"{'='*60}")
    print(f"Total songs processed: {stats['total']:,}")
    print(f"Matched to MP3: {stats['matched']:,} ({100*stats['matched']/max(1,stats['total']):.1f}%)")
    print(f"Unmatched: {stats['unmatched']:,}")
    print(f"Files copied: {stats['copied']:,}")

    print(f"\nMatched by Priority Tier:")
    for tier in ['A', 'B', 'C', 'D']:
        count = stats['by_tier'].get(tier, 0)
        pct = 100 * count / max(1, stats['matched'])
        bar = '█' * int(pct / 2)
        print(f"  Tier {tier}: {count:>6,} ({pct:>5.1f}%) {bar}")

    if unmatched and len(unmatched) <= 10:
        print(f"\nSample unmatched:")
        for u in unmatched[:10]:
            print(f"  - {u.get('title', 'Unknown')} by {u.get('artist', 'Unknown')}")


def main():
    args = parse_args()
    setup_logging(args.verbose)

    source_config = SOURCES[args.source]

    # Process
    all_songs, matched, unmatched, stats = process_songs(source_config, args)

    if all_songs is None:
        return 1

    # Print stats
    print_stats(stats, matched, unmatched)

    # Save outputs
    print(f"\n{'='*60}")
    print("SAVING OUTPUTS")
    print(f"{'='*60}")

    # Main songs file
    save_json({"songs": all_songs}, source_config['output_file'], args.dry_run)

    # Matched list
    save_json(matched, source_config['matched_file'], args.dry_run)

    # Unmatched list
    save_json(unmatched, source_config['unmatched_file'], args.dry_run)

    if args.dry_run:
        print(f"\n{'='*60}")
        print("DRY RUN COMPLETE - No files were copied")
        print(f"Run without --dry-run to copy files")
        print(f"{'='*60}")
    else:
        print(f"\n✓ Processing complete!")
        if not args.skip_copy:
            print(f"  Files copied to: {source_config['target_folder']}")
        print(f"  Metadata saved to: {source_config['output_file']}")

    return 0


if __name__ == "__main__":
    exit(main())
