#!/usr/bin/env python3
"""
process_tango_songs.py

A Python script to clean and transform song data from 'songs.json' to 'tango_songs.json'
and generate a unique list of artists in 'artists.json'.

Features:
1. Removes special characters and diacritics from text fields.
2. Removes leading numbers and spaces from song names.
3. Replaces specific words ("Osvalo" -> "Osvaldo") in applicable fields.
4. Generates a unique list of artists in 'artists.json'.
5. Includes error handling and logging for robust execution.

Usage:
    Ensure 'songs.json' is present in the specified directory.
    Run the script:
        python3 process_tango_songs.py

Outputs:
    - tango_songs.json: Cleaned and transformed song data.
    - artists.json: Unique list of artists.
"""

import os
import sys
import json
import logging
import unicodedata
import re
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("process_tango_songs.log")
    ]
)

# Transformations dictionary for replacing specific words
TRANSFORMATIONS = {
    "Osvalo": "Osvaldo"
}

def apply_transformations(text):
    """
    Apply word transformations based on the TRANSFORMATIONS dictionary.

    Parameters:
        text (str): The input string.

    Returns:
        str: The transformed string.
    """
    if not isinstance(text, str):
        logging.warning(f"Expected string for transformation, got {type(text)}. Skipping.")
        return text

    for old_word, new_word in TRANSFORMATIONS.items():
        text = text.replace(old_word, new_word)
    return text

def remove_diacritics(text):
    """
    Remove diacritics from a given text, converting characters like 'á' to 'a'.

    Parameters:
        text (str): The input string with potential diacritics.

    Returns:
        str: The cleaned string without diacritics.
    """
    if not isinstance(text, str):
        logging.warning(f"Expected string for diacritics removal, got {type(text)}. Skipping.")
        return text
    normalized = unicodedata.normalize('NFD', text)
    without_diacritics = ''.join(
        char for char in normalized if unicodedata.category(char) != 'Mn'
    )
    return without_diacritics

def remove_leading_numbers(text):
    """
    Remove leading numbers followed by a space from a string.

    Parameters:
        text (str): The input string.

    Returns:
        str: The string without leading numbers and spaces.
    """
    cleaned_text = re.sub(r'^\d+\s+', '', text)
    return cleaned_text

def load_json_file(filepath):
    """
    Load JSON data from a file.

    Parameters:
        filepath (Path): Path to the JSON file.

    Returns:
        list: List of song dictionaries.

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
        data (any): The data to serialize to JSON.
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

def clean_song_entry(song):
    """
    Clean a single song entry by applying transformations, removing diacritics,
    and leading numbers from 'name'.

    Parameters:
        song (dict): The original song dictionary.

    Returns:
        dict: The cleaned song dictionary.
    """
    cleaned_song = song.copy()
    for field in ['name', 'artist', 'album']:
        original = song.get(field, "")
        cleaned = remove_diacritics(original)
        cleaned = apply_transformations(cleaned)
        if field == 'name':
            cleaned = remove_leading_numbers(cleaned)
        cleaned_song[field] = cleaned
        if original != cleaned:
            logging.debug(f"Cleaned field '{field}': '{original}' -> '{cleaned}'")
    return cleaned_song

def process_songs(input_file, output_file):
    """
    Process 'songs.json' to apply transformations, remove diacritics,
    leading numbers, and save as 'tango_songs.json'.

    Parameters:
        input_file (Path): Path to 'songs.json'.
        output_file (Path): Path to 'tango_songs.json'.

    Returns:
        list: List of cleaned song dictionaries.
    """
    try:
        songs = load_json_file(input_file)
    except Exception as e:
        logging.critical(f"Cannot proceed without valid '{input_file.name}'. Exiting.")
        sys.exit(1)

    cleaned_songs = []
    for idx, song in enumerate(songs, start=1):
        try:
            cleaned_song = clean_song_entry(song)
            cleaned_songs.append(cleaned_song)
        except Exception as e:
            logging.error(f"Error processing song at index {idx}: {e}")
            continue

    try:
        save_json_file(cleaned_songs, output_file)
    except Exception as e:
        logging.critical(f"Failed to save '{output_file.name}'. Exiting.")
        sys.exit(1)

    logging.info(f"Processed {len(cleaned_songs)} songs successfully.")
    return cleaned_songs

def extract_unique_artists(songs):
    """
    Extract a unique list of artists from the songs.

    Parameters:
        songs (list): List of song dictionaries.

    Returns:
        list: List of unique artist dictionaries.
    """
    artist_set = set()
    for song in songs:
        artist = song.get('artist', "").strip()
        if artist:
            artist_set.add(artist)

    unique_artists = [
        {"name": artist, "active": "true", "level": "1", "grouped": []}
        for artist in sorted(artist_set)
    ]
    logging.info(f"Extracted {len(unique_artists)} unique artists.")
    return unique_artists

def save_artists(artists, filepath):
    """
    Save the list of artists to 'artists.json'.

    Parameters:
        artists (list): List of artist dictionaries.
        filepath (Path): Path to 'artists.json'.
    """
    try:
        save_json_file(artists, filepath)
        logging.info(f"Saved artists data to '{filepath.name}'.")
    except Exception as e:
        logging.critical(f"Failed to save '{filepath.name}'. Exiting.")
        sys.exit(1)

def main():
    """
    Main function to orchestrate the processing of song data.
    """
    current_dir = Path.cwd()
    input_file = current_dir / "/Users/tobybalsley/Music/RecordedWAVs/songs.json"
    tango_songs_file = current_dir / "tango_songs.json"
    artists_file = current_dir / "ArtistsRaw.json"

    logging.info("Starting processing of song data.")

    # Step 1: Process 'songs.json' to 'tango_songs.json'
    cleaned_songs = process_songs(input_file, tango_songs_file)

    # Step 2: Extract unique artists and save to 'artists.json'
    unique_artists = extract_unique_artists(cleaned_songs)
    save_artists(unique_artists, artists_file)

    logging.info("Processing completed successfully.")

if __name__ == "__main__":
    main()