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
    """Find all MP3 files in a folder."""
    return [file for file in Path(folder).glob("*.mp3")]

def match_mp3_to_track_locations(mp3_files, track_locations, djId_to_songID, unmatched_songs):
    """Match MP3 files to track locations using djId_to_songID mapping.
       If no songID is found for a given djId, that file is considered unmatched.
    """
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
            # If it's not in track_locations, we don't know djId or songID. Consider it unmatched.
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

def create_songs_upload_folder():
    """Clean or create the djSongsUpload folder."""
    upload_folder = Path("./djSongsUpload")
    if upload_folder.exists():
        shutil.rmtree(upload_folder)
    upload_folder.mkdir()
    logging.info("Cleaned and recreated ./djSongsUpload folder.")
    return upload_folder

def copy_and_rename_mp3(mp3, song_id, upload_folder):
    """Copy and rename MP3 files to the djSongsUpload folder."""
    new_file_path = upload_folder / f"{song_id}.mp3"
    shutil.copy(mp3, new_file_path)
    logging.info(f"Copied {mp3.name} to {new_file_path}")
    return new_file_path

def get_tango_song_metadata(song_id, tango_songs):
    """Retrieve metadata from djTangoSongs.json based on songID."""
    for song in tango_songs:
        if song["songID"] == song_id:
            return song
    return None

# Paths
mp3_folder = Path("./djSongsRaw").resolve()
track_locations_file = Path("./djTrack_locations.json").resolve()
tango_songs_file = Path("./djTangoSongs.json").resolve()
matched_output_file = Path("./djMatchedSongs.json").resolve()
songs_json_file = Path("./djSongs.json").resolve()
unmatched_output_file = Path("./jsUnMatchedSongs.json").resolve()

# Load data
mp3_files = find_mp3_files(mp3_folder)
track_locations = load_json(track_locations_file)
tango_songs = load_json(tango_songs_file)

# Create a map from djId to songID
djId_to_songID = {}
for song in tango_songs:
    dj_id_str = str(song["djId"])
    djId_to_songID[dj_id_str] = song["songID"]

unmatched_songs = []
matched_tracks = match_mp3_to_track_locations(mp3_files, track_locations, djId_to_songID, unmatched_songs)

# Prepare upload folder
upload_folder = create_songs_upload_folder()

# We'll store all matched song metadata in this list, then overwrite djSongs.json once
all_songs_metadata = []

# Process matched tracks
for match in matched_tracks:
    song_id = match["songID"]
    mp3 = Path(match["filepath"])

    # Look up metadata from djTangoSongs.json by songID
    tango_metadata = get_tango_song_metadata(song_id, tango_songs)
    if not tango_metadata:
        logging.warning(f"No metadata found for songID: {song_id}")
        # If we can't find metadata, consider it unmatched
        unmatched_songs.append({"filename": match["filename"]})
        continue

    # Copy and rename MP3
    copy_and_rename_mp3(mp3, tango_metadata["songID"], upload_folder)

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

# Overwrite djSongs.json with all matched metadata
save_json({"songs": all_songs_metadata}, songs_json_file)

# djMatchedSongs.json only needs the filename of matched songs
matched_filenames = [{"filename": t["filename"]} for t in matched_tracks]
save_json(matched_filenames, matched_output_file)

# jsUnMatchedSongs.json only needs the filename for unmatched
save_json(unmatched_songs, unmatched_output_file)