# PLAN.md — WorldCup 2026 Hub Implementation Plan

Steps are labeled STEP-N for easy reference and modification.

---

## Phase 1 — Foundation

### STEP-1: Project Scaffolding
Create the directory structure and config files.

```
worldcup/
  backend/
    app/
      routes/
      db/
      auth/
      admin/
    tests/
    requirements.txt
    .env.example
    wsgi.py
  frontend/
    src/
      pages/
      components/
      api/
    package.json
    tailwind.config.js
    vite.config.js
```

- `requirements.txt`: flask, flask-cors, redis, pymysql, bcrypt, python-dotenv
- `.env.example` with all variables from PRD §13
- Verify: `flask run` starts without errors

---

### STEP-2: MySQL Schema
Write and apply `schema.sql` defining all tables, indexes, stored procedures, and triggers from PRD §5.

Tables:
- `users` — id, username, email, password_hash, is_admin, is_active, failed_login_count, locked_until, favorite_team_id, created_at
- `teams` — id, name, country_code, group_name, fifa_ranking, coach
- `players` — id, team_id, name, position, jersey_number, goals, assists
- `venues` — id, name, city, country, capacity
- `matches` — id, home_team_id, away_team_id, venue_id, match_date, stage, status, home_score, away_score, group_name
- `match_events` — id, match_id, player_id, event_type, minute
- `predictions` — id, user_id, match_id, home_score, away_score, points_earned, created_at, updated_at
- `user_activity` — id, user_id, action, ip_address, created_at
- `session_audit` — id, user_id, session_id, created_at, destroyed_at

Stored procedures: `calculate_prediction_points(match_id)`, `get_group_standings(group_name)`
Trigger: `update_player_stats` on `match_events` INSERT

Indexes per PRD §5.3.

- Verify: `mysql < schema.sql` runs clean; `SHOW TABLES` lists all 9 tables

---

### STEP-3: Seed Data
Write `seed.sql` to populate static tournament data:

- 48 teams with group assignments (Groups A–L, 4 teams each), FIFA rankings, coaches
- 16 venues (USA/Canada/Mexico cities from PRD §1)
- 104 matches (group stage + knockout rounds) with dates, venues, stages
- ~1,200 placeholder players (at least 1 per team for schema validation)

- Verify: `SELECT COUNT(*) FROM teams` → 48; `SELECT COUNT(*) FROM matches` → 104

---

### STEP-4: Database Connection Layer
`backend/app/db/connection.py` — thin wrapper around PyMySQL with connection pooling.

- `get_connection()` returns a connection from pool (pool size: 20)
- `query(sql, params)` — parameterized execute, returns rows as dicts
- `execute(sql, params)` — parameterized execute for INSERT/UPDATE/DELETE
- No string concatenation in any query (PRD §4.2)

- Verify: unit test calls `query("SELECT 1")` and gets `[{'1': 1}]`

---

### STEP-5: Redis Session Layer
`backend/app/auth/session.py` — session create/read/refresh/destroy.

- `create_session(user_id, username, is_admin, favorite_team)` → session_id (UUID4)
  - Stores JSON in Redis key `session:{session_id}` with 24h TTL
  - Tracks per-user session list in `user_sessions:{user_id}` (max 5; evict oldest)
  - Appends to `session_audit` table
- `get_session(session_id)` → dict or None; refreshes TTL on success
- `destroy_session(session_id)` — deletes Redis key, marks audit record
- `destroy_all_sessions(user_id)` — used on password change / admin revoke

Cookie settings: httpOnly, SameSite=Lax, Secure in production (from env).

- Verify: create → get → destroy round-trip; max-5 eviction test

---

### STEP-6: Auth API
`backend/app/routes/auth.py` — register, login, logout endpoints.

`POST /api/auth/register`
- Validate username (3–50 chars, `^[a-zA-Z0-9_]+$`), email format, password strength
- Uniqueness check (409 on conflict)
- Hash password with bcrypt (12 rounds)
- Insert user, create session, set cookie
- Rate limit: 5/hour per IP (Redis counter `ratelimit:register:{ip}`)

