# LedgerLine data dictionary

Source of truth: `sql/schema.sql` + `sql/migrations/002_frontend_additions.sql` + `003_users_email_lowercase.sql` (PostgreSQL on Supabase). 19 tables, 3NF.
Conventions: generated `id` primary keys (lookups use fixed ids), `<table>_id` foreign keys, `created_at`/`updated_at` with a `set_updated_at` trigger,
RLS enabled with no policies on every table (Supabase Data API locked; Flask connects as owner).

## rcm_levels
Lookup: Royal Conservatory levels (13 rows: Prep A, Prep B, Level 1–10, ARCT).

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | smallint | no |  | Fixed id (not generated). |
| name | text | no |  | Display name, e.g. "Level 8". |
| sort_order | smallint | no |  | Correct sort order (text would put Level 10 before Level 2). |

## stages
Lookup: the 6 learning stages of a piece.

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | smallint | no |  | Fixed id 1–6. |
| name | text | no |  | learning notes … performance ready. |
| position | smallint | no |  | Order 1–6 (CHECK). |

## cities
One row per city; holds map coordinates once (3NF fix: lat/lon depend on the city, not the studio).

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | integer | no | identity | Generated id. |
| name | text | no |  | City name. |
| state | char(2) | no |  | 2 capital letters (CHECK regex). |
| lat | numeric(8,5) | no |  | Latitude −90..90. |
| lon | numeric(8,5) | no |  | Longitude −180..180. |

## users
Every login account, teacher or student. Fake rows have is_generated = true.

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | bigint | no | identity | Generated id. |
| email | text | no |  | Login email, UNIQUE, must be lowercase (CHECK, migration 003); Flask lowercases at signup/login. |
| password_hash | text | no |  | werkzeug hash; never the password. |
| display_name | text | no |  | Name shown in the app; public card shows first name + last initial. |
| role | text | no |  | 'teacher' or 'student' (CHECK). |
| is_generated | boolean | no | false | true = seed/fake data (labelled as generated). |
| created_at | timestamptz | no | now() | Row created. |
| updated_at | timestamptz | no | now() | Last edit (trigger). |

## studios
A teacher's studio. One studio per teacher in MVP (UNIQUE teacher_id).

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | bigint | no | identity | Generated id. |
| teacher_id | bigint | no |  | Owner → users. CASCADE. |
| city_id | integer | no |  | → cities. RESTRICT. |
| name | text | no |  | Studio name. |
| created_at | timestamptz | no | now() | Row created. |
| updated_at | timestamptz | no | now() | Last edit (trigger). |
| join_code | text | no |  | 6-digit code students type to join; UNIQUE; "Make a new code" overwrites it (migration 002). |

## students
Student profile; one per student user. studio_id NULL = Student Solo.

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | bigint | no | identity | Generated id. |
| user_id | bigint | no |  | → users, UNIQUE (one profile per account). CASCADE. |
| studio_id | bigint | yes |  | → studios; NULL = Student Solo. SET NULL. |
| parent_email | text | yes |  | Optional guardian email (must contain @). Never shown on public pages. |
| parent_phone | text | yes |  | Optional guardian phone, text so +, dashes, leading 0 survive. |
| insights_opt_in | boolean | no | false | Opted in to anonymized Insights (default false). |
| created_at | timestamptz | no | now() | Row created. |
| updated_at | timestamptz | no | now() | Last edit (trigger). |
| weekly_goal_minutes | integer | yes |  | Weekly practice-minutes target, 1–5000, set by the TEACHER only; student reads it. Not derived from assignments (migration 002). |

## pieces
Shared catalog of piano pieces.

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | bigint | no | identity | Generated id. |
| title | text | no |  | Piece title. |
| composer | text | no | 'Unknown'::text | Composer; default 'Unknown'. UNIQUE (title, composer). |
| rcm_level_id | smallint | yes |  | → rcm_levels; NULL if not graded. RESTRICT. |
| henle_level | smallint | yes |  | Henle difficulty 1–9 (CHECK); NULL if unknown. |
| created_at | timestamptz | no | now() | Row created. |
| updated_at | timestamptz | no | now() | Last edit (trigger). |

