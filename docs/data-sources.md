# Data sources

## Data-source log
| Dataset | Source | Real or generated | Personal data? | Consent | License / terms | Stored in |
|---|---|---|---|---|---|---|
| Theo's practice logs | Entered by me | Real, but may be exaggerated | Yes | I consent | Own data | Supabase `practice_logs` |
| Demo studios, teachers, students (2 teachers with 8 + 4 students, extra studios in Utah cities) | `scripts/seed.py` | Generated, labeled as generated | No (fake names, fake emails) | Not needed | Own code | `studios`, `users`, `students` |
| Demo practice logs, lesson notes, tags, stage changes (8 weeks) | `scripts/seed.py` | Generated, labeled as generated | No | Not needed | Own code | `practice_logs`, `lesson_notes`, `student_tags`, `stage_changes` |
| Piece catalog (titles, composers) | My repertoire knowledge | Real facts | No | Not needed | Titles are facts; no sheet music stored | `pieces` |
| Stages lookup (6 rows) | Project decision | Defined by Me | No | Not needed | Own design | `stages` |
| Utah city coordinates | TBD: pick a public-domain source and verify on Thu (map block) | Real | No | Not needed | Verify before use | `studios.lat`, `studios.lon` |
| Tester accounts and logs | Testers using the deployed app | Real | Yes (names, emails, logs) | Ask each tester first; explain what is stored; delete on request after Nov 23 (proposal) | Testers' data | `users`, `practice_logs` |
| Practice Insights aggregates | SQL over opted-in students | Derived | No, if groups have 10+ students | Opt-in flag per student | Own analysis | Query results, not stored |s