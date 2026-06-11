# PLAN.md — WorldCup Hub Implementation Plan

**Tournament data:** 2022 FIFA World Cup (real data, Qatar). 32 teams / 8 groups / 64 matches.
**Switch to 2026:** drop DB → re-apply `schema.sql` → replace `seed.sql`. App code unchanged.

Each step includes a test file in `backend/tests/`. Run all tests with `pytest` from `backend/`.

---

## Status

| Step | Description | Status |
|------|-------------|--------|
| STEP-1 | Project Scaffolding | ✅ done |
| STEP-2 | MySQL Schema | ✅ done |
| STEP-3 | Seed Data (2022 WC) | ✅ done |
| STEP-4 | Database Connection Layer | ✅ done |
| STEP-5 | Redis Session Layer | ✅ done |
| STEP-6 | Auth API | ✅ done |
| STEP-7 | Auth Middleware | ✅ done |
| STEP-8 | Teams API | ✅ done |
| STEP-9 | Matches API | ✅ done |
| STEP-10 | Venues API | ✅ done |
| STEP-11 | Player Leaderboards API | ✅ done |
| STEP-12 | Group Standings API | ✅ done |
| STEP-13 | Knockout Bracket API | ✅ done |
| STEP-14 | Predictions API | ✅ done |
| STEP-15 | Prediction Scoring | ✅ done |
| STEP-16 | User Profile API | ✅ done |
| STEP-17 | Activity Logging | ✅ done |
| STEP-18 | Admin API | ✅ done |
| STEP-19 | React App Setup | ✅ done |
| STEP-20 | Auth Pages | ⬜ |
| STEP-21 | Home Page | ⬜ |
| STEP-22 | Matches Page + Match Detail | ⬜ |
| STEP-23 | Standings Page | ⬜ |
| STEP-24 | Teams Page + Team Detail | ⬜ |
| STEP-25 | Players Page | ⬜ |
| STEP-26 | Predictions Page | ⬜ |
| STEP-27 | Leaderboard Page | ⬜ |
| STEP-28 | Profile Page | ⬜ |
| STEP-29 | Admin Page | ⬜ |
| STEP-30 | Gunicorn Config | ⬜ |
| STEP-31 | End-to-End Validation | ⬜ |

---

## Phase 1 — Foundation

### ✅ STEP-1: Project Scaffolding
Flask app with all blueprint stubs, `requirements.txt`, `.env.example`, `wsgi.py`.

**Purpose:** Creates the Flask application skeleton with all route blueprints registered and stubbed out. Establishes the directory structure, dependency manifest, and entry point so every subsequent step has a consistent, importable app to extend — and a 404 on unknown routes confirms the app wires up correctly from day one.

- Tests: `tests/test_step1_scaffold.py` (3 tests — app creates, blueprints registered, 404 on unknown route)

---

### ✅ STEP-2: MySQL Schema
`schema.sql` — 9 tables, 8 indexes, 2 stored procedures, 1 trigger.

**Purpose:** Defines the full relational model for the tournament hub. The 9-table schema captures teams, players, venues, matches, events, users, predictions, activity, and sessions — along with stored procedures and a trigger that keep derived stats consistent without requiring app-level orchestration. All downstream steps depend on this schema existing.

Tables: `users`, `teams`, `players`, `venues`, `matches`, `match_events`, `predictions`, `user_activity`, `session_audit`

Stored procedures: `calculate_prediction_points(match_id)`, `get_group_standings(group_name)`

Trigger: `update_player_stats` on `match_events` INSERT

- Tests: `tests/test_step2_schema.py` (6 tests — tables, procedures, trigger, indexes, unique constraints)

---

### ✅ STEP-3: Seed Data
`generate_seed.py` → `seed.sql` — real 2022 World Cup data.

**Purpose:** Populates the database with real 2022 FIFA World Cup data so the app has a complete, realistic dataset from day one. Accurate scores, player stats, and bracket progression let every downstream API return meaningful responses during development — no placeholder data, no guessing at edge cases.

- 32 teams (Groups A–H, real coaches, FIFA rankings)
- 8 venues (Qatar stadiums)
- 736 players (23/team; detailed real squads for ARG, FRA, BRA, ENG, POR, CRO, MAR, GER)
- 64 matches, all `completed` with real scores (48 group + 16 knockout)

