import os
import subprocess
import json
from mutagen import File as MutagenFile
import glob
import traceback

def get_audio_metadata(file_path):
    audio = MutagenFile(file_path)
    if not audio:
        return {}
    # Mutagen can read common tags from MP4/M4A files
    title = audio.tags.get("©nam") if audio.tags and "©nam" in audio.tags else None
    artist = audio.tags.get("©ART") if audio.tags and "©ART" in audio.tags else None
    album = audio.tags.get("©alb") if audio.tags and "©alb" in audio.tags else None

    return {
        "title": title[0] if title else None,
        "artist": artist[0] if artist else None,
        "album": album[0] if album else None
    }

def convert_to_wav(input_path, output_path):
    cmd = ["ffmpeg", "-y", "-i", input_path, "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", output_path]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error converting {input_path} to WAV: {e}")
        print(e.stderr.decode('utf-8', errors='replace'))

def main():
    # Adjust this path as needed
    # Example path from screenshot (Note: verify this path actually exists and has M4A files)
    music_folder = os.path.expanduser("~/Music/ooops downgrand/Media.localized/Apple Music/Alfredo de Angelis/Acordes Porteños")

    print(f"Searching for .m4a files recursively in: {music_folder}")

    # Find all M4A files recursively
    m4a_files = glob.glob(os.path.join(music_folder, "**/*.m4a"), recursive=True)
    
    if not m4a_files:
        print("No M4A files found in the specified directory.")
        return

    print(f"Found {len(m4a_files)} M4A file(s).")

    processed_songs = []

    for i, file_path in enumerate(m4a_files[:50]):  # limit to 50 songs for demonstration
        print(f"Processing file {i+1}/{len(m4a_files)}: {file_path}")
        try:
            metadata = get_audio_metadata(file_path)
            print(f"Metadata extracted: {metadata}")

            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_wav = os.path.join(os.path.dirname(file_path), base_name + ".wav")

            convert_to_wav(file_path, output_wav)
            print(f"Converted {file_path} to {output_wav}\n")

            # Store the results
            processed_songs.append({
                "original_file": file_path,
                "wav_file": output_wav,
                "metadata": metadata
            })

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            traceback.print_exc()

    # Print final JSON output of processed songs
    print("\nAll Processed Songs Metadata:")
    print(json.dumps(processed_songs, indent=2))

if __name__ == "__main__":
    main()