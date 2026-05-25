# myTIMeS Direct V2 — Full Code Review & Audit

Date: 2026-05-25

Author: Automated repository audit

Summary
-------
- This document contains a full project audit performed across the repository.
- It includes a per-file summary, findings, security notes, Docker and environment checks, and final scores with actionable recommendations.

Project layout (high level)
---------------------------
- backend/: Flask backend, database module, Dockerfile, Haar cascade XML
- backend/database/: sqlite helpers, schema, queries, analytics, export, maintenance
- frontend/: Expo React Native app with screens and components
- scripts/: helper scripts `setup.sh`, `start.sh`, `stop.sh`, `check-health.sh`
- docker-compose.yml, .gitignore, .dockerignore, README.md

Key findings (top-level)
------------------------
- The codebase is well-structured with a solid SQLite-based schema and helpful utility modules.
- Secrets (firebase service account) are correctly excluded from VCS and mounted at runtime by compose; however several environment/example files are missing which will block a first-time run.
- Frontend is a demo-style Expo app using local mock data (no API calls), so cross-checks between front and backend endpoints are limited.
- A few functional issues and omissions were found that should be addressed before production use.

Missing / attention-required files
---------------------------------
- `backend/.env` and `backend/.env.example` are referenced (in docker-compose and scripts) but are not present. `scripts/setup.sh` attempts to copy from `.env.example` — this will fail.
- `frontend/.env.example` and `frontend/.env` are also referenced by the setup script but missing.
- `backend/firebase_credentials.json` is intentionally not in repo (correct), but must be provided by operator for Firebase features.
- `reportlab` is required by `export_attendance_pdf` but is not listed in `backend/requirements.txt`.

Per-file audit (concise)
------------------------

1. .gitignore
- Purpose: ignore local files and secrets
- Findings: Good — `.env` and `firebase_credentials.json` ignored; `attendance.db` ignored. Consider explicitly ignoring `frontend/.env` if you add it.

2. .dockerignore
- Purpose: keep Docker context lean
- Findings: Good; secrets excluded from image build context.

3. docker-compose.yml
- Purpose: define services and mounts
- Findings: Backend service mapped to port 5000, mounts `./backend/database` and `./backend/models_storage`, and mounts `backend/firebase_credentials.json` and Haar cascade.
- Issue: `DATABASE_URL` is set but backend code does not read it; this is a duplication and could confuse operators. `backend/.env` is required but missing.

4. README.md
- Purpose: documentation
- Findings: Mostly placeholders; add installation steps, env variables, and deployment instructions.

5. scripts/setup.sh, start.sh, stop.sh, check-health.sh
- Purpose: convenience scripts
- Findings: `setup.sh` attempts to copy from `.env.example` which are not present; update script to create templates or include `.env.example` files. start.sh correctly fails early if backend/.env missing.

6. backend/Dockerfile
- Purpose: multi-stage Dockerfile
- Findings: Good two-stage build. Installs system deps for OpenCV, creates non-root `appuser`, runs gunicorn with `app:create_app()`. Ensure that installed packages from builder are placed correctly (the current copy to `/usr/local` is OK).

7. backend/requirements.txt
- Purpose: Python dependencies
- Findings: Contains Flask, OpenCV headless, firebase-admin, bcrypt, PyJWT, etc. Missing `reportlab` (used for PDF export) if PDF export is required.

8. backend/app.py
- Purpose: Flask app factory
- Findings: `create_app()` calls `init_db()` at startup and registers `health_bp`. It does not explicitly load `.env` into `os.environ`; consider using `python-dotenv` to load backend/.env (python-dotenv is present in requirements but not used here).

9. backend/health.py
- Purpose: simple health endpoints `/health/ping` and `/health/`
- Findings: returns DB table list and status; safe (no sensitive data leaked).

10. backend/haarcascade_frontalface_default.xml
- Purpose: OpenCV Haar cascade model file
- Findings: Present and licensed; OpenCV data license included. Keep as read-only mount in production.

11. backend/database/db.py
- Purpose: sqlite connection management
- Findings: Sets `DATABASE_PATH` to backend/database/attendance.db, uses `PRAGMA foreign_keys = ON`, and provides `get_db()` context manager. Suggestion: allow overriding path via env var to align with `DATABASE_URL` from compose.

12. backend/database/models.py
- Purpose: DDL for schema creation
- Findings: Schema includes users, students, classes, enrollments, sessions, attendance_logs, attendance_records, face_data, waiver_requests, notifications. Uses FKs with ON DELETE CASCADE. Consider adding indexes on FK columns frequently used in joins for better performance.