- Tests: `tests/test_step3_seed.py` (12 tests — counts, group sizes, score integrity, final result, no duplicate jerseys)

---

### STEP-4: Database Connection Layer
`backend/app/db/connection.py` — PyMySQL wrapper with connection pooling.

**Purpose:** Provides a thin, safe wrapper around PyMySQL with connection pooling. Centralizing `query` and `execute` helpers ensures parameterized queries are used everywhere — eliminating SQL injection at the library boundary rather than relying on per-call discipline across every route.

- `get_connection()` — pool size 20
- `query(sql, params)` — parameterized SELECT, returns list of dicts
- `execute(sql, params)` — parameterized INSERT/UPDATE/DELETE, returns lastrowid / rowcount
- No string concatenation in any query

- Tests: `tests/test_step4_db.py`
  - `query("SELECT 1")` returns `[{'1': 1}]`
  - `execute` INSERT round-trips via `query`
  - Parameterized query prevents SQL injection

---

### STEP-5: Redis Session Layer
`backend/app/auth/session.py`

**Purpose:** Implements server-side session storage in Redis with a 24-hour TTL, per-user session cap of 5, and an audit trail in MySQL. Keeping session data server-side means the server can invalidate sessions instantly — a hard requirement for logout, password change, and account lock — none of which are possible with stateless JWTs or signed cookies alone.

- `create_session(user_id, username, is_admin, favorite_team)` → UUID4 session_id
  - Redis key `session:{id}`, 24h TTL
  - Per-user list `user_sessions:{user_id}`, max 5 (evict oldest)
  - Inserts into `session_audit`
- `get_session(session_id)` → dict or None; refreshes TTL
- `destroy_session(session_id)` — deletes Redis key, marks audit record
- `destroy_all_sessions(user_id)`

- Tests: `tests/test_step5_session.py`
  - create → get → destroy round-trip
  - get on expired/missing key returns None
  - 6th session evicts oldest

---

### STEP-6: Auth API
`backend/app/routes/auth.py`

**Purpose:** Exposes registration, login, and logout endpoints. Handles bcrypt hashing, account locking after 10 failed attempts, and per-IP rate limiting so the auth surface is hardened before any user-facing features are built on top of it. All authenticated features in the app depend on this step producing a valid session cookie.

`POST /api/auth/register` — validate, bcrypt hash (12 rounds), insert user, create session, set cookie
  - Rate limit: 5/hour per IP (`ratelimit:register:{ip}`)
  - 409 on duplicate username/email

`POST /api/auth/login` — accept username or email; lock at 10 failures (15 min); rate limit 10/min
`POST /api/auth/logout` — destroy session, clear cookie

- Tests: `tests/test_step6_auth.py`
  - Register → cookie set, user in DB
  - Duplicate username → 409
  - Login wrong password 10× → 423 locked
  - Logout → session destroyed

---

### STEP-7: Auth Middleware
`backend/app/auth/middleware.py`

**Purpose:** Provides `@require_auth` and `@require_admin` decorators that validate the session cookie and attach the user to the Flask request context via `g.user`. Centralizing this logic means every protected route gets consistent, tested auth enforcement with a single decorator — no route can accidentally skip the check.

- `@require_auth` — reads cookie, calls `get_session`, attaches `g.user`; 401 if missing/expired
- `@require_admin` — wraps `@require_auth`, checks `g.user['is_admin']`; 403 if not

- Tests: `tests/test_step7_middleware.py`
  - No cookie → 401
  - Valid non-admin cookie → 403 on admin route
  - Valid admin cookie → passes through

---

## Phase 2 — Teams, Matches, Venues

### ✅ STEP-8: Teams API
`backend/app/routes/teams.py`

**Purpose:** Lets the frontend fetch all 32 teams (optionally filtered by group) and retrieve a full 23-player squad for any team. Used to power group-stage tabs, team picker dropdowns in match filters, and team detail pages — any view that needs to display who is in the tournament.

`GET /api/teams` — all 32 teams sorted by group then name; optional `?group=A` filters to 4 teams in that group.
`GET /api/teams/{id}` — team metadata + full 23-player squad ordered by jersey number. 404 if not found.

