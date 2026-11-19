# PROGRESS — LedgerLine

One entry per block: what got done, what's left, any blockers, confidence (1–5), and the commit.

## Mon Nov 16

### 09:40–10:30 · Setup (Cloud/DevOps) · Objectives 13, 14
- Done:
  - Public repo `tng5/LedgerLine-Piano` on `main` (2 commits)
  - `.gitignore` uses the Python template and covers `.env`, `.venv`, `venv/` and `__pycache__/`
  - venv created
  - `app/app.py` Flask hello route ("Hello, LedgerLine!")
  - README stub with "All rights reserved"
  - Supabase project created
- Left:
  - `requirements.txt` (`pip freeze > requirements.txt`)
  - Confirm the hello page runs locally (`flask --app app/app run`)
  - GitHub Projects board (To do / Doing / Done)
  - Render + Vercel accounts
  - README skeleton sections
- Blockers: none
- Confidence: 5/5
- Commit: `20235f6` "Start project setup."

2026-11-16 10:30 | Cloud/DevOps | done: repo, .gitignore (.env verified ignored), venv, README skeleton, Projects board, Supabase/Render/Vercel accounts | blocked: none (Render maintenance Tue 7–7:30pm MST blocks deploys only) | next: problem framing + governance

2026-11-16 11:55 | Product & Business Strategist | done: problem statement, stakeholders, MoSCoW requirements, tool comparison (verified prices + sources), data-source log; plan research + differentiator corrected | blocked: none | next: data-quality checklist + privacy/bias reflection (carry-over), then DB design

2026-11-16 15:15 | Database Designer | done: 3NF design (16 tables), Lucid ERD v2, schema.sql with constraints/triggers/RLS + local tests | blocked: none | next: run schema on Supabase, data dictionary (+Future: studio_members/enrollments), 3 join queries

2026-11-16 21:30 | data-analyst | done: generator spec docs/data-generator.md (9 sections, decisions locked) | blocked: none | next: Lucid flowchart from spec, then seed.py + import own logs + row-count checks

2026-11-17 07:15 | data-analyst | done: scripts/seed.py (tested locally, 112 students, all checks pass) | blocked: none | next: run seed on Supabase, import own logs, row-count checks

2026-11-18 08:00 | data-analyst | done: seed run on Supabase, 3 row-count checks match spec (10 teachers, 112 students, 8/4 demo, 6455 logs 9/24-11/18) | blocked: none | next: chart data for dashboard

2026-11-18 09:35 | Flask Backend Developer | done: app factory, config, db.py (get_db/close_db), login, logout, login_required, role_required; seeded teacher + student login verified | blocked: none | next: register (both roles, one transaction), then teacher flows

2026-11-18 11:20 | Flask Backend | done: register (teacher+student, one transaction, email-validator, 15-char min), teacher dashboard + student list | blocked: none | next: student practice log form; add default tags to teacher signup in tags block

2026-11-18 13:35 | Flask Backend | done: student log form (INSERT...SELECT ownership, Denver→UTC times, 7-day window) | blocked: none | next: dashboard chart data

2026-11-18 14:45 | Flask Backend | done: weekly-minutes + daily-studio-minutes APIs (LEFT JOIN from students/days, Denver weeks) | blocked: none | next: tags (incl. default tags on teacher signup), then deploy prep

2026-11-18 14:40 | Flask Backend | done: register, teacher dashboard + student list, student log form, 2 chart APIs, role redirect | blocked: none | next: tags (+ default tags on teacher signup), then deploy prep for 8:25 PM

2026-11-19 14:05 | Database Designer | done: migrations 002+003 applied, ERD v3, data dictionary, queries a–g verified on live data | blocked: seed needs weekly_goal_minutes, preset tags, invites, share link | next: explain-back on queries; Insights aggregate queries (10+ opted-in rule)

## Later
- Multiple teachers per student → enrollments(student_id, teacher_id, started_on, ended_on); also keeps history when a student switches teachers
- Multiple teachers per studio → studio_members(studio_id, user_id, role); pricing decision in Strategist chat
- Preset assignment UI (tables exist; build after core)