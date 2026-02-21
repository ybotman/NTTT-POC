# NTTT Quiz Analytics Schema

## Overview

Track user quiz performance to:
1. Measure individual progress (correct/wrong, speed)
2. Identify difficult songs/orchestras (system-wide patterns)
3. Cross-reference with user feedback to find data quality issues
4. Enable cross-platform upsell/engagement with TangoTiempo

---

## User Identification (Shared with TangoTiempo)

Reuse TangoTiempo's tracking system:

| ID Type | Storage | Scope |
|---------|---------|-------|
| `visitorId` | Cookie (UUID v4) | Anonymous, persistent 365 days |
| `firebaseUserId` | Firebase Auth | Authenticated users |
| `appId` | Config | `3` = NTTT (vs `1`=TangoTiempo, `2`=HarmonyJunction) |

**Cross-Platform Link**: Same Firebase UID across apps enables:
- "You got 8/10 on D'Arienzo - see D'Arienzo events near you on TangoTiempo!"
- Shared user preferences (home location, favorite orchestras)

---

## Quiz Answer Tracking

### Collection: `NTTTQuizAnswers`

Records every answer for detailed analytics.

```json
{
  "_id": "ObjectId",

  // User identification
  "visitorId": "uuid-v4",
  "firebaseUserId": "firebase-uid or null",
  "appId": "3",

  // Session tracking
  "sessionId": "uuid-v4",
  "questionNumber": 5,

  // Question details
  "songId": "uuid-v5",
  "questionType": "orchestra",  // orchestra | title | year | style | singer
  "correctAnswer": "Juan D'Arienzo",
  "options": ["Juan D'Arienzo", "Carlos Di Sarli", "Osvaldo Pugliese", "Aníbal Troilo"],

  // User response
  "userAnswer": "Carlos Di Sarli",
  "isCorrect": false,
  "responseTimeMs": 4250,

  // Song metadata (denormalized for analytics)
  "songTitle": "La Cumparsita",
  "songOrchestra": "Juan D'Arienzo",
  "songYear": "1937",
  "songStyle": "Tango",
  "songRating": 5,
  "songTimesplayed": 25,
  "songPriorityTier": "A",

  // Context
  "timestamp": "2026-02-20T20:30:00Z",
  "deviceType": "mobile",
  "userAgent": "...",

  "createdAt": "ISODate"
}
```

### Indexes for QuizAnswers

```javascript
// User history queries
db.NTTTQuizAnswers.createIndex({ visitorId: 1, timestamp: -1 });
db.NTTTQuizAnswers.createIndex({ firebaseUserId: 1, timestamp: -1 });

// Session reconstruction
db.NTTTQuizAnswers.createIndex({ sessionId: 1, questionNumber: 1 });

// Song difficulty analysis
db.NTTTQuizAnswers.createIndex({ songId: 1, isCorrect: 1 });
db.NTTTQuizAnswers.createIndex({ songOrchestra: 1, isCorrect: 1 });

// Question type analysis
db.NTTTQuizAnswers.createIndex({ questionType: 1, isCorrect: 1 });

// Speed analysis
db.NTTTQuizAnswers.createIndex({ responseTimeMs: 1 });

// TTL - auto-delete after 2 years
db.NTTTQuizAnswers.createIndex({ createdAt: 1 }, { expireAfterSeconds: 63072000 });
```

---

## User Performance Analytics

### Collection: `NTTTUserAnalytics`

Aggregated stats per user (updated after each session).

```json
{
  "_id": "ObjectId",

  // User identification
  "visitorId": "uuid-v4",
  "firebaseUserId": "firebase-uid or null",

  // Overall stats
  "totalQuestions": 250,
  "totalCorrect": 175,
  "totalWrong": 75,
  "overallAccuracy": 0.70,

  // Speed stats
  "avgResponseTimeMs": 3500,
  "fastestResponseMs": 850,
  "slowestResponseMs": 15000,

  // Performance by question type
  "byQuestionType": {
    "orchestra": { "total": 100, "correct": 80, "accuracy": 0.80, "avgTimeMs": 3200 },
    "title": { "total": 50, "correct": 30, "accuracy": 0.60, "avgTimeMs": 4500 },
    "year": { "total": 40, "correct": 20, "accuracy": 0.50, "avgTimeMs": 5000 },
    "style": { "total": 40, "correct": 35, "accuracy": 0.875, "avgTimeMs": 2500 },
    "singer": { "total": 20, "correct": 10, "accuracy": 0.50, "avgTimeMs": 4000 }
  },

  // Performance by orchestra (top 20 most answered)
  "byOrchestra": [
    { "orchestra": "Juan D'Arienzo", "total": 30, "correct": 28, "accuracy": 0.93 },
    { "orchestra": "Carlos Di Sarli", "total": 25, "correct": 20, "accuracy": 0.80 },
    { "orchestra": "Osvaldo Pugliese", "total": 20, "correct": 12, "accuracy": 0.60 }
  ],

  // Performance by style
  "byStyle": {
    "Tango": { "total": 180, "correct": 130, "accuracy": 0.72 },
    "Vals": { "total": 40, "correct": 28, "accuracy": 0.70 },
    "Milonga": { "total": 30, "correct": 17, "accuracy": 0.57 }
  },

  // Session history
  "totalSessions": 15,
  "lastSessionAt": "ISODate",
  "firstSessionAt": "ISODate",

  // Streaks
  "currentStreak": 5,
  "longestStreak": 12,
  "lastCorrectAt": "ISODate",

  // Cross-platform (for TangoTiempo upsell)
  "favoriteOrchestras": ["Juan D'Arienzo", "Carlos Di Sarli"],
  "weakOrchestras": ["Francisco Canaro", "Rodolfo Biagi"],
  "tangoTiempoLinked": true,

  "createdAt": "ISODate",
  "updatedAt": "ISODate"
}
```

