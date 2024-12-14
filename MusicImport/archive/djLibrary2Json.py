import csv
import json
import uuid
import re
from pathlib import Path

def clean_special_characters(text):
    """Remove diacritics and special characters."""
    import unicodedata
    cleaned_text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return cleaned_text.strip().lstrip('.')

def clean_commas(text):
    """Swap comma-separated names like 'Last, First' for specific patterns."""
    patterns = [
        (r"\bDi Sarli, Carlos\b", "Carlos Di Sarli"),
        (r"\bDe Angelis, Alfredo\b", "Alfredo De Angelis")
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    if ',' in text:
        parts = text.split(',')
        if len(parts) == 2 and len(parts[1].split()) <= 2:
            return f"{parts[1].strip()} {parts[0].strip()}"
    return text

def remove_square_brackets(text):
    """Remove content inside square brackets."""
    return re.sub(r'\[.*?\]', '', text).strip()

def determine_style1(genre):
    """Determine Style1 based on genre."""
    for style in ['tango', 'vals', 'waltz', 'milonga', 'marcha']:
        if style in genre.lower():
            return style.capitalize()
    return "Unknown"

def determine_alternative(genre):
    """Determine if 'Alternative' applies."""
    alt_keywords = ['alt', 'alt.', 'alternative']
    if any(kw in genre.lower() for kw in alt_keywords) and 'waltz' not in genre.lower():
        return "Y"
    if 'alt waltz' in genre.lower() or 'alternative waltz' in genre.lower():
        return "Y"
    return "N"

def determine_candombe(genre):
    """Determine if 'Candombe' applies."""
    return "Y" if 'candombe' in genre.lower() else "N"

def determine_cancion(genre):
    """Determine if Cancion applies."""
    return "Y" if 'canción' in genre.lower() or 'cancion' in genre.lower() else "N"

def process_csv(input_path, output_path, master_output_path):
    """Process CSV and create JSON file."""
    with open(input_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        filtered_rows = [row for row in reader if any(kw in row['genre'].lower() for kw in ['tango', 'vals', 'waltz', 'milonga', 'marcha'])]
        
        result = []
        artist_set = set()  # To keep track of unique artistCleanL2
        for row in filtered_rows:
            song_id = uuid.uuid4().hex
            dj_id = row['id']  # Add djId from the 'id' field in the CSV
            song_title_original = row['title']
            song_title_clean_l1 = clean_special_characters(song_title_original)
            album_title_original = row['album']
            album_title_clean_l1 = clean_special_characters(album_title_original)
            album_title_clean_l2 = remove_square_brackets(album_title_clean_l1)
            artist_original = row['artist']
            artist_clean_l1 = clean_special_characters(artist_original)
            artist_clean_l2 = clean_commas(artist_clean_l1)
            artist2_original = row['album_artist']
            artist2_clean_l1 = clean_special_characters(artist2_original)
            composer_original = row['composer']
            composer_clean_l1 = clean_special_characters(composer_original)
            year = row['year']
            duration = round(float(row['duration'])) if row['duration'] else None
            bpm = round(float(row['bpm'])) if row['bpm'] else None
            genre = row['genre']

            # Add artistCleanL2 to the set
            artist_set.add(artist_clean_l2)

            result.append({
                "songID": song_id,
                "djId": dj_id,
                "songTitleOriginal": song_title_original,
                "songTitleCleanL1": song_title_clean_l1,
                "albumTitleOriginal": album_title_original,
                "albumTitleCleanL1": album_title_clean_l1,
                "albumTitleCleanL2": album_title_clean_l2,
                "artistOriginal": artist_original,
                "artistCleanL1": artist_clean_l1,
                "artistCleanL2": artist_clean_l2,
                "artist2Original": artist2_original,
                "artist2CleanL1": artist2_clean_l1,
                "composerOriginal": composer_original,
                "composerCleanL1": composer_clean_l1,
                "year": year,
                "duration": duration,
                "bpm": bpm,
                "Style1": determine_style1(genre),
                "Alternative": determine_alternative(genre),
                "Candombe": determine_candombe(genre),
                "Cancion": determine_cancion(genre)
            })

        # Save tangoSongs.json
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(result, jsonfile, ensure_ascii=False, indent=2)
        print(f"Processed {len(result)} records and saved to {output_path}")

        # Create tmp_tangoSongsMasters.json
        master_data = [
            {"artist": artist, "active": "true", "level": "", "similars": []}
            for artist in sorted(artist_set)
        ]
        with open(master_output_path, 'w', encoding='utf-8') as masterfile:
            json.dump(master_data, masterfile, ensure_ascii=False, indent=2)
        print(f"Created {len(master_data)} unique artists and saved to {master_output_path}")

# Input and output paths
input_csv = Path("~/Downloads/library.csv").expanduser()
output_json = Path("./djTangoSongs.json").resolve()
master_json = Path("./dj_tmp_tangoSongsMasters.json").resolve()

# Process the CSV file
process_csv(input_csv, output_json, master_json)