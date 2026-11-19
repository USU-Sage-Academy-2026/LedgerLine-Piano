-- Migration 002: frontend additions (approved by Theo, Thu Nov 19)
-- Runs AFTER sql/schema.sql. Do not edit schema.sql; this file is the change record.
-- Whole migration is one transaction: if any statement fails, nothing is applied.
BEGIN;

-- 0. Carry-over fix from the Supabase advisor (Nov 17): pin the trigger function's search_path.
ALTER FUNCTION public.set_updated_at() SET search_path = '';

-- 1. Weekly minutes goal (teacher sets it, student only reads it; Flask checks ownership)
ALTER TABLE students
  ADD COLUMN weekly_goal_minutes integer CHECK (weekly_goal_minutes BETWEEN 1 AND 5000);

-- 2. Length limits that match the form counters
ALTER TABLE practice_logs
  ADD CONSTRAINT practice_logs_note_length CHECK (char_length(note) <= 500);
ALTER TABLE lesson_notes
  ADD CONSTRAINT lesson_notes_body_length CHECK (char_length(body) BETWEEN 1 AND 2000);

-- 3. Lesson note "About": one piece, or NULL = the whole lesson
--    Flask must check the piece belongs to the same student.
ALTER TABLE lesson_notes
  ADD COLUMN student_piece_id bigint REFERENCES student_pieces(id) ON DELETE SET NULL;

-- 4. Share links for the weekly progress card
CREATE TABLE share_links (
  id                 bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  student_id         bigint NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  created_by         bigint REFERENCES users(id) ON DELETE SET NULL,
  token              text NOT NULL UNIQUE CHECK (char_length(token) >= 20),
  week_start         date NOT NULL CHECK (EXTRACT(ISODOW FROM week_start) = 1),
  expires_at         timestamptz NOT NULL DEFAULT now() + interval '30 days',
  revoked_at         timestamptz,
  show_name          boolean NOT NULL DEFAULT true,
  show_pieces        boolean NOT NULL DEFAULT true,
  show_stages        boolean NOT NULL DEFAULT true,
  show_minutes       boolean NOT NULL DEFAULT true,
  show_teacher_notes boolean NOT NULL DEFAULT true,
  created_at         timestamptz NOT NULL DEFAULT now(),
  CHECK (show_name OR show_pieces OR show_stages OR show_minutes OR show_teacher_notes)
);
CREATE INDEX share_links_student_id_idx ON share_links (student_id);

-- 5. Goals (weekly = core; month / year / general = secondary, same table)
--    "Completed" rule: completed_at IS NOT NULL is the ONLY signal.
--    For count goals, Flask sets completed_at in the same UPDATE that makes done_count = target_count.
CREATE TABLE goals (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  student_id   bigint NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  period       text NOT NULL CHECK (period IN ('week', 'month', 'year', 'general')),
  period_start date,
  body         text NOT NULL CHECK (char_length(body) BETWEEN 1 AND 140),
  kind         text NOT NULL CHECK (kind IN ('check', 'count')),
  target_count integer,
  done_count   integer NOT NULL DEFAULT 0,
  completed_at timestamptz,
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now(),
  -- period_start must exist and line up with the period (NULL only for general)
  CHECK (
       (period = 'general' AND period_start IS NULL)
    OR (period = 'week'  AND period_start IS NOT NULL AND EXTRACT(ISODOW FROM period_start) = 1)
    OR (period = 'month' AND period_start IS NOT NULL AND EXTRACT(DAY FROM period_start) = 1)
    OR (period = 'year'  AND period_start IS NOT NULL AND EXTRACT(DOY FROM period_start) = 1)
  ),
  -- check goals have no counter; count goals have a 1–50 target and 0..target progress
  CHECK (
       (kind = 'check' AND target_count IS NULL AND done_count = 0)
    OR (kind = 'count' AND target_count BETWEEN 1 AND 50 AND done_count BETWEEN 0 AND target_count)
  ),
  -- a completed count goal must actually be full
  CHECK (kind = 'check' OR completed_at IS NULL OR done_count = target_count)
);
CREATE INDEX goals_student_period_idx ON goals (student_id, period, period_start);
CREATE TRIGGER goals_set_updated_at BEFORE UPDATE ON goals
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 6. Invites (teacher adds a student by email; student accepts in the app)
CREATE TABLE invites (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  studio_id    bigint NOT NULL REFERENCES studios(id) ON DELETE CASCADE,
  email        text NOT NULL CHECK (email LIKE '%@%' AND email = lower(email)),
  status       text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined')),
  created_at   timestamptz NOT NULL DEFAULT now(),
  responded_at timestamptz,
  -- answered invites have a response time; pending ones don't
  CHECK ((status = 'pending') = (responded_at IS NULL))
);
-- Only one PENDING invite per studio + email; old accepted/declined rows don't block a new one.
CREATE UNIQUE INDEX invites_one_pending_idx ON invites (studio_id, email) WHERE status = 'pending';
CREATE INDEX invites_email_idx ON invites (email);

-- 7. Join code per studio (6 digits; "Make a new code" overwrites it)
ALTER TABLE studios ADD COLUMN join_code text;
-- Backfill existing studios with random codes. A collision makes the UNIQUE step below fail,
-- which rolls back the whole migration; just run it again.
UPDATE studios
SET join_code = lpad(floor(random() * 1000000)::int::text, 6, '0');
ALTER TABLE studios
  ALTER COLUMN join_code SET NOT NULL,
  ADD CONSTRAINT studios_join_code_key UNIQUE (join_code),
  ADD CONSTRAINT studios_join_code_format CHECK (join_code ~ '^[0-9]{6}$');

-- 8. Tags: locked presets, default color, case-insensitive duplicate names
ALTER TABLE tags ADD COLUMN is_preset boolean NOT NULL DEFAULT false;
UPDATE tags
SET is_preset = true
WHERE applies_to = 'student'
  AND name IN ('Beginner', 'Adult', 'RCM 4');
ALTER TABLE tags ALTER COLUMN color SET DEFAULT '#1F3B63';
-- The old UNIQUE is case-sensitive ("adult" ≠ "Adult"); the new index compares lower(name).
ALTER TABLE tags DROP CONSTRAINT tags_teacher_id_name_applies_to_key;
CREATE UNIQUE INDEX tags_teacher_lower_name_applies_to_idx
  ON tags (teacher_id, lower(name), applies_to);

-- 9. Lock the Data API on the new tables (same rule as schema.sql)
ALTER TABLE share_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals       ENABLE ROW LEVEL SECURITY;
ALTER TABLE invites     ENABLE ROW LEVEL SECURITY;

-- OPTIONAL, NOT YET APPROVED: make every account email lowercase so invites match users.
-- 0 existing rows break it (checked Nov 19). Uncomment only if Theo says yes.
-- ALTER TABLE users ADD CONSTRAINT users_email_lowercase CHECK (email = lower(email));

COMMIT;