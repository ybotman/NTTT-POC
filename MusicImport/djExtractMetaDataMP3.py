import os
import json
import re
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

# Directory containing the MP3 files
input_directory = "./djSongsRaw"
output_json_file = "./djSongsMetadata.json"

def clean_string_with_extension(filename):
    """
    Cleans a filename by removing special characters while retaining the file extension.
    """
    name, extension = os.path.splitext(filename)
    # Remove accents and special characters from the name
    cleaned_name = re.sub(r"[^\w\s]", "", name)
    cleaned_name = re.sub(r"\s+", " ", cleaned_name).strip()  # Normalize spaces
    return f"{cleaned_name}{extension}"

# Function to extract metadata from an MP3 file
def extract_metadata(file_path):
    try:
        mp3_file = MP3(file_path, ID3=ID3)
        filename = os.path.basename(file_path)
        metadata = {
            "filename": filename,
            "filenameCleanL1": clean_string_with_extension(filename),
            "attributes": {key: str(value) for key, value in mp3_file.tags.items()},
        }
        return metadata
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

# Main logic to process all MP3 files in the directory
def process_directory(input_dir, output_file):
    if not os.path.exists(input_dir):
        print(f"Input directory does not exist: {input_dir}")
        return

    metadata_list = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".mp3"):
                file_path = os.path.join(root, file)
                metadata = extract_metadata(file_path)
                if metadata:
                    metadata_list.append(metadata)

    # Save all metadata to a JSON file
    try:
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(metadata_list, json_file, indent=2)
        print(f"Metadata saved to {output_file}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

# Run the script
process_directory(input_directory, output_json_file)