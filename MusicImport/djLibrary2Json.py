import json
import uuid
import re
import unicodedata
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

def clean_special_characters(text):
    """Remove diacritics and special characters."""
    if not text:
        return ""
    cleaned_text = ''.join(c for c in unicodedata.normalize('NFD', text) 
                           if unicodedata.category(c) != 'Mn')
    return cleaned_text.strip().lstrip('.')

def clean_commas(text):
    """Reformat comma-separated names like 'Last, First' for specific patterns."""
    if not text:
        return ""
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

def fix_di_arienzo(text):
    """Replace all occurrences of 'DiArienzo' (case-insensitive) with 'D'Arienzo'."""
    if not text:
        return ""
    return re.sub(r"diarienzo", "D'Arienzo", text, flags=re.IGNORECASE)

def remove_square_brackets(text):
    """Remove any content inside square brackets and the brackets themselves."""
    if not text:
        return ""
    return re.sub(r"\[.*?\]", "", text).strip()

def determine_style1(genre):
    """Determine Style1 based on genre."""
    if not genre:
        return "Unknown"
    genre_lower = genre.lower()
    if 'tango' in genre_lower:
        return "Tango"
    if 'vals' in genre_lower or 'waltz' in genre_lower:
        return "Vals"
    if 'milonga' in genre_lower:
        return "Milonga"
    if 'marcha' in genre_lower:
        return "Marcha"
    return "Unknown"

def determine_alternative(genre):
    """Determine if 'Alternative' applies."""
    if not genre:
        return "N"
    genre_lower = genre.lower()
    if any(kw in genre_lower for kw in ['alt', 'alt.', 'alternative']) and 'waltz' not in genre_lower:
        return "Y"
    if 'alt waltz' in genre_lower or 'alternative waltz' in genre_lower:
        return "Y"
    return "N"

def determine_candombe(genre):
    """Determine if 'Candombe' applies."""
    if not genre:
        return "N"
    return "Y" if 'candombe' in genre.lower() else "N"

def determine_cancion(genre):
    """Determine if Cancion applies."""
    if not genre:
        return "N"
    return "Y" if 'canción' in genre.lower() or 'cancion' in genre.lower() else "N"

def load_json(file_path):
    """Load JSON from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path):
    """Save JSON to a file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logging.info(f"Saved results to {file_path}")

def generate_deterministic_song_id(album_title, song_title):
    """Generate a deterministic UUID v5 based on album and song title."""
    namespace = uuid.NAMESPACE_DNS  # Fixed namespace
    input_string = f"{album_title}::{song_title}"
    return str(uuid.uuid5(namespace, input_string))

def process_library(library_path, artist_master_path, output_path, not_found_path):
    library = load_json(library_path)
    artist_master_list = load_json(artist_master_path)
    master_artists = {a["artist"].lower(): a["artist"] for a in artist_master_list}

    results = []
    not_found_artists = set()

    valid_genres = ['tango', 'vals', 'waltz', 'milonga', 'marcha']

    for record in library:
        genre = record.get('genre', '')
        if not genre or not any(vg in genre.lower() for vg in valid_genres):
            continue

        dj_id = record.get('id', "")
        song_title_original = record.get('title', '')
        song_title_clean_l1 = clean_special_characters(song_title_original)
        song_title_clean_l1 = fix_di_arienzo(song_title_clean_l1)  # Fix DiArienzo

        album_title_original = record.get('album', '')
        album_title_clean_l1 = clean_special_characters(album_title_original)
        album_title_clean_l1 = fix_di_arienzo(album_title_clean_l1)  # Fix DiArienzo
        album_title_clean_l2 = remove_square_brackets(album_title_clean_l1)

        artist_original = record.get('artist', '') or ""
        artist_clean_l1 = clean_special_characters(artist_original)
        artist_clean_l2 = clean_commas(artist_clean_l1)

        matched_artist = ""
        lowered_clean_artist = artist_clean_l2.lower()
        if lowered_clean_artist in master_artists:
            matched_artist = master_artists[lowered_clean_artist]
        else:
            for ma_key, ma_val in master_artists.items():
                if ma_key in lowered_clean_artist:
                    matched_artist = ma_val
                    break

        if not matched_artist and artist_original:
            not_found_artists.add(artist_original)

        style1 = determine_style1(genre)
        alternative = determine_alternative(genre)
        candombe = determine_candombe(genre)
        cancion = determine_cancion(genre)

        song_id = generate_deterministic_song_id(album_title_original, song_title_original)

        results.append({
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
            "artistMaster": matched_artist if matched_artist else "",
            "Style1": style1,
            "Alternative": alternative,
            "Candombe": candombe,
            "Cancion": cancion
        })

    save_json(results, output_path)

    not_found_list = [artist for artist in not_found_artists if artist]
    not_found_data = [{"artist": artist} for artist in sorted(not_found_list)]
    save_json(not_found_data, not_found_path)

    logging.info(f"Processed {len(results)} songs matching the filter criteria.")

# Example usage
library_path = Path("./djLibrary.json").resolve()
artist_master_path = Path("./ArtistMaster.json").resolve()
output_path = Path("./djTangoSongs.json").resolve()
not_found_path = Path("./djNotFoundArtistMasters.json").resolve()

process_library(library_path, artist_master_path, output_path, not_found_path)