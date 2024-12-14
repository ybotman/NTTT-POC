#!/usr/bin/env python3
import os
import sys
import json
import logging
import subprocess
import argparse
import uuid
import random
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def check_ffmpeg():
    """Check if ffmpeg is installed and in PATH."""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        logging.info("ffmpeg found.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error("ffmpeg not found. Please install ffmpeg and ensure it's in your PATH.")
        return False

def generate_random_id(length=50):
    """Generate a pseudo-random ID."""
    uid = uuid.uuid4().hex
    while len(uid) < length:
        uid += uuid.uuid4().hex
    return uid[:length]

def find_m4p_files(base_path):
    """Recursively find all .m4p files under the given base directory."""
    files = []
    for root, dirs, filenames in os.walk(base_path):
        for fname in filenames:
            if fname.lower().endswith('.m4p'):
                files.append(Path(root) / fname)
    return files

def extract_metadata(m4p_path, base_path):
    """
    Extract artist, album, and song metadata from the .m4p file path.
    Automatically handles paths where artist folders are subdirectories of the input base path.
    """
    relative_path = m4p_path.relative_to(base_path)
    parts = relative_path.parts

    if len(parts) >= 3:  # Expecting <Artist>/<Album>/<Song>.m4p
        artist = parts[0]
        album = parts[1]
        song = m4p_path.stem
        return {'artist': artist, 'album': album, 'song': song}
    elif len(parts) == 2:  # Handle <Album>/<Song>.m4p
        artist = "Unknown"
        album = parts[0]
        song = m4p_path.stem
        return {'artist': artist, 'album': album, 'song': song}
    else:
        logging.warning(f"Path structure not as expected: {m4p_path}")
        return {'artist': "Unknown", 'album': "Unknown", 'song': m4p_path.stem}

def record_audio(output_wav_path, duration=None):
    """
    Record audio from BlackHole for the specified duration using ffmpeg.
    
    Parameters:
        output_wav_path (Path): Path to save the recorded WAV file.
        duration (int or None): Duration in seconds to record. If None, record full song.

    Returns:
        bool: True if recording was successful, False otherwise.
    """
    logging.info(f"Starting recording to {output_wav_path}")
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite without asking
        "-f", "avfoundation",
        "-i", ":BlackHole 2ch"
    ]
    if duration is not None:
        cmd.extend(["-t", str(duration)])
    cmd.append(str(output_wav_path))

    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"Recording completed: {output_wav_path}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to record audio: {e.stderr.decode('utf-8', errors='replace')}")
        return False

def validate_wav_file(file_path):
    """Validate that the WAV file is not empty and contains audio data."""
    if not file_path.exists():
        return False
    if file_path.stat().st_size == 0:
        logging.error(f"File {file_path} is empty.")
        return False
    try:
        cmd = ["ffprobe", "-i", str(file_path), "-show_streams", "-select_streams", "a", "-loglevel", "error"]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        logging.error(f"File {file_path} does not contain valid audio data.")
        return False

def load_json_list(json_path):
    """Load JSON array from file or return an empty list if file doesn't exist."""
    if not json_path.exists():
        return []
    try:
        with json_path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.warning(f"JSON file {json_path} is corrupted or empty. Starting fresh.")
        return []

def save_json_list(json_path, data):
    """Save a list of JSON objects to file."""
    try:
        with json_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Failed to write JSON file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Traverse M4P files, extract metadata, record via BlackHole, and append JSON.")
    parser.add_argument("--input", required=True, help="Path to the input directory containing .m4p files.")
    parser.add_argument("--output", required=True, help="Path to the output directory where .wav and JSON will be stored.")
    parser.add_argument("--record-duration", type=str, default="full", help="Recording duration: 'full' or seconds as an integer.")
    parser.add_argument("--test", type=int, default=None, help="Number of random tracks to process in test mode.")
    parser.add_argument("--json-output", default="songs.json", help="Name of the JSON output file.")
    args = parser.parse_args()

    input_dir = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    json_file = output_dir / args.json_output

    if not input_dir.exists():
        logging.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    if not check_ffmpeg():
        sys.exit(1)

    m4p_files = find_m4p_files(input_dir)
    if not m4p_files:
        logging.warning("No .m4p files found in the input directory.")
        sys.exit(0)

    # TEST mode: limit to a random subset
    if args.test:
        logging.info(f"TEST mode enabled. Selecting {args.test} random files.")
        m4p_files = random.sample(m4p_files, min(args.test, len(m4p_files)))

    # Parse recording duration
    record_duration = None if args.record_duration == "full" else int(args.record_duration)

    # Load existing JSON data
    songs_data = load_json_list(json_file)

    for i, m4p in enumerate(m4p_files, start=1):
        logging.info(f"Processing file {i}/{len(m4p_files)}: {m4p}")
        try:
            metadata = extract_metadata(m4p, base_path=input_dir)
            song_id = generate_random_id()
            wav_filename = f"{song_id}.wav"
            wav_path = output_dir / wav_filename

            # Record the audio
            recorded = record_audio(wav_path, duration=record_duration)
            if not recorded or not validate_wav_file(wav_path):
                logging.error(f"Failed to process or validate track: {m4p}")
                continue

            new_entry = {
                "songId": song_id,
                "name": metadata["song"],
                "album": metadata["album"],
                "artist": metadata["artist"],
                "fullPath": str(m4p.resolve())
            }
            songs_data.append(new_entry)

            # Save updated JSON
            if not save_json_list(json_file, songs_data):
                logging.error("Failed to update JSON with new song entry.")

        except Exception as e:
            logging.error(f"Error processing {m4p}: {e}")
        logging.info(f"Finished processing file {i}/{len(m4p_files)}: {m4p}")

    logging.info(f"Processed {len(songs_data)} songs total. JSON file updated: {json_file}")

if __name__ == "__main__":
    main()