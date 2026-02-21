# BORIS Data Replacement Plan

## Overview

**REPLACE** (not merge) TOSHI music data with BORIS data in NTTT (Name That Tango Tune). BORIS has cleaner data. Maintain backout strategy to revert if needed.

**New Feature**: User feedback mechanism for reporting incorrect song metadata.

---

## Goals

1. **Replace TOSHI with BORIS** - Full replacement, not merge
2. **Backout Strategy** - Ability to revert to TOSHI if issues found
3. **User Feedback Feature** - Capture reports of incorrect song data

---

## Current State Analysis

### Source Data Locations

| Source | Path | Size | Status |
|--------|------|------|--------|
| TOSHI | `/Volumes/EXTVideo1/djImports/toshi/` | 92GB | Current (has errors) → ARCHIVE |
| BORIS | `/Volumes/EXTVideo1/djImports/boris/` | 98GB | Target (cleaner data) → PRIMARY |

### Key Difference: BORIS has Mixxx Database

```
/Volumes/EXTVideo1/djImports/boris/Mixxx Database/
├── mixxxdb.sqlite          (32MB - full library database)
├── analysis/               (13,318 waveform files)
└── controllers/, effects/  (DJ configs)
```

TOSHI does NOT have this database - the original import used manual exports.

---

## Existing Pipeline (TOSHI)

```
Step 1: djLibrary.json
        └── Exported from Mixxx (manual process, now lost)
        └── 37.7MB, 1.3M lines
                ↓
Step 2: djLibrary2Json.py
        ├── Filters to tango genres only
        ├── Cleans diacritics & special chars
        ├── Matches to ArtistMaster.json
        └── Outputs: djTangoSongs.json (12.9MB)
                ↓
Step 3: djSongsRawMatch.py
        ├── Matches MP3 files on disk to database records
        ├── Copies files to flat folder with {songID}.mp3 naming
        ├── Updates ID3 tags with metadata
        └── Outputs: djSongs.json (70MB, 2,770 songs)
                ↓
Step 4: Upload to Azure (MANUAL - NO SCRIPT)
        └── Target: namethattangotune.blob.core.windows.net/djsongs/
```

### Scripts Location

```
/Users/tobybalsley/MyDocs/AppDev/NTTT/MusicImport/
├── djLibrary2Json.py       (181 lines) - Filter & clean metadata
├── djSongsRawMatch.py      (259 lines) - Match files & copy
├── djExtractMetaDataMP3.py (59 lines)  - Extract MP3 tags
├── ArtistMaster.json       (157 artists)
└── archive/                (8 older reference scripts)
```

---

## BORIS Replacement Plan

### Phase 1: Archive TOSHI (Backout Preparation)

**Goal**: Preserve TOSHI data for rollback capability

**Tasks**:
1. Archive current `djSongs.json` → `djSongs_toshi_backup.json`
2. Create Azure container `djsongs-toshi-backup` or enable blob versioning
3. Document current song count and checksums
4. Create rollback script/procedure

**Backout Strategy**:
```
To rollback:
1. Point app config to djsongs-toshi-backup container
   OR
2. Restore djSongs_toshi.json to djSongs.json
3. Redeploy app
```

### Phase 2: Extract Library from SQLite

**Goal**: Get equivalent of `djLibrary.json` from BORIS's Mixxx database

**Steps**:
1. Connect to `/Volumes/EXTVideo1/djImports/boris/Mixxx Database/mixxxdb.sqlite`
2. Query library table for all tracks
3. Export to `djLibrary_boris.json` matching existing schema

**New Script Needed**: `extractMixxxSqlite.py`

```python
# Schema mapping needed:
# SQLite table: library
# Fields: id, title, artist, album, genre, duration, bpm, year,
#         location, bitrate, channels, samplerate, comment
```

### Phase 3: Update Processing Scripts

**Goal**: Adapt existing scripts for BORIS paths

**Changes to djLibrary2Json.py**:
- Add config for input/output file paths
- Parameter: `--source=boris|toshi`
- Output: `djTangoSongs_boris.json`

**Changes to djSongsRawMatch.py**:
- Update `SOURCE_FOLDER` to BORIS path
- Update `TARGET_FOLDER` for new upload batch
- Output: `djSongs_boris.json`

### Phase 4: Azure Upload Script

**Goal**: Automate Azure Blob upload (currently manual)

**New Script Needed**: `uploadToAzure.py`

```python
# Using azure-storage-blob SDK
# Config: Connection string from env var
# Target: namethattangotune.blob.core.windows.net/djsongs/
# Process:
#   1. Read djSongs_boris.json
#   2. For each song, upload {songID}.mp3
#   3. Verify upload success
#   4. Log progress
```