13. backend/database/queries.py
- Purpose: attendance queries and upsert logic
- Findings: Parameterized SQL is used (good). `update_attendance_record` uses SQLite UPSERT syntax `ON CONFLICT ... DO UPDATE` — this requires SQLite >= 3.24.0. Ensure runtime SQLite supports it.

14. backend/database/analytics.py
- Purpose: aggregate reports
- Findings: Queries for averages, trends and summaries look correct; handle NULL/zero cases gracefully in consuming code.

15. backend/database/export.py
- Purpose: CSV and PDF exports
- Findings: CSV export works; PDF export uses `reportlab` wrapped in try/except ImportError. `reportlab` is not in requirements, so `export_attendance_pdf` will return `None` silently. Add `reportlab` to requirements or document that PDF export is optional and clearly surfaced to callers.

16. backend/database/maintenance.py
- Purpose: backups, cleanup, foreign key verification
- Findings: Provides backup_database (copies DB file), cleanup_old_sessions, verify_foreign_keys (PRAGMA), and statistics. `get_database_stats` constructs table counts by string substitution — OK since table names are internal; avoid user-provided table names to prevent SQL injection.

17. frontend/
- Purpose: Expo React Native app
- Findings: App is composed of multiple screens using local mock data. No network/API calls found in the screen implementations reviewed. Key points:
  - Navigation is defined in `App.js` and most screens registered match nav usage.
  - `TeacherBottomNav` references a `TeacherStudents` route which is not registered in `App.js` → pressing that tab will cause a runtime navigation error. Fix by registering the screen or removing the tab.
  - Many screens use static/demo data and Alert boxes; implement real API integration and robust error handling for production.

18. frontend/package.json and package-lock.json
- Purpose: frontend dependencies
- Findings: Uses Expo and react navigation. Run `npm audit` in CI to detect vulnerabilities before release.

Security review
---------------
- Secrets handling: `firebase_credentials.json` is excluded from Git and from Docker build context — correct.
- Injection: Backend uses parameterized SQL placeholders for user inputs — safe from SQL injection; only internal table name interpolation exists and is safe.
- Dependences: run `pip audit` and `npm audit` to detect known vulnerabilities. Keep pinned versions and update frequently.

Docker & deployment notes
-------------------------
- Dockerfile and docker-compose.yml are acceptable for small deployments. Key items:
  - Ensure the host-mounted `backend/database` directory permissions allow the container `appuser` to write the database file.
  - Confirm container SQLite version supports UPSERT if `ON CONFLICT DO UPDATE` is used.
  - Add `.env.example` files so `scripts/setup.sh` can create `.env` automatically.

Actionable recommendations (priority-ordered)
-------------------------------------------
High priority
- Add `backend/.env.example` and `frontend/.env.example` with required variables (no secrets). Update `scripts/setup.sh` to copy them if present, or create minimal `.env` if example missing.
- Add `reportlab` to `backend/requirements.txt` or change `export_attendance_pdf` to return an explicit error explaining the missing dependency.
- Fix `TeacherBottomNav` to reference an existing screen or add `TeacherStudents` screen.
- Ensure runtime SQLite version in Docker supports UPSERT, or update code to an UPDATE fallback.

Medium priority
- Allow `DATABASE_PATH` and other file paths to be overridden using environment variables so docker-compose envs are honored.
- Add DB indexes for FK fields used in joins (attendance_logs.student_id, sessions.class_id, etc.).
- Add migrations (alembic or similar) if schema will evolve.

Low priority
- Replace map-based lists in React Native with `FlatList` for large lists.
- Add unit tests for DB queries and API endpoints.

Final scores
------------
- Database: 8/10 — solid schema and constraints, add indexes/migrations for improvement.
- Security: 8/10 — secrets excluded, parameterized SQL; run dependency audits and add runtime checks.
- Backend: 8/10 — clean structure; unify env var usage and fix minor missing dependency.
- Docker: 8/10 — multi-stage build and non-root user; add docs and ensure correct host permissions.
- Overall: 8/10

Next steps I can take
--------------------
- I can create `backend/.env.example` and `frontend/.env.example` templates and update `scripts/setup.sh` accordingly.
- I can add `reportlab` to `backend/requirements.txt` and run quick checks.
- I can patch `TeacherBottomNav` to remove the missing route or add a placeholder screen.

If you want, tell me which of these I should implement next.
