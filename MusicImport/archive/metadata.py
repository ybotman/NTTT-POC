import os
import json
from mutagen import File as MutagenFile
import glob
import traceback

def get_audio_metadata(file_path):
    """Extract metadata from an audio file."""
    try:
        audio = MutagenFile(file_path)
        if not audio or not audio.tags:
            return {"error": "No metadata found or file is unreadable"}
        
        # Extract common metadata tags
        title = audio.tags.get("©nam", [None])[0]  # Track title
        artist = audio.tags.get("©ART", [None])[0]  # Artist
        album = audio.tags.get("©alb", [None])[0]  # Album

        return {
            "title": title if title else "Unknown Title",
            "artist": artist if artist else "Unknown Artist",
            "album": album if album else "Unknown Album"
        }
    except Exception as e:
        # Handle any unexpected errors
        return {"error": str(e)}

def main():
    # Example: Adjust this to your specific directory
    music_folder = os.path.expanduser("~/Music/ooops downgrand/Media.localized/Apple Music")

    print(f"Searching for .m4a and .m4p files recursively in: {music_folder}")

    # Search for all `.m4a` and `.m4p` files recursively
    audio_files = glob.glob(os.path.join(music_folder, "**/*.m4[ap]"), recursive=True)

    if not audio_files:
        print("No audio files found in the specified directory.")
        return

    print(f"Found {len(audio_files)} audio file(s).")

    metadata_results = []

    for i, file_path in enumerate(audio_files):
        print(f"Processing file {i+1}/{len(audio_files)}: {file_path}")
        try:
            metadata = get_audio_metadata(file_path)
            print(f"Metadata: {metadata}\n")
            
            # Append result to the list
            metadata_results.append({
                "file_path": file_path,
                "metadata": metadata
            })

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            traceback.print_exc()

    # Save metadata results to JSON file
    output_json_path = os.path.expanduser("~/Desktop/audio_metadata.json")
    with open(output_json_path, "w") as json_file:
        json.dump(metadata_results, json_file, indent=2)
    print(f"Metadata saved to: {output_json_path}")

if __name__ == "__main__":
    main()