**Sample: `GET /api/teams?group=A`**
Returns the 4 teams in Group A, sorted alphabetically. Useful for building group-stage tabs.
```json
[
  { "id": 2, "name": "Ecuador",     "country_code": "ECU", "group_name": "A", "fifa_ranking": 44, "coach": "Gustavo Alfaro" },
  { "id": 4, "name": "Netherlands", "country_code": "NED", "group_name": "A", "fifa_ranking":  8, "coach": "Louis van Gaal" },
  { "id": 1, "name": "Qatar",       "country_code": "QAT", "group_name": "A", "fifa_ranking": 50, "coach": "Felix Sanchez" },
  { "id": 3, "name": "Senegal",     "country_code": "SEN", "group_name": "A", "fifa_ranking": 18, "coach": "Aliou Cisse" }
]
```

**Sample: `GET /api/teams/9`** (Argentina)
Returns team info plus `players` array. Teams with real squads (ARG, FRA, BRA, ENG, POR, CRO, MAR, GER) have actual names; others have generic `Player N`.
```json
{
  "id": 9, "name": "Argentina", "country_code": "ARG", "group_name": "C",
  "fifa_ranking": 3, "coach": "Lionel Scaloni",
  "players": [
    { "id": 186, "name": "Juan Musso",         "position": "GK",  "jersey_number": 1, "goals": 0, "assists": 0 },
    { "id": 195, "name": "Nicolas Tagliafico", "position": "DEF", "jersey_number": 3, "goals": 0, "assists": 0 },
    { "id": 189, "name": "Gonzalo Montiel",    "position": "DEF", "jersey_number": 4, "goals": 0, "assists": 0 }
  ]
}
```

- Tests: `tests/test_step8_teams.py`
  - `/api/teams` returns 32 teams
  - `?group=A` returns exactly 4
  - Team detail includes `players` array

---

### ✅ STEP-9: Matches API
`backend/app/routes/matches.py`

**Purpose:** Exposes the full 64-match schedule with combinable filters and match detail with embedded team/venue objects. The embedded shape means the frontend can render a complete match card from a single API response without needing follow-up requests for team or venue data, keeping the Matches page fast.

`GET /api/matches` — all 64 matches ordered by date. Combinable filters: `?date=YYYY-MM-DD`, `?stage=group|round_of_16|quarterfinal|semifinal|third_place|final`, `?team_id=N`, `?venue_id=N`.
`GET /api/matches/{id}` — match detail with nested home/away team objects, venue, and `events` array ordered by minute. 404 if not found.

**Sample: `GET /api/matches` (first 2)**
Each match embeds team and venue objects so the frontend never needs a second request.
```json
[
  {
    "id": 1, "match_date": "2022-11-20T19:00:00", "stage": "group", "status": "completed",
    "group_name": "A", "home_score": 0, "away_score": 2,
    "home_team": { "id": 1, "name": "Qatar",   "country_code": "QAT" },
    "away_team": { "id": 2, "name": "Ecuador", "country_code": "ECU" },
    "venue":     { "id": 2, "name": "Al Bayt Stadium", "city": "Al Khor" }
  },
  {
    "id": 7, "match_date": "2022-11-21T13:00:00", "stage": "group", "status": "completed",
    "group_name": "B", "home_score": 6, "away_score": 2,
    "home_team": { "id": 5, "name": "England", "country_code": "ENG" },
    "away_team": { "id": 6, "name": "Iran",    "country_code": "IRN" },
    "venue":     { "id": 6, "name": "Khalifa International Stadium", "city": "Doha" }
  }
]
```

**Sample: `GET /api/matches/64`** (the final — ARG vs FRA 3-3)
`events` is empty in seed data for most matches; populated when match events are inserted.
```json
{
  "id": 64, "match_date": "2022-12-18T17:00:00", "stage": "final", "status": "completed",
  "group_name": null, "home_score": 3, "away_score": 3,
  "home_team": { "id": 9,  "name": "Argentina", "country_code": "ARG" },
  "away_team": { "id": 13, "name": "France",    "country_code": "FRA" },
  "venue":     { "id": 1,  "name": "Lusail Stadium", "city": "Lusail" },
  "events": []
}
```

- Tests: `tests/test_step9_matches.py`
  - No filter returns 64 matches
  - `?stage=group` returns 48
  - `?team_id` returns only that team's matches
  - Match detail shape correct

---

### ✅ STEP-10: Venues API
`backend/app/routes/venues.py`

