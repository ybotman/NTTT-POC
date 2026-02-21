# SQLite Field Analysis: TOSHI vs BORIS

## Summary

Both TOSHI and BORIS have the same fields, but **BORIS has significantly more curated data** (ratings, play counts).

---

## Field Comparison

### Fields Used by Current Pipeline

| Field | TOSHI | BORIS | Current Usage |
|-------|-------|-------|---------------|
| `genre` | Yes | Yes | **Used** - filter tango/vals/milonga |
| `title` | Yes | Yes | **Used** - song title |
| `artist` | Yes | Yes | **Used** - orchestra name |
| `album` | Yes | Yes | **Used** - album for UUID generation |
| `rating` | Yes (sparse) | Yes (rich) | **NOT USED** - should be! |
| `timesplayed` | Yes (sparse) | Yes (rich) | **NOT USED** - should be! |

### Rating Distribution

| Rating | TOSHI | BORIS |
|--------|-------|-------|
| 5 stars | 4 | 783 |
| 4 stars | 26 | 2,260 |
| 3 stars | 214 | 2,311 |
| 2 stars | 1 | 737 |
| 1 star | 0 | 171 |
| 0 (unrated) | 25,733 | 21,186 |
| **Total Rated** | **245** | **6,262** |

**BORIS has 25x more rated songs!**

### Play Count Distribution

| Metric | TOSHI | BORIS |
|--------|-------|-------|
| Songs with plays > 0 | 1,750 | ~2,000+ |
| Max play count | 50 | 52 |
| Songs played 10+ times | ~100 | ~500+ |

---

## Genre Values for Style Classification

### Primary Genres (Use These)

| Genre | Count | Style1 |
|-------|-------|--------|
| `Tango` | 17,549 | Tango |
| `Argentine Tango` | 2,025 | Tango |
| `Vals` | 1,984 | Vals |
| `Milonga` | 1,319 | Milonga |

### Secondary Genres (Include with flags)

| Genre | Count | Style1 | Flag |
|-------|-------|--------|------|
| `Alt Tango` | 142 | Tango | Alternative=Y |
| `Neotango` | 144 | Tango | Alternative=Y |
| `NeoTango` | 112 | Tango | Alternative=Y |
| `Tango Canción` | 44 | Tango | Cancion=Y |
| `Tantrad` | 48 | Tango | - |

### Exclude from Quiz

| Genre | Count | Reason |
|-------|-------|--------|
| `Cortina` | 661 | Not dance music - DJ transitions |
| `Foxtrot` | 213 | Not tango |
| `Pasodoble` | 142 | Not tango |
| Other non-tango | ~1,000 | Various |

---

## Recommended Fields for Quiz Prioritization

### Priority Score Algorithm

```python
def calculate_priority(song):
    """Higher score = show more often in quiz"""
    score = 0

    # Rating boost (0-5 stars)
    score += song['rating'] * 20  # Max +100

    # Play count boost (capped)
    plays = min(song['timesplayed'], 20)
    score += plays * 5  # Max +100

    # Style bonus (traditional tango more likely correct)
    if song['genre'] == 'Tango':
        score += 10

    # Penalty for alternative/neo
    if 'alt' in song['genre'].lower() or 'neo' in song['genre'].lower():
        score -= 20  # Less certain metadata

    return score
```

### Priority Tiers

| Tier | Criteria | Est. Songs | Quiz Weight |
|------|----------|------------|-------------|
| **A** | Rating >= 4 AND timesplayed >= 5 | ~500 | 40% |
| **B** | Rating >= 3 OR timesplayed >= 10 | ~2,000 | 35% |
| **C** | Any rated OR any plays | ~4,000 | 20% |
| **D** | Unrated, never played | ~16,000 | 5% |

---

## High-Value Quiz Candidates

### BORIS: Top Rated + Most Played (Rating=5, Plays>10)

| Artist | Title | Genre | Rating | Plays |
|--------|-------|-------|--------|-------|
| Osvaldo Fresedo - Roberto Ray | Telon | Tango | 5 | 33 |
| Miguel Caló - Raúl Berón | El vals sonador | Vals | 5 | 32 |
| Carlos Di Sarli Sextet | Soy Un Arlequin | Tango | 5 | 30 |
| Osvaldo Pugliese | Emancipación | Tango | 5 | 29 |
| Francisco Lomuto - Jorge Omar | Qué tiempo aquel | Milonga | 5 | 25 |
| Edgardo Donato - Horacio Lagos | Sinsabor | Tango | 5 | 22 |

### Tango-Only High Quality Count

| Filter | Count |
|--------|-------|
| All tango genres | 23,367 |
| Rated 4-5 stars | 2,655 |
| Played 5+ times | 412 |
| **Rating >= 4 OR Plays >= 5** | **2,660** |

---

## New Fields to Extract from BORIS

Add these to `extractMixxxSqlite.py`:

```python
FIELDS_TO_EXTRACT = [
    # Existing
    'id', 'title', 'artist', 'album', 'genre', 'year',
    'duration', 'bpm', 'comment', 'location',

    # NEW - for quiz prioritization
    'rating',           # 0-5 stars
    'timesplayed',      # play count
    'last_played_at',   # recent = more relevant

    # Useful metadata
    'key',              # musical key
    'datetime_added',   # when added to library
    'album_artist',     # sometimes different from artist
]
```

---

## Schema for Quiz Song Selection

```json
{
  "songId": "uuid",
  "title": "La Cumparsita",
  "artist": "Juan D'Arienzo",
  "album": "El Rey del Compás",
  "genre": "Tango",
  "style": "Tango",
  "year": "1937",

  "rating": 5,
  "timesplayed": 25,
  "priorityScore": 175,
  "priorityTier": "A",

  "audioUrl": "https://...",
  "flags": {
    "alternative": false,
    "candombe": false,
    "cancion": false
  }
}
```

---

## Recommendations

1. **Extract rating + timesplayed from BORIS** - Much richer than TOSHI
2. **Add priorityScore field** - Weight quiz selection
3. **Exclude Cortinas** - Not dance music
4. **Normalize genre values** - Map variants to standard styles
5. **Flag low-confidence songs** - Neo/Alt less certain metadata

---

*Created: 2026-02-20*
*Author: Quinn (Cross-Project Coordinator)*