### Phase 5: Deploy & Cutover

**Goal**: Replace TOSHI with BORIS in production

**Steps**:
1. Upload BORIS songs to Azure (new container or replace)
2. Update app config to point to BORIS data
3. Deploy updated app
4. Verify quiz functionality
5. Monitor for issues

---

## NEW FEATURE: User Feedback for Incorrect Songs

### Purpose

Allow users to report when song metadata (orchestra, title, year, etc.) appears incorrect. Capture feedback for research and correction.

### User Interface

During or after a quiz question, user can:
1. Click "Report Incorrect Info" button
2. Select reason from dropdown:
   - Wrong Orchestra
   - Wrong Title
   - Wrong Year
   - Wrong Singer
   - Wrong Style (Tango/Vals/Milonga)
   - Duplicate Song
   - Other
3. Optional: Enter free-text details/correction suggestion
4. Submit feedback

### Data Model

```json
{
  "feedbackId": "uuid",
  "songId": "uuid",
  "timestamp": "ISO-8601",
  "reason": "Wrong Orchestra",
  "reasonCode": "WRONG_ORCHESTRA",
  "userComment": "This is actually Troilo, not D'Arienzo",
  "status": "pending",
  "reviewed": false,
  "resolution": null
}
```

### Reason Codes (Dropdown)

| Code | Label |
|------|-------|
| `WRONG_ORCHESTRA` | Wrong Orchestra |
| `WRONG_TITLE` | Wrong Title |
| `WRONG_YEAR` | Wrong Year |
| `WRONG_SINGER` | Wrong Singer |
| `WRONG_STYLE` | Wrong Style |
| `DUPLICATE` | Duplicate Song |
| `AUDIO_ISSUE` | Audio Quality/Wrong File |
| `OTHER` | Other (specify below) |

### Storage

- Store feedback in Azure Table Storage or Cosmos DB
- Or simple JSON file for MVP: `feedback.json`

### Admin Review

- List all pending feedback
- View song details + user feedback
- Mark as: Verified, Invalid, Fixed
- Apply corrections to master data

---

## Azure Resources

**Storage Account**: `namethattangotune`

| Container | Purpose |
|-----------|---------|
| `djsongs` | Primary song files (BORIS after cutover) |
| `djsongs-toshi-backup` | TOSHI backup for rollback |
| `feedback` | User feedback data (or Table Storage) |

**URL Pattern**: `https://namethattangotune.blob.core.windows.net/djsongs/{songID}.mp3`

**Web App**: Azure Static Web Apps (see `.github/workflows/`)

---

## Deliverables

### Data Pipeline
1. **New Script**: `extractMixxxSqlite.py` - Extract BORIS library from SQLite
2. **Updated Script**: `djLibrary2Json.py` - Add source parameter
3. **Updated Script**: `djSongsRawMatch.py` - Configurable paths
4. **New Script**: `uploadToAzure.py` - Automate blob upload
5. **Data File**: `djSongs_boris.json` - BORIS song inventory
6. **Backup**: `djSongs_toshi_backup.json` + Azure backup container

### User Feedback Feature
7. **UI Component**: "Report Incorrect" button + modal
8. **API/Storage**: Feedback capture endpoint
9. **Admin View**: Review pending feedback
10. **Documentation**: Updated README

---

## Dependencies

- Python 3.x
- `mutagen` - MP3 tag reading/writing
- `azure-storage-blob` - Azure upload
- `sqlite3` - Mixxx database access
- Access to EXTVideo1 external drive
- Azure storage credentials

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| BORIS has different errors than TOSHI | User feedback feature captures issues |
| Rollback needed | TOSHI backup container + documented procedure |
| Azure credentials expired | Check/refresh before upload |
| Large upload time (~100GB) | Batch upload with progress tracking |
| Missing MP3 files | Log mismatches, don't fail entire job |

---

## JIRA Ticket

**Project**: NTTT
**Ticket**: [NTTT-1](https://hdtsllc.atlassian.net/browse/NTTT-1)
**Title**: Replace TOSHI Data with BORIS + Add User Feedback Feature

---

## Next Steps

1. [x] Create JIRA project and ticket
2. [ ] Verify EXTVideo1 drive is connected
3. [ ] Examine BORIS SQLite schema
4. [ ] Archive TOSHI data (backout prep)
5. [ ] Create extractMixxxSqlite.py script
6. [ ] Test extraction on small subset
7. [ ] Full pipeline run
8. [ ] Implement user feedback UI
9. [ ] Deploy and cutover

---

*Created: 2026-02-20*
*Updated: 2026-02-20 - Changed from merge to replace strategy, added user feedback feature*
*Author: Quinn (Cross-Project Coordinator)*