## student_pieces
A piece in one student's ordered repertoire. Pieces are never deleted from a repertoire; completed_on is set instead.

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | bigint | no | identity | Generated id. |
| student_id | bigint | no |  | → students. CASCADE. |
| piece_id | bigint | no |  | → pieces. RESTRICT. |
| seq_order | integer | no |  | Position in the list (> 0). UNIQUE (student_id, seq_order) DEFERRABLE so ↑/↓ swaps work in one transaction. |
| current_stage_id | smallint | no |  | → stages. INTENTIONAL DUPLICATE of the newest stage_changes row; Flask updates both in one transaction. |
| started_on | date | yes |  | Date work began. |
| completed_on | date | yes |  | Date finished (>= started_on). |
| created_at | timestamptz | no | now() | Row created. |
| updated_at | timestamptz | no | now() | Last edit (trigger). |

## stage_changes
Append-only history of stage moves (no updated_at).

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | bigint | no | identity | Generated id. |
| student_piece_id | bigint | no |  | → student_pieces. CASCADE. |
| from_stage_id | smallint | yes |  | → stages; NULL = first stage set. |
| to_stage_id | smallint | no |  | → stages; must differ from from_stage_id. |
| changed_by | bigint | yes |  | → users (teacher or student); SET NULL. |
| changed_at | timestamptz | no | now() | When it changed. |

## practice_logs
One practice session on one piece.

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | bigint | no | identity | Generated id. |
| student_piece_id | bigint | no |  | → student_pieces. CASCADE. |
| started_at | timestamptz | no |  | Session start (timestamptz). End = started_at + minutes. |
| minutes | integer | no |  | Length in minutes (> 0). |
| note | text | yes |  | Optional note, max 500 chars (migration 002). Editable for 7 days (Flask rule). |
| created_at | timestamptz | no | now() | Row created. |
| updated_at | timestamptz | no | now() | Last edit (trigger). |

## assignment_templates
A teacher's saved preset assignments.

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | bigint | no | identity | Generated id. |
| teacher_id | bigint | no |  | → users. CASCADE. |
| title | text | no |  | Preset title, e.g. "Hands Separate". |
| body | text | yes |  | Preset instructions. |
| created_at | timestamptz | no | now() | Row created. |
| updated_at | timestamptz | no | now() | Last edit (trigger). |

## assignments
A task on one repertoire piece. Loading a preset COPIES title/body here.

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | bigint | no | identity | Generated id. |
| student_piece_id | bigint | no |  | → student_pieces. CASCADE. |
| template_id | bigint | yes |  | → assignment_templates it was copied from; SET NULL. |
| title | text | no |  | Required title the teacher writes (UI has a required Title field). |
| body | text | yes |  | Instructions. |
| minutes_per_day | integer | yes |  | Optional target (> 0). |
| assigned_on | date | no | CURRENT_DATE | Defaults to today. |
| due_on | date | yes |  | Optional; >= assigned_on. |
| created_at | timestamptz | no | now() | Row created. |
| updated_at | timestamptz | no | now() | Last edit (trigger). |

## lesson_notes
Teacher notes from a lesson. Author = the studio's teacher (no teacher_id: that would be a transitive dependency).

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | bigint | no | identity | Generated id. |
| student_id | bigint | no |  | → students. CASCADE. |
| lesson_date | date | no | CURRENT_DATE | Defaults to today. |
| body | text | no |  | Note text, 1–2000 chars (migration 002). |
| created_at | timestamptz | no | now() | Row created. |
| updated_at | timestamptz | no | now() | Last edit (trigger). |
| student_piece_id | bigint | yes |  | "About" field → student_pieces; NULL = whole lesson. SET NULL. Flask checks it is the same student (migration 002). |

## tags
A teacher's labels for students or pieces.

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | bigint | no | identity | Generated id. |
| teacher_id | bigint | no |  | → users. CASCADE. |
| name | text | no |  | Label. Unique per teacher + applies_to, case-insensitive (index on lower(name), migration 002). |
| applies_to | text | no |  | 'student' or 'piece'. |
| color | text | no | '#1F3B63'::text | Hex color; default '#1F3B63' (UI is text-only now). |
| created_at | timestamptz | no | now() | Row created. |
| updated_at | timestamptz | no | now() | Last edit (trigger). |
| is_preset | boolean | no | false | true for the 3 signup tags (Beginner, Adult, RCM 4); Flask blocks rename/delete (migration 002). |

