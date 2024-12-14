#!/usr/bin/env python3
"""
generate_artist_master.py

A Python script to generate a distinct `ArtistMaster.json` from `AlbumArtists.json`.
Each unique artist entry is consolidated into a single list with their corresponding attributes.

Usage:
    Ensure `AlbumArtists.json` is present in the specified directory.
    Run the script:
        python3 generate_artist_master.py

Outputs:
    - ArtistMaster.json: A JSON file with consolidated unique artists.
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
        logging.FileHandler("generate_artist_master.log")
    ]
)

def load_json_file(filepath):
    """
    Load JSON data from a file.

    Parameters:
        filepath (Path): Path to the JSON file.

    Returns:
        list: List of artist dictionaries.

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

def consolidate_artists(album_artists):
    """
    Consolidate distinct artists from `AlbumArtists.json`.

    Parameters:
        album_artists (list): List of artist dictionaries from AlbumArtists.json.

    Returns:
        list: A list of unique artist dictionaries for ArtistMaster.json.
    """
    artist_map = {}

    for record in album_artists:
        artist_name = record.get("artist", "").strip()
        if not artist_name:
            continue

        if artist_name not in artist_map:
            # Add the artist with attributes
            artist_map[artist_name] = {
                "artist": artist_name,
                "active": record.get("active", "false"),
                "level": record.get("level", "0"),
                "grouped": record.get("grouped", [])
            }
        else:
            # Ensure active status is true if any record has it true
            if record.get("active", "false") == "true":
                artist_map[artist_name]["active"] = "true"

    logging.info(f"Consolidated {len(artist_map)} unique artists.")
    return list(artist_map.values())

def main():
    """
    Main function to orchestrate the creation of ArtistMaster.json.
    """
    # File paths
    input_file = Path("/Users/tobybalsley/MyDocs/AppDev/NameThatTangoTune/MusicImport/AlbumArtists.json")
    output_file = Path("/Users/tobybalsley/MyDocs/AppDev/NameThatTangoTune/MusicImport/ArtistMaster.json")

    # Load AlbumArtists.json
    try:
        album_artists = load_json_file(input_file)
    except Exception as e:
        logging.critical(f"Cannot proceed without valid '{input_file.name}'. Exiting.")
        return

    # Consolidate unique artists
    artist_master = consolidate_artists(album_artists)

    # Save to ArtistMaster.json
    try:
        save_json_file(artist_master, output_file)
    except Exception as e:
        logging.critical(f"Failed to save '{output_file.name}'. Exiting.")
        return

    logging.info("ArtistMaster.json created successfully.")

if __name__ == "__main__":
    main()