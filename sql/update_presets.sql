-- Data fix (Nov 19), no schema change. Safe to run more than once.
-- 1. seed.py's bracketed level tags ("[RCM 3]", "[Prep A]", "[ARCT]") are presets: lock them.
-- 2. Every teacher gets the 3 locked default student tags (new signups already get them in auth.py).
-- Run in the Supabase SQL editor (or psql) after migrations 002 and 003.

BEGIN;

UPDATE tags
SET is_preset = true
WHERE applies_to = 'student'
  AND name ~ '^\[.+\]$';

INSERT INTO tags (teacher_id, name, applies_to, is_preset)
SELECT u.id, preset.name, 'student', true
FROM users u
CROSS JOIN (VALUES ('Beginner'), ('Adult'), ('RCM 4')) AS preset(name)
WHERE u.role = 'teacher'
ON CONFLICT DO NOTHING;          -- skips teachers who already have a tag with that name

COMMIT;
