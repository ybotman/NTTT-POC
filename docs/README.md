# NTTT v2.0 Documentation

## Quick Links

| Document | Purpose |
|----------|---------|
| [JIRA-TICKETS.md](./JIRA-TICKETS.md) | All tickets with execution order |
| [BORIS-DATA-LOADING-PATH.md](./BORIS-DATA-LOADING-PATH.md) | End-to-end data pipeline (deep dive) |
| [BORIS-MIGRATION-PLAN.md](./BORIS-MIGRATION-PLAN.md) | High-level migration plan |
| [BORIS-READINESS-ASSESSMENT.md](./BORIS-READINESS-ASSESSMENT.md) | Gap analysis & scorecard |
| [SQLITE-FIELD-ANALYSIS.md](./SQLITE-FIELD-ANALYSIS.md) | BORIS fields for prioritization |
| [QUIZ-ANALYTICS-SCHEMA.md](./QUIZ-ANALYTICS-SCHEMA.md) | Quiz tracking schema |

## Handoffs

Session handoffs are in `handoffs/` directory. Read the latest one to resume.

```bash
ls -t handoffs/*.md | head -1 | xargs cat
```

## Project Structure

```
/Users/tobybalsley/MyDocs/AppDev/NTTT/
├── FE-POC/              # Original v1.0 (frozen reference)
├── NTTT-app/            # New v2.0 app
├── MusicImport/         # Data pipeline scripts
│   ├── extractMixxxSqlite.py    # Step 1: SQLite → JSON
│   ├── djLibrary2Json_v2.py     # Step 2: Filter + priority
│   ├── djSongsRawMatch_v2.py    # Step 3: Match files
│   ├── uploadToAzure_v2.py      # Step 4: Upload to Azure
│   └── spotcheck_v2.py          # Validation tool
└── docs/                # This folder
```

## Azure Resources

| Resource | Value |
|----------|-------|
| Storage Account | `nttt` |
| Resource Group | `tangotiempo` |
| Container | `v20` (version 2.0) |
| Public URL | `https://nttt.blob.core.windows.net/v20/{songID}.mp3` |

## Data Flow

```
BORIS SQLite → extractMixxxSqlite.py → djLibrary_boris.json
                                              ↓
                     djLibrary2Json_v2.py → djTangoSongs_boris.json
                                              ↓
                     djSongsRawMatch_v2.py → djSongs_boris.json + MP3 copies
                                              ↓
                     uploadToAzure_v2.py → Azure Blob (nttt/v20/)
```

## Current Status

- ✅ Step 1-3: Data extracted, filtered, matched
- ⏳ Step 4: Upload blocked (permissions - use --auth-mode key)
- 📊 27,447 tracks → 23,799 tango songs → 6,894 matchable MP3s

## Next Session

1. Fix upload permissions (`--auth-mode key`)
2. Run full upload
3. Update app to use new Azure URLs
4. Add top 50 artists to ArtistMaster.json

---

*Last updated: 2026-02-21*
