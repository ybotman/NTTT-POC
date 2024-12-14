#!/usr/bin/env python3
"""
update_tango_songs.py

A Python script to add a new attribute `MasterArtist` to each song in `tango_songs.json` using `ArtistMaster.json`.

Features:
1. Matches `artist` in `tango_songs.json` with `artist` in `ArtistMaster.json`.
2. Adds a new attribute `MasterArtist` to each song in `tango_songs.json`:
    - If a match is found, `MasterArtist` is set to the matching `artist` from `ArtistMaster.json`.
    - If no match is found, `MasterArtist` is set to "Unknown".
3. Saves the updated data into `tango_songs_copy.json`.

Usage:
    Ensure `tango_songs.json` and `ArtistMaster.json` are present in the specified directory.
    Run the script:
        python3 update_tango_songs.py

Outputs:
    - tango_songs_copy.json: Updated JSON file with the `MasterArtist` attribute added.
"""

import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("update_tango_songs.log")
    ]
)

def load_json_file(filepath):
    """
    Load JSON data from a file.

    Parameters:
        filepath (Path): Path to the JSON file.

    Returns:
        list: List of dictionaries representing JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    try:
        with filepath.open('r', encoding='utf-8') as f:
            data = json.load(f)
        logging.info(f"Loaded {len(data)} records from '{filepath.name}'.")
        return data
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON format in '{filepath.name}': {e}")
        raise

def save_json_file(data, filepath):
    """
    Save data to a JSON file with indentation for readability.

    Parameters:
        data (list): The data to serialize to JSON.
        filepath (Path): Path to the output JSON file.

    Raises:
        IOError: If writing to the file fails.
    """
    try:
        with filepath.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"Saved {len(data)} records to '{filepath.name}'.")
    except IOError as e:
        logging.error(f"Failed to write to '{filepath.name}': {e}")
        raise

def add_master_artist_to_songs(tango_songs, artist_master):
    """
    Add the `MasterArtist` attribute to each song in `tango_songs` based on `ArtistMaster.json`.

    Parameters:
        tango_songs (list): List of dictionaries representing songs from `tango_songs.json`.
        artist_master (list): List of dictionaries representing artists from `ArtistMaster.json`.

    Returns:
        list: Updated list of songs with `MasterArtist` attribute added.
    """
    master_artists = [artist["artist"] for artist in artist_master]

    for song in tango_songs:
        song_artist = song.get("artist", "")
        # Check if any `MasterArtist` appears in the song's artist
        master_artist = next((ma for ma in master_artists if ma in song_artist), "Unknown")
        song["MasterArtist"] = master_artist
        logging.debug(f"Processed song '{song.get('name')}', MasterArtist: {master_artist}")

    return tango_songs

def main():
    """
    Main function to orchestrate the update of tango songs.
    """
    # File paths
    current_dir = Path.cwd()
    tango_songs_file = current_dir / "tango_songs.json"
    artist_master_file = current_dir / "ArtistMaster.json"
    output_file = current_dir / "tango_songs_copy.json"

    # Load JSON data
    try:
        tango_songs = load_json_file(tango_songs_file)
        artist_master = load_json_file(artist_master_file)
    except Exception as e:
        logging.critical("Failed to load required files. Exiting.")
        return

    # Add MasterArtist attribute
    updated_songs = add_master_artist_to_songs(tango_songs, artist_master)

    # Save updated JSON to file
    try:
        save_json_file(updated_songs, output_file)
    except Exception as e:
        logging.critical("Failed to save updated songs. Exiting.")
        return

    logging.info("Updated tango songs with MasterArtist successfully.")

if __name__ == "__main__":
    main()