## student_tags
Junction: tag ↔ student. Composite PK. Flask checks applies_to = student and same teacher.

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| student_id | bigint | no |  | → students. CASCADE. |
| tag_id | bigint | no |  | → tags. CASCADE. |
| created_at | timestamptz | no | now() | When tagged. |

## piece_tags
Junction: tag ↔ piece. Composite PK. Flask checks applies_to = piece.

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| piece_id | bigint | no |  | → pieces. CASCADE. |
| tag_id | bigint | no |  | → tags. CASCADE. |
| created_at | timestamptz | no | now() | When tagged. |

## share_links
Public link to one week of a progress card (migration 002).

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | bigint | no | identity | Generated id; NEVER used in the URL. |
| student_id | bigint | no |  | → students. CASCADE. |
| created_by | bigint | yes |  | → users (teacher or student); SET NULL. |
| token | text | no |  | URL secret from secrets.token_urlsafe(16); UNIQUE, >= 20 chars. |
| week_start | date | no |  | Monday of the week shown (CHECK ISODOW = 1). |
| expires_at | timestamptz | no | (now() + '30 days'::interval) | Default now() + 30 days. |
| revoked_at | timestamptz | yes |  | Set = link turned off; row kept so the page can say so. |
| show_name | boolean | no | true | Show first name + last initial. |
| show_pieces | boolean | no | true | Show pieces. |
| show_stages | boolean | no | true | Show stages. |
| show_minutes | boolean | no | true | Show minutes. |
| show_teacher_notes | boolean | no | true | Show lesson notes. At least one show_* must be true (CHECK). |
| created_at | timestamptz | no | now() | Row created. |

## goals
Student goals. Weekly = core; month/year/general = secondary (migration 002).

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | bigint | no | identity | Generated id. |
| student_id | bigint | no |  | → students. CASCADE. |
| period | text | no |  | 'week','month','year','general'. |
| period_start | date | yes |  | Monday / 1st of month / Jan 1; NULL only for general (CHECK). |
| body | text | no |  | Goal text, 1–140 chars. |
| kind | text | no |  | 'check' (done/not done) or 'count' (e.g. 3 of 5). |
| target_count | integer | yes |  | 1–50 for count goals; NULL for check goals. |
| done_count | integer | no | 0 | Progress 0..target_count; always 0 for check goals. |
| completed_at | timestamptz | yes |  | The ONLY "Completed" signal. Count goals can only be completed when done_count = target_count. |
| created_at | timestamptz | no | now() | Row created. |
| updated_at | timestamptz | no | now() | Last edit (trigger). |

## invites
Teacher invites a student by email; student accepts in the app (migration 002).

| Column | Type | Null | Default | Meaning / constraints |
|---|---|---|---|---|
| id | bigint | no | identity | Generated id. |
| studio_id | bigint | no |  | → studios. CASCADE. |
| email | text | no |  | Invitee email, must be lowercase and contain @. |
| status | text | no | 'pending'::text | 'pending' (default), 'accepted', 'declined'. One PENDING invite per studio + email (partial unique index). |
| created_at | timestamptz | no | now() | Sent. |
| responded_at | timestamptz | yes |  | Set exactly when status is not pending (CHECK). |

## Rules the schema cannot enforce (Flask must)
- `student_tags` / `piece_tags`: the tag's `applies_to` matches, and the tag belongs to the student's teacher.
- `students.user_id` points at a `role = 'student'` user; only the owning teacher sets `weekly_goal_minutes`.
- `lesson_notes.student_piece_id` belongs to the same student.
- Invites: "already in your studio" error; accepting sets `students.studio_id` and the invite status in one transaction.
- Stage change: UPDATE `student_pieces.current_stage_id` + INSERT `stage_changes` in one transaction.
- Practice-log notes editable for 7 days; preset tags cannot be renamed or deleted.

## Known gaps
- 6-digit join codes can be guessed by brute force; Flask should rate-limit join attempts.

## Future
- `studio_members (studio_id, user_id, role)` + `enrollments (student_id, teacher_id, started_on, ended_on)` for a multi-teacher "Music School" plan. Additive migration; existing joins keep working.