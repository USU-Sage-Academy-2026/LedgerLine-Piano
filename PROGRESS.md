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

## Later
- Multiple teachers per student → enrollments(student_id, teacher_id, started_on, ended_on); also keeps history when a student switches teachers
- Multiple teachers per studio → studio_members(studio_id, user_id, role); pricing decision in Strategist chat
- Preset assignment UI (tables exist; build after core)