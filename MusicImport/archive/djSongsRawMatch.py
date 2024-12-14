import json
import os
import logging
from pathlib import Path
import unicodedata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("djMatch.log", mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def normalize_filename(name):
    """Normalize a filename by removing diacritics and converting to NFC form."""
    return ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')

def load_json(file_path):
    """Load JSON from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path):
    """Save JSON to a file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logging.info(f"Saved results to {file_path}")

def find_mp3_files(folder):
    """Find all MP3 files in a folder."""
    return [file for file in Path(folder).glob("*.mp3")]

def match_mp3_to_track_locations(mp3_files, track_locations):
    """Match MP3 files to track locations with normalization."""
    matched_tracks = []
    total_matches = 0
    multiple_matches = 0

    for mp3 in mp3_files:
        mp3_name = mp3.name
        normalized_mp3_name = normalize_filename(mp3_name)
        mp3_size = mp3.stat().st_size

        # Find matches by normalized filename
        matches = [
            track for track in track_locations
            if normalize_filename(track['filename']) == normalized_mp3_name
        ]

        if not matches:
            logging.info(f"File not found in track_locations: {mp3_name}")
            continue

        total_matches += len(matches)
        if len(matches) > 1:
            multiple_matches += 1

        # Handle multiple matches by filesize
        closest_match = None
        min_size_diff = float('inf')
        for match in matches:
            try:
                track_size = int(match['filesize'])
                size_diff = abs(track_size - mp3_size)
                if size_diff < min_size_diff:
                    closest_match = match
                    min_size_diff = size_diff
            except ValueError:
                continue  # Skip invalid sizes

        if closest_match:
            matched_track = {
                "djId": closest_match['id'],
                "filename": closest_match['filename'],
                "filepath": str(mp3.resolve()),
                "filesize": mp3_size,
                "closestMatch": closest_match
            }
            matched_tracks.append(matched_track)
            logging.info(f"Matched file: {mp3_name} (ID: {closest_match['id']}, Size Diff: {min_size_diff})")
        else:
            logging.info(f"Multiple matches found for {mp3_name}, but no size match.")

    logging.info(f"Summary: Found {len(matched_tracks)} exact matches.")
    logging.info(f"Total matches (including duplicates): {total_matches}")
    logging.info(f"Files with multiple matches: {multiple_matches}")

    return matched_tracks

# Paths
mp3_folder = Path("./djSongsRaw").resolve()
track_locations_file = Path("./djTrack_locations.json").resolve()
output_file = Path("./djMatchedSongs.json").resolve()

# Load data
mp3_files = find_mp3_files(mp3_folder)
track_locations = load_json(track_locations_file)

# Match MP3 files to track locations
matched_tracks = match_mp3_to_track_locations(mp3_files, track_locations)

# Save results
save_json(matched_tracks, output_file)