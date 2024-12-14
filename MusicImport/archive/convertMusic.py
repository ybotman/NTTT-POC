#!/usr/bin/env python3
import os
import sys
import json
import logging
import subprocess
import argparse
import uuid
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
    """
    Generate a pseudo-random ID.
    Using UUID and concatenation to achieve desired length.
    """
    uid = uuid.uuid4().hex
    while len(uid) < length:
        uid += uuid.uuid4().hex
    return uid[:length]

def find_m4p_files(base_path):
    """
    Recursively find all .m4p files under the given base directory.
    
    Parameters:
        base_path (Path): The base directory to search.
    
    Returns:
        list[Path]: List of paths to .m4p files.
    """
    files = []
    for root, dirs, filenames in os.walk(base_path):
        for fname in filenames:
            if fname.lower().endswith('.m4p'):
                files.append(Path(root) / fname)
    return files

def extract_metadata(m4p_path, pivot='Pass 1'):
    """
    Extract artist, album, and song metadata from the .m4p file path.
    We expect a structure like:
      ~/Music/TangoMusic/Pass 1/<Artist>/<Album>/<Song>.m4p
    
    Parameters:
        m4p_path (Path): Full path to the .m4p file.
        pivot (str): The directory name to pivot extraction from.
    
    Returns:
        dict: {
            'artist': str,
            'album': str,
            'song': str
        }
    """
    parts = m4p_path.parts
    try:
        pivot_index = parts.index(pivot)
    except ValueError:
        logging.warning(f"Pivot directory '{pivot}' not found in path: {m4p_path}")
        if len(parts) < 4:
            raise ValueError("Cannot extract metadata - path structure too shallow.")
        # Attempt fallback (not guaranteed to be correct)
        artist = parts[-3]
        album = parts[-2]
        song = m4p_path.stem
        return {'artist': artist, 'album': album, 'song': song}

    try:
        artist = parts[pivot_index + 1]
        album = parts[pivot_index + 2]
        song = m4p_path.stem
    except IndexError:
        logging.error(f"Path structure not as expected: {m4p_path}")
        raise ValueError("Not enough directories to extract metadata.")

    return {'artist': artist, 'album': album, 'song': song}

def record_audio(output_wav_path, duration=30):
    """
    Record audio from BlackHole for a given duration using ffmpeg.
    Assumes BlackHole is set as system audio output.
    
    Parameters:
        output_wav_path (Path): Where to save the recorded WAV.
        duration (int): Duration in seconds to record.
    
    Returns:
        bool: True if success, False otherwise.
    """
    cmd = [
        "ffmpeg",
        "-y", # overwrite without asking
        "-f", "avfoundation",
        "-i", ":BlackHole 2ch",
        "-t", str(duration),
        str(output_wav_path)
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"Recorded WAV file: {output_wav_path}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to record audio: {e}")
        return False

def load_json_list(json_path):
    """
    Load JSON array from file or return an empty list if file doesn't exist.
    """
    if not json_path.exists():
        return []
    try:
        with json_path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.warning(f"JSON file {json_path} is corrupted or empty. Starting fresh.")
        return []
    except Exception as e:
        logging.error(f"Error reading JSON file {json_path}: {e}")
        return []

def save_json_list(json_path, data):
    """
    Save a list of JSON objects to file.
    """
    try:
        with json_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Failed to write JSON file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Traverse M4P files, extract metadata, record via BlackHole, and incrementally append JSON.")
    parser.add_argument("--input", required=True, help="Path to the input directory containing .m4p files.")
    parser.add_argument("--output", required=True, help="Path to the output directory where .wav and JSON will be stored.")
    parser.add_argument("--pivot", default="Pass 1", help="Directory name to pivot extraction of artist/album/song.")
    parser.add_argument("--duration", type=int, default=30, help="Duration in seconds to record each track.")
    parser.add_argument("--json-output", default="songs.json", help="Name of the JSON output file.")
    args = parser.parse_args()

    input_dir = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    json_file = output_dir / args.json_output

    if not input_dir.exists():
        logging.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created output directory: {output_dir}")
        except Exception as e:
            logging.error(f"Could not create output directory: {e}")
            sys.exit(1)
    
    if not check_ffmpeg():
        sys.exit(1)
    
    m4p_files = find_m4p_files(input_dir)
    if not m4p_files:
        logging.warning("No .m4p files found in the input directory.")
        sys.exit(0)

    # Load or initialize the JSON data
    songs_data = load_json_list(json_file)

    for m4p in m4p_files:
        try:
            metadata = extract_metadata(m4p, pivot=args.pivot)
        except ValueError as ve:
            logging.error(f"Skipping file due to metadata extraction issue: {m4p} - {ve}")
            continue

        song_id = generate_random_id()
        # Create a unique wav filename from the song_id
        wav_filename = f"{song_id}.wav"
        wav_path = output_dir / wav_filename

        # Optional: start playing the track here if needed
        # e.g., subprocess.run(["afplay", str(m4p)], check=True)
        # Sleep briefly if necessary to ensure playback starts before recording.

        # Record the audio
        recorded = record_audio(wav_path, duration=args.duration)
        if not recorded:
            logging.error(f"Failed to record track for {m4p}")
            continue

        # Append this song's data to JSON
        new_entry = {
            "songId": song_id,
            "name": metadata["song"],
            "album": metadata["album"],
            "artist": metadata["artist"],
            "fullPath": str(m4p.resolve())
        }
        songs_data.append(new_entry)

        # Save the updated JSON file
        if not save_json_list(json_file, songs_data):
            logging.error("Failed to update JSON with new song entry. Continuing anyway.")

    logging.info(f"Processed {len(songs_data)} songs total. JSON file updated: {json_file}")

if __name__ == "__main__":
    main()