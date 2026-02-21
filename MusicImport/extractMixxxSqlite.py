#!/usr/bin/env python3
"""
NTTT v2.0 - Step 1: Extract Mixxx Library from SQLite

Extracts BORIS (or TOSHI) Mixxx library from SQLite database to JSON format.
Includes rating and timesplayed fields for quiz prioritization.

Usage:
    python extractMixxxSqlite.py --source=boris --dry-run
    python extractMixxxSqlite.py --source=boris
"""

import sqlite3
import json
import argparse
import os
from pathlib import Path
from datetime import datetime

# Configuration
SOURCES = {
    'boris': {
        'sqlite_path': '/Volumes/EXTVideo1/djImports/boris/Mixxx Database/mixxxdb.sqlite',
        'output_file': './djLibrary_boris.json',
        'description': 'BORIS Mixxx Library'
    },
    'toshi': {
        'sqlite_path': '/Volumes/EXTVideo1/djImports/toshi/Mixxx/mixxxdb.sqlite',  # May not exist
        'output_file': './djLibrary_toshi_new.json',
        'description': 'TOSHI Mixxx Library'
    }
}

def parse_args():
    parser = argparse.ArgumentParser(description='Extract Mixxx SQLite library to JSON')
    parser.add_argument('--source', choices=['boris', 'toshi'], default='boris',
                        help='Source library to extract (default: boris)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be extracted without writing files')
    parser.add_argument('--limit', type=int, default=0,
                        help='Limit number of records (0 = all)')
    parser.add_argument('--output', type=str, default=None,
                        help='Override output file path')
    return parser.parse_args()


def check_sqlite_exists(path):
    """Verify SQLite file exists and is accessible"""
    if not os.path.exists(path):
        return False, f"SQLite file not found: {path}"
    try:
        conn = sqlite3.connect(path)
        conn.execute("SELECT 1")
        conn.close()
        return True, "OK"
    except Exception as e:
        return False, f"Cannot open SQLite: {e}"


def get_schema_info(cursor):
    """Get table schema for library table"""
    cursor.execute("PRAGMA table_info(library)")
    columns = cursor.fetchall()
    return [(col[1], col[2]) for col in columns]  # (name, type)


def extract_library(source_config, limit=0, dry_run=False):
    """
    Extract library from SQLite database.

    Returns:
        list: List of track dictionaries
        dict: Statistics about extraction
    """
    sqlite_path = source_config['sqlite_path']

    print(f"\n{'='*60}")
    print(f"NTTT v2.0 - SQLite Extraction")
    print(f"{'='*60}")
    print(f"Source: {source_config['description']}")
    print(f"SQLite: {sqlite_path}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")

    # Connect to SQLite
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Show schema info
    schema = get_schema_info(cursor)
    print(f"Library table has {len(schema)} columns")

    # Check for key fields
    column_names = [col[0] for col in schema]
    key_fields = ['rating', 'timesplayed', 'last_played_at']
    for field in key_fields:
        status = "✓" if field in column_names else "✗"
        print(f"  {status} {field}")

    # Build query - join with track_locations for file paths
    query = """
        SELECT
            l.id,
            l.title,
            l.artist,
            l.album,
            l.genre,
            l.year,
            l.duration,
            l.bpm,
            l.comment,
            l.bitrate,
            l.samplerate,
            l.channels,
            l.key,
            l.rating,
            l.timesplayed,
            l.last_played_at,
            l.datetime_added,
            l.album_artist,
            l.composer,
            t.location as file_path,
            t.directory as file_directory
        FROM library l
        LEFT JOIN track_locations t ON l.location = t.id
        WHERE (l.mixxx_deleted = 0 OR l.mixxx_deleted IS NULL)
    """

    if limit > 0:
        query += f" LIMIT {limit}"

    print(f"\nExecuting query...")
    cursor.execute(query)
    rows = cursor.fetchall()

    print(f"Retrieved {len(rows)} tracks")

    # Convert to list of dicts
    results = []
    stats = {
        'total': len(rows),
        'with_rating': 0,
        'with_plays': 0,
        'by_genre': {},
        'rating_distribution': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    }

    for row in rows:
        record = dict(row)
        results.append(record)

        # Collect stats
        rating = record.get('rating') or 0
        plays = record.get('timesplayed') or 0
        genre = record.get('genre') or 'Unknown'

        if rating > 0:
            stats['with_rating'] += 1
        if plays > 0:
            stats['with_plays'] += 1

        stats['rating_distribution'][min(rating, 5)] += 1
        stats['by_genre'][genre] = stats['by_genre'].get(genre, 0) + 1

    conn.close()

    return results, stats


def print_stats(stats):
    """Print extraction statistics"""
    print(f"\n{'='*60}")
    print("EXTRACTION STATISTICS")
    print(f"{'='*60}")
    print(f"Total tracks: {stats['total']:,}")
    print(f"With rating > 0: {stats['with_rating']:,} ({100*stats['with_rating']/stats['total']:.1f}%)")
    print(f"With plays > 0: {stats['with_plays']:,} ({100*stats['with_plays']/stats['total']:.1f}%)")

    print(f"\nRating distribution:")
    for rating, count in sorted(stats['rating_distribution'].items(), reverse=True):
        bar = '█' * (count // 500) if count > 0 else ''
        print(f"  {rating} stars: {count:>6,} {bar}")

    print(f"\nTop genres:")
    sorted_genres = sorted(stats['by_genre'].items(), key=lambda x: x[1], reverse=True)[:15]
    for genre, count in sorted_genres:
        print(f"  {genre}: {count:,}")


def save_json(data, output_path, dry_run=False):
    """Save data to JSON file"""
    if dry_run:
        print(f"\n[DRY RUN] Would write {len(data):,} records to: {output_path}")
        print(f"[DRY RUN] Estimated file size: ~{len(json.dumps(data[:100])) * len(data) // 100 // 1024:,} KB")
        return

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    file_size = output_path.stat().st_size
    print(f"\n✓ Saved {len(data):,} records to: {output_path}")
    print(f"  File size: {file_size / 1024 / 1024:.1f} MB")


def main():
    args = parse_args()

    source_config = SOURCES[args.source]
    output_path = args.output or source_config['output_file']

    # Check SQLite exists
    exists, message = check_sqlite_exists(source_config['sqlite_path'])
    if not exists:
        print(f"ERROR: {message}")
        print("\nIs the external drive mounted?")
        print(f"Expected path: {source_config['sqlite_path']}")
        return 1

    # Extract
    results, stats = extract_library(
        source_config,
        limit=args.limit,
        dry_run=args.dry_run
    )

    # Print stats
    print_stats(stats)

    # Save
    save_json(results, output_path, dry_run=args.dry_run)

    if args.dry_run:
        print(f"\n{'='*60}")
        print("DRY RUN COMPLETE - No files were written")
        print(f"Run without --dry-run to extract data")
        print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    exit(main())