**Purpose:** Returns all 8 Qatar stadiums so the frontend can populate venue filter dropdowns on the Matches page. Kept as a separate endpoint so venue data is fetched once and cached client-side rather than repeated inside every match response, which would bloat the 64-match payload unnecessarily.

`GET /api/venues` — all 8 Qatar stadiums sorted by name, including capacity. Used to populate venue filter dropdowns.

**Sample: `GET /api/venues`**
```json
[
  { "id": 5, "name": "Ahmad Bin Ali Stadium",       "city": "Al Rayyan", "country": "Qatar", "capacity": 44740 },
  { "id": 2, "name": "Al Bayt Stadium",             "city": "Al Khor",   "country": "Qatar", "capacity": 60000 },
  { "id": 3, "name": "Al Janoub Stadium",           "city": "Al Wakrah", "country": "Qatar", "capacity": 40000 },
  { "id": 7, "name": "Al Thumama Stadium",          "city": "Doha",      "country": "Qatar", "capacity": 40000 },
  { "id": 4, "name": "Education City Stadium",      "city": "Al Rayyan", "country": "Qatar", "capacity": 45350 },
  { "id": 6, "name": "Khalifa International Stadium","city": "Doha",     "country": "Qatar", "capacity": 45416 },
  { "id": 1, "name": "Lusail Stadium",              "city": "Lusail",    "country": "Qatar", "capacity": 89000 },
  { "id": 8, "name": "Stadium 974",                 "city": "Doha",      "country": "Qatar", "capacity": 40000 }
]
```

- Tests: `tests/test_step10_venues.py`
  - Returns 8 records
  - Each record has `name`, `city`, `country`, `capacity`

---

### ✅ STEP-11: Player Leaderboards API
`backend/app/routes/leaderboards.py`

**Purpose:** Surfaces the top 10 scorers and top 10 assisters for the tournament, giving users a quick view of individual standout performances. Reads from pre-aggregated `goals` and `assists` columns on the `players` table (kept current by the `update_player_stats` trigger), so responses are a simple sorted query rather than a live aggregation over match events.

`GET /api/leaderboards/goals` — top 10 scorers, sorted goals DESC then assists DESC. Includes team name and country code.
`GET /api/leaderboards/assists` — top 10 assisters, sorted assists DESC then goals DESC.

**Sample: `GET /api/leaderboards/goals` (top 3)**
Mbappé leads with 8 goals (Golden Boot), Messi second with 7.
```json
[
  { "id": 294, "name": "Kylian Mbappe",  "position": "FWD", "jersey_number": 10, "goals": 8, "assists": 2, "team_name": "France",    "country_code": "FRA" },
  { "id": 203, "name": "Lionel Messi",   "position": "FWD", "jersey_number": 10, "goals": 7, "assists": 3, "team_name": "Argentina", "country_code": "ARG" },
  { "id": 202, "name": "Julian Alvarez", "position": "FWD", "jersey_number":  9, "goals": 4, "assists": 2, "team_name": "Argentina", "country_code": "ARG" }
]
```

**Sample: `GET /api/leaderboards/assists` (top 3)**
Messi and Griezmann tied on 3 assists; tie-broken by goals (Messi: 7, Griezmann: 0).
```json
[
  { "id": 203, "name": "Lionel Messi",     "position": "FWD", "jersey_number": 10, "goals": 7, "assists": 3, "team_name": "Argentina", "country_code": "ARG" },
  { "id": 291, "name": "Antoine Griezmann","position": "MID", "jersey_number":  7, "goals": 0, "assists": 3, "team_name": "France",    "country_code": "FRA" },
  { "id": 294, "name": "Kylian Mbappe",   "position": "FWD", "jersey_number": 10, "goals": 8, "assists": 2, "team_name": "France",    "country_code": "FRA" }
]
```

- Tests: `tests/test_step11_leaderboards.py`
  - Each endpoint returns exactly 10 records
  - Sorted correctly (Mbappe leads goals with 8, Messi second with 7)

---

## Phase 3 — Standings

### ✅ STEP-12: Group Standings API
`backend/app/routes/standings.py`

**Purpose:** Returns the current group standings table for each of the 8 groups, calculated by the `get_group_standings` stored procedure. The tiebreaker order (points → goal difference → goals for → FIFA ranking) matches official FIFA rules, making this the authoritative source for who qualifies from each group.