`POST /api/auth/login`
- Accept username or email + password
- Reject if account locked (423); check `locked_until`
- Verify bcrypt hash; increment `failed_login_count` on failure; lock at 10 (15 min)
- On success: reset counter, create session, set cookie
- Rate limit: 10/min per IP

`POST /api/auth/logout`
- Destroy session from cookie; clear cookie

- Verify: register → cookie set; login with wrong password 10× → locked; logout → session gone

---

### STEP-7: Auth Middleware
`backend/app/auth/middleware.py` — decorators for route protection.

- `@require_auth` — reads session cookie, calls `get_session`, attaches `g.user`; returns 401 if missing/expired
- `@require_admin` — wraps `@require_auth`, checks `g.user['is_admin']`; returns 403 if not

- Verify: protected route returns 401 without cookie; 403 with non-admin cookie

---

## Phase 2 — Teams, Matches, Venues

### STEP-8: Teams API
`backend/app/routes/teams.py`

`GET /api/teams` — list all 48 teams; optional `?group=A` filter
`GET /api/teams/{id}` — team detail + full squad (players joined)

- Verify: `/api/teams?group=A` returns exactly 4 teams; team detail includes player array

---

### STEP-9: Matches API
`backend/app/routes/matches.py`

`GET /api/matches` — list matches; filters: `?date=YYYY-MM-DD`, `?stage=group`, `?team_id=5`, `?venue_id=3`
`GET /api/matches/{id}` — match detail + match_events timeline (goals, cards in minute order)

Status field: `scheduled | live | completed | cancelled`

- Verify: date filter returns only matches on that day; match detail includes events array

---

### STEP-10: Venues API
`backend/app/routes/venues.py`

`GET /api/venues` — list all 16 venues with city and country

- Verify: returns 16 records

---

### STEP-11: Player Leaderboards API
`backend/app/routes/leaderboards.py`

`GET /api/leaderboards/goals` — top 10 by goals DESC, assists DESC; includes team name
`GET /api/leaderboards/assists` — top 10 by assists DESC, goals DESC

- Verify: returns exactly 10 records each; sorted correctly

---

## Phase 3 — Standings

### STEP-12: Group Standings API
`backend/app/routes/standings.py`

`GET /api/standings/group` — calls `get_group_standings` stored procedure for all 8 groups (or `?group=A` for one)

Each team row: matches_played, wins, draws, losses, goals_for, goals_against, goal_difference, points

Tie-breaker order per PRD §9.2: points → GD → GF → head-to-head → fair play → FIFA ranking

- Verify: after seeding 3 completed group matches, standings reflect correct points and order

---

### STEP-13: Knockout Bracket API
`backend/app/routes/standings.py` (add to same file)

`GET /api/standings/knockout` — returns bracket structure as nested JSON

Rounds: Round of 32, Round of 16, Quarterfinals, Semifinals, Third place, Final
Each slot: match_id (or null), home_team, away_team, score, status

- Verify: endpoint returns all 5 round keys; null slots for unplayed matches

---

## Phase 4 — Predictions

### STEP-14: Predictions API
`backend/app/routes/predictions.py`

`POST /api/predictions/{match_id}` — `@require_auth`
- Validate match exists and status = `scheduled`
- Validate home_score / away_score: integer 0–20
- UPSERT (create if none, update if exists)
- Rate limit: 30/min per user

`GET /api/user/predictions` — `@require_auth` — all user predictions with match info, predicted score, actual score, points_earned

`GET /api/predictions/leaderboard` — public — top 50 users by SUM(points_earned), plus exact_count

- Verify: predict on completed match → 400; predict on scheduled match → 201; update → 200; leaderboard sorted by total DESC

---

### STEP-15: Prediction Scoring
`backend/app/db/scoring.py`

Called by admin match update (STEP-18) after setting status = `completed`.
Calls stored procedure `calculate_prediction_points(match_id)` which:
- Exact score → 3 points
- Correct outcome (W/D/L) → 1 point
- Otherwise → 0 points
- Updates `predictions.points_earned` for all rows matching match_id

- Verify: set a match complete with score 2-1; users who predicted 2-1 get 3pts; users who predicted 3-0 get 0pts; users who predicted 1-0 get 1pt

---

## Phase 5 — User Profile & Admin

### STEP-16: User Profile API
`backend/app/routes/user.py`

