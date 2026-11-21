# LedgerLine — plan, decisions, research

## Brief
Piano teachers can't see what students actually practice between lessons. LedgerLine: teacher assigns pieces in order and tracks each through 6 stages; students log practice; teacher sees a dashboard and sends a weekly progress card. Studio-management tools (e.g. My Music Staff, $16.95/mo + $4.95 per extra teacher) focus on scheduling and billing; they do include a basic practice log (time + notes) and generic progress labels, but LedgerLine is practice-first: per-piece logs, a 6-stage path per piece, dashboard charts and a shareable weekly progress card.

## Business model (updated Nov 21, approved by Theo; full detail in docs/business-plan.md)
Target market: teacher-led studios first (independent piano teachers with ~10–30 students, starting in Utah); Student Solo is secondary.
| Plan | Price | Annual ("2 months free", ≈17% off) | For |
|---|---|---|---|
| 14-day trial (replaces Free) | $0, no card required | — | Teachers or solo students trying everything; prompted to pay on day 14 |
| Student Solo | $3–5/mo | $30–50/yr | Self-taught learners: goals, streaks, charts (parents pay for minors) |
| Teacher Studio | $8–10/mo | $80–100/yr | Unlimited students, assignments, dashboard, progress cards; students under a teacher pay nothing |
| Practice Insights | per report (price not set) | — | Anonymized, aggregated, opt-in trends (10+ students per group) |
No $0.01 card charge (costs ~30¢ in Stripe fees, invites card-testing fraud, cuts signups, under-13s can't pay). Display only: no real payments.
Differentiator: "convenience + price, built on practice-first features." Practice-first = stage-based progress per piece + same-day, per-piece logs + a weekly progress card parents can see. Convenience may only be claimed after it is measured (usability test / tester sessions). Price alone is not a moat; possible moats are progress history (switching costs), studio-wide adoption, and the opt-in Insights data network. Logs are still self-reported: LedgerLine replaces week-later recall, it does not verify practice.
Most marketable feature: the weekly progress card (also helps students who can't take notes during lessons).
Data note: selling identifiable student data is a legal and trust risk (SOPIPA-style state laws, COPPA for under-13s). Insights are aggregated and opt-in only.
Open decision: position LedgerLine as a replacement for My Music Staff or as a practice add-on used alongside it (changes landing/pricing copy).

## Database (16 tables, approved Nov 16; applied to Supabase Nov 17 from sql/schema.sql)
users · cities (name, state, lat, lon) · studios (teacher_id UNIQUE, city_id) · students (user_id, studio_id nullable = Student Solo, parent_email, parent_phone, insights_opt_in) · rcm_levels (lookup: Prep A, Prep B, Levels 1–10, ARCT; sort_order) · pieces (title, composer, rcm_level_id, henle_level 1–9) · stages (6-row lookup) · student_pieces (seq_order, current_stage_id, started_on, completed_on) · stage_changes (from/to stage, changed_by) · practice_logs (student_piece_id, started_at, minutes) · assignment_templates (teacher presets: title, body) · assignments (title, body, minutes_per_day, assigned_on, due_on, template_id copied-from) · lesson_notes · tags (teacher-owned, applies_to student|piece, hex color) · student_tags · piece_tags
Every table has created_at; edited tables also have updated_at (trigger set_updated_at). Difficulty lives in pieces columns, not tags. Default student tags (Beginner, Adult, RCM 4) are copied into each teacher's tags on signup.
Constraints: identity ids (seed scripts must omit id); CHECKs (minutes > 0, henle 1–9, hex color, role, applies_to, date order); composite UNIQUEs incl. student_pieces (student_id, seq_order) DEFERRABLE INITIALLY DEFERRED.
ON DELETE: owned rows CASCADE (incl. practice_logs; the app never deletes a piece from a repertoire, it sets completed_on); students.studio_id SET NULL (→ Student Solo); pieces, cities, stages, rcm_levels RESTRICT; stage_changes.changed_by and assignments.template_id SET NULL.
Security: RLS enabled with no policies on all 16 tables. Flask connects as the table owner via the pooler string (bypasses RLS); the public anon key gets no rows. Never disable.
Flask must enforce (not possible in schema): tag applies_to matches its junction table; tag belongs to the student's teacher; a students row points at a role='student' user.
Intentional denormalization: student_pieces.current_stage_id duplicates the latest stage_changes row; always update both in one transaction.
ERD: Lucid "LedgerLine ERD (v2, 16 tables)" → docs/erd.png.
Stages: learning notes → slow speed → articulation+details → up to tempo → polished → performance ready.
Approved additions (Nov 19, approved by Theo; Database Designer writes sql/migrations/002_frontend_additions.sql): share_links (incl. 5 show_* checkbox columns), goals, invites, studios.join_code, students.weekly_goal_minutes (teacher sets), tags.is_preset, length CHECKs on practice_logs.note (500) and lesson_notes.body (2,000), optional lesson_notes.student_piece_id. assignments.title stays NOT NULL (teacher writes it).

## Week plan (see Google Calendar "LedgerLine:" events for exact blocks)
Sage schedule (Nov 16): in office Mon/Wed/Fri 9–4 (Fri early release 11); Tue/Thu virtual (no standups — no group this week).
Breaks: one 20-minute bathroom break in every LedgerLine block of 90+ minutes (on the calendar as "Break (20 min)").
Status Thu 13:20: BEHIND. Built (Wed): register/login/logout + role decorator, teacher dashboard skeleton + student list, student log form, 2 chart JSON APIs, role home pages. Not built: charts on the dashboard, assign pieces + stage change, progress card, lesson notes, tags, weekly goal; Render deploy not confirmed. No commits since Wed 21:13.
- Mon: setup · problem framing + governance · DB design · business review meeting · generator spec
- Tue: Flask + DB + login (partly; afternoon/evening blocks missed)
- Wed: DB/env catch-up · register, dashboard skeleton, log form, chart APIs (deploy not confirmed)
- Thu (re-planned 13:20): 13:35 deploy check · 13:55 2 Plotly charts on dashboard · 14:45 break · 15:05 assign pieces + stage change · 20:15 weekly progress card
- Fri: Personal Brand lecture 9–11 · 11:15 lesson notes + tags · 12:50 fixes, redeploy, professor link, usability checklist · FEATURE LOCK 1:30 PM · 13:30 record deep dive (break 14:40)
- Sat: record demo + trailer · Resolve basics
- Sun: edit, export, retrospective, practice
- Mon 23: Turkey Tank Demo Day — Theo out of town (prof pre-approved); videos shown
CUT (Thu 13:20): Excel report, map, Insights page, pricing page, Vercel landing page. Landing/3D prototype and clickable demo may appear in the videos, labeled as prototypes.
Data Crunching coverage after cuts: seed.py logic, sql/queries.sql joins and the messy-CSV cleaning, shown in the deep dive.
Testers: professor (link Fri 12:50), parents (Fri evening), piano teacher (Sat lesson).

## Risks
| Risk | Prevention | Fallback |
|---|---|---|
| Secrets in public repo | .env in .gitignore; reviewer checks | Rotate password immediately |
| First-ever deploy | Deploy Wed, not Fri (slipped: confirm Thu 13:35) | Demo locally |
| Supabase direct connection is IPv6-only | Session pooler string | — |
| Render free sleeps after 15 min | Open app before recording | — |
| Supabase free pauses after 7 days idle | Note in README | Restore in dashboard |
| Mentor pace slower than planned | Daily brief re-plans | Cut order above |
| Video editing new | Simple edits only | Clipchamp / OBS trim |
| Overclaiming vs competitors in videos | Only claim verified differences; say "not found" not "doesn't have" | Correct in README |
| Sage events cut ~1 hr Wed (core) and Fri morning | Feature lock moved to Fri 1:30 PM | Cut order above |
| AI-written seed script Theo can't explain | Theo writes the spec; explain-back before running; Code Reviewer quiz | Regenerate simpler version |
| Core not finished by Fri 1:30 lock | Order: deploy → charts → assign/stages → progress card → notes → tags | Unfinished core shown via the clickable demo, labeled prototype |
| Calendar overlaps (Free Time, Gaming, Skills) eat LedgerLine blocks | LedgerLine block wins any overlap | Move the block, don't skip it |
| Demo/design scope runs ahead of the real Flask app (Nov 19) | The demo is a reference only; schema additions limited to what core screens need; Secondary pieces (month/year goals, invites UI polish) cut first | Show the clickable demo in the video for screens not built in Flask, labeled as a prototype |
| Migration 002 lands mid-build (Nov 19) | Apply it before the progress-card block (Thu 20:15); seed.py updated in the same step | Build the card without share links; share = Secondary |
| Large AI-written page batch (Nov 19) Theo can't explain on video | Code Reviewer chat quiz on teacher.py routes + _card_body.html before recording; record only what Theo can explain | Show unexplained screens in the demo video only, not the deep dive |
| Seed data uses [RCM n] level tags, not the Beginner / Adult / RCM 4 presets (is_preset false) | Fixed Nov 19: seed.py marks level tags + the 3 defaults as presets; sql/update_presets.sql fixes the live DB (run once) | New teachers still get presets at signup |
| Removing the Free tier shrinks the pool of studios that can opt into Insights (weakens the data-network moat) (Nov 21) | 14-day no-card trial; studio data stays readable after the trial ends | Reconsider a small Free tier once Insights has real opt-in data |
| Videos or README quote old pricing (Free / $3 / $8) or "big TAM" (Nov 21) | Use $3–5 / $8–10, 14-day trial, and "small, underserved software niche" in all recordings and the README business section | Correct with an on-screen note in editing (Sun) |

## Decisions log
| Date | Decision |
|---|---|
| Nov 16 | Project: LedgerLine, piano teacher–student practice app |
| Nov 16 | Stack: Flask + Jinja + vanilla JS + Supabase Postgres (psycopg 3, raw SQL) + Plotly; Render + Vercel |
| Nov 16 | Auth: Flask session + werkzeug hashing (not Supabase Auth) |
| Nov 16 | Business: Free / $3 Student / $8 Teacher / Insights reports; progress card in core (superseded Nov 21) |
| Nov 16 | Insights threshold 10+ students; more fake data generated to reach it |
| Nov 16 | Repo public, no open-source license ("All rights reserved"); AI may commit/push only after asking |
| Nov 16 | AI summary on progress card = stretch goal |
| Nov 16 | Deep dive recorded Fri afternoon; demo + trailer Sat; edit Sun |
| Nov 16 | Research correction: My Music Staff has a practice log (time + notes) and progress labels. Differentiator reframed to stage-based per-piece progress + same-day per-piece logs + shareable weekly progress card; no claim that competitors lack practice tracking. Tagline finalized Thu. |
| Nov 16 | Practice Insights price not yet set; decide with Thu pricing copy. Report-subscription discount idea → "later" list |
| Nov 16 | Schema 13 → 16 tables: + cities (3NF fix for lat/lon), rcm_levels, assignment_templates. Parent email/phone on students; practice logs store start time + minutes; tag colors + applies_to. No street addresses (privacy). Preset-assignment UI after core. |
| Nov 16 | Later list (schema noted): multiple teachers per student (enrollments junction) and multiple teachers per studio (studio_members junction + possible "Music School" plan → Strategist chat) |
| Nov 16 | Schema finalized: rcm_levels kept as a lookup (text sorts wrong; number codes clash with Level 10); updated_at + trigger kept; practice_logs CASCADE + no "delete piece" in UI; one studio per teacher for MVP; RLS on all tables. |
| Nov 16 | Dependencies: requirements.txt (flask, psycopg[binary], python-dotenv, gunicorn) for Render; requirements-dev.txt (+ pandas, plotly, jupyterlab, openpyxl, pytest) local only. Pin Python with .python-version (Render default is 3.14.x). |
| Nov 16 | Calendar re-planned around Sage Turkey Tank week schedule: attend Ted Talks (Wed 3), ASC Studio (Thu 12–1:30), Personal Brand lecture (Fri 9–11). Feature lock stays Fri 10:30. |
| Nov 16 | Seed data: Data Analyst chat (AI) writes scripts/seed.py from Theo's pseudocode spec (docs/data-generator.md). Theo keeps the spec, hand-trace, review/explain-back and importing his own logs. Freed time → business plan. Script, not hand-inserted rows, so the DB can be rebuilt. |
| Nov 16–17 | UX (Frontend chat): mobile-first; plan for phones, iPad Split View (320–507 px), tablet portrait (744–834) and landscape (1024+); CSS breakpoints 768 and 1024. AI makes design decisions (layout, color, type); Theo writes all HTML/CSS/JS. |
| Nov 16–17 | Design: "The Practice Journal" concept; dark blue + teal, no pink; Newsreader (headings) + Atkinson Hyperlegible Next (UI); light + dark mode (follows device, toggle overrides); the 6-step stage ladder (number + name, never color alone) is the signature detail. |
| Nov 17 | Log form: time set automatically; "Practiced earlier?" link allows up to 7 days back; started_at = submit time − minutes; minutes 1–300; students edit/delete own logs within 7 days; week starts Monday (America/Denver). |
| Nov 17 | Notes: student log note up to 500 chars (per log; each log = one piece); teacher lesson notes up to 2,000 chars. |
| Nov 17 | SCOPE CHANGE (approved by Theo): goals. Weekly goal = core; monthly / yearly / general goals = Secondary (Thu). |
| Nov 17 | Progress card shared by link (expires after 30 days, revocable), created by teacher or student; a link shows first name + last initial, pieces, stages, minutes, notes only. Print stylesheet for Save as PDF (reach). |
| Nov 17 | Joining: teacher enters the student's email → student approves in app; a join code is also supported. Schema additions (share links, goals, invites, log note column check) go to the Database Designer chat once the Frontend design is final. |
| Nov 17 | Stage changes: teacher only for now. "Needs attention" = no log in 4+ days. Dashboard charts: minutes per student this week (bar) + studio minutes per day over 8 weeks (line); reach: per-student minutes by piece. |
| Nov 17 | Motion: the app stays quiet (View Transitions page wipe ~350 ms, progress-card cover flip, bars grow once; all off under reduced motion). |
| Nov 17 | STACK ADDITION (approved by Theo): Three.js (v0.160, loaded from CDN) for the 3D piano scroll story on the Vercel landing page only; never inside the Flask app. |
| Nov 18 | Mentor protocol: tutor writes code one function / file-start at a time (≤ ~40 lines) with line-by-line explanation; multiple-choice checks by default, open-ended for SQL, pandas, Git, deployment and after a wrong answer; end-of-block explain-back = 2 MC + 1 open. |
| Nov 18 | 3D model: Blend Swap #29080 by Roy_1508348 (CC0; credited anyway). Steinway logo, interior, bench and MaterialiQ textures removed; strings replaced with our own texture; sheet-music book + loose pages added; compressed GLB ~1.2 MB. Never use the Steinway name or logo. |
| Nov 18 | Landing motion: scroll glides to the next chapter immediately (no waiting); white room (light) / black room with a stage light (dark). Motion toggle respects reduced motion; with motion off the piano stays still. |
| Nov 18 | Student side (from Theo's wireframes): no inbox, studio invite shows as a banner (Yes / No); plain textarea + 3 note templates instead of a rich editor (Jinja autoescape stays on, so no XSS risk); one "Full name" field; no forgot-password for MVP; Privacy link only; separate optional parent email on register. Student nav: Log · Pieces · Goals · Card · Profile. |
| Nov 19 | Teacher side (from Theo's wireframes): nav Dashboard · Students · Cards · Add student · Tags · Profile. Piece reorder uses ↑/↓ buttons (WCAG 2.5.7 non-drag alternative). Assignment text is plain; preset assignments stay on the later list. |
| Nov 19 | Tags: all tags text-only and styled the same (tags.color no longer shown in the UI). The 3 default student tags (Beginner, Adult, RCM 4) are locked presets: can't be renamed or deleted. RCM and Henle levels are read-only labels from pieces, not tags. |
| Nov 19 | Share checkboxes kept: when creating a card link, the sharer picks what viewers see (Name, Pieces, Stages, Minutes, Teacher notes; at least one). A link points at one fixed week. Needs share_links columns → Database Designer. |
| Nov 19 | Clickable demo (no backend) added to the prototype artifact: 4 demo accounts (teacher Maria Alvarez + students John Doe, Ava Chen, Leo Park; password practice-every-day), every screen with empty / loading / error / undo states, phone + iPad layouts. Reference for Theo's templates; the Flask app is still written by Theo. |
| Nov 19 | FEATURE LOCK moved Fri 10:30 → Fri 1:30 PM (approved by Theo) because core is unfinished. CUT: Insights page, pricing page, Vercel landing page (Excel and map already cut). Core order: deploy → charts → assign/stages → progress card → lesson notes → tags. 20-minute bathroom break in every 90+ minute block. |
| Nov 19 | Skills added: supabase-postgres-best-practices, web-design-guidelines, test-driven-development (TDD scoped to pytest work, not every feature). |
| Nov 19 | SCHEMA CHANGE (approved by Theo): migration 002 adds share_links (token, week_start, expires_at, revoked_at, 5 show_* columns), goals, invites, studios.join_code, students.weekly_goal_minutes, tags.is_preset (+ color default, case-insensitive unique name), length CHECKs on practice_logs.note (500) and lesson_notes.body (2,000), optional lesson_notes.student_piece_id. |
| Nov 19 | Weekly minutes goal is set by the teacher; the student only sees it. assignments.title stays NOT NULL and is written by the teacher (the assignment editor gets a Title field). |
| Nov 19 | Feature crunch (Theo's request, 18:40): AI wrote the remaining pages + their routes on branch frontend-pages, tested on a local copy of the schema + seed. Teacher: dashboard rows, student page (pieces, stage change, ↑/↓, finish, assignment edit, piece/student tags, lesson notes, weekly goal, share links with checkboxes), card preview, tags page, add-student (invites + join code). Student: log (chips, templates, invite banner, join code), pieces, own card + share. Theo reviews/explains before recording; undo toasts from the demo became confirm dialogs + flash messages. |
| Nov 19 | STACK CHANGE (requested by Theo): the 3D piano landing page becomes the Flask home page at / (the Vercel landing page stays cut). Three.js 0.160 now loads only on that page; the app pages never load it. The clickable demo artifact stays a prototype. |
| Nov 19 | Register form: "parent email" relabeled "Contact email (optional)" so adult students aren't confused. Column stays students.parent_email (renaming it would be a schema change). |
| Nov 19 | Page transitions: cross-document View Transitions (fade + 8 px rise, ~280 ms; top bar and nav stay still); bars grow once; both off under reduced motion. Light/Dark toggle shared by home and app (localStorage "ll-theme"). |
| Nov 19 | All nav tabs from the wireframes added. Student: Log · Pieces · Goals · Card · Profile. Teacher: Dashboard · Students · Cards · Add student · Tags · Profile. Goals uses the migration-002 table (week/month/year/general/completed tabs, check and count goals), so the Secondary month/year/general goals are in. Profile: student edits the contact email; teacher renames the studio. |
| Nov 19 | Difficulty: RCM level + Henle level (1–9) set on each piece (new-piece form + a Difficulty section per piece) and shown as dashed 🔒 labels next to the piece tags; the Tags page explains them. Difficulty is a property of the shared pieces row, so it shows for every studio. Locked preset tags get an SVG padlock (tags page, student chips, "(preset)" in the add-tag list). |
| Nov 19 | 3D landing: loose sheets darker (Blender materials + runtime tint, halved under the stage light) and all page images kept inside margins (128 / 108 / 110 px of 1024 × 1400); the last music system no longer runs off the page. Spacing pass on buttons, alerts and radio cards. |
| Nov 21 | BUSINESS MODEL CHANGE (approved by Theo, from the Nov 16 business review): Student Solo $3–5/mo; Teacher Studio $8–10/mo; annual billing ≈17% off ("2 months free"); Free tier replaced by a 14-day trial with no card; $0.01 card charge rejected. Display only, no real payments. |
| Nov 21 | Differentiator: "convenience + price, built on practice-first features" (stage-based per-piece progress, same-day logs, weekly progress card). Convenience is claimed only after it is measured. Price is not a moat; moats to build = progress history, studio-wide adoption, opt-in Insights data network. |
| Nov 21 | Target market: teacher-led studios first (start in Utah via UMTA chapters, then MTNA local affiliates, studio referrals and the progress card); Student Solo secondary. Market framed as a small, underserved software niche (not "big TAM"). |
| Nov 21 | Business plan added: docs/business-plan.md (TAM/SAM/SOM, moat, differentiation, business model, marketing plan, AI-scoring roadmap). |
| Nov 21 | Later list: AI-based scoring + studio/top-player rankings (needs audio data; opt-in + parental consent for minors; conflicts with the 10+ rule, so group percentiles only across studios); "Made with LedgerLine" footer on the progress card; refer-a-teacher offer (one month free each). |
| Nov 21 | OPEN: position LedgerLine as a replacement for My Music Staff or as a practice add-on used alongside it. Decide before any landing/pricing copy. |

## Research summary (Nov 16, 2026; business plan sources added Nov 21)
- My Music Staff pricing ($16.95/mo + $4.95 per extra teacher; 30-day trial; lesson notes included): https://www.mymusicstaff.com/?p=75253
- My Music Staff practice log (students log time + notes, timer; teacher reviews): https://www.mymusicstaff.com/student-portal/
- My Music Staff progress labels (In-Progress, Completed, Requested): https://www.mymusicstaff.com/?p=64549
- MakeMusic Cloud classroom ($39.99/yr per teacher, $13.99/yr per student, 20+ discount): https://www.makemusic.com/pricing/
- Studio-tool buyer guide (practice engagement framed as a weaker area; treat as secondary given the above): https://trynovamusic.com/blog/how-to-choose-the-best-music-studio-management-software-in-2026
- Render free tier (15-min sleep, ~1 min wake): https://render.com/articles/platforms-with-a-real-free-tier-for-developers-in-2026
- Render Python version (default 3.14.x for new services; .python-version file): https://render.com/docs/python-version
- Supabase free pausing: https://supabase.com/kb/faqs/platform/free-project-pausing
- Supabase RLS (tables without RLS readable with the anon key): https://supabase.com/docs/guides/database/postgres/row-level-security
- SOPIPA (no selling student data): https://www.edweek.org/technology/ed-tech-industry-weighs-impact-of-new-data-privacy-laws/2014/10
- Plotly MapLibre maps (no token): https://plotly.com/python/mapbox-to-maplibre/
- Licensing (public ≠ open source): https://opensource.guide/legal/
- Henle difficulty levels 1–9 (easy 1–3, medium 4–6, difficult 7–9): https://www.henle.de/Levels-of-Difficulty/
- RCM piano levels (Prep A/B, Levels 1–10, ARCT): https://files.rcmusic.com/sites/default/files/files/S41_PianoSyllabus_2016_online_f.pdf
- Practito sends parents weekly summaries + read-only parent portal (so stage-per-piece is the card's differentiator): https://practito.com/blog/how-music-teachers-track-student-progress-online
- Cross-document View Transitions support (Chrome 126+, Safari 18.2+ incl. iOS; Firefox sources disagree): https://developer.chrome.com/docs/web-platform/view-transitions/cross-document
- Landing scroll prototype + clickable app demo (Nov 17, updated Nov 19): https://claude.ai/artifact/YMyQCJ4T1KgsaE18gUCMQH
- 3D model used: Blend Swap #29080 by Roy_1508348 (CC0): https://blendswap.com/blend/29080
- Free grand piano models considered (CC BY, credit required): farhad.Guli 10.7k tris https://sketchfab.com/3d-models/grand-piano-371090c279ff4e77a59acdebc25b5892 · richterbelmont26 613k tris https://sketchfab.com/3d-models/grand-piano-4ce9e8dbeb74425eb215e4168807dcb5 · Meast concert grand 550k tris https://sketchfab.com/3d-models/realistic-custom-concert-grand-piano-1331f07bb85f4a3f9ed3e2f03b244902
- Agent skills (skills.sh, checked Nov 19): supabase/agent-skills, vercel-labs/agent-skills, obra/superpowers
- Business plan (docs/business-plan.md, sources checked Nov 16): IBISWorld US private music classes $724.8M (2026) https://www.ibisworld.com/united-states/market-research-reports/private-music-classes-industry/ · MTNA ~17,000 members https://en.wikipedia.org/wiki/Music_Teachers_National_Association · MTNA 73% independent https://www.mtna.org/Demographics.html · MTNA 2024 survey (avg 60-min lesson $65.72) https://certification.mtna.org/downloads/Business/General/MemberSurvey2024_Highlights.pdf · UMTA 500+ teachers https://www.saltlakecountyarts.org/?p=11919 · NEA adults playing instruments https://www.arts.gov/sites/default/files/NationalReportforADPAccess.pdf · YouGov 2022 instruments https://yougov.com/en-us/articles/43512-young-americans-increasingly-exposed-music · Stripe pricing https://stripe.com/pricing · Stripe card testing https://stripe.com/newsroom/news/card-testing-surge · Stripe Setup Intents https://docs.stripe.com/payments/save-and-reuse · Trial benchmarks https://userpilot.com/blog/free-trial-conversion-rate/ · Chargebee card vs no-card https://www.chargebee.com/blog/credit-card-trials-credit-card-trials-go/ · FTC COPPA voice recordings https://ftc.gov/system/files/documents/public_statements/1266473/coppa_policy_statement_audiorecordings.pdf

## Glossary
Stage: one of the 6 learning steps for a piece. Repertoire order: seq_order in student_pieces. Progress card: weekly summary page for a student. Insights: aggregated, opt-in, 10+ students per group. Pooler: Supabase's IPv4 connection string. RLS: row level security; on with no policies = API locked, owner (Flask) unaffected. Share link: a random-token URL to one week's progress card, showing only the ticked fields. TAM / SAM / SOM: total / serviceable / obtainable market. Moat: a lasting reason customers stay that competitors can't copy quickly.