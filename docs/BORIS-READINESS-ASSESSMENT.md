# BORIS Migration Readiness Assessment

## Executive Summary

**Overall Readiness: 65%** - Core data pipeline exists, but gaps in automation, backend, and app features.

---

## Readiness Scorecard

| Area | Score | Status | Blocker? |
|------|-------|--------|----------|
| **Data Pipeline Scripts** | 80% | Exists, needs update | No |
| **Azure Upload Automation** | 0% | Missing script | **YES** |
| **TOSHI Backup Strategy** | 0% | No backup container | **YES** |
| **Frontend App** | 60% | Works, needs improvements | No |
| **Firebase Auth** | 0% | Not integrated | No (Phase 2) |
| **Backend API** | 0% | Doesn't exist | No (Phase 2) |
| **User Feedback** | 0% | Not implemented | No (Phase 2) |
| **Analytics/Tracking** | 0% | Not implemented | No (Phase 2) |

---

## Phase 1: BORIS Data Migration (BLOCKERS)

### ✅ READY: Data Extraction Scripts

| Script | Status | Gap |
|--------|--------|-----|
| `djLibrary2Json.py` | ✅ Exists | Add `--source` param |
| `djSongsRawMatch.py` | ✅ Exists | Add configurable paths |
| `ArtistMaster.json` | ✅ Exists | May need expansion |

### ❌ BLOCKER: SQLite Extraction

| Item | Status | Action |
|------|--------|--------|
| `extractMixxxSqlite.py` | ❌ Missing | Create new script |
| BORIS SQLite schema | ✅ Analyzed | 23,367 tango songs available |
| Fields: rating, timesplayed | ✅ Available | Include in extraction |

### ❌ BLOCKER: Azure Upload Automation

| Item | Status | Action |
|------|--------|--------|
| `uploadToAzure.py` | ❌ Missing | Create new script |
| Azure SDK (`azure-storage-blob`) | ❌ Not installed | Add to requirements |
| Connection string | ⚠️ Manual | Store in env var |

### ❌ BLOCKER: Backup Strategy

| Item | Status | Action |
|------|--------|--------|
| `djsongs-toshi-backup` container | ❌ Doesn't exist | Create in Azure |
| TOSHI data archive | ❌ Not done | Copy before replacing |
| Rollback procedure | ❌ Not documented | Document steps |

---

## Phase 2: App Improvements

### Frontend Gaps (FE-POC)

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| Only 2 active artists (level=1) | Critical | Low | P0 |
| No Firebase Auth | High | Medium | P1 |
| No progress indicator | Medium | Low | P1 |
| No keyboard navigation | Medium | Low | P2 |
| No error handling | Medium | Low | P1 |
| No loading states | Medium | Low | P1 |
| No score persistence | Medium | Low | P2 |
| Hardcoded data paths | Medium | Low | P1 |
| No question type variety | Medium | High | P2 |

### Backend Gaps

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| No backend API exists | Critical | High | P1 |
| No database for analytics | High | Medium | P1 |
| No feedback storage | High | Medium | P1 |
| No user tracking | Medium | Medium | P2 |

### Cross-Platform Gaps

| Gap | Impact | Action |
|-----|--------|--------|
| Firebase not integrated | High | Share Firebase project with TangoTiempo |
| No shared visitorId | Medium | Reuse `visitorTracking.js` |
| No CrossPlatformUserPrefs | Medium | Add collection to shared MongoDB |
| appId not defined | Low | Assign appId=3 for NTTT |

---

## App Improvement Suggestions

### UI/UX Improvements

1. **Visual Timer** - Replace text timer with animated countdown circle
2. **Progress Bar** - Show "Question 3 of 10"
3. **Answer Animations** - Fade/slide transitions when revealing correct answer
4. **Sound Effects** - Ding for correct, buzz for wrong
5. **Streak Display** - Show consecutive correct answers
6. **Difficulty Indicator** - Show song difficulty tier (A/B/C/D)

### Quiz Logic Improvements

1. **Expand Artist Pool** - Enable level=2 and level=3 artists
2. **Question Types** - Add title, year, style, singer questions
3. **Smart Distractors** - Use orchestra attributes for similar-sounding options
4. **Adaptive Difficulty** - Adjust based on user performance
5. **Priority Weighting** - Show high-rated songs more often

### Data Quality

1. **Clean ArtistMaster** - Many songs missing ArtistMaster field
2. **Add Rating/Timesplayed** - Use BORIS fields for prioritization
3. **Validate AudioUrls** - Check all URLs resolve before quiz

### Technical Improvements

1. **Environment Config** - Move paths to `.env.local`
2. **Error Boundaries** - Catch and display errors gracefully
3. **Code Splitting** - Lazy load components
4. **TypeScript** - Add type safety
5. **Unit Tests** - Add Jest tests for quiz logic

---

## Migration Execution Plan

### Week 1: Foundation (BLOCKERS)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Create `djsongs-toshi-backup` container | Azure container |
| 1 | Copy TOSHI data to backup | Backup complete |
| 2 | Create `extractMixxxSqlite.py` | Working script |
| 2 | Test SQLite extraction | `djLibrary_boris.json` |
| 3 | Update `djLibrary2Json.py` | `--source` param |
| 3 | Update `djSongsRawMatch.py` | Configurable paths |
| 4 | Create `uploadToAzure.py` | Working script |
| 4 | Test upload on small batch | 100 songs uploaded |
| 5 | Full BORIS extraction | `djSongs_boris.json` |
| 5 | Full Azure upload | All BORIS songs in Azure |

### Week 2: Frontend Fixes

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Update data paths to env vars | Config-driven |
| 1 | Expand artist pool (level 1-3) | More quiz variety |
| 2 | Add loading states | Spinner while loading |
| 2 | Add error handling | User-friendly errors |
| 3 | Add progress indicator | "Song X of N" |
| 3 | Add keyboard navigation | Arrow keys + Enter |
| 4 | Add visual timer | Countdown circle |
| 5 | Test full quiz flow | Working app |

### Week 3: Firebase Auth + Backend

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Integrate Firebase Auth | Login/logout working |
| 3-4 | Create backend API skeleton | Express.js or Azure Functions |
| 5 | Deploy backend to Azure | API endpoints live |

### Week 4: Analytics & Feedback

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Implement quiz answer tracking | Answers stored |
| 3-4 | Implement user feedback UI | Report button working |
| 5 | Connect to shared MongoDB | Cross-platform ready |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| BORIS SQLite schema differs | Low | Medium | Examine schema first |
| Azure upload fails mid-batch | Medium | Low | Idempotent upload script |
| Audio URLs broken | Low | High | Validate URLs before deploy |
| User data loss on rollback | Low | High | Test rollback procedure |
| Firebase integration issues | Low | Medium | Use same project as TangoTiempo |

---

## Success Criteria

### Phase 1 Complete When:
- [ ] TOSHI data backed up to `djsongs-toshi-backup`
- [ ] BORIS songs extracted and processed
- [ ] All BORIS MP3s uploaded to Azure
- [ ] Frontend loads and plays BORIS songs
- [ ] Quiz functions correctly with BORIS data

### Phase 2 Complete When:
- [ ] Firebase Auth integrated (shared with TangoTiempo)
- [ ] User feedback captured and stored
- [ ] Quiz answers tracked with response times
- [ ] Song difficulty analytics calculated
- [ ] Cross-platform user prefs working

---

*Created: 2026-02-20*
*Author: Quinn (Cross-Project Coordinator)*