`GET /api/standings/group` — standings for all 8 groups as a single object keyed A–H. `?group=A` returns just that group.
Delegates to the `get_group_standings(group)` MySQL stored procedure. Sorted by points → goal difference → goals for → FIFA ranking.
Note: SUM() values from stored procedures come back as strings from PyMySQL — cast to `int` when doing arithmetic.

**Sample: `GET /api/standings/group?group=A`**
NED top (7 pts), SEN second (6 pts), ECU third (4 pts), QAT bottom (0 pts, -6 GD).
```json
{
  "A": [
    { "id": 4, "name": "Netherlands", "country_code": "NED", "fifa_ranking":  8, "matches_played": 3, "wins": "2", "draws": "1", "losses": "0", "goals_for": "5", "goals_against": "1", "goal_difference":  "4", "points": "7" },
    { "id": 3, "name": "Senegal",     "country_code": "SEN", "fifa_ranking": 18, "matches_played": 3, "wins": "2", "draws": "0", "losses": "1", "goals_for": "5", "goals_against": "4", "goal_difference":  "1", "points": "6" },
    { "id": 2, "name": "Ecuador",     "country_code": "ECU", "fifa_ranking": 44, "matches_played": 3, "wins": "1", "draws": "1", "losses": "1", "goals_for": "4", "goals_against": "3", "goal_difference":  "1", "points": "4" },
    { "id": 1, "name": "Qatar",       "country_code": "QAT", "fifa_ranking": 50, "matches_played": 3, "wins": "0", "draws": "0", "losses": "3", "goals_for": "1", "goals_against": "7", "goal_difference": "-6", "points": "0" }
  ]
}
```

- Tests: `tests/test_step12_standings.py`
  - All 8 groups present
  - Group A: Netherlands and Senegal at top
  - Points arithmetic correct

---

### ✅ STEP-13: Knockout Bracket API
`backend/app/routes/standings.py` (same file)

**Purpose:** Returns the full knockout bracket as a single nested JSON object keyed by round, allowing the frontend to render the entire bracket — round of 16 through the final — in one API call with no client-side join logic. Having all 16 knockout matches in a single response makes it straightforward to draw the bracket tree left-to-right.

`GET /api/standings/knockout` — full bracket as a single nested JSON object with 5 round keys.
Each slot has `match_id`, `status`, `home_score`, `away_score`, `home_team`, `away_team`.
Match counts: `round_of_16` = 8, `quarterfinal` = 4, `semifinal` = 2, `third_place` = 1, `final` = 1.

**Sample: `GET /api/standings/knockout`** (trimmed to 1–2 entries per round)
```json
{
  "round_of_16": [
    { "match_id": 49, "status": "completed", "home_score": 3, "away_score": 1,
      "home_team": { "id": 4,  "name": "Netherlands", "country_code": "NED" },
      "away_team": { "id": 7,  "name": "USA",         "country_code": "USA" } },
    { "match_id": 50, "status": "completed", "home_score": 2, "away_score": 1,
      "home_team": { "id": 9,  "name": "Argentina",   "country_code": "ARG" },
      "away_team": { "id": 14, "name": "Australia",   "country_code": "AUS" } }
  ],
  "quarterfinal": [
    { "match_id": 57, "status": "completed", "home_score": 1, "away_score": 1,
      "home_team": { "id": 24, "name": "Croatia", "country_code": "CRO" },
      "away_team": { "id": 25, "name": "Brazil",  "country_code": "BRA" } }
  ],
  "semifinal": [
    { "match_id": 61, "status": "completed", "home_score": 3, "away_score": 0,
      "home_team": { "id": 9,  "name": "Argentina", "country_code": "ARG" },
      "away_team": { "id": 24, "name": "Croatia",   "country_code": "CRO" } }
  ],
  "third_place": [
    { "match_id": 63, "status": "completed", "home_score": 2, "away_score": 1,
      "home_team": { "id": 24, "name": "Croatia", "country_code": "CRO" },
      "away_team": { "id": 23, "name": "Morocco", "country_code": "MAR" } }
  ],
  "final": [
    { "match_id": 64, "status": "completed", "home_score": 3, "away_score": 3,
      "home_team": { "id": 9,  "name": "Argentina", "country_code": "ARG" },
      "away_team": { "id": 13, "name": "France",    "country_code": "FRA" } }
  ]
}
```

