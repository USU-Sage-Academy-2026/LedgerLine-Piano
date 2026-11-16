# Problem

## Problem statement
Piano teachers can't find students' day-to-day practice info because most practice happens at home between weekly lessons, where the teacher can't see.
Today they ask students, which may lead to wasted class time figuring out what students have done instead of teaching.
LedgerLine allows students to log daily practice on the same day so that piano teachers can know which pieces need work and can track trends and practice streaks on the dashboard.

## Stakeholders
| Stakeholder | Pays? | Uses daily? | Main benefit | Main concern |
|---|---|---|---|---|
| Piano teacher | Yes, Teacher Studio ~$8/mo | Yes, dashboard + notes | Lessons start with real data | Setup time; student buy-in |
| Student (has a teacher) | No, paid by teacher | Yes, practice log | Track and log daily practice, efficient lessons| Logging convenience |
| Self-taught student | Yes, Student Solo ~$3/mo | Yes, dashboard + notes | Track and log daily practice, plan for future practice | Convenience, extra features |
| Parent | No, unless self-taught student is minor | Not daily. Weekly progress card (shared link) | Efficient classes, make sure child is practicing | Child's data privacy, ease of access |
| Practice Insights buyer | Yes, per report (price TBD) | No | Check trends, view data dashboard as non-teacher | Data type, readability, presentability, sample size/representativeness |

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