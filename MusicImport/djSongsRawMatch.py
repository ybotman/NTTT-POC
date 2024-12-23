import json
import os
import logging
from pathlib import Path
import unicodedata
import shutil
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TCON, COMM, error
from mutagen.mp3 import MP3

# --------------------------------------
# Configuration
# --------------------------------------
test_mode = False  # Set to False in production
SOURCE_FOLDER = Path("/Volumes/External SSD 1T/Mixxx").resolve()
TARGET_FOLDER = Path("/Volumes/External SSD 1T/NTTTUpload").resolve()

TRACK_LOCATIONS_FILE = Path("./djTrack_locations.json").resolve()
TANGO_SONGS_FILE = Path("./djTangoSongs.json").resolve()
MATCHED_OUTPUT_FILE = Path("./djMatchedSongs.json").resolve()
SONGS_JSON_FILE = Path("./djSongs.json").resolve()
UNMATCHED_OUTPUT_FILE = Path("./djUnMatchedSongs.json").resolve()

LOG_FILE = "djMatch.log"

# --------------------------------------
# Logging Configuration
# --------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


def update_mp3_metadata(mp3_file, song_metadata):
    """Update MP3 metadata using Mutagen."""
    try:
        audio = MP3(mp3_file, ID3=ID3)

        # If no ID3 tag exists, create one
        try:
            audio.add_tags()
        except error:
            pass

        # Update metadata fields
        audio.tags["TIT2"] = TIT2(encoding=3, text=song_metadata['Title'])  # Title
        audio.tags["TALB"] = TALB(encoding=3, text=song_metadata['Album'])  # Album
        audio.tags["TPE1"] = TPE1(encoding=3, text=song_metadata['ArtistMaster'])  # Artist
        audio.tags["TCON"] = TCON(encoding=3, text=song_metadata['Style'])  # Genre/Style
        audio.tags["COMM"] = COMM(encoding=3, lang="eng", desc="Comment", text=f"SongID: {song_metadata['SongID']}")  # SongID in comments

        audio.save()
        logging.info(f"Updated metadata for {mp3_file}")
    except Exception as e:
        logging.error(f"Failed to update metadata for {mp3_file}: {e}")


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


def get_subpath_after_mixxx(path_str):
    """Extract the subpath after 'Mixxx/' from the given path (case-insensitive)."""
    norm_path = path_str.replace('\\', '/')
    idx = norm_path.lower().find('mixxx/')
    if idx == -1:
        return ""
    return norm_path[idx + len('mixxx/'):].strip("/")

def match_mp3_to_track_locations(mp3_files, track_locations, djId_to_songID, unmatched_songs):
    matched_tracks = []
    total_processed = 0
    total_matched = 0
    total_unmatched = 0

    # Index track locations by full normalized subpath (directory + filename)
    track_index = {}
    for tl in track_locations:
        tl_subpath = get_subpath_after_mixxx(tl['location'])
        normalized_tl_subpath = normalize_filename(tl_subpath)  # normalize the entire subpath
        key = normalized_tl_subpath.lower()
        track_index.setdefault(key, []).append(tl)

    for mp3 in mp3_files:
        mp3_subpath = get_subpath_after_mixxx(str(mp3.resolve()))
        normalized_mp3_subpath = normalize_filename(mp3_subpath)
        mp3_key = normalized_mp3_subpath.lower()

        total_processed += 1
        possible_matches = track_index.get(mp3_key, [])

        if not possible_matches:
            # No matches found
            unmatched_songs.append({
                "filename": mp3.name,
                "fullpath": str(mp3.resolve()),
                "normalized_mp3_subpath": normalized_mp3_subpath,
            })
            total_unmatched += 1
        else:
            # Check by filesize
            mp3_size = mp3.stat().st_size
            closest_match = None
            min_size_diff = float('inf')
            for match in possible_matches:
                try:
                    track_size = int(match['filesize'])
                    size_diff = abs(track_size - mp3_size)
                    if size_diff < min_size_diff:
                        closest_match = match
                        min_size_diff = size_diff
                except ValueError:
                    continue

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
                    total_matched += 1
                else:
                    unmatched_songs.append({
                        "filename": mp3.name,
                        "fullpath": str(mp3.resolve()),
                        "normalized_mp3_subpath": normalized_mp3_subpath,
                        "closest_match_location": closest_match['location'],
                        "closest_match_filename": closest_match['filename']
                    })
                    total_unmatched += 1
            else:
                unmatched_songs.append({
                    "filename": mp3.name,
                    "fullpath": str(mp3.resolve()),
                    "normalized_mp3_subpath": normalized_mp3_subpath
                })
                total_unmatched += 1

        if total_processed % 50 == 0:
            logging.info(f"Processed {total_processed} files. Matched: {total_matched}, Unmatched: {total_unmatched}")

    return matched_tracks

