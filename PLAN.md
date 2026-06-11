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
| STEP-6 | Auth API | ⬜ |
| STEP-7 | Auth Middleware | ⬜ |
| STEP-8 | Teams API | ⬜ |
| STEP-9 | Matches API | ⬜ |
| STEP-10 | Venues API | ⬜ |
| STEP-11 | Player Leaderboards API | ⬜ |
| STEP-12 | Group Standings API | ⬜ |
| STEP-13 | Knockout Bracket API | ⬜ |
| STEP-14 | Predictions API | ⬜ |
| STEP-15 | Prediction Scoring | ⬜ |
| STEP-16 | User Profile API | ⬜ |
| STEP-17 | Activity Logging | ⬜ |
| STEP-18 | Admin API | ⬜ |
| STEP-19 | React App Setup | ⬜ |
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
- Tests: `tests/test_step1_scaffold.py` (3 tests — app creates, blueprints registered, 404 on unknown route)

---

### ✅ STEP-2: MySQL Schema
`schema.sql` — 9 tables, 8 indexes, 2 stored procedures, 1 trigger.

Tables: `users`, `teams`, `players`, `venues`, `matches`, `match_events`, `predictions`, `user_activity`, `session_audit`

Stored procedures: `calculate_prediction_points(match_id)`, `get_group_standings(group_name)`

Trigger: `update_player_stats` on `match_events` INSERT

- Tests: `tests/test_step2_schema.py` (6 tests — tables, procedures, trigger, indexes, unique constraints)

---

### ✅ STEP-3: Seed Data
`generate_seed.py` → `seed.sql` — real 2022 World Cup data.

- 32 teams (Groups A–H, real coaches, FIFA rankings)
- 8 venues (Qatar stadiums)
- 736 players (23/team; detailed real squads for ARG, FRA, BRA, ENG, POR, CRO, MAR, GER)
- 64 matches, all `completed` with real scores (48 group + 16 knockout)

- Tests: `tests/test_step3_seed.py` (12 tests — counts, group sizes, score integrity, final result, no duplicate jerseys)

---

### STEP-4: Database Connection Layer
`backend/app/db/connection.py` — PyMySQL wrapper with connection pooling.

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

- `@require_auth` — reads cookie, calls `get_session`, attaches `g.user`; 401 if missing/expired
- `@require_admin` — wraps `@require_auth`, checks `g.user['is_admin']`; 403 if not

- Tests: `tests/test_step7_middleware.py`
  - No cookie → 401
  - Valid non-admin cookie → 403 on admin route
  - Valid admin cookie → passes through

---

## Phase 2 — Teams, Matches, Venues

### STEP-8: Teams API
`backend/app/routes/teams.py`

`GET /api/teams` — all 32 teams; optional `?group=A`
`GET /api/teams/{id}` — team + full squad

- Tests: `tests/test_step8_teams.py`
  - `/api/teams` returns 32 teams
  - `?group=A` returns exactly 4
  - Team detail includes `players` array

---

### STEP-9: Matches API
`backend/app/routes/matches.py`

`GET /api/matches` — filters: `?date=YYYY-MM-DD`, `?stage=group`, `?team_id=5`, `?venue_id=3`
`GET /api/matches/{id}` — match detail + `events` array (minute order)

- Tests: `tests/test_step9_matches.py`
  - No filter returns 64 matches
  - `?stage=group` returns 48
  - `?team_id` returns only that team's matches
  - Match detail shape correct

---

### STEP-10: Venues API
`backend/app/routes/venues.py`

`GET /api/venues` — all 8 venues

- Tests: `tests/test_step10_venues.py`
  - Returns 8 records
  - Each record has `name`, `city`, `country`, `capacity`

---

### STEP-11: Player Leaderboards API
`backend/app/routes/leaderboards.py`

`GET /api/leaderboards/goals` — top 10 by goals DESC, assists DESC; includes team name
`GET /api/leaderboards/assists` — top 10 by assists DESC, goals DESC

- Tests: `tests/test_step11_leaderboards.py`
  - Each endpoint returns exactly 10 records
  - Sorted correctly (Mbappe leads goals with 8, Messi second with 7)

---

## Phase 3 — Standings

### STEP-12: Group Standings API
`backend/app/routes/standings.py`

`GET /api/standings/group` — all 8 groups; `?group=A` for one
Calls `get_group_standings` stored procedure.
Each row: `matches_played`, `wins`, `draws`, `losses`, `goals_for`, `goals_against`, `goal_difference`, `points`