`GET /api/user/profile` — `@require_auth`
`PUT /api/user/profile` — update email, favorite_team_id
`POST /api/user/change-password` — verify old password, hash new, call `destroy_all_sessions`, re-create session
`DELETE /api/user/profile` — soft delete: set `is_active = false`
`PUT /api/user/favorite-team` — shortcut to set favorite_team_id

- Verify: change-password invalidates other sessions; soft delete blocks login (401)

---

### STEP-17: Activity Logging
`backend/app/auth/activity.py`

`log_activity(user_id, action, ip_address)` — INSERT into `user_activity`

Hook into: registration, login, prediction submit, profile update
Auto-purge: records older than 90 days deleted on read (lazy) or via a cleanup call

`GET /api/user/activity` — `@require_auth` — returns user's own activity log (last 100)

- Verify: register → login → predict produces 3 activity rows for that user

---

### STEP-18: Admin API
`backend/app/routes/admin.py` — all routes use `@require_admin`

`PUT /api/admin/matches/{id}/score`
- Accepts home_score, away_score, status
- Validates status enum
- Updates match; if status = `completed`, calls `calculate_prediction_points`

`GET /api/admin/users` — paginated list of all users
`POST /api/admin/users/{id}/lock` — set `locked_until = now + 15min` (or permanent flag)
`POST /api/admin/users/{id}/unlock` — clear lock
`GET /api/admin/sessions` — list all active Redis sessions (scan `session:*`)
`DELETE /api/admin/sessions/{user_id}` — calls `destroy_all_sessions(user_id)`
`GET /api/admin/stats` — active session count, total users, predictions in last 24h

- Verify: update score to completed → predictions scored; lock user → login returns 423; stats endpoint returns all 3 keys

---

## Phase 6 — Frontend

### STEP-19: React App Setup
Bootstrap with Vite + React + TailwindCSS.

- `npm create vite@latest frontend -- --template react`
- Install: tailwindcss, react-router-dom, axios
- Configure Vite proxy: `/api` → `http://localhost:5000`
- Global layout: `<Navbar>` (links, login/logout state) + `<Outlet>`
- Auth context: `AuthContext` — stores user from `/api/user/profile` on load; provides login/logout helpers
- Protected route wrapper: redirects to `/login` if unauthenticated

- Verify: `npm run dev` loads; navbar renders; `/login` redirects unauthenticated `/predictions`

---

### STEP-20: Auth Pages
`frontend/src/pages/Login.jsx` and `Register.jsx`

Login:
- Username or email field + password
- Shows field errors from API (400/401/423)
- Redirects to home on success

Register:
- Username, email, password fields
- Client-side password strength meter (uppercase + number + special char indicators)
- Shows per-field errors from API (400/409)
- Auto-login and redirect on success (201)

- Verify: wrong password shows error; duplicate username shows "already taken"; successful register lands on home

---

### STEP-21: Home Page
`frontend/src/pages/Home.jsx`

- Today's matches section (calls `/api/matches?date=TODAY`)
- Upcoming matches (next 3 days) if no matches today
- Quick links: Standings, Teams, Predictions (if logged in), Leaderboard

- Verify: matches for today's date appear; links navigate correctly

---

### STEP-22: Matches Page + Match Detail
`frontend/src/pages/Matches.jsx` and `MatchDetail.jsx`

Matches:
- Filter bar: date picker, stage dropdown, team select, venue select
- Match card: teams, date/time, venue, status badge, score (if completed), "Predict" button (if scheduled + logged in)
- "Predict" opens inline score input form; submit calls `POST /api/predictions/{match_id}`

Match Detail (`/match/{id}`):
- Teams, date, venue, score, status
- Events timeline (minute, player, event type icon) for completed matches

- Verify: filter by team shows only that team's matches; predict form submits and shows confirmation; events list displays for completed match

---

### STEP-23: Standings Page
`frontend/src/pages/Standings.jsx`

Two tabs: "Group Stage" | "Knockout Bracket"

Group Stage:
- Group selector (A–L)
- Table: Team | MP | W | D | L | GF | GA | GD | Pts
- Top 2 highlighted (qualify)

