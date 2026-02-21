# BORIS Data Loading Path - End to End Deep Dive

## Overview

Complete flow from BORIS Mixxx SQLite database to playable quiz in NTTT app.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         BORIS DATA LOADING PIPELINE                          │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   STEP 1    │    │   STEP 2    │    │   STEP 3    │    │   STEP 4    │
│   Extract   │───▶│   Filter    │───▶│   Match     │───▶│   Upload    │
│   SQLite    │    │   & Clean   │    │   Files     │    │   Azure     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
 djLibrary_      djTangoSongs_     djSongs_boris    Azure Blob
 boris.json      boris.json           .json         + djSongs.json
```

---

## STEP 1: Extract SQLite Library

### Source
```
Path: /Volumes/EXTVideo1/djImports/boris/Mixxx Database/mixxxdb.sqlite
Size: 32 MB
Type: SQLite 3 database
```

### Script: `extractMixxxSqlite.py` (NEW - TO CREATE)

```python
#!/usr/bin/env python3
"""
Extract BORIS Mixxx library from SQLite to JSON format.
"""

import sqlite3
import json
from pathlib import Path

# Configuration
SQLITE_PATH = "/Volumes/EXTVideo1/djImports/boris/Mixxx Database/mixxxdb.sqlite"
OUTPUT_PATH = "./djLibrary_boris.json"

# Fields to extract (matching existing djLibrary.json schema)
FIELDS = [
    "id",
    "title",
    "artist",
    "album",
    "genre",
    "year",
    "duration",
    "bpm",
    "comment",
    "bitrate",
    "samplerate",
    "channels",
    "key",
    "rating",           # NEW - for quiz prioritization
    "timesplayed",      # NEW - for quiz prioritization
    "last_played_at",   # NEW - for recency
    "datetime_added",
    "location",         # References track_locations table
]

