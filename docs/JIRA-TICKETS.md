# NTTT JIRA Tickets

**Project**: [NTTT](https://hdtsllc.atlassian.net/browse/NTTT)
**Created**: 2026-02-20

---

## Phase 1: Data Pipeline (BLOCKERS)

| Ticket | Summary | Labels |
|--------|---------|--------|
| [NTTT-1](https://hdtsllc.atlassian.net/browse/NTTT-1) | Replace TOSHI with BORIS + User Feedback (Epic) | data-migration, azure |
| [NTTT-2](https://hdtsllc.atlassian.net/browse/NTTT-2) | Create extractMixxxSqlite.py - Include rating/timesplayed | data-pipeline, sqlite |
| [NTTT-5](https://hdtsllc.atlassian.net/browse/NTTT-5) | Create uploadToAzure.py - Automate blob upload | azure, data-pipeline |
| [NTTT-6](https://hdtsllc.atlassian.net/browse/NTTT-6) | Archive TOSHI data - Backout strategy | backout, azure |
| [NTTT-10](https://hdtsllc.atlassian.net/browse/NTTT-10) | [BLOCKER] Create extractMixxxSqlite.py - Extract BORIS | blocker, data-pipeline |
| [NTTT-11](https://hdtsllc.atlassian.net/browse/NTTT-11) | [BLOCKER] Create TOSHI backup container | blocker, azure |

## Phase 2: Quiz Logic & Prioritization

| Ticket | Summary | Labels |
|--------|---------|--------|
| [NTTT-3](https://hdtsllc.atlassian.net/browse/NTTT-3) | Quiz song prioritization using rating + timesplayed | quiz-logic, prioritization |
| [NTTT-14](https://hdtsllc.atlassian.net/browse/NTTT-14) | Expand artist pool - enable level 2 and 3 artists | data, quiz-logic |

## Phase 3: User Feedback & Analytics

| Ticket | Summary | Labels |
|--------|---------|--------|
| [NTTT-4](https://hdtsllc.atlassian.net/browse/NTTT-4) | User feedback - Flag incorrect song metadata | user-feedback, ui |
| [NTTT-7](https://hdtsllc.atlassian.net/browse/NTTT-7) | Quiz answer tracking (correct/wrong + speed) | analytics, tracking |
| [NTTT-8](https://hdtsllc.atlassian.net/browse/NTTT-8) | Song difficulty analytics - find data issues | analytics, data-quality |
| [NTTT-9](https://hdtsllc.atlassian.net/browse/NTTT-9) | Cross-platform TangoTiempo integration (upsell/ads) | cross-platform, tangotiempo |

## Phase 4: App Improvements

| Ticket | Summary | Labels |
|--------|---------|--------|
| [NTTT-12](https://hdtsllc.atlassian.net/browse/NTTT-12) | Mobile-friendly responsive UI redesign | ui, mobile, priority |
| [NTTT-13](https://hdtsllc.atlassian.net/browse/NTTT-13) | Integrate Firebase Auth - shared across tango apps | auth, cross-platform |
| [NTTT-15](https://hdtsllc.atlassian.net/browse/NTTT-15) | Add progress indicator - Song X of N | ui, ux |
| [NTTT-16](https://hdtsllc.atlassian.net/browse/NTTT-16) | Add visual countdown timer | ui, ux |
| [NTTT-17](https://hdtsllc.atlassian.net/browse/NTTT-17) | Add error handling and loading states | frontend, reliability |
| [NTTT-18](https://hdtsllc.atlassian.net/browse/NTTT-18) | Environment configuration - remove hardcoded paths | technical, config |
| [NTTT-19](https://hdtsllc.atlassian.net/browse/NTTT-19) | Add keyboard navigation for answers | accessibility, ux |
| [NTTT-20](https://hdtsllc.atlassian.net/browse/NTTT-20) | Create backend API - Azure Functions or App Service | backend, azure |

## Phase 5: DevOps & Infrastructure

| Ticket | Summary | Labels |
|--------|---------|--------|
| NTTT-21 | Git branch strategy - localhost/DEV/TEST/PROD | devops, git |
| NTTT-22 | DEV/TEST point to PROD Azure (no file updates) | devops, azure |
| NTTT-23 | Architecture decision: Analytics storage (Firebase vs MongoDB) | architecture, decision |
| NTTT-24 | Session metrics tracking (v2.0.0 MVP) | analytics, mvp |
| NTTT-25 | User action logging - sharing, social, quiz answers | analytics, tracking |

---

## Architecture Decision: Analytics Storage (NTTT-23)

**Options:**

| Option | Pros | Cons |
|--------|------|------|
| **Firebase** | Already using Auth, real-time sync, free tier, easy setup | Vendor lock-in, query limits |
| **MongoDB Atlas** | Flexible schema, powerful queries, good free tier | Additional service to manage |

**Data to capture:**
- Session metrics (start, end, duration, songs played)
- Quiz answers (correct/wrong, response time)
- User actions (sharing, social clicks)
- Song difficulty analytics

**Recommendation:** Start with **Firebase Firestore** for v2.0.0 since we already have Firebase Auth. Migrate to MongoDB later if query needs grow.

---

## Execution Order

### Week 1: Data Migration
1. NTTT-10 ✅ extractMixxxSqlite.py (DONE)
2. NTTT-11 Archive TOSHI to backup container
3. NTTT-2 ✅ Filter with rating/timesplayed (DONE)
4. NTTT-5 ✅ Upload to Azure (5,496 rated/played songs)
5. NTTT-6 Document rollback procedure
6. NTTT-21 Git branch setup (localhost/DEV/TEST/PROD)
7. NTTT-22 Configure DEV/TEST → PROD Azure

### Week 2: App Fixes
1. NTTT-18 Environment config
2. NTTT-14 Expand artist pool
3. NTTT-17 Error handling
4. NTTT-15 Progress indicator
5. NTTT-12 Mobile UI

### Week 3: Auth & Backend
1. NTTT-13 Firebase Auth
2. NTTT-20 Backend API
3. NTTT-4 User feedback UI

### Week 4: Analytics
1. NTTT-7 Quiz tracking
2. NTTT-8 Song difficulty
3. NTTT-3 Priority scoring
4. NTTT-9 Cross-platform

---

*Updated: 2026-02-21*
