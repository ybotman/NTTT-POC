#!/usr/bin/env python3
"""
NTTT v2.0 - Spot Check & Validation Tool

Validates data quality and identifies import issues that need fixing.
Run this after extraction to find problems before loading.

Usage:
    python spotcheck_v2.py --source=boris
    python spotcheck_v2.py --source=boris --check=all
    python spotcheck_v2.py --source=boris --check=artists
    python spotcheck_v2.py --source=boris --check=files --sample=100
    python spotcheck_v2.py --source=boris --fix-report
"""

import json
import argparse
import os
from pathlib import Path
from collections import Counter, defaultdict
import re

# =============================================================================
# CONFIGURATION
# =============================================================================

SOURCES = {
    'boris': {
        'library_file': './djLibrary_boris.json',
        'tango_file': './djTangoSongs_boris.json',
        'songs_file': './djSongs_boris.json',
        'source_folder': '/Volumes/EXTVideo1/djImports/boris/Music',
        'description': 'BORIS'
    },
    'toshi': {
        'library_file': './djLibrary.json',
        'tango_file': './djTangoSongs.json',
        'songs_file': './djSongs.json',
        'source_folder': '/Volumes/External SSD 1T/Mixxx',
        'description': 'TOSHI'
    }
}

ARTIST_MASTER_FILE = './ArtistMaster.json'


def parse_args():
    parser = argparse.ArgumentParser(description='Spot check data quality')
    parser.add_argument('--source', choices=['boris', 'toshi'], default='boris')
    parser.add_argument('--check', choices=['all', 'artists', 'genres', 'files', 'duplicates', 'quality'],
                        default='all', help='What to check')
    parser.add_argument('--sample', type=int, default=0, help='Sample size (0=all)')
    parser.add_argument('--fix-report', action='store_true', help='Generate fix report')
    parser.add_argument('--verbose', '-v', action='store_true')
    return parser.parse_args()


