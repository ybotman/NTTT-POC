#!/usr/bin/env python3
"""
NTTT v2.0 - Step 2: Filter & Transform Library to Tango Songs

Filters Mixxx library to tango genres only, cleans metadata,
matches to ArtistMaster, and adds priority scoring.

Usage:
    python djLibrary2Json_v2.py --source=boris --dry-run
    python djLibrary2Json_v2.py --source=boris --sample=100
    python djLibrary2Json_v2.py --source=boris
"""

import json
import uuid
import re
import unicodedata
import argparse
from pathlib import Path
from datetime import datetime

# Configuration
SOURCES = {
    'boris': {
        'library_path': './djLibrary_boris.json',
        'output_path': './djTangoSongs_boris.json',
        'not_found_path': './djNotFoundArtistMasters_boris.json',
        'description': 'BORIS Library'
    },
    'toshi': {
        'library_path': './djLibrary.json',
        'output_path': './djTangoSongs.json',
        'not_found_path': './djNotFoundArtistMasters.json',
        'description': 'TOSHI Library'
    }
}

ARTIST_MASTER_PATH = './ArtistMaster.json'

# Valid tango genres (case-insensitive matching)
VALID_GENRES = ['tango', 'vals', 'waltz', 'milonga', 'marcha']

# Genres to EXCLUDE (not dance music)
EXCLUDE_GENRES = ['cortina']


def parse_args():
    parser = argparse.ArgumentParser(description='Filter library to tango songs')
    parser.add_argument('--source', choices=['boris', 'toshi'], default='boris',
                        help='Source library to process (default: boris)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show statistics without writing files')
    parser.add_argument('--sample', type=int, default=0,
                        help='Output sample of N records (0 = all)')
    parser.add_argument('--show-sample', type=int, default=5,
                        help='Show N sample records in output (default: 5)')
    return parser.parse_args()


# =============================================================================
# TEXT CLEANING FUNCTIONS
# =============================================================================

def clean_special_characters(text):
    """Remove diacritics and special characters."""
    if not text:
        return ""
    cleaned_text = ''.join(c for c in unicodedata.normalize('NFD', text)
                           if unicodedata.category(c) != 'Mn')
    return cleaned_text.strip().lstrip('.')