Knockout Bracket:
- Visual bracket from `/api/standings/knockout`
- Rounds displayed left-to-right; null slots show "TBD"

- Verify: group select switches table data; bracket renders all rounds

---

### STEP-24: Teams Page + Team Detail
`frontend/src/pages/Teams.jsx` and `TeamDetail.jsx`

Teams:
- Group filter tabs (All / A / B / …)
- Team card: flag placeholder, name, FIFA ranking, coach
- Click → Team Detail

Team Detail (`/team/{id}`):
- Header: name, group, ranking, coach
- Squad table: #, Name, Position

- Verify: group filter shows 4 teams; squad table populates

---

### STEP-25: Players Page
`frontend/src/pages/Players.jsx`

Two tabs: "Top Scorers" | "Top Assists"
Table: Rank | Player | Team | Goals | Assists

- Verify: each tab shows 10 rows; sorted correctly

---

### STEP-26: Predictions Page
`frontend/src/pages/Predictions.jsx` — `@require_auth`

- Table of user's predictions: Match | Predicted Score | Actual Score | Points
- Status badges: pending / correct / wrong
- Quick-edit for scheduled matches (inline score inputs)

- Verify: completed predictions show actual score and points; scheduled show edit form

---

### STEP-27: Leaderboard Page
`frontend/src/pages/Leaderboard.jsx`

- Table: Rank | Username | Total Points | Exact Predictions
- Top 50 users
- Current user row highlighted if in top 50

- Verify: sorted by points DESC; 50 rows max

---

### STEP-28: Profile Page
`frontend/src/pages/Profile.jsx` — `@require_auth`

- Display: username, email, join date, favorite team (with edit)
- Change password form (old + new + confirm)
- Activity log table (last 100 actions)
- Deactivate account button (with confirmation modal)

- Verify: update email persists; password change logs out other sessions; deactivate → logged out

---

### STEP-29: Admin Page
`frontend/src/pages/Admin.jsx` — admin only (redirects non-admins)

Three sections (tabs):
1. **Match Management** — match list with "Update Score" button → modal for score + status
2. **User Management** — user table with lock/unlock buttons; "Revoke Sessions" button
3. **System Stats** — cards: active sessions, total users, predictions (24h)

- Verify: update score to completed → prediction points recalculate; lock user → login blocked

---

## Phase 7 — Integration & Deployment

### STEP-30: Gunicorn Config
`wsgi.py` entry point for Gunicorn.
`gunicorn.conf.py`: workers = (2 × CPU cores) + 1, timeout = 30s, bind = 0.0.0.0:5000

Flask serves the React build as static files from `frontend/dist/` (via `send_from_directory`).
CORS configured in Flask to allow only `CORS_ORIGINS` env value.
Cookie `Secure` flag driven by `SESSION_COOKIE_SECURE` env var.

- Verify: `gunicorn -c gunicorn.conf.py wsgi:app` starts; `curl /api/teams` responds

---

### STEP-31: End-to-End Validation
Run through all PRD user flows manually (or with a test script):

1. Register new user → auto-login ✓
2. Browse matches → make prediction → see in `/predictions` ✓
3. Admin updates match score → prediction points calculated ✓
4. View standings → group table correct ✓
5. View knockout bracket ✓
6. Leaderboard reflects correct points ✓
7. 10 failed logins → account locked → admin unlocks ✓
8. Password change → other sessions invalidated ✓
9. Rate limits return 429 when exceeded ✓
10. Non-admin blocked from `/admin` ✓

- Verify: all 10 flows pass without errors

---

## Step Dependency Map

```
STEP-1 (scaffold)
  └─ STEP-2 (schema) ─── STEP-3 (seed)
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
                                     ├─ STEP-20 (auth pages)
                                     ├─ STEP-21 (home)
                                     ├─ STEP-22 (matches)
                                     ├─ STEP-23 (standings)
                                     ├─ STEP-24 (teams)
                                     ├─ STEP-25 (players)
                                     ├─ STEP-26 (predictions page)
                                     ├─ STEP-27 (leaderboard page)
                                     ├─ STEP-28 (profile page)
                                     └─ STEP-29 (admin page)
                                          └─ STEP-30 (gunicorn)
                                               └─ STEP-31 (e2e validation)
```