def load_json_safe(path):
    """Load JSON or return empty list/dict."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {path}: {e}")
        return []


# =============================================================================
# CHECKS
# =============================================================================

def check_artists(data, artist_master):
    """Check artist matching issues."""
    print(f"\n{'='*60}")
    print("ARTIST CHECK")
    print(f"{'='*60}")

    master_set = {a['artist'].lower() for a in artist_master}

    issues = {
        'no_artist': [],
        'no_match': [],
        'suspicious': []
    }

    artist_counts = Counter()
    unmatched_counts = Counter()

    for record in data:
        artist = record.get('artistOriginal') or record.get('artist') or ''
        artist_master_match = record.get('artistMaster', '')

        if not artist.strip():
            issues['no_artist'].append(record)
            continue

        artist_counts[artist] += 1

        if not artist_master_match:
            unmatched_counts[artist] += 1
            issues['no_match'].append(record)

        # Check for suspicious patterns
        if re.search(r'^\d+', artist):  # Starts with number
            issues['suspicious'].append({'record': record, 'reason': 'starts_with_number'})
        if len(artist) < 3:
            issues['suspicious'].append({'record': record, 'reason': 'too_short'})

    # Stats
    print(f"Total records: {len(data):,}")
    print(f"Unique artists: {len(artist_counts):,}")
    print(f"No artist: {len(issues['no_artist']):,}")
    print(f"No ArtistMaster match: {len(issues['no_match']):,}")
    print(f"Suspicious: {len(issues['suspicious']):,}")

    # Top unmatched
    print(f"\nTop 20 Unmatched Artists (by frequency):")
    for artist, count in unmatched_counts.most_common(20):
        print(f"  {count:>5}x  {artist}")

    return issues


def check_genres(data):
    """Check genre distribution and issues."""
    print(f"\n{'='*60}")
    print("GENRE CHECK")
    print(f"{'='*60}")

    genre_counts = Counter()
    issues = {
        'no_genre': [],
        'non_tango': [],
        'cortina': []
    }

    tango_genres = ['tango', 'vals', 'waltz', 'milonga', 'marcha']

    for record in data:
        genre = record.get('genre', '') or ''
        genre_counts[genre] += 1

        if not genre.strip():
            issues['no_genre'].append(record)
        elif 'cortina' in genre.lower():
            issues['cortina'].append(record)
        elif not any(t in genre.lower() for t in tango_genres):
            issues['non_tango'].append(record)

    print(f"Total records: {len(data):,}")
    print(f"No genre: {len(issues['no_genre']):,}")
    print(f"Cortinas (excluded): {len(issues['cortina']):,}")
    print(f"Non-tango: {len(issues['non_tango']):,}")

    print(f"\nAll Genres:")
    for genre, count in genre_counts.most_common():
        marker = ""
        if 'cortina' in genre.lower():
            marker = " [EXCLUDED]"
        elif not any(t in genre.lower() for t in tango_genres) and genre:
            marker = " [NON-TANGO]"
        print(f"  {count:>6}x  {genre or '(empty)'}{marker}")

    return issues


def check_duplicates(data):
    """Find duplicate songs."""
    print(f"\n{'='*60}")
    print("DUPLICATE CHECK")
    print(f"{'='*60}")

    # By songID
    song_id_counts = Counter()
    for record in data:
        song_id = record.get('songID', '')
        if song_id:
            song_id_counts[song_id] += 1

    duplicates = {k: v for k, v in song_id_counts.items() if v > 1}

    # By title+artist
    title_artist_counts = Counter()
    for record in data:
        title = (record.get('songTitleOriginal') or record.get('title') or '').lower().strip()
        artist = (record.get('artistOriginal') or record.get('artist') or '').lower().strip()
        key = f"{title}|{artist}"
        title_artist_counts[key] += 1

    title_artist_dups = {k: v for k, v in title_artist_counts.items() if v > 1}

    print(f"Duplicate songIDs: {len(duplicates)}")
    print(f"Duplicate title+artist combos: {len(title_artist_dups)}")

    if duplicates:
        print(f"\nDuplicate songIDs (top 10):")
        for song_id, count in sorted(duplicates.items(), key=lambda x: -x[1])[:10]:
            print(f"  {count}x  {song_id[:40]}...")

    if title_artist_dups:
        print(f"\nDuplicate title+artist (top 10):")
        for key, count in sorted(title_artist_dups.items(), key=lambda x: -x[1])[:10]:
            title, artist = key.split('|')
            print(f"  {count}x  {title[:30]} by {artist[:20]}")

    return {'songID': duplicates, 'title_artist': title_artist_dups}


def check_files(data, source_folder, sample=0):
    """Check if MP3 files exist."""
    print(f"\n{'='*60}")
    print("FILE CHECK")
    print(f"{'='*60}")

    if not os.path.exists(source_folder):
        print(f"ERROR: Source folder not found: {source_folder}")
        return {'missing': [], 'found': 0}

    print(f"Source folder: {source_folder}")

    # Build file index
    print("Scanning for MP3 files...")
    mp3_files = set()
    for root, dirs, files in os.walk(source_folder):
        for f in files:
            if f.lower().endswith('.mp3'):
                mp3_files.add(os.path.join(root, f).lower())

    print(f"Found {len(mp3_files):,} MP3 files on disk")

    # Check records
    check_data = data[:sample] if sample > 0 else data
    print(f"Checking {len(check_data):,} records...")

    found = 0
    missing = []

    for record in check_data:
        file_path = record.get('filePath') or record.get('file_path') or ''
        if not file_path:
            missing.append({'record': record, 'reason': 'no_path'})
            continue

        # Try to find file
        normalized = file_path.lower().replace('\\', '/')
        if any(normalized in mp3 or mp3.endswith(os.path.basename(normalized)) for mp3 in mp3_files):
            found += 1
        else:
            missing.append({'record': record, 'reason': 'not_found', 'path': file_path})

    print(f"\nFiles found: {found:,} ({100*found/max(1,len(check_data)):.1f}%)")
    print(f"Missing: {len(missing):,}")

    if missing and len(missing) <= 10:
        print(f"\nSample missing files:")
        for m in missing[:10]:
            title = m['record'].get('title') or m['record'].get('songTitleOriginal') or 'Unknown'
            print(f"  - {title}: {m.get('reason')}")

    return {'missing': missing, 'found': found}


def check_quality(data):
    """Check data quality metrics."""
    print(f"\n{'='*60}")
    print("QUALITY CHECK")
    print(f"{'='*60}")

    stats = {
        'total': len(data),
        'with_rating': 0,
        'with_plays': 0,
        'with_year': 0,
        'with_artist_master': 0,
        'tier_a': 0,
        'tier_b': 0,
        'tier_c': 0,
        'tier_d': 0
    }

    issues = []

    for record in data:
        rating = record.get('rating') or 0
        plays = record.get('timesplayed') or 0
        year = record.get('year', '')
        artist_master = record.get('artistMaster', '')
        tier = record.get('priorityTier', 'D')

        if rating > 0:
            stats['with_rating'] += 1
        if plays > 0:
            stats['with_plays'] += 1
        if year and str(year).strip():
            stats['with_year'] += 1
        if artist_master:
            stats['with_artist_master'] += 1

        stats[f'tier_{tier.lower()}'] = stats.get(f'tier_{tier.lower()}', 0) + 1

        # Quality issues
        title = record.get('songTitleOriginal') or record.get('title') or ''
        if len(title) < 2:
            issues.append({'record': record, 'issue': 'title_too_short'})
        if re.search(r'track\s*\d+', title.lower()):
            issues.append({'record': record, 'issue': 'generic_track_name'})

    print(f"Total records: {stats['total']:,}")
    print(f"\nCompleteness:")
    print(f"  With rating: {stats['with_rating']:,} ({100*stats['with_rating']/max(1,stats['total']):.1f}%)")
    print(f"  With plays: {stats['with_plays']:,} ({100*stats['with_plays']/max(1,stats['total']):.1f}%)")
    print(f"  With year: {stats['with_year']:,} ({100*stats['with_year']/max(1,stats['total']):.1f}%)")
    print(f"  With ArtistMaster: {stats['with_artist_master']:,} ({100*stats['with_artist_master']/max(1,stats['total']):.1f}%)")

    print(f"\nPriority Tiers:")
    for tier in ['a', 'b', 'c', 'd']:
        count = stats.get(f'tier_{tier}', 0)
        pct = 100 * count / max(1, stats['total'])
        bar = '█' * int(pct / 2)
        print(f"  Tier {tier.upper()}: {count:>6,} ({pct:>5.1f}%) {bar}")

    print(f"\nQuality issues: {len(issues)}")

    return {'stats': stats, 'issues': issues}


def generate_fix_report(source_config):
    """Generate report of issues that need manual fixing."""
    print(f"\n{'='*60}")
    print("FIX REPORT")
    print(f"{'='*60}")

    # Load data
    tango_data = load_json_safe(source_config['tango_file'])
    artist_master = load_json_safe(ARTIST_MASTER_FILE)

    if not tango_data:
        print("No tango data found. Run djLibrary2Json_v2.py first.")
        return

    # Collect all issues
    fixes_needed = {
        'add_to_artist_master': [],
        'review_genre': [],
        'missing_data': [],
        'potential_duplicates': []
    }

    # Unmatched artists (add to ArtistMaster.json)
    unmatched = Counter()
    for record in tango_data:
        if not record.get('artistMaster') and record.get('artistOriginal'):
            unmatched[record['artistOriginal']] += 1

    for artist, count in unmatched.most_common(50):
        if count >= 5:  # Only suggest if appears 5+ times
            fixes_needed['add_to_artist_master'].append({
                'artist': artist,
                'count': count,
                'action': 'Add to ArtistMaster.json'
            })

    # Write report
    report_file = f'./fix_report_{source_config["description"].lower()}.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(fixes_needed, f, ensure_ascii=False, indent=2)

    print(f"\nFixes needed:")
    print(f"  Add to ArtistMaster: {len(fixes_needed['add_to_artist_master'])} artists")
    print(f"\nReport saved to: {report_file}")

    # Show top fixes
    if fixes_needed['add_to_artist_master']:
        print(f"\nTop artists to add to ArtistMaster.json:")
        for fix in fixes_needed['add_to_artist_master'][:15]:
            print(f"  {fix['count']:>5}x  {fix['artist']}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    args = parse_args()
    source_config = SOURCES[args.source]

    print(f"\n{'='*60}")
    print(f"NTTT v2.0 - Spot Check Tool")
    print(f"{'='*60}")
    print(f"Source: {source_config['description']}")
    print(f"Check: {args.check}")

    # Load data
    if os.path.exists(source_config['tango_file']):
        data = load_json_safe(source_config['tango_file'])
        data_source = 'tango_file'
    elif os.path.exists(source_config['library_file']):
        data = load_json_safe(source_config['library_file'])
        data_source = 'library_file'
    else:
        print(f"No data files found. Run extraction first.")
        return 1

    print(f"Loaded {len(data):,} records from {data_source}")

    artist_master = load_json_safe(ARTIST_MASTER_FILE)
    print(f"Loaded {len(artist_master)} artists from ArtistMaster")

    # Run checks
    if args.fix_report:
        generate_fix_report(source_config)
    elif args.check == 'all':
        check_artists(data, artist_master)
        check_genres(data)
        check_duplicates(data)
        check_quality(data)
    elif args.check == 'artists':
        check_artists(data, artist_master)
    elif args.check == 'genres':
        check_genres(data)
    elif args.check == 'files':
        check_files(data, source_config['source_folder'], args.sample)
    elif args.check == 'duplicates':
        check_duplicates(data)
    elif args.check == 'quality':
        check_quality(data)

    print(f"\n{'='*60}")
    print("SPOT CHECK COMPLETE")
    print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    exit(main())
