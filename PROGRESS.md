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