---

## Song Difficulty Analytics

### Collection: `NTTTSongAnalytics`

Track which songs are consistently hard/easy (regardless of data quality).

```json
{
  "_id": "ObjectId",

  // Song identification
  "songId": "uuid-v5",
  "songTitle": "La Cumparsita",
  "songOrchestra": "Juan D'Arienzo",
  "songYear": "1937",
  "songStyle": "Tango",

  // Overall difficulty
  "totalAnswers": 500,
  "totalCorrect": 450,
  "totalWrong": 50,
  "accuracy": 0.90,
  "difficultyScore": 10,  // 0-100, higher = harder

  // Speed analysis
  "avgResponseTimeMs": 2800,
  "medianResponseTimeMs": 2500,

  // Difficulty by question type
  "byQuestionType": {
    "orchestra": { "total": 200, "correct": 190, "accuracy": 0.95 },
    "title": { "total": 150, "correct": 120, "accuracy": 0.80 },
    "year": { "total": 100, "correct": 90, "accuracy": 0.90 },
    "singer": { "total": 50, "correct": 50, "accuracy": 1.00 }
  },

  // Common wrong answers (for potential data issues)
  "commonWrongAnswers": [
    { "answer": "Carlos Di Sarli", "count": 25, "percentage": 0.50 },
    { "answer": "Aníbal Troilo", "count": 15, "percentage": 0.30 }
  ],

  // User feedback correlation
  "feedbackCount": 3,
  "feedbackReasons": ["Wrong Orchestra", "Wrong Year"],
  "flaggedForReview": true,

  // Trending
  "recentAccuracy": 0.85,  // Last 50 answers
  "accuracyTrend": "declining",  // stable | improving | declining

  "createdAt": "ISODate",
  "updatedAt": "ISODate"
}
```

### Difficulty Score Algorithm

```python
def calculate_difficulty_score(song):
    """
    0-100 scale where higher = harder
    """
    base_score = (1 - song['accuracy']) * 100

    # Adjust for sample size (low samples = less confident)
    confidence = min(song['totalAnswers'] / 100, 1.0)

    # Adjust for response time (slower = harder)
    time_factor = min(song['avgResponseTimeMs'] / 10000, 1.0) * 10

    # Combine
    score = (base_score * confidence) + time_factor

    return min(max(score, 0), 100)
```

---

## Orchestra Difficulty Analytics

### Collection: `NTTTOrchestraAnalytics`

Aggregate difficulty by orchestra.

```json
{
  "_id": "ObjectId",

  "orchestra": "Juan D'Arienzo",

  // Overall stats
  "totalSongs": 45,
  "totalAnswers": 2500,
  "totalCorrect": 2300,
  "accuracy": 0.92,
  "avgDifficultyScore": 8,

  // Speed
  "avgResponseTimeMs": 2600,

  // Songs breakdown
  "easiestSongs": [
    { "songId": "...", "title": "La Cumparsita", "accuracy": 0.98 }
  ],
  "hardestSongs": [
    { "songId": "...", "title": "Paciencia", "accuracy": 0.65 }
  ],

  // Confusion matrix (most confused with)
  "confusedWith": [
    { "orchestra": "Rodolfo Biagi", "confusionRate": 0.05 },
    { "orchestra": "Ricardo Tanturi", "confusionRate": 0.03 }
  ],

  "updatedAt": "ISODate"
}
```

---

## Session Tracking

### Collection: `NTTTQuizSessions`

Track complete quiz sessions.