def clean_commas(text):
    """Reformat comma-separated names like 'Last, First'."""
    if not text:
        return ""
    patterns = [
        (r"\bDi Sarli, Carlos\b", "Carlos Di Sarli"),
        (r"\bDe Angelis, Alfredo\b", "Alfredo De Angelis")
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    if ',' in text:
        parts = text.split(',')
        if len(parts) == 2 and len(parts[1].split()) <= 2:
            return f"{parts[1].strip()} {parts[0].strip()}"
    return text


def fix_di_arienzo(text):
    """Replace DiArienzo with D'Arienzo."""
    if not text:
        return ""
    return re.sub(r"diarienzo", "D'Arienzo", text, flags=re.IGNORECASE)


def remove_square_brackets(text):
    """Remove content inside square brackets."""
    if not text:
        return ""
    return re.sub(r"\[.*?\]", "", text).strip()


# =============================================================================
# CLASSIFICATION FUNCTIONS
# =============================================================================

def determine_style(genre):
    """Determine Style based on genre."""
    if not genre:
        return "Unknown"
    genre_lower = genre.lower()
    if 'tango' in genre_lower:
        return "Tango"
    if 'vals' in genre_lower or 'waltz' in genre_lower:
        return "Vals"
    if 'milonga' in genre_lower:
        return "Milonga"
    if 'marcha' in genre_lower:
        return "Marcha"
    return "Unknown"


def determine_alternative(genre):
    """Determine if Alternative."""
    if not genre:
        return "N"
    genre_lower = genre.lower()
    if any(kw in genre_lower for kw in ['alt', 'alternative', 'neo']):
        return "Y"
    return "N"


def determine_candombe(genre):
    """Determine if Candombe."""
    if not genre:
        return "N"
    return "Y" if 'candombe' in genre.lower() else "N"


def determine_cancion(genre):
    """Determine if Cancion."""
    if not genre:
        return "N"
    return "Y" if 'canción' in genre.lower() or 'cancion' in genre.lower() else "N"


def calculate_priority_tier(record):
    """
    Calculate priority tier A/B/C/D based on rating and play count.

    Tier A: High rating AND played often (best candidates)
    Tier B: Good rating OR played often
    Tier C: Some engagement
    Tier D: Unknown quality
    """
    rating = record.get('rating') or 0
    plays = record.get('timesplayed') or 0

    if rating >= 4 and plays >= 5:
        return "A"
    elif rating >= 3 or plays >= 10:
        return "B"
    elif rating >= 1 or plays >= 1:
        return "C"
    else:
        return "D"


def calculate_priority_score(record):
    """
    Calculate numeric priority score (0-200).
    Higher = show more often in quiz.
    """
    rating = record.get('rating') or 0
    plays = record.get('timesplayed') or 0

    score = 0
    score += rating * 20  # Max 100 from rating
    score += min(plays, 20) * 5  # Max 100 from plays (capped at 20)

    return score


def generate_song_id(album_title, song_title):
    """Generate deterministic UUID v5 based on album and song title."""
    namespace = uuid.NAMESPACE_DNS
    input_string = f"{album_title}::{song_title}"
    return str(uuid.uuid5(namespace, input_string))


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def is_valid_genre(genre):
    """Check if genre is a valid tango genre (not cortina, etc.)"""
    if not genre:
        return False

    genre_lower = genre.lower()

    # Exclude non-dance genres
    for exclude in EXCLUDE_GENRES:
        if exclude in genre_lower:
            return False

    # Include valid tango genres
    for valid in VALID_GENRES:
        if valid in genre_lower:
            return True

    return False


def process_library(source_config, artist_master_path, dry_run=False, sample=0):
    """
    Process library and filter to tango songs.

    Returns:
        tuple: (results, not_found_artists, stats)
    """
    print(f"\n{'='*60}")
    print(f"NTTT v2.0 - Filter & Transform")
    print(f"{'='*60}")
    print(f"Source: {source_config['description']}")
    print(f"Input: {source_config['library_path']}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")

    # Load data
    library_path = Path(source_config['library_path'])
    if not library_path.exists():
        print(f"ERROR: Library file not found: {library_path}")
        print(f"Run extractMixxxSqlite.py first to create it.")
        return None, None, None

    with open(library_path, 'r', encoding='utf-8') as f:
        library = json.load(f)

    print(f"Loaded {len(library):,} records from library")

    # Load artist master
    artist_master_path = Path(artist_master_path)
    if not artist_master_path.exists():
        print(f"WARNING: ArtistMaster.json not found, will skip artist matching")
        artist_master_list = []
    else:
        with open(artist_master_path, 'r', encoding='utf-8') as f:
            artist_master_list = json.load(f)
        print(f"Loaded {len(artist_master_list)} artists from ArtistMaster")

    master_artists = {a["artist"].lower(): a["artist"] for a in artist_master_list}

    # Process records
    results = []
    not_found_artists = set()
    stats = {
        'total_input': len(library),
        'filtered_out': 0,
        'tango_songs': 0,
        'with_artist_master': 0,
        'by_style': {},
        'by_tier': {'A': 0, 'B': 0, 'C': 0, 'D': 0},
        'by_genre': {}
    }

    for record in library:
        genre = record.get('genre', '')

        # Filter to tango genres
        if not is_valid_genre(genre):
            stats['filtered_out'] += 1
            continue

        stats['tango_songs'] += 1
        stats['by_genre'][genre] = stats['by_genre'].get(genre, 0) + 1

        # Extract and clean fields
        dj_id = record.get('id', "")
        song_title_original = record.get('title', '') or ''
        song_title_clean = fix_di_arienzo(clean_special_characters(song_title_original))

        album_title_original = record.get('album', '') or ''
        album_title_clean = fix_di_arienzo(clean_special_characters(album_title_original))
        album_title_clean_l2 = remove_square_brackets(album_title_clean)

        artist_original = record.get('artist', '') or ''
        artist_clean = clean_commas(clean_special_characters(artist_original))

        # Match to ArtistMaster
        matched_artist = ""
        lowered_artist = artist_clean.lower()
        if lowered_artist in master_artists:
            matched_artist = master_artists[lowered_artist]
        else:
            for ma_key, ma_val in master_artists.items():
                if ma_key in lowered_artist:
                    matched_artist = ma_val
                    break

        if matched_artist:
            stats['with_artist_master'] += 1
        elif artist_original:
            not_found_artists.add(artist_original)

        # Determine classifications
        style = determine_style(genre)
        alternative = determine_alternative(genre)
        candombe = determine_candombe(genre)
        cancion = determine_cancion(genre)

        # Priority scoring (NEW in v2.0)
        priority_tier = calculate_priority_tier(record)
        priority_score = calculate_priority_score(record)

        stats['by_style'][style] = stats['by_style'].get(style, 0) + 1
        stats['by_tier'][priority_tier] += 1

        # Generate song ID
        song_id = generate_song_id(album_title_original, song_title_original)

        # Build output record
        output_record = {
            "songID": song_id,
            "djId": dj_id,
            "songTitleOriginal": song_title_original,
            "songTitleClean": song_title_clean,
            "albumTitleOriginal": album_title_original,
            "albumTitleClean": album_title_clean,
            "albumTitleCleanL2": album_title_clean_l2,
            "artistOriginal": artist_original,
            "artistClean": artist_clean,
            "artistMaster": matched_artist,
            "genre": genre,
            "style": style,
            "alternative": alternative,
            "candombe": candombe,
            "cancion": cancion,
            "year": record.get('year', ''),

            # NEW v2.0 fields from BORIS
            "rating": record.get('rating') or 0,
            "timesplayed": record.get('timesplayed') or 0,
            "priorityTier": priority_tier,
            "priorityScore": priority_score,

            # File path for matching
            "filePath": record.get('file_path', '')
        }

        results.append(output_record)

    return results, not_found_artists, stats


def print_stats(stats, not_found_artists, show_sample_records=None):
    """Print processing statistics"""
    print(f"\n{'='*60}")
    print("PROCESSING STATISTICS")
    print(f"{'='*60}")
    print(f"Total input records: {stats['total_input']:,}")
    print(f"Filtered out (non-tango): {stats['filtered_out']:,}")
    print(f"Tango songs: {stats['tango_songs']:,}")
    print(f"With ArtistMaster match: {stats['with_artist_master']:,} ({100*stats['with_artist_master']/max(1,stats['tango_songs']):.1f}%)")

    print(f"\nBy Style:")
    for style, count in sorted(stats['by_style'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {style}: {count:,}")

    print(f"\nBy Priority Tier:")
    for tier in ['A', 'B', 'C', 'D']:
        count = stats['by_tier'][tier]
        pct = 100 * count / max(1, stats['tango_songs'])
        bar = '█' * int(pct / 2)
        print(f"  Tier {tier}: {count:>6,} ({pct:>5.1f}%) {bar}")

    print(f"\nTop Genres:")
    sorted_genres = sorted(stats['by_genre'].items(), key=lambda x: x[1], reverse=True)[:10]
    for genre, count in sorted_genres:
        print(f"  {genre}: {count:,}")

    print(f"\nUnmatched Artists: {len(not_found_artists)}")
    if not_found_artists and len(not_found_artists) <= 10:
        for artist in sorted(not_found_artists)[:10]:
            print(f"  - {artist}")

    if show_sample_records:
        print(f"\n{'='*60}")
        print(f"SAMPLE RECORDS (first {len(show_sample_records)})")
        print(f"{'='*60}")
        for i, rec in enumerate(show_sample_records):
            print(f"\n[{i+1}] {rec['songTitleOriginal']}")
            print(f"    Artist: {rec['artistOriginal']} → {rec['artistMaster'] or '(no match)'}")
            print(f"    Style: {rec['style']} | Tier: {rec['priorityTier']} | Score: {rec['priorityScore']}")
            print(f"    Rating: {rec['rating']} | Plays: {rec['timesplayed']}")


def save_results(results, not_found_artists, source_config, dry_run=False, sample=0):
    """Save results to JSON files"""
    output_path = Path(source_config['output_path'])
    not_found_path = Path(source_config['not_found_path'])

    # Apply sample limit
    output_data = results[:sample] if sample > 0 else results

    if dry_run:
        print(f"\n[DRY RUN] Would write {len(output_data):,} records to: {output_path}")
        print(f"[DRY RUN] Would write {len(not_found_artists):,} unmatched artists to: {not_found_path}")
        return

    # Save tango songs
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    file_size = output_path.stat().st_size
    print(f"\n✓ Saved {len(output_data):,} records to: {output_path}")
    print(f"  File size: {file_size / 1024 / 1024:.1f} MB")

    # Save unmatched artists
    not_found_data = [{"artist": a} for a in sorted(not_found_artists) if a]
    with open(not_found_path, 'w', encoding='utf-8') as f:
        json.dump(not_found_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved {len(not_found_data)} unmatched artists to: {not_found_path}")


def main():
    args = parse_args()

    source_config = SOURCES[args.source]

    # Process
    results, not_found_artists, stats = process_library(
        source_config,
        ARTIST_MASTER_PATH,
        dry_run=args.dry_run,
        sample=args.sample
    )

    if results is None:
        return 1

    # Get sample records for display
    sample_records = results[:args.show_sample] if args.show_sample > 0 else None

    # Print stats
    print_stats(stats, not_found_artists, sample_records)

    # Save
    save_results(results, not_found_artists, source_config, args.dry_run, args.sample)

    if args.dry_run:
        print(f"\n{'='*60}")
        print("DRY RUN COMPLETE - No files were written")
        print(f"Run without --dry-run to save output")
        print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    exit(main())