def copy_and_rename_mp3_flat(mp3, song_id, target_folder):
    """Copy MP3 files to a flat folder in the target directory, renaming by song_id."""
    new_file_path = target_folder / f"{song_id}.mp3"
    shutil.copy(mp3, new_file_path)
    return new_file_path


def get_tango_song_metadata(song_id, tango_songs):
    """Retrieve metadata from djTangoSongs.json based on songID."""
    for song in tango_songs:
        if song["songID"] == song_id:
            return song
    return None


def copy_and_rename_mp3_flat(mp3, song_id, target_folder, song_metadata):
    """Copy MP3 files to a flat folder in the target directory, renaming by song_id and updating metadata."""
    new_file_path = target_folder / f"{song_id}.mp3"
    shutil.copy(mp3, new_file_path)

    # Update the metadata for the copied file
    update_mp3_metadata(new_file_path, song_metadata)

    return new_file_path

# --------------------------------------
# Main Process
# --------------------------------------
if __name__ == "__main__":
    # Ensure target folder exists
    TARGET_FOLDER.mkdir(parents=True, exist_ok=True)

    # Load data
    mp3_files = find_mp3_files(SOURCE_FOLDER)
    track_locations = load_json(TRACK_LOCATIONS_FILE)
    tango_songs = load_json(TANGO_SONGS_FILE)

    # Test mode: limit mp3_files to first 100 if test_mode is True
    if test_mode:
        mp3_files = mp3_files[:100]

    # Create a map from djId to songID
    djId_to_songID = {str(song["djId"]): song["songID"] for song in tango_songs}

    unmatched_songs = []
    matched_tracks = match_mp3_to_track_locations(mp3_files, track_locations, djId_to_songID, unmatched_songs)

    # Process matched tracks
   # Process matched tracks
    all_songs_metadata = []
    for match in matched_tracks:
        song_id = match["songID"]
        mp3 = Path(match["filepath"])

        # Look up metadata from djTangoSongs.json by songID
        tango_metadata = get_tango_song_metadata(song_id, tango_songs)
        if not tango_metadata:
            unmatched_songs.append({"filename": match["filename"], "fullpath": match["filepath"]})
            continue

        # Prepare song metadata for djSongs.json
        song_metadata = {
            "SongID": tango_metadata["songID"],
            "Title": tango_metadata["songTitleCleanL1"],
            "Orchestra": tango_metadata["artistCleanL2"],
            "Album": tango_metadata["albumTitleCleanL2"],
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

        # Copy and rename MP3 into a flat folder and update metadata
        copy_and_rename_mp3_flat(mp3, song_id, TARGET_FOLDER, song_metadata)

        # Append song metadata
        all_songs_metadata.append(song_metadata)

    # Save outputs
    save_json({"songs": all_songs_metadata}, SONGS_JSON_FILE)
    matched_filenames = [{"filename": t["filename"]} for t in matched_tracks]
    save_json(matched_filenames, MATCHED_OUTPUT_FILE)
    save_json(unmatched_songs, UNMATCHED_OUTPUT_FILE)

    logging.info("Processing complete.")