```json
{
  "_id": "ObjectId",

  "sessionId": "uuid-v4",
  "visitorId": "uuid-v4",
  "firebaseUserId": "firebase-uid or null",

  // Session config
  "quizType": "standard",  // standard | challenge | practice
  "questionCount": 10,
  "difficulty": "medium",
  "filters": {
    "orchestras": [],  // empty = all
    "styles": ["Tango", "Vals"],
    "yearRange": [1935, 1955]
  },

  // Results
  "totalCorrect": 8,
  "totalWrong": 2,
  "accuracy": 0.80,
  "totalTimeMs": 35000,
  "avgTimePerQuestionMs": 3500,

  // Session flow
  "startedAt": "ISODate",
  "completedAt": "ISODate",
  "abandoned": false,
  "abandonedAtQuestion": null,

  // Device/location
  "deviceType": "desktop",
  "userAgent": "...",
  "ipCity": "New York",
  "ipCountry": "US",

  "createdAt": "ISODate"
}
```

---

## Cross-Platform Integration

### Upsell/Engagement Triggers

Track events for TangoTiempo cross-promotion:

```json
{
  "event": "quiz_complete",
  "userId": "firebase-uid",
  "data": {
    "score": 8,
    "total": 10,
    "topOrchestras": ["Juan D'Arienzo", "Carlos Di Sarli"],
    "weakOrchestras": ["Francisco Canaro"]
  },

  // Trigger TangoTiempo notification
  "crossPlatformAction": {
    "type": "event_recommendation",
    "message": "You aced D'Arienzo! There's a milonga with D'Arienzo tandas tonight in Brooklyn.",
    "link": "https://tangotiempo.com/events?orchestra=darienzo&near=brooklyn"
  }
}
```

### Shared User Preferences (Collection: `CrossPlatformUserPrefs`)

```json
{
  "firebaseUserId": "firebase-uid",

  "nttt": {
    "favoriteOrchestras": ["Juan D'Arienzo"],
    "skillLevel": "intermediate",
    "totalQuizzes": 50
  },

  "tangotiempo": {
    "homeLocation": { "lat": 40.7, "lng": -74.0 },
    "favoriteVenues": ["venue-id-1"],
    "eventsAttended": 12
  },

  "marketing": {
    "canEmail": true,
    "canPush": true,
    "interests": ["milongas", "workshops", "d'arienzo"]
  }
}
```

---

## Analytics Queries

### Find Hardest Songs (Potential Data Issues)

```javascript
db.NTTTSongAnalytics.find({
  totalAnswers: { $gte: 50 },  // Minimum sample size
  accuracy: { $lt: 0.60 }      // Less than 60% correct
}).sort({ accuracy: 1 }).limit(20);
```

### Find Confusing Orchestra Pairs

```javascript
db.NTTTQuizAnswers.aggregate([
  { $match: { isCorrect: false, questionType: "orchestra" } },
  { $group: {
    _id: { correct: "$correctAnswer", wrong: "$userAnswer" },
    count: { $sum: 1 }
  }},
  { $sort: { count: -1 } },
  { $limit: 20 }
]);
```

### User Progress Over Time

```javascript
db.NTTTQuizSessions.aggregate([
  { $match: { firebaseUserId: "user-123" } },
  { $group: {
    _id: { $dateToString: { format: "%Y-%m-%d", date: "$completedAt" } },
    avgAccuracy: { $avg: "$accuracy" },
    totalQuestions: { $sum: "$questionCount" }
  }},
  { $sort: { _id: 1 } }
]);
```

### Correlation: Low Accuracy + User Feedback

```javascript
// Songs that are both hard AND flagged by users
db.NTTTSongAnalytics.find({
  accuracy: { $lt: 0.70 },
  feedbackCount: { $gte: 2 }
}).sort({ feedbackCount: -1 });
```

---

## API Endpoints Needed

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/nttt/answer` | POST | Record quiz answer |
| `/api/nttt/session/start` | POST | Start new quiz session |
| `/api/nttt/session/complete` | POST | Complete quiz session |
| `/api/nttt/user/stats` | GET | Get user performance stats |
| `/api/nttt/leaderboard` | GET | Get leaderboard data |
| `/api/nttt/song/{id}/difficulty` | GET | Get song difficulty stats |
| `/api/nttt/analytics/hard-songs` | GET | Admin: list hardest songs |

---

## Metrics Dashboard

### User Metrics
- Total quizzes taken
- Overall accuracy trend
- Improvement rate
- Favorite question types
- Session length

### System Metrics
- Songs with <60% accuracy (potential data issues)
- Most confused orchestra pairs
- Question type difficulty distribution
- User retention (returning vs new)

### Cross-Platform Metrics
- TangoTiempo users who use NTTT
- Conversion: NTTT → TangoTiempo signup
- Event attendance correlation with quiz performance

---

*Created: 2026-02-20*
*Author: Quinn (Cross-Project Coordinator)*