def extract_library():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Join with track_locations to get file paths
    query = """
        SELECT
            l.id, l.title, l.artist, l.album, l.genre, l.year,
            l.duration, l.bpm, l.comment, l.bitrate, l.samplerate,
            l.channels, l.key, l.rating, l.timesplayed, l.last_played_at,
            l.datetime_added, t.location as file_path
        FROM library l
        LEFT JOIN track_locations t ON l.location = t.id
        WHERE l.mixxx_deleted = 0 OR l.mixxx_deleted IS NULL
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    results = []
    for row in rows:
        record = dict(row)
        results.append(record)

    conn.close()

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

    print(f"Extracted {len(results)} tracks to {OUTPUT_PATH}")
    return results

if __name__ == "__main__":
    extract_library()
```

### Output: `djLibrary_boris.json`

```json
[
  {
    "id": 12345,
    "title": "La Cumparsita",
    "artist": "Juan D'Arienzo",
    "album": "El Rey del Compás",
    "genre": "Tango",
    "year": "1937",
    "duration": 180.5,
    "bpm": 132.0,
    "comment": "",
    "bitrate": 320,
    "samplerate": 44100,
    "channels": 2,
    "key": "Am",
    "rating": 5,              // ← NEW
    "timesplayed": 25,        // ← NEW
    "last_played_at": "2025-12-15T20:30:00",  // ← NEW
    "datetime_added": "2024-06-01T10:00:00",
    "file_path": "C:/Users/boris/Music/[Coleccionista]/D'Arienzo/La Cumparsita.mp3"
  },
  // ... ~27,000 tracks
]
```

### Expected Output Size
- Records: ~27,000+
- File size: ~40-50 MB
- Tango-filtered: ~23,000 records

---

## STEP 2: Filter & Clean Metadata

### Script: `djLibrary2Json.py` (EXISTING - UPDATE)

### Changes Needed

```python
# Add source parameter
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--source', choices=['toshi', 'boris'], default='boris')
args = parser.parse_args()

# Set paths based on source
if args.source == 'boris':
    LIBRARY_PATH = "./djLibrary_boris.json"
    OUTPUT_PATH = "./djTangoSongs_boris.json"
else:
    LIBRARY_PATH = "./djLibrary.json"
    OUTPUT_PATH = "./djTangoSongs.json"
```

### Processing Logic (Existing)

```python
# Line 109-113: Genre filtering
valid_genres = ['tango', 'vals', 'waltz', 'milonga', 'marcha']

for record in library:
    genre = record.get('genre', '')
    if not genre or not any(vg in genre.lower() for vg in valid_genres):
        continue  # Skip non-tango
```

### NEW: Add Priority Fields

```python
# Add to output record (after line 165)
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
    "artistMaster": matched_artist,
    "Style1": style1,
    "Alternative": alternative,
    "Candombe": candombe,
    "Cancion": cancion,

    # NEW FIELDS from BORIS
    "rating": record.get('rating', 0),
    "timesplayed": record.get('timesplayed', 0),
    "priorityTier": calculate_priority_tier(record),
})

def calculate_priority_tier(record):
    """A/B/C/D tier based on rating and play count"""
    rating = record.get('rating', 0) or 0
    plays = record.get('timesplayed', 0) or 0

    if rating >= 4 and plays >= 5:
        return "A"
    elif rating >= 3 or plays >= 10:
        return "B"
    elif rating >= 1 or plays >= 1:
        return "C"
    else:
        return "D"
```

### Output: `djTangoSongs_boris.json`

```json
[
  {
    "songID": "550e8400-e29b-41d4-a716-446655440000",
    "djId": 12345,
    "songTitleOriginal": "La Cumparsita",
    "songTitleCleanL1": "La Cumparsita",
    "albumTitleOriginal": "El Rey del Compás",
    "albumTitleCleanL1": "El Rey del Compas",
    "albumTitleCleanL2": "El Rey del Compas",
    "artistOriginal": "Juan D'Arienzo",
    "artistCleanL1": "Juan D'Arienzo",
    "artistCleanL2": "Juan D'Arienzo",
    "artistMaster": "Juan D'Arienzo",
    "Style1": "Tango",
    "Alternative": "N",
    "Candombe": "N",
    "Cancion": "N",
    "rating": 5,
    "timesplayed": 25,
    "priorityTier": "A"
  },
  // ... ~23,000 tango songs
]
```

### Expected Output
- Records: ~23,000 (tango genres only)
- File size: ~15-20 MB
- Tier A songs: ~500
- Tier B songs: ~2,000
- Tier C songs: ~4,000
- Tier D songs: ~16,500

---

## STEP 3: Match MP3 Files & Tag

### Script: `djSongsRawMatch.py` (EXISTING - UPDATE)

### Changes Needed

```python
# Configuration section - make configurable
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--source', choices=['toshi', 'boris'], default='boris')
args = parser.parse_args()

if args.source == 'boris':
    SOURCE_FOLDER = "/Volumes/EXTVideo1/djImports/boris/Music"
    INPUT_FILE = "./djTangoSongs_boris.json"
    OUTPUT_FILE = "./djSongs_boris.json"
    TRACK_LOCATIONS = "./djTrack_locations_boris.json"
else:
    SOURCE_FOLDER = "/Volumes/External SSD 1T/Mixxx"
    INPUT_FILE = "./djTangoSongs.json"
    OUTPUT_FILE = "./djSongs.json"
    TRACK_LOCATIONS = "./djTrack_locations.json"

TARGET_FOLDER = "/Volumes/External SSD 1T/NTTTUpload_boris"
```

### Matching Logic (Existing)

```python
# Line 150-180: File matching algorithm

def match_song_to_file(song, source_folder):
    """
    Match database record to actual MP3 file on disk.
    Uses normalized path matching.
    """
    # Get expected subpath from database location
    db_location = song.get('file_path', '')

    # Normalize: convert Windows path to Mac, lowercase
    subpath = normalize_path(db_location)

    # Search for file in source folder
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file.lower().endswith('.mp3'):
                full_path = os.path.join(root, file)
                if normalize_path(full_path).endswith(subpath):
                    return full_path

    return None
```

### File Operations

```python
# Line 200-240: Copy and tag

def process_matched_song(song, source_path, target_folder):
    """
    1. Generate new filename: {songID}.mp3
    2. Copy to flat target folder
    3. Update ID3 tags with metadata
    """
    song_id = song['songID']
    target_path = os.path.join(target_folder, f"{song_id}.mp3")

    # Copy file
    shutil.copy2(source_path, target_path)

    # Update ID3 tags using mutagen
    audio = MP3(target_path, ID3=ID3)
    audio.tags["TIT2"] = TIT2(encoding=3, text=song['songTitleCleanL1'])
    audio.tags["TALB"] = TALB(encoding=3, text=song['albumTitleCleanL2'])
    audio.tags["TPE1"] = TPE1(encoding=3, text=song['artistMaster'])
    audio.tags["TCON"] = TCON(encoding=3, text=song['Style1'])
    audio.tags["COMM"] = COMM(encoding=3, lang='eng', desc='',
                               text=f"SongID: {song_id}")
    audio.save()

    return target_path
```

### Output: `djSongs_boris.json`

```json
{
  "songs": [
    {
      "SongID": "550e8400-e29b-41d4-a716-446655440000",
      "Title": "La Cumparsita",
      "Orchestra": "Juan D'Arienzo",
      "ArtistMaster": "Juan D'Arienzo",
      "Album": "El Rey del Compas",
      "AudioUrl": "https://namethattangotune.blob.core.windows.net/djsongs/550e8400-e29b-41d4-a716-446655440000.mp3",
      "Style": "Tango",
      "Year": "1937",
      "Alternative": "N",
      "Candombe": "N",
      "Cancion": "N",
      "Singer": "",
      "rating": 5,
      "timesplayed": 25,
      "priorityTier": "A"
    },
    // ... matched songs
  ]
}
```

### File Outputs

```
/Volumes/External SSD 1T/NTTTUpload_boris/
├── 550e8400-e29b-41d4-a716-446655440000.mp3
├── 550e8400-e29b-41d4-a716-446655440001.mp3
├── 550e8400-e29b-41d4-a716-446655440002.mp3
└── ... (~2,000-3,000 MP3 files)

Total size: ~50-80 GB
```

---

## STEP 4: Upload to Azure Blob Storage

### Script: `uploadToAzure.py` (NEW - TO CREATE)

```python
#!/usr/bin/env python3
"""
Upload BORIS MP3 files to Azure Blob Storage.
Idempotent: skips already-uploaded files.
"""

import os
import json
from pathlib import Path
from azure.storage.blob import BlobServiceClient, ContentSettings
from tqdm import tqdm

# Configuration
CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
CONTAINER_NAME = "djsongs"
SOURCE_FOLDER = "/Volumes/External SSD 1T/NTTTUpload_boris"
MANIFEST_FILE = "./djSongs_boris.json"

def get_existing_blobs(container_client):
    """Get set of already-uploaded blob names"""
    existing = set()
    for blob in container_client.list_blobs():
        existing.add(blob.name)
    return existing

def upload_songs():
    # Connect to Azure
    blob_service = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    container = blob_service.get_container_client(CONTAINER_NAME)

    # Get list of songs to upload
    with open(MANIFEST_FILE, 'r') as f:
        manifest = json.load(f)
    songs = manifest.get('songs', manifest)

    # Get already uploaded
    existing = get_existing_blobs(container)
    print(f"Already uploaded: {len(existing)} files")

    # Upload missing files
    uploaded = 0
    skipped = 0
    failed = []

    for song in tqdm(songs, desc="Uploading"):
        song_id = song['SongID']
        blob_name = f"{song_id}.mp3"
        local_path = os.path.join(SOURCE_FOLDER, blob_name)

        # Skip if already uploaded
        if blob_name in existing:
            skipped += 1
            continue

        # Skip if local file missing
        if not os.path.exists(local_path):
            failed.append({'song_id': song_id, 'reason': 'file not found'})
            continue

        try:
            # Upload with content type
            blob_client = container.get_blob_client(blob_name)
            with open(local_path, 'rb') as data:
                blob_client.upload_blob(
                    data,
                    content_settings=ContentSettings(content_type='audio/mpeg'),
                    overwrite=False
                )
            uploaded += 1
        except Exception as e:
            failed.append({'song_id': song_id, 'reason': str(e)})

    # Summary
    print(f"\nUpload complete:")
    print(f"  Uploaded: {uploaded}")
    print(f"  Skipped (existing): {skipped}")
    print(f"  Failed: {len(failed)}")

    if failed:
        with open('upload_failures.json', 'w') as f:
            json.dump(failed, f, indent=2)
        print(f"  Failures logged to upload_failures.json")

if __name__ == "__main__":
    if not CONNECTION_STRING:
        print("ERROR: Set AZURE_STORAGE_CONNECTION_STRING environment variable")
        exit(1)
    upload_songs()
```

### Azure Blob Storage Structure

```
Storage Account: namethattangotune
Endpoint: https://namethattangotune.blob.core.windows.net/

Containers:
├── djsongs/                          (BORIS - PRIMARY)
│   ├── 550e8400-e29b-41d4-a716-446655440000.mp3
│   ├── 550e8400-e29b-41d4-a716-446655440001.mp3
│   └── ... (~3,000 files, ~70GB)
│
└── djsongs-toshi-backup/             (TOSHI - ARCHIVE)
    ├── <existing TOSHI files>
    └── ... (~2,770 files, ~70GB)
```

### Upload Command

```bash
# Set connection string
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=namethattangotune;AccountKey=xxx;EndpointSuffix=core.windows.net"

# Run upload
python uploadToAzure.py
```

### Expected Duration
- Files: ~3,000
- Total size: ~70 GB
- Upload speed: ~50 MB/s (depends on connection)
- Estimated time: 20-30 minutes

---

## STEP 5: Update Frontend Data

### Deploy New `djSongs.json`

```bash
# Copy to frontend public folder
cp djSongs_boris.json /Users/tobybalsley/MyDocs/AppDev/NTTT/FE-POC/public/songData/djSongs.json

# Verify
ls -la /Users/tobybalsley/MyDocs/AppDev/NTTT/FE-POC/public/songData/
```

### Update ArtistMaster.json

Expand to include more artists at level 1-3:

```json
[
  {"artist": "Juan D'Arienzo", "active": "true", "level": "1"},
  {"artist": "Carlos Di Sarli", "active": "true", "level": "1"},
  {"artist": "Osvaldo Pugliese", "active": "true", "level": "1"},
  {"artist": "Aníbal Troilo", "active": "true", "level": "1"},
  {"artist": "Francisco Canaro", "active": "true", "level": "2"},
  {"artist": "Osvaldo Fresedo", "active": "true", "level": "2"},
  {"artist": "Miguel Caló", "active": "true", "level": "2"},
  {"artist": "Rodolfo Biagi", "active": "true", "level": "2"},
  {"artist": "Ricardo Tanturi", "active": "true", "level": "3"},
  {"artist": "Edgardo Donato", "active": "true", "level": "3"},
  // ... more artists
]
```

### Deploy to Azure Static Web Apps

```bash
cd /Users/tobybalsley/MyDocs/AppDev/NTTT/FE-POC
git add public/songData/djSongs.json
git add public/songData/ArtistMaster.json
git commit -m "feat: Update to BORIS data with priority tiers"
git push origin main

# Triggers GitHub Actions → Azure Static Web Apps deployment
```

---

## Complete Command Sequence

```bash
# ===========================================
# BORIS DATA LOADING - FULL EXECUTION
# ===========================================

# Prerequisites
cd /Users/tobybalsley/MyDocs/AppDev/NTTT/MusicImport
pip install azure-storage-blob mutagen tqdm

# Step 0: Backup TOSHI
az storage container create --name djsongs-toshi-backup --account-name namethattangotune
az storage blob copy start-batch --source-container djsongs --destination-container djsongs-toshi-backup --account-name namethattangotune

# Step 1: Extract BORIS SQLite
python extractMixxxSqlite.py
# Output: djLibrary_boris.json (~40MB, ~27,000 tracks)

# Step 2: Filter & Clean
python djLibrary2Json.py --source=boris
# Output: djTangoSongs_boris.json (~15MB, ~23,000 tango songs)

# Step 3: Match Files & Tag
python djSongsRawMatch.py --source=boris
# Output: djSongs_boris.json + /NTTTUpload_boris/*.mp3

# Step 4: Upload to Azure
export AZURE_STORAGE_CONNECTION_STRING="..."
python uploadToAzure.py
# Output: Files in namethattangotune/djsongs/

# Step 5: Update Frontend
cp djSongs_boris.json ../FE-POC/public/songData/djSongs.json
cd ../FE-POC
git add . && git commit -m "feat: BORIS data migration" && git push

# Verify
curl -I "https://namethattangotune.blob.core.windows.net/djsongs/SAMPLE_SONG_ID.mp3"
```

---

## Validation Checklist

### After Step 1 (Extract)
- [ ] `djLibrary_boris.json` created
- [ ] Contains ~27,000 records
- [ ] Has rating and timesplayed fields
- [ ] File paths reference boris Music folder

### After Step 2 (Filter)
- [ ] `djTangoSongs_boris.json` created
- [ ] Contains ~23,000 tango songs
- [ ] Priority tiers calculated (A/B/C/D)
- [ ] ArtistMaster matched

### After Step 3 (Match)
- [ ] `djSongs_boris.json` created
- [ ] `/NTTTUpload_boris/` folder populated
- [ ] MP3 files renamed to {songID}.mp3
- [ ] ID3 tags updated

### After Step 4 (Upload)
- [ ] Files visible in Azure portal
- [ ] URLs accessible: `https://namethattangotune.blob.core.windows.net/djsongs/{id}.mp3`
- [ ] Audio plays in browser

### After Step 5 (Deploy)
- [ ] Frontend loads new djSongs.json
- [ ] Quiz plays BORIS songs
- [ ] No 404 errors on audio

---

## Rollback Procedure

If BORIS has issues, revert to TOSHI:

```bash
# 1. Restore TOSHI djSongs.json
cp djSongs_toshi_backup.json ../FE-POC/public/songData/djSongs.json

# 2. Point to backup container (if songs were deleted)
# Update AudioUrl pattern in djSongs.json:
# FROM: https://namethattangotune.blob.core.windows.net/djsongs/
# TO:   https://namethattangotune.blob.core.windows.net/djsongs-toshi-backup/

# 3. Deploy
cd ../FE-POC && git add . && git commit -m "rollback: Revert to TOSHI data" && git push
```

---

*Created: 2026-02-20*
*Author: Quinn (Cross-Project Coordinator)*
