# Problem

## Problem Statement
Piano teachers can't find students' day-to-day practice info because most practice happens at home between weekly lessons, where the teacher can't see.
Today they ask students, which may lead to wasted class time figuring out what students have done instead of teaching.
LedgerLine allows students to log daily practice on the same day so that piano teachers can know which pieces need work and can track trends and practice streaks on the dashboard.

## Brief
Piano teachers can't see what students actually practice between lessons. LedgerLine: teacher assigns pieces in order and tracks each through 6 stages; students log practice; teacher sees a dashboard and sends a weekly progress card. Studio-management tools (e.g. My Music Staff, $16.95/mo + $4.95 per extra teacher) focus on scheduling and billing; they do include a basic practice log (time + notes) and generic progress labels, but LedgerLine is practice-first: per-piece logs, a 6-stage path per piece, dashboard charts and a shareable weekly progress card.

## Stakeholders
| Stakeholder | Pays? | Uses daily? | Main benefit | Main concern |
|---|---|---|---|---|
| Piano teacher | Yes, Teacher Studio ~$8/mo | Yes, dashboard + notes | Lessons start with real data | Setup time; student buy-in |
| Student (has a teacher) | No, paid by teacher | Yes, practice log | Track and log daily practice, efficient lessons| Logging convenience |
| Self-taught student | Yes, Student Solo ~$3/mo | Yes, dashboard + notes | Track and log daily practice, plan for future practice | Convenience, extra features |
| Parent | No, unless self-taught student is minor | Not daily. Weekly progress card (shared link) | Efficient classes, make sure child is practicing | Child's data privacy, ease of access |
| Practice Insights buyer | Yes, per report (price TBD) | No | Check trends, view data dashboard as non-teacher | Data type, readability, presentability, sample size/representativeness |

## Pricing Plan
| Plan | Price | For |
|---|---|---|
| Free | $0 | 1 teacher + up to 3 students, or a solo student (basic logs) |
| Student Solo | ~$3/mo | Self-taught learners: goals, streaks, charts |
| Teacher Studio | ~$8/mo | Unlimited students, assignments, dashboard, progress cards |
| Practice Insights | per report (price TBD Thu) | Anonymized, aggregated, opt-in trends (10+ students per group) |

Differentiator: stage-based progress per piece + same-day, per-piece logs + a weekly progress card parents can see. Logs are still self-reported: LedgerLine replaces week-later recall, it does not verify practice. Exact tagline to be finalized in Thu pricing/landing copy.
Most marketable feature: the weekly progress card (also helps students who can't take notes during lessons).
Data note: selling identifiable student data is a legal and trust risk (SOPIPA-style state laws, COPPA for under-13s). Insights are aggregated and opt-in only.

## Requirements (MoSCoW)
### Must (core, by Wed night)
- [ ] Teacher and student accounts with login
- [ ] Teacher can write class notes
- [ ] Teacher can assign songs to an ordered repetoire with 6 stages, tags on students and pieces
- [ ] Student can write daily practice log
- [ ] Student can log practice times for each song
- [ ] Teacher dashboard with 2 Plotly charts
- [ ] Weekly progress card
- [ ] Deployed
### Should (secondary, Thu–Fri, cut from the bottom)
- [ ] Practice insights page
- [ ] Map
- [ ] Pricing page (no checkout)
- [ ] Vercel landing page
- [ ] Excel reports
- [ ] CSV import
- [ ] Pytest
### Could (stretch)
- [ ] Messages
- [ ] Audio recording upload
- [ ] AI summary on progress card
### Won't (out of scope)
- Actual payment
- Connect to competitions

## Tool comparison
| | Paper / asking | My Music Staff | MakeMusic Cloud | LedgerLine |
|---|---|---|---|---|
| Price | **Free**| **$16.95/mo** + **$4.95** per extra teacher| **$39.99/yr** per teacher, **$13.99/yr** per student, with discounts shown for **20+** subscriptions. **Free** for individuals with basic red/green note assessments and composing| **Free** for basic logging, **$3/mo** for self-taught, **$8/mo** for teacher studios, by report (price TBD) for Practice Insights
| Main purpose | Easy notetaking| **Studio admin:** scheduling, attendance, billing and lesson notes for private teachers| **School music classrooms:** assigned practice with automatic note assessment| **Practice tracking for private piano studios**|
| Practice log | Physical, may be undetailed, may be lost| Students log time **manually** or with a timer, add notes, upload files<sup>1</sup>| **Automatic**, counting **only** time spent playing or recording in the app<sup>2</sup>| Students log minutes per piece, **the same day**, and notes about each piece|
| Per-piece stages | Only if teacher writes them| **Generic** labels: In-Progress, Completed, Requested, and more| Not found| **6 stages**, from learning notes to performance ready|
| Parent-facing summary | None| "Portal lesson notes: students and parents can view their recent **lesson notes** on the Home page of the Student Portal." **No weekly summary found**.| Opt-in weekly highlights email (practice time, content explored)<sup>3</sup>| **Weekly progress card (shareable link):** week + 3–4 week overview + stage per piece + notes|

<sup>1</sup> "Students can either manually add time or use the built-in practice timer. They can also upload files, like a video of their practice session."
<sup>2</sup> The teacher sees total active minutes they spent on this title (either playing back, or recording). This is the one tool here that measures practice instead of relying on self-reports, but it only counts practice done inside the app.  
<sup>3</sup> "Parents and guardians can opt in to receive a weekly message that gives them insights about their child’s activities in MakeMusic Cloud like practice time, content they’ve explored."

Sources (checked 2026-11-16): 
- My Music Staff pricing: https://www.mymusicstaff.com/?p=75253 
- My Music Staff practice log: https://www.mymusicstaff.com/student-portal/ 
- My Music Staff progress labels + lesson notes: https://www.mymusicstaff.com/?p=64549 
- My Music Staff portal lesson notes: https://www.mymusicstaff.com/the-next-level/ 
- MakeMusic Cloud pricing: https://www.makemusic.com/pricing/ 
- MakeMusic Cloud practice time: https://help.makemusic.com/hc/en-us/articles/360026372113 
- MakeMusic Cloud parent weekly emails: https://www.makemusic.com/?p=45559