- Tests: `tests/test_step13_bracket.py`
  - All 5 round keys present
  - `round_of_16` has 8 matches
  - Final slot shows Argentina vs France, 3-3

---

## Phase 4 — Predictions

### ✅ STEP-14: Predictions API
`backend/app/routes/predictions.py`

**Purpose:** The core engagement feature. Lets authenticated users submit and revise score predictions for any scheduled match, view their full prediction history with points earned, and compete on a public leaderboard. Predictions are blocked on completed or live matches to prevent retroactive cheating — the gate is enforced server-side, not just in the UI.

`POST /api/predictions/{match_id}` — `@require_auth`. Body: `{"home_score": N, "away_score": N}`. UPSERTs — first call returns 201, subsequent calls return 200. Rejects if match status is not `scheduled` (400).
`GET /api/user/predictions` — `@require_auth`. Returns the logged-in user's predictions with match details and points earned (null until match completes and scoring runs).
`GET /api/predictions/leaderboard` — public. Top 50 users by total `points_earned` DESC, then `exact_count` DESC. Returns 0 points for users with no scored predictions yet.

**Sample: `POST /api/predictions/1`** (first submission → 201)
```json
{ "created": true }
```

**Sample: `POST /api/predictions/1`** (update same match → 200)
```json
{ "updated": true }
```

**Sample: `POST /api/predictions/2`** (match already completed → 400)
```json
{ "error": "predictions only allowed for scheduled matches" }
```

**Sample: `GET /api/user/predictions`**
`points_earned` is null until admin marks the match completed and scoring runs (STEP-15).
```json
[
  {
    "id": 6,
    "match_id": 1,
    "predicted_home": 0, "predicted_away": 2,
    "actual_home": 0,    "actual_away": 2,
    "points_earned": null,
    "home_team": "Qatar", "away_team": "Ecuador",
    "match_date": "2022-11-20T19:00:00",
    "stage": "group", "status": "scheduled",
    "created_at": "2026-06-11T06:32:19",
    "updated_at": "2026-06-11T06:32:19"
  }
]
```

**Sample: `GET /api/predictions/leaderboard`**
`total_points` and `exact_count` come back as strings from MySQL aggregation — cast to int in frontend.
```json
[
  { "id": 42, "username": "alice", "total_points": "12", "exact_count": "3" },
  { "id": 17, "username": "bob",   "total_points":  "9", "exact_count": "2" }
]
```

- Tests: `tests/test_step14_predictions.py`
  - Predict on completed match → 400
  - Predict on scheduled match → 201; update → 200
  - Leaderboard sorted by total DESC

---

### ✅ STEP-15: Prediction Scoring
`backend/app/db/scoring.py`

**Purpose:** Scores all outstanding predictions for a match after its result is finalized. Called by the admin score-update endpoint the moment a match transitions to `completed`. Delegates to the `calculate_prediction_points` stored procedure, which runs the scoring logic atomically inside the database — 3 points for an exact score, 1 point for the correct outcome, 0 otherwise.

Called by admin match update after status → `completed`.
Calls `calculate_prediction_points(match_id)`.

- Tests: `tests/test_step15_scoring.py`
  - Exact score → 3 pts
  - Correct outcome → 1 pt
  - Wrong → 0 pts

---

## Phase 5 — User Profile & Admin

### ✅ STEP-16: User Profile API
`backend/app/routes/user.py`

**Purpose:** Lets users manage their own account without admin involvement. Email updates, favorite team selection, and password changes are self-service. Password change is the security-sensitive operation here: it destroys all existing sessions (logging out any other active devices) and immediately issues a fresh session for the current request — so the user stays logged in but all stale sessions are invalidated. Soft delete preserves prediction history on the leaderboard while blocking future logins.

`GET /api/user/profile`, `PUT /api/user/profile`, `PUT /api/user/favorite-team`
`POST /api/user/change-password` — verify old, hash new, destroy all sessions, re-create
`DELETE /api/user/profile` — soft delete (`is_active = false`)

- Tests: `tests/test_step16_user.py`
  - Profile update persists
  - Password change invalidates other sessions
  - Soft delete blocks login

---

### STEP-17: Activity Logging
`backend/app/auth/activity.py`

**Purpose:** Records a timestamped audit row for every significant user action (register, login, predict, password change, etc.) and surfaces the last 100 to the authenticated user on their profile page. Gives users transparency into their account activity and provides an audit trail for security investigations. Auto-purges records older than 90 days on read to bound storage growth without a background job.

`log_activity(user_id, action, ip_address)` — INSERT into `user_activity`
Auto-purge: records older than 90 days on read
`GET /api/user/activity` — `@require_auth` — last 100 records

- Tests: `tests/test_step17_activity.py`
  - register → login → predict produces 3 activity rows

---

### STEP-18: Admin API
`backend/app/routes/admin.py` — all `@require_admin`

**Purpose:** Provides the operational control plane for running the tournament hub. Score updates are the most critical path: marking a match `completed` triggers prediction scoring for all users who predicted that match. User lock/unlock handles account abuse. Session management lets admins force-logout a user. The stats endpoint gives a live snapshot of platform health. All endpoints are gated behind `@require_admin`.

`PUT /api/admin/matches/{id}/score` — update score/status; calls scoring on completion
`GET /api/admin/users`, `POST /api/admin/users/{id}/lock`, `POST /api/admin/users/{id}/unlock`
`GET /api/admin/sessions`, `DELETE /api/admin/sessions/{user_id}`
`GET /api/admin/stats` — active sessions, total users, predictions last 24h

- Tests: `tests/test_step18_admin.py`
  - Score update triggers prediction scoring
  - Lock → login returns 423
  - Stats returns all 3 keys

---

## Phase 6 — Frontend

### STEP-19: React App Setup
Vite + React + TailwindCSS in `frontend/`.

**Purpose:** Bootstraps the frontend application with the toolchain, routing, and shared infrastructure that all page components depend on. The Vite dev proxy routes `/api` requests to the Flask backend so there are no CORS issues during development. `AuthContext` provides login state to the entire component tree, and the protected route wrapper enforces authentication at the router level rather than inside each page.

- Vite proxy: `/api` → `http://localhost:5000`
- `AuthContext` — user state, login/logout helpers
- `<Navbar>` + `<Outlet>` layout
- Protected route wrapper → redirects to `/login`

- Tests: `tests/test_step19_frontend.py` — `npm run build` exits 0; proxy config present

---

### STEP-20: Auth Pages
`Login.jsx`, `Register.jsx`

**Purpose:** The entry point for all non-public features. Login accepts username or email to match the backend. Registration shows a password strength meter so users understand requirements before submitting rather than after a 400 response. Both forms display field-level errors from the API inline. Successful auth updates `AuthContext` and redirects without a full page reload.

- Field errors from API; password strength meter on register
- Auto-login redirect on success

---

### STEP-21: Home Page
`Home.jsx` — today's matches; upcoming if none today; quick links

**Purpose:** The landing page for returning users. Shows today's matches front and center so a user checking in on match day sees relevant content immediately. Falls back to the next scheduled matches when there are none today. Quick links to Standings, Predictions, and Leaderboard cover the other high-traffic destinations without requiring navigation.

---

### STEP-22: Matches Page + Match Detail
`Matches.jsx` — filter bar (date, stage, team, venue); inline predict form
`MatchDetail.jsx` — events timeline for completed matches

**Purpose:** The primary browsing surface for the tournament. The filter bar lets users slice 64 matches by any combination of date, stage, team, or venue. The inline prediction form lets authenticated users submit a prediction without navigating away from the match list, reducing friction. Match detail shows the full events timeline (goals, cards, substitutions) for completed matches.

---

### STEP-23: Standings Page
`Standings.jsx` — tabs: Group Stage | Knockout Bracket
- Group Stage: group selector A–H, table with MP/W/D/L/GF/GA/GD/Pts; top 2 highlighted
- Knockout: bracket from `/api/standings/knockout`, rounds left-to-right

**Purpose:** Covers both tournament phases in a single tabbed page. The group standings tab highlights the top 2 teams per group (who advance) to give users immediate visual clarity on who is through. The knockout bracket tab renders all 16 knockout matches as a visual bracket progressing left-to-right from round of 16 to the final.

---

### STEP-24: Teams Page + Team Detail
`Teams.jsx` — group filter tabs; team cards
`TeamDetail.jsx` — squad table (#, Name, Position)

**Purpose:** Lets users explore the 32 participating teams, filtered by group. Team cards link to detail pages showing the full 23-player squad sorted by jersey number — useful for checking a player's position before making a prediction or browsing the leaderboard.

---

### STEP-25: Players Page
`Players.jsx` — tabs: Top Scorers | Top Assists; 10 rows each

**Purpose:** Highlights individual tournament performances. The two-tab layout mirrors the two leaderboard endpoints and gives users a quick way to see who is dominating the Golden Boot and assist charts without needing to browse through team rosters.

---

### STEP-26: Predictions Page
`Predictions.jsx` — `@require_auth`; table with predicted/actual/points; inline edit for scheduled

**Purpose:** The personal scorecard for each user. Shows the full prediction history with predicted scores, actual results, and points earned side by side. Scheduled matches show an inline edit form so users can revise their prediction before kickoff. Completed matches show the points outcome. This page is the primary feedback loop that drives re-engagement.

---

### STEP-27: Leaderboard Page
`Leaderboard.jsx` — top 50 by points; current user highlighted

**Purpose:** The competitive centerpiece of the app. Ranks the top 50 users by total prediction points and highlights the current user's row regardless of their rank, so they can see how they stack up even if they are outside the top 50. Exact score counts are shown as a secondary column to break ties visually.

---

### STEP-28: Profile Page
`Profile.jsx` — `@require_auth`; update email/team; change password; activity log; deactivate

**Purpose:** Account management hub. Lets users update their email and favorite team, change their password (with confirmation of the old one), review their recent activity log for security awareness, and deactivate their account if they want to leave. All profile API endpoints from STEP-16 are exercised here.

---

### STEP-29: Admin Page
`Admin.jsx` — admin only; tabs: Match Management | User Management | System Stats

**Purpose:** The operational dashboard for whoever is running the tournament hub. Match Management is the primary tab during the tournament — it's where scores get entered, which triggers prediction scoring for all users. User Management handles abuse cases (lock/unlock). System Stats gives a live view of active sessions, total users, and prediction volume over the last 24 hours.

---

## Phase 7 — Deployment

### STEP-30: Gunicorn Config
`wsgi.py` + `gunicorn.conf.py` (workers = 2×CPU+1, timeout 30s)
Flask serves `frontend/dist/` as static files.

**Purpose:** Collapses the two development servers (Flask on 5000, Vite on 5173) into a single deployable process. Gunicorn provides the multi-worker concurrency that Flask's built-in server cannot. Flask serving the built `frontend/dist/` means the same process handles both API requests and static file delivery — no separate static file server needed for a single-VM deployment.

- Tests: `tests/test_step30_gunicorn.py` — gunicorn starts; `/api/teams` responds

---

### STEP-31: End-to-End Validation
Manual + scripted run through all PRD flows.

**Purpose:** Verifies that all 31 steps work correctly as an integrated system, not just in isolation. Unit and integration tests confirm individual endpoints; this step confirms the full user journeys — registration through prediction through scoring through leaderboard — produce correct results end-to-end. Also exercises the security flows: rate limits, account locking, admin-only gates, and session invalidation on password change.

1. Register → auto-login
2. Browse matches → predict → see in `/predictions`
3. Admin updates score → predictions scored
4. Standings correct
5. Knockout bracket renders
6. Leaderboard reflects points
7. 10 failed logins → locked → admin unlocks
8. Password change → other sessions invalidated
9. Rate limits return 429
10. Non-admin blocked from `/admin`

---

## Dependency Map

```
STEP-1 (scaffold)
  └─ STEP-2 (schema) ── STEP-3 (seed)
       └─ STEP-4 (db layer)
            └─ STEP-5 (redis sessions)
                 └─ STEP-6 (auth API)
                      └─ STEP-7 (middleware)
                           ├─ STEP-8  (teams API)
                           ├─ STEP-9  (matches API)
                           ├─ STEP-10 (venues API)
                           ├─ STEP-11 (leaderboards API)
                           ├─ STEP-12 (group standings)
                           ├─ STEP-13 (knockout bracket)
                           ├─ STEP-14 (predictions API)
                           │    └─ STEP-15 (scoring)
                           ├─ STEP-16 (user profile API)
                           ├─ STEP-17 (activity logging)
                           └─ STEP-18 (admin API)
                                └─ STEP-19 (React setup)
                                     ├─ STEP-20 through STEP-29 (pages)
                                     └─ STEP-30 (gunicorn)
                                          └─ STEP-31 (e2e)
```
