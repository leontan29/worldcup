```markdown
# Product Requirements Document (PRD)
## 2026 World Cup Web Application

---

## 1. Executive Summary

**Product Name**: WorldCup 2026 Hub

**Description**: A web application for the 2026 FIFA World Cup (48 teams, 104 matches, 16 host cities across USA, Canada, Mexico). Supports multiple users with registration/login, session management, match predictions, and leaderboards.

**Target Launch**: May 2026

---

## 2. Technical Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+ with Flask |
| Database | MySQL 8.0 |
| Session Store | Redis |
| Frontend | React + TailwindCSS |
| Authentication | Session-based (Redis) |
| Password Hashing | bcrypt |
| Deployment | Gunicorn + Nginx |

**Constraints**: No ORM (raw SQL only), no Celery (synchronous operations), no auto-documentation tools.

---

## 3. Functional Requirements

### 3.1 User Authentication

**3.1.1 Registration**
- Users can register with username, email, password
- Username: 3-50 characters, alphanumeric + underscore only, unique
- Email: valid format, unique
- Password: minimum 8 characters, requires uppercase letter, number, and special character
- Successful registration creates user account and automatically logs user in
- Rate limit: 5 registrations per IP per hour

**3.1.2 Login**
- Users can log in with username OR email plus password
- Failed login attempts tracked per user
- Account locks after 10 failed attempts (15 minute lockout)
- Successful login creates Redis session (24 hour TTL)
- Session includes: user_id, username, is_admin flag, favorite team

**3.1.3 Logout**
- Users can log out, destroying their Redis session
- Session cookie removed from browser

**3.1.4 Session Management**
- Sessions stored in Redis (not in-memory)
- Session TTL refreshes on each authenticated request
- Session cookie: httpOnly, secure in production, SameSite=Lax
- Maximum 5 concurrent sessions per user

### 3.2 Team & Player Information

**3.2.1 Team Listing**
- Display all 48 teams with group filtering (Groups A-H)
- Each team shows: name, country code, FIFA ranking, coach, flag icon

**3.2.2 Team Detail**
- View individual team page with full squad list
- Squad shows: player name, position, jersey number

**3.2.3 Player Leaderboards**
- Top 10 goal scorers
- Top 10 assists
- Sort by goals (descending), then assists

### 3.3 Match Schedule & Results

**3.3.1 Match Listing**
- Display all 104 matches with filtering by: date, stage, team, venue
- Show match status: scheduled, live, completed
- For completed matches: show final score
- For live matches: show current score (if implemented)

**3.3.2 Match Detail**
- Individual match page with: teams, date, venue, score, status
- Match events timeline (goals, cards) for completed matches

**3.3.3 Group Standings**
- Standings for each of 8 groups
- Sort by: points (win=3, draw=1, loss=0), goal difference, goals scored, head-to-head
- Show: matches played, wins, draws, losses, goals for/against, points

**3.3.4 Knockout Bracket**
- Visual bracket showing: Round of 32, Round of 16, Quarterfinals, Semifinals, Final
- Third place match included
- Bracket populates as matches complete

### 3.4 Predictions (Authenticated Users Only)

**3.4.1 Making Predictions**
- Users predict exact score for any scheduled match
- Predictions can be created or updated until match kickoff
- Score range: 0-20 for each team

**3.4.2 Scoring System**
- Exact score match: 3 points
- Correct winner (or correct draw): 1 point
- Incorrect: 0 points
- Points auto-calculated when match status becomes "completed"

**3.4.3 User Prediction History**
- Users view all their predictions
- Shows: match, predicted score, actual score (if completed), points earned

**3.4.4 Global Leaderboard**
- Display top 50 users by total prediction points
- Shows: rank, username, total points, exact predictions count

### 3.5 User Profile

**3.5.1 Profile Management**
- View profile: username, email, join date, favorite team
- Update: email, favorite team
- Change password: requires old password confirmation
- Deactivate account (soft delete)

**3.5.2 Activity Log**
- User views their own activity history
- Actions logged: registration, login, prediction submissions, profile updates

### 3.6 Admin Functions

**3.6.1 Match Management**
- Update match scores
- Change match status (scheduled → live → completed → cancelled)
- Set match winner (automatically derived from score or manually set)

**3.6.2 User Management**
- View all registered users
- Manually lock/unlock user accounts
- View active sessions for any user
- Revoke specific user sessions

**3.6.3 System Overview**
- View active session count
- View total registered users
- View prediction submission rates

---

## 4. Non-Functional Requirements

### 4.1 Performance
- API response time: < 200ms (95th percentile)
- Session lookup from Redis: < 10ms
- Concurrent users supported: 10,000
- Page load time: < 3 seconds on 3G connection

### 4.2 Security
- Passwords hashed with bcrypt (12 rounds)
- Session cookies: httpOnly, secure flag in production
- Rate limiting: per IP address
- SQL injection prevention: all queries parameterized (no string concatenation)
- CORS configured to allow only frontend domain

### 4.3 Availability
- Target uptime: 99.9% during tournament
- Read-only mode possible if database issues occur (scores and standings still visible)
- Graceful degradation: anonymous views work without Redis

### 4.4 Data Retention
- User accounts: retained until deleted (soft delete)
- Predictions: retained permanently
- User activity logs: retained for 90 days
- Session audit: retained for 30 days
- Active Redis sessions: until TTL expires or logout

---

## 5. Database Requirements

### 5.1 Core Tables
| Table | Purpose | Estimated Row Count |
|-------|---------|---------------------|
| users | Authentication and profiles | 50,000 |
| teams | Tournament teams | 48 |
| players | Team rosters | ~1,200 |
| matches | Schedule and results | 104 |
| venues | Stadium information | 16 |
| predictions | User match predictions | 5.2 million (50k users × 104 matches) |
| match_events | Goals, cards, substitutions | ~2,000 |
| user_activity | Audit trail | 500,000 |
| session_audit | Session backup | 100,000 |

### 5.2 Key Relationships
- Users → predictions (one-to-many)
- Users → favorite_team (many-to-one)
- Teams → matches as home or away
- Matches → predictions (one-to-many)

### 5.3 Indexing Strategy
- Index on matches.match_date for schedule queries
- Index on predictions.user_id and predictions.match_id for lookups
- Index on teams.group_name for standings queries
- Unique constraint on users.username and users.email
- Composite index on predictions(user_id, points_earned) for leaderboard

### 5.4 Stored Procedures
- calculate_prediction_points: updates points for all predictions on a completed match
- get_group_standings: returns sorted standings with tie-breakers

### 5.5 Triggers
- update_player_stats: auto-updates goal/assist counts when match_events inserted

---

## 6. API Endpoints

### 6.1 Public Endpoints (No Authentication Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/teams | List all teams (filter by group) |
| GET | /api/teams/{id} | Team details with squad |
| GET | /api/matches | List matches (filter by date, stage, team, venue) |
| GET | /api/matches/{id} | Match details with events |
| GET | /api/standings/group | Group standings |
| GET | /api/standings/knockout | Knockout bracket structure |
| GET | /api/leaderboards/goals | Top goal scorers |
| GET | /api/leaderboards/assists | Top assists |
| GET | /api/venues | List all venues |

### 6.2 Authentication Endpoints (Public)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Create new user account |
| POST | /api/auth/login | Authenticate and create session |
| POST | /api/auth/logout | Destroy session |

### 6.3 Protected Endpoints (Authentication Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/user/profile | Get current user profile |
| PUT | /api/user/profile | Update profile |
| PUT | /api/user/favorite-team | Set favorite team |
| POST | /api/user/change-password | Change password |
| GET | /api/user/predictions | Get user's predictions with points |
| GET | /api/user/activity | Get user activity log |
| POST | /api/predictions/{match_id} | Create/update prediction |
| GET | /api/predictions/leaderboard | Global prediction leaderboard |

### 6.4 Admin Endpoints (Admin Role Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| PUT | /api/admin/matches/{id}/score | Update match score and status |
| GET | /api/admin/users | List all users |
| POST | /api/admin/users/{id}/lock | Lock user account |
| POST | /api/admin/users/{id}/unlock | Unlock user account |
| GET | /api/admin/sessions | View all active sessions |
| DELETE | /api/admin/sessions/{user_id} | Revoke user's sessions |
| GET | /api/admin/stats | System statistics |

---

## 7. Frontend Pages

| Page | Route | Authentication | Description |
|------|-------|----------------|-------------|
| Home | / | Public | Today's matches, featured content |
| Login | /login | Public | Login form |
| Register | /register | Public | Registration form |
| Matches | /matches | Public | Full schedule with filters |
| Match Detail | /match/{id} | Public | Single match view |
| Standings | /standings | Public | Group tables + bracket |
| Teams | /teams | Public | Team listing by group |
| Team Detail | /team/{id} | Public | Squad and stats |
| Players | /players | Public | Goal/assist leaderboards |
| Predictions | /predictions | Required | User's predictions and form |
| Leaderboard | /leaderboard | Public | Top predictors |
| Profile | /profile | Required | User settings and history |
| Admin | /admin | Admin | Management dashboard |

---

## 8. User Flows

### 8.1 New User Registration Flow
1. User clicks "Register" on home page
2. User enters username, email, password
3. Frontend validates format, shows password strength meter
4. Submit → API validates uniqueness and format
5. On success: user auto-logged in, redirected to home page
6. On failure: error messages displayed for each field

### 8.2 Making a Prediction Flow
1. User logs in
2. User navigates to Matches page
3. Finds a scheduled match, clicks "Predict"
4. Modal or form opens with home/away score inputs
5. User enters scores, submits
6. Confirmation message appears
7. User can edit prediction until match starts (form shows existing prediction)

### 8.3 Match Completion Flow (Admin)
1. Admin logs in, navigates to Admin panel
2. Finds completed match, clicks "Update Score"
3. Enters final home/away scores
4. Submits → API updates match status to "completed"
5. System automatically calculates points for all user predictions
6. Leaderboards refresh (cached data invalidated)

### 8.4 Viewing Standings Flow
1. User clicks "Standings" in navigation
2. View loads group tables (default: Group A)
3. User can switch groups via dropdown
4. Knockout bracket tab shows tournament progression
5. No login required

---

## 9. Business Rules

### 9.1 Prediction Rules
- Users cannot predict matches that have already started
- Predictions can be edited any time before kickoff
- No limit on number of predictions per user
- Predictions cannot be deleted (only updated)

### 9.2 Tie-Breakers for Group Standings
1. Points
2. Goal difference
3. Goals scored
4. Head-to-head results
5. Fair play points (yellow/red cards)
6. FIFA ranking

### 9.3 Account Lockout Rules
- 10 failed login attempts within any time period
- Lock duration: 15 minutes
- Successful login resets counter
- Admin can manually unlock

### 9.4 Session Rules
- Idle session timeout: 24 hours
- Active session timeout refreshed on each request
- Password change invalidates all existing sessions
- Admin can revoke any user's sessions

---

## 10. Data Validation Rules

### 10.1 Registration
| Field | Rule |
|-------|------|
| Username | Required, 3-50 chars, alphanumeric + underscore only, unique |
| Email | Required, valid format (contains @ and domain), unique |
| Password | Required, 8+ chars, 1 uppercase, 1 number, 1 special character |

### 10.2 Prediction
| Field | Rule |
|-------|------|
| home_score | Required, integer 0-20 |
| away_score | Required, integer 0-20 |
| match_id | Must exist and be in 'scheduled' status |

### 10.3 Match Score (Admin)
| Field | Rule |
|-------|------|
| home_score | Required, integer 0-20 |
| away_score | Required, integer 0-20 |
| status | One of: scheduled, live, completed, cancelled |

---

## 11. Error Handling

### 11.1 HTTP Status Codes

| Code | Use Case |
|------|----------|
| 200 | Success |
| 201 | Resource created (registration) |
| 400 | Validation error (invalid input) |
| 401 | Not authenticated |
| 403 | Forbidden (admin required) |
| 404 | Resource not found |
| 409 | Conflict (duplicate username/email) |
| 423 | Locked (account locked) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

### 11.2 Error Response Format
```json
{
  "error": "Human readable message",
  "details": {} // Optional field-specific errors
}
```

### 11.3 Validation Error Example
```json
{
  "error": "Validation failed",
  "details": {
    "username": ["Username already taken"],
    "password": ["Must contain uppercase letter", "Must contain number"]
  }
}
```

---

## 12. Rate Limiting

| Endpoint Category | Limit | Period |
|-------------------|-------|--------|
| Registration | 5 requests | 1 hour per IP |
| Login | 10 requests | 1 minute per IP |
| Prediction submission | 30 requests | 1 minute per user |
| Public GET endpoints | 100 requests | 1 minute per IP |
| Admin endpoints | 20 requests | 1 minute per user |

---

## 13. Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| SECRET_KEY | Flask session signing | Yes |
| DB_HOST | MySQL host | Yes |
| DB_USER | MySQL username | Yes |
| DB_PASSWORD | MySQL password | Yes |
| DB_NAME | MySQL database name | Yes |
| REDIS_URL | Redis connection string | Yes |
| CORS_ORIGINS | Frontend domain(s) | Yes |
| FLASK_ENV | development/production | Yes |
| SESSION_COOKIE_SECURE | true/false (HTTPS only) | Yes |

---

## 14. Performance Targets

| Metric | Target |
|--------|--------|
| API response (p95) | < 200ms |
| Database query (p95) | < 100ms |
| Redis session lookup | < 10ms |
| Group standings calculation | < 500ms |
| Leaderboard generation | < 300ms |
| Page load (3G) | < 3 seconds |
| Concurrent users | 10,000 |
| Requests per second | 500+ |

---

## 15. Success Metrics

| Metric | Target |
|--------|--------|
| User registrations | 50,000 pre-tournament |
| Daily active users | 25,000 during tournament |
| Predictions per match | 15,000 average |
| Session duration | 15 minutes average |
| API uptime | 99.9% |
| Login success rate | > 99% |

---

## 16. Development Phases

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1 | 2 weeks | Database schema, user auth, Redis session |
| Phase 2 | 2 weeks | Teams, matches, venues data models and APIs |
| Phase 3 | 2 weeks | Standings calculation, match schedule views |
| Phase 4 | 2 weeks | Predictions system, scoring, leaderboards |
| Phase 5 | 1 week | Admin functions, user profiles, activity logging |
| Phase 6 | 1 week | Frontend integration, testing, deployment |

---

## 17. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| High traffic during matches | High | High | Redis caching for read endpoints, connection pooling |
| Prediction scoring performance | Medium | Medium | Stored procedure optimization, batch scoring |
| Session storage exhaustion | Low | High | Redis memory monitoring, TTL enforcement |
| Database connection pool saturation | Low | Medium | Connection limits, read replicas for heavy queries |
| Rate limit bypass | Low | Medium | Redis-backed rate limiting per IP |

---

## 18. Assumptions & Dependencies

### Assumptions
- Tournament schedule finalized by March 2026
- Team rosters available 30 days before tournament
- Internet connection required for all users
- Modern browser with JavaScript enabled

### Dependencies
- MySQL database service operational
- Redis service operational
- Frontend built separately (React app)
- SSL certificate for production
- Backup storage for database
```

This PRD focuses on requirements, rules, and specifications without including code or detailed schema definitions.
