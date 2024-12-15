import json
import os
import logging
from pathlib import Path
import unicodedata
import shutil

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
    """Recursively find all MP3 files in a folder and its subdirectories."""
    return [file for file in Path(folder).rglob("*.mp3")]

def match_mp3_to_track_locations(mp3_files, track_locations, djId_to_songID, unmatched_songs):
    """Match MP3 files to track locations using djId_to_songID mapping."""
    matched_tracks = []
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
            unmatched_songs.append({"filename": mp3_name})
            continue

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
            dj_id_str = str(closest_match['id'])
            if dj_id_str in djId_to_songID:
                song_id = djId_to_songID[dj_id_str]
                matched_tracks.append({
                    "songID": song_id,
                    "filename": closest_match['filename'],
                    "filepath": str(mp3.resolve()),
                    "filesize": mp3_size
                })
                logging.info(f"Matched file: {mp3_name} (djId: {closest_match['id']}, songID: {song_id}, Size Diff: {min_size_diff})")
            else:
                logging.warning(f"No songID found for djId: {closest_match['id']}")
                unmatched_songs.append({"filename": mp3_name})

    return matched_tracks

def copy_and_rename_mp3_flat(mp3, song_id, target_folder):
    """Copy MP3 files to a flat folder in the target directory, renaming by song_id."""
    new_file_path = target_folder / f"{song_id}.mp3"
    shutil.copy(mp3, new_file_path)
    logging.info(f"Copied {mp3} to {new_file_path}")
    return new_file_path

def get_tango_song_metadata(song_id, tango_songs):
    """Retrieve metadata from djTangoSongs.json based on songID."""
    for song in tango_songs:
        if song["songID"] == song_id:
            return song
    return None

# Paths
source_folder = Path("/Volumes/External SSD 1T/Mixxx2").resolve()
target_folder = Path("/Volumes/External SSD 1T/NTTTUpload").resolve()
track_locations_file = Path("./djTrack_locations.json").resolve()
tango_songs_file = Path("./djTangoSongs.json").resolve()
matched_output_file = Path("./djMatchedSongs.json").resolve()
songs_json_file = Path("./djSongs.json").resolve()
unmatched_output_file = Path("./jsUnMatchedSongs.json").resolve()

# Ensure target folder exists
target_folder.mkdir(parents=True, exist_ok=True)

# Load data
mp3_files = find_mp3_files(source_folder)
track_locations = load_json(track_locations_file)
tango_songs = load_json(tango_songs_file)

# Create a map from djId to songID
djId_to_songID = {}
for song in tango_songs:
    dj_id_str = str(song["djId"])
    djId_to_songID[dj_id_str] = song["songID"]

unmatched_songs = []
matched_tracks = match_mp3_to_track_locations(mp3_files, track_locations, djId_to_songID, unmatched_songs)

# Process matched tracks
all_songs_metadata = []
for match in matched_tracks:
    song_id = match["songID"]
    mp3 = Path(match["filepath"])

    # Look up metadata from djTangoSongs.json by songID
    tango_metadata = get_tango_song_metadata(song_id, tango_songs)
    if not tango_metadata:
        logging.warning(f"No metadata found for songID: {song_id}")
        unmatched_songs.append({"filename": match["filename"]})
        continue

    # Copy and rename MP3 into a flat folder
    copy_and_rename_mp3_flat(mp3, song_id, target_folder)

    # Prepare song metadata for djSongs.json
    song_metadata = {
        "SongID": tango_metadata["songID"],
        "Title": tango_metadata["songTitleCleanL1"],
        "Orchestra": tango_metadata["artistCleanL2"],
        "ArtistMaster": tango_metadata["artistMaster"],
        "AudioUrl": f"https://namethattangotune.blob.core.windows.net/djsongs/{tango_metadata['songID']}.mp3",
        "Composer": tango_metadata.get("composerCleanL1", ""),  
        "Year": tango_metadata.get("year", ""),
        "Style": tango_metadata["Style1"],
        "Alternative": tango_metadata["Alternative"],
        "Candombe": tango_metadata["Candombe"],
        "Cancion": tango_metadata["Cancion"],
        "Singer": ""
    }
    all_songs_metadata.append(song_metadata)

# Save outputs
save_json({"songs": all_songs_metadata}, songs_json_file)
matched_filenames = [{"filename": t["filename"]} for t in matched_tracks]
save_json(matched_filenames, matched_output_file)
save_json(unmatched_songs, unmatched_output_file)