- Tests: `tests/test_step12_standings.py`
  - All 8 groups present
  - Group A: Netherlands and Senegal at top
  - Points arithmetic correct

---

### STEP-13: Knockout Bracket API
`backend/app/routes/standings.py` (same file)

`GET /api/standings/knockout` — bracket as nested JSON

Rounds: `round_of_16`, `quarterfinal`, `semifinal`, `third_place`, `final`
Each slot: `match_id`, `home_team`, `away_team`, `score`, `status`

- Tests: `tests/test_step13_bracket.py`
  - All 5 round keys present
  - Final slot shows Argentina vs France, 3-3

---

## Phase 4 — Predictions

### STEP-14: Predictions API
`backend/app/routes/predictions.py`

`POST /api/predictions/{match_id}` — `@require_auth`, UPSERT; match must be `scheduled`
`GET /api/user/predictions` — `@require_auth` — user's predictions with match info and points
`GET /api/predictions/leaderboard` — public — top 50 by SUM(points_earned) + exact_count

- Tests: `tests/test_step14_predictions.py`
  - Predict on completed match → 400
  - Predict on scheduled match → 201; update → 200
  - Leaderboard sorted by total DESC

---

### STEP-15: Prediction Scoring
`backend/app/db/scoring.py`

Called by admin match update after status → `completed`.
Calls `calculate_prediction_points(match_id)`.

- Tests: `tests/test_step15_scoring.py`
  - Exact score → 3 pts
  - Correct outcome → 1 pt
  - Wrong → 0 pts

---

## Phase 5 — User Profile & Admin

### STEP-16: User Profile API
`backend/app/routes/user.py`

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

`log_activity(user_id, action, ip_address)` — INSERT into `user_activity`
Auto-purge: records older than 90 days on read
`GET /api/user/activity` — `@require_auth` — last 100 records

- Tests: `tests/test_step17_activity.py`
  - register → login → predict produces 3 activity rows

---

### STEP-18: Admin API
`backend/app/routes/admin.py` — all `@require_admin`

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

- Vite proxy: `/api` → `http://localhost:5000`
- `AuthContext` — user state, login/logout helpers
- `<Navbar>` + `<Outlet>` layout
- Protected route wrapper → redirects to `/login`

- Tests: `tests/test_step19_frontend.py` — `npm run build` exits 0; proxy config present

---

### STEP-20: Auth Pages
`Login.jsx`, `Register.jsx`

- Field errors from API; password strength meter on register
- Auto-login redirect on success

---

### STEP-21: Home Page
`Home.jsx` — today's matches; upcoming if none today; quick links

---

### STEP-22: Matches Page + Match Detail
`Matches.jsx` — filter bar (date, stage, team, venue); inline predict form
`MatchDetail.jsx` — events timeline for completed matches

---

### STEP-23: Standings Page
`Standings.jsx` — tabs: Group Stage | Knockout Bracket
- Group Stage: group selector A–H, table with MP/W/D/L/GF/GA/GD/Pts; top 2 highlighted
- Knockout: bracket from `/api/standings/knockout`, rounds left-to-right

---

### STEP-24: Teams Page + Team Detail
`Teams.jsx` — group filter tabs; team cards
`TeamDetail.jsx` — squad table (#, Name, Position)

---

### STEP-25: Players Page
`Players.jsx` — tabs: Top Scorers | Top Assists; 10 rows each

---

### STEP-26: Predictions Page
`Predictions.jsx` — `@require_auth`; table with predicted/actual/points; inline edit for scheduled

---

### STEP-27: Leaderboard Page
`Leaderboard.jsx` — top 50 by points; current user highlighted

---

### STEP-28: Profile Page
`Profile.jsx` — `@require_auth`; update email/team; change password; activity log; deactivate

---

### STEP-29: Admin Page
`Admin.jsx` — admin only; tabs: Match Management | User Management | System Stats

---

## Phase 7 — Deployment

### STEP-30: Gunicorn Config
`wsgi.py` + `gunicorn.conf.py` (workers = 2×CPU+1, timeout 30s)
Flask serves `frontend/dist/` as static files.

- Tests: `tests/test_step30_gunicorn.py` — gunicorn starts; `/api/teams` responds

---

### STEP-31: End-to-End Validation
Manual + scripted run through all PRD flows:
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
