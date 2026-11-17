# Fake data generator — spec

## 1. Purpose and scope
The purpose is to generate basic starter data in order to test the data pipeline. Additionally, it should test all data analysis and report-building features. It should have 2 demo teachers with 8 and 4 students respectively, and extra studios such that each Insights group has 10 or more opted-in students.

Script: `scripts/seed.py`.

Tables filled, in fill order:
1. cities
2. users
3. studios
4. students
5. pieces
6. tags
7. student_pieces
8. stage_changes
9. practice_logs
10. assignment_templates
11. assignments
12. lesson_notes
13. student_tags
14. piece_tags

Not filled by the generator (seeded in schema.sql): stages, rcm_levels.

## 2. Labeling generated data
To label generated data, we will use @example.com emails and set `users.is_generated = true`. This will apply to both students and teachers (studios are labeled through their teacher), and will be used for all demo accounts, excluding my personal and definitely not exaggerated personal account.

## 3. Insights groups
Insights groups are based on student level band. If the student has a preset level tag given by their instructor, that is used. Otherwise, the average difficulty of their 3 hardest completed pieces (if fewer than 3 completed pieces, then the average of all completed pieces), rounded down, is used. If the student has 0 completed pieces, the algorithm takes their current piece and subtracts 2 RCM levels from it, capped at Prep A (assumption: students usually work above their level). The calculation doesn't need to be exact, as 4 bands will be used:
- Prep A–Level 2
- Levels 3–5
- Levels 6–8
- Levels 9–ARCT

Rules:
- Only exact preset tag names count. Format: `[RCM #]` where # is the level (e.g. `[RCM 5]`), except `[Prep A]`, `[Prep B]` and `[ARCT]`. Spacing and brackets must match exactly; custom tags are ignored.
- Difficulty uses `rcm_levels.sort_order`.
- Current piece = lowest `seq_order` with `completed_on` empty.
- Students with no pieces are left out. Pieces with no RCM level are skipped; if a student's only pieces have no RCM level, the student is left out.
- A group is only shown if it has 10 or more opted-in students.

## 4. Volumes
We will assume that 50% of all students opt in to data collection. For 4 bands, we will need 80 students minimum. For safety, we will generate 100 students: 25 per band, with at least 12 opted in per band. The 12 demo students do not count toward the 100 (112 students total).

## 5. Generation order
Order follows foreign keys: a table is filled only after every table it references.
- Demo teachers and their studios are created first, so their ids and logins stay the same on every run.
- Everything runs in one transaction (all or nothing).
- Re-run: first `DELETE FROM users WHERE is_generated` (cascades to studios, students, student_pieces, logs, notes, tags). Cities and pieces stay; inserts skip existing rows (`ON CONFLICT DO NOTHING`).

| Table | Comes after | Why |
|---|---|---|
| cities | — | references nothing |
| users | — | references nothing |
| studios | users, cities | `teacher_id`, `city_id` |
| students | users, studios | `user_id`, `studio_id` |
| pieces | rcm_levels | `rcm_level_id` |
| tags | users | `teacher_id` |
| student_pieces | students, pieces, stages | `student_id`, `piece_id`, `current_stage_id` |
| stage_changes | student_pieces, users | `student_piece_id`, `changed_by` |
| practice_logs | student_pieces | `student_piece_id` |
| assignment_templates | users | `teacher_id` |
| assignments | student_pieces, assignment_templates | `student_piece_id`, `template_id` |
| lesson_notes | students | `student_id` |
| student_tags | students, tags | both halves of the key |
| piece_tags | pieces, tags | both halves of the key |

## 6. Realism rules
- Lessons: each student has one fixed weekday lesson.
- Weekly practice shape: each student gets one shape via `random.choice`: taper (high after lesson, fading), taper + cram (fading, jump the day before the lesson), or flat.
- Skipped days: 3 student types — steady (~10% of days skipped), average (~30%), sporadic (~55%).
- Minutes per practice day, by band (doubled from the first draft): Prep A–L2 20–40, L3–5 40–70, L6–8 60–120, L9–ARCT 90–180. The day's total is split across that day's in-progress pieces (each `practice_logs` row is one piece).
- Stages: 1–3 weeks per stage, slower when the piece is harder than the student's level. `stage_changes.changed_by` = the student's teacher.
- Window: logs cover the last 8 weeks. Pieces may have started before the window (assumption: history from before the student joined LedgerLine), so some pieces are already completed.
- Practiced pieces: only in-progress pieces (started, not completed), 1–3 at a time.
- Log notes: about 30% of logs get a note from a small list, including some funny ones.
- Lesson notes: one per lesson, demo studios only.
- Logins: every generated user shares one password from `.env` (`DEMO_PASSWORD`), hashed with werkzeug. Fine because all data is fake; never a real password.

## 7. Reproducibility
- Fixed random seed constant in `seed.py`.
- Dates are relative: the 8 weeks end on the day the script runs. Same pattern every run, always current, never in the future.
- Names: small hand-written lists of funny names; a very few reference famous composers.

## 8. Checks after seeding
Saved as SQL in `sql/queries.sql` and as asserts at the end of `seed.py`:
- Row counts per table
- Every band has 12+ opted-in students
- No logs dated in the future
- No log earlier than its piece's `started_on`
- Newest `stage_changes` row matches `current_stage_id`
- Every generated user has `is_generated = true` and an @example.com email

## 9. Out of scope
- Cleaning (Thursday notebook). The generator does write a separate messy CSV export for it (duplicates, blanks, text in number columns, an outlier like a 600-minute log); the database stays clean for the demo.