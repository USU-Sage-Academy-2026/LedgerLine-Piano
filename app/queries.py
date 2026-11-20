"""App SQL. Mirrors sql/queries.sql (a-g) - change both together.

Every query uses %(name)s parameters; pass a dict to db.execute().
%(teacher_id)s is always session["user_id"] (studios.teacher_id -> users.id).
%(student_id)s is a students.id, never taken from a URL without an ownership check.
"""

# Shared "this week" bounds: Monday 00:00 to next Monday 00:00, America/Denver.
_WEEK = """
WITH week AS (
  SELECT
    date_trunc('week', now() AT TIME ZONE 'America/Denver') AT TIME ZONE 'America/Denver'
      AS week_start,
    (date_trunc('week', now() AT TIME ZONE 'America/Denver') + interval '7 days') AT TIME ZONE 'America/Denver'
      AS week_end
)
"""

# ---------------------------------------------------------------- lookups / ownership

TEACHER_STUDIO = """
SELECT s.id, s.name, c.name AS city, c.state
FROM studios s
JOIN cities c ON c.id = s.city_id
WHERE s.teacher_id = %(teacher_id)s
"""

# The logged-in student's own students row.
STUDENT_FOR_USER = """
SELECT st.id, st.weekly_goal_minutes
FROM students st
WHERE st.user_id = %(user_id)s
"""

# Returns a row ONLY if the student is in this teacher's studio (ownership check).
TEACHER_STUDENT = """
SELECT st.id, u.display_name, st.weekly_goal_minutes
FROM students st
JOIN users u   ON u.id = st.user_id
JOIN studios s ON s.id = st.studio_id
WHERE st.id = %(student_id)s
  AND s.teacher_id = %(teacher_id)s
"""

# ---------------------------------------------------------------- a-g (from sql/queries.sql)

# a. Minutes each of my students practiced this week vs. their weekly goal.
STUDIO_WEEK_MINUTES = _WEEK + """
SELECT
  st.id                          AS student_id,
  u.display_name,
  COALESCE(SUM(pl.minutes), 0)   AS minutes_this_week,
  st.weekly_goal_minutes
FROM studios s
CROSS JOIN week w
JOIN students st        ON st.studio_id = s.id
JOIN users u            ON u.id = st.user_id
LEFT JOIN student_pieces sp ON sp.student_id = st.id
LEFT JOIN practice_logs pl  ON pl.student_piece_id = sp.id
                           AND pl.started_at >= w.week_start
                           AND pl.started_at <  w.week_end
WHERE s.teacher_id = %(teacher_id)s
GROUP BY st.id, u.display_name, st.weekly_goal_minutes
ORDER BY u.display_name
"""

# b. Each active piece: current assignment, last practice session, current stage.
STUDENT_PIECES_DETAIL = """
SELECT
  sp.id               AS student_piece_id,
  sp.seq_order,
  p.title,
  p.composer,
  sg.name             AS stage,
  a.title             AS assignment_title,
  a.body              AS assignment_body,
  a.minutes_per_day,
  last_log.minutes    AS last_minutes,
  last_log.started_at AS last_started_at
FROM student_pieces sp
JOIN pieces p  ON p.id = sp.piece_id
JOIN stages sg ON sg.id = sp.current_stage_id
LEFT JOIN LATERAL (
  SELECT pl.minutes, pl.started_at
  FROM practice_logs pl
  WHERE pl.student_piece_id = sp.id
  ORDER BY pl.started_at DESC
  LIMIT 1
) last_log ON true
LEFT JOIN LATERAL (
  SELECT asg.title, asg.body, asg.minutes_per_day
  FROM assignments asg
  WHERE asg.student_piece_id = sp.id
  ORDER BY asg.assigned_on DESC, asg.id DESC
  LIMIT 1
) a ON true
WHERE sp.student_id = %(student_id)s
  AND sp.completed_on IS NULL
ORDER BY sp.seq_order
"""

# c. One student's minutes this week, split by piece (0-minute pieces included).
STUDENT_WEEK_BY_PIECE = _WEEK + """
SELECT
  p.title,
  COALESCE(SUM(pl.minutes), 0) AS minutes_this_week
FROM student_pieces sp
CROSS JOIN week w
JOIN pieces p ON p.id = sp.piece_id
LEFT JOIN practice_logs pl ON pl.student_piece_id = sp.id
                          AND pl.started_at >= w.week_start
                          AND pl.started_at <  w.week_end
WHERE sp.student_id = %(student_id)s
  AND sp.completed_on IS NULL
GROUP BY sp.id, sp.seq_order, p.title
ORDER BY sp.seq_order
"""

# d. When each student last practiced; needs_attention = 4+ days or never.
STUDIO_LAST_PRACTICE = """
SELECT
  st.id                                  AS student_id,
  u.display_name,
  MAX(pl.started_at)                     AS last_practiced_at,
  (MAX(pl.started_at) IS NULL
   OR MAX(pl.started_at) < now() - interval '4 days') AS needs_attention
FROM studios s
JOIN students st        ON st.studio_id = s.id
JOIN users u            ON u.id = st.user_id
LEFT JOIN student_pieces sp ON sp.student_id = st.id
LEFT JOIN practice_logs pl  ON pl.student_piece_id = sp.id
WHERE s.teacher_id = %(teacher_id)s
GROUP BY st.id, u.display_name
ORDER BY needs_attention DESC, last_practiced_at NULLS FIRST
"""

# e. Share link state ('active' / 'expired' / 'revoked') and what the card may show.
SHARE_LINK_BY_TOKEN = """
SELECT
  sl.student_id,
  sl.week_start,
  sl.show_name, sl.show_pieces, sl.show_stages, sl.show_minutes, sl.show_teacher_notes,
  CASE
    WHEN sl.revoked_at IS NOT NULL THEN 'revoked'
    WHEN sl.expires_at <= now()    THEN 'expired'
    ELSE 'active'
  END AS state
FROM share_links sl
WHERE sl.token = %(token)s
"""

# f. My studio's invitations still waiting for an answer.
STUDIO_PENDING_INVITES = """
SELECT i.id, i.email, i.created_at
FROM invites i
JOIN studios s ON s.id = i.studio_id
WHERE s.teacher_id = %(teacher_id)s
  AND i.status = 'pending'
ORDER BY i.created_at DESC
"""

# g. The logged-in student's newest pending invite (banner on the log page).
STUDENT_PENDING_INVITE = """
SELECT i.id, s.name AS studio_name, i.created_at
FROM invites i
JOIN studios s ON s.id = i.studio_id
JOIN users u   ON u.email = i.email
WHERE u.id = %(user_id)s
  AND i.status = 'pending'
ORDER BY i.created_at DESC
LIMIT 1
"""

# ---------------------------------------------------------------- writes

INSERT_PRACTICE_LOG = """
INSERT INTO practice_logs (student_piece_id, started_at, minutes, note)
SELECT sp.id, %(started_at)s, %(minutes)s, %(note)s
FROM student_pieces sp
JOIN students s ON s.id = sp.student_id
WHERE sp.id = %(student_piece_id)s
  AND s.user_id = %(user_id)s
  AND sp.completed_on IS NULL
RETURNING id
"""

# Ownership is inside the WHERE: 0 rows updated if the student isn't this teacher's.
SET_WEEKLY_GOAL = """
UPDATE students st
SET weekly_goal_minutes = %(goal)s
FROM studios s
WHERE st.id = %(student_id)s
  AND s.id = st.studio_id
  AND s.teacher_id = %(teacher_id)s
RETURNING st.id
"""

# week_start = this Monday in Denver (the table CHECK requires a Monday).
SHARE_LINK_CREATE = """
INSERT INTO share_links (student_id, created_by, token, week_start)
VALUES (
  %(student_id)s,
  %(teacher_id)s,
  %(token)s,
  date_trunc('week', now() AT TIME ZONE 'America/Denver')::date
)
RETURNING id
"""

SHARE_LINKS_FOR_STUDENT = """
SELECT
  sl.id, sl.token, sl.week_start, sl.expires_at,
  CASE
    WHEN sl.revoked_at IS NOT NULL THEN 'revoked'
    WHEN sl.expires_at <= now()    THEN 'expired'
    ELSE 'active'
  END AS state
FROM share_links sl
WHERE sl.student_id = %(student_id)s
ORDER BY sl.created_at DESC
"""

# Only revokes a link for a student in this teacher's studio.
SHARE_LINK_REVOKE = """
UPDATE share_links sl
SET revoked_at = now()
FROM students st
JOIN studios s ON s.id = st.studio_id
WHERE sl.id = %(link_id)s
  AND sl.student_id = st.id
  AND s.teacher_id = %(teacher_id)s
  AND sl.revoked_at IS NULL
RETURNING sl.student_id
"""

# ---------------------------------------------------------------- charts

# Studio total minutes per day, last 56 days (line chart).
STUDIO_DAILY_MINUTES = """
WITH days AS (
  SELECT generate_series(
    (now() AT TIME ZONE 'America/Denver')::date - 55,
    (now() AT TIME ZONE 'America/Denver')::date,
    interval '1 day'
  )::date AS day
),
studio_logs AS (
  SELECT (pl.started_at AT TIME ZONE 'America/Denver')::date AS log_day, pl.minutes
  FROM practice_logs pl
  JOIN student_pieces sp ON sp.id = pl.student_piece_id
  JOIN students st       ON st.id = sp.student_id
  JOIN studios s         ON s.id = st.studio_id
  WHERE s.teacher_id = %(teacher_id)s
)
SELECT d.day, COALESCE(SUM(sl.minutes), 0) AS total_minutes
FROM days d
LEFT JOIN studio_logs sl ON sl.log_day = d.day
GROUP BY d.day
ORDER BY d.day
"""

# ---------------------------------------------------------------- progress card (public)
# All card queries take %(student_id)s and %(week_start)s from the share link row.

CARD_STUDENT = """
SELECT u.display_name, st.weekly_goal_minutes
FROM students st
JOIN users u ON u.id = st.user_id
WHERE st.id = %(student_id)s
"""

# Minutes per day for the link's week (7 rows, Mon-Sun, zeros included).
CARD_DAILY_MINUTES = """
WITH days AS (
  SELECT generate_series(%(week_start)s::date, %(week_start)s::date + 6, interval '1 day')::date AS day
),
logs AS (
  SELECT (pl.started_at AT TIME ZONE 'America/Denver')::date AS log_day, pl.minutes
  FROM practice_logs pl
  JOIN student_pieces sp ON sp.id = pl.student_piece_id
  WHERE sp.student_id = %(student_id)s
)
SELECT d.day, COALESCE(SUM(l.minutes), 0) AS minutes
FROM days d
LEFT JOIN logs l ON l.log_day = d.day
GROUP BY d.day
ORDER BY d.day
"""

# Weekly totals for the link's week and the 3 weeks before it (4 rows, oldest first).
CARD_WEEKLY_TOTALS = """
WITH weeks AS (
  SELECT generate_series(%(week_start)s::date - 21, %(week_start)s::date, interval '7 days')::date AS week_start
),
logs AS (
  SELECT (pl.started_at AT TIME ZONE 'America/Denver')::date AS log_day, pl.minutes
  FROM practice_logs pl
  JOIN student_pieces sp ON sp.id = pl.student_piece_id
  WHERE sp.student_id = %(student_id)s
)
SELECT w.week_start, COALESCE(SUM(l.minutes), 0) AS minutes
FROM weeks w
LEFT JOIN logs l ON l.log_day >= w.week_start
                AND l.log_day <  w.week_start + 7
GROUP BY w.week_start
ORDER BY w.week_start
"""

# Active pieces with their current stage (stage is "now", not as of that week).
CARD_PIECES = """
SELECT p.title, p.composer, sg.name AS stage, sg.position AS stage_position
FROM student_pieces sp
JOIN pieces p  ON p.id = sp.piece_id
JOIN stages sg ON sg.id = sp.current_stage_id
WHERE sp.student_id = %(student_id)s
  AND sp.completed_on IS NULL
ORDER BY sp.seq_order
"""

# Lesson notes dated inside the link's week; piece_title is NULL for whole-lesson notes.
CARD_NOTES = """
SELECT ln.lesson_date, ln.body, p.title AS piece_title
FROM lesson_notes ln
LEFT JOIN student_pieces sp ON sp.id = ln.student_piece_id
LEFT JOIN pieces p          ON p.id = sp.piece_id
WHERE ln.student_id = %(student_id)s
  AND ln.lesson_date >= %(week_start)s::date
  AND ln.lesson_date <  %(week_start)s::date + 7
ORDER BY ln.lesson_date
"""


# ================================================================ Nov 19: queries for the remaining pages
# (Frontend chat, for the pages Theo asked for at feature crunch. Same rules: %(name)s params,
#  every teacher write checks ownership inside the SQL.)

# ---------------------------------------------------------------- ownership for one student_piece

# Returns a row ONLY if this student_piece belongs to a student in this teacher's studio.
TEACHER_PIECE = """
SELECT sp.id, sp.student_id, sp.seq_order, sp.current_stage_id, sp.started_on
FROM student_pieces sp
JOIN students st ON st.id = sp.student_id
JOIN studios s   ON s.id = st.studio_id
WHERE sp.id = %(student_piece_id)s
  AND s.teacher_id = %(teacher_id)s
"""

# ---------------------------------------------------------------- lookups for the student page

STAGES = "SELECT id, name, position FROM stages ORDER BY position"

# Extra fields for the teacher's student page header.
STUDENT_PROFILE = """
SELECT u.display_name, u.email, st.parent_email,
       MAX(pl.started_at) AS last_practiced_at
FROM students st
JOIN users u ON u.id = st.user_id
LEFT JOIN student_pieces sp ON sp.student_id = st.id
LEFT JOIN practice_logs pl  ON pl.student_piece_id = sp.id
WHERE st.id = %(student_id)s
GROUP BY u.display_name, u.email, st.parent_email
"""

# Current stage position for each active piece (for the stage ladder + select).
STUDENT_PIECE_STAGES = """
SELECT sp.id AS student_piece_id, sp.current_stage_id, sg.position AS stage_position, sp.piece_id,
       p.rcm_level_id, r.name AS rcm_level, p.henle_level
FROM student_pieces sp
JOIN stages sg ON sg.id = sp.current_stage_id
JOIN pieces p  ON p.id = sp.piece_id
LEFT JOIN rcm_levels r ON r.id = p.rcm_level_id
WHERE sp.student_id = %(student_id)s
  AND sp.completed_on IS NULL
"""

# Finished pieces, newest first.
STUDENT_FINISHED_PIECES = """
SELECT p.title, p.composer, sg.name AS stage, sg.position AS stage_position, sp.completed_on
FROM student_pieces sp
JOIN pieces p  ON p.id = sp.piece_id
JOIN stages sg ON sg.id = sp.current_stage_id
WHERE sp.student_id = %(student_id)s
  AND sp.completed_on IS NOT NULL
ORDER BY sp.completed_on DESC
"""

# The last 5 logs per active piece (shown under "Notes & logs").
STUDENT_RECENT_LOGS = """
SELECT ranked.student_piece_id, ranked.started_at, ranked.minutes, ranked.note
FROM (
  SELECT pl.student_piece_id, pl.started_at, pl.minutes, pl.note,
         ROW_NUMBER() OVER (PARTITION BY pl.student_piece_id ORDER BY pl.started_at DESC) AS rn
  FROM practice_logs pl
  JOIN student_pieces sp ON sp.id = pl.student_piece_id
  WHERE sp.student_id = %(student_id)s
    AND sp.completed_on IS NULL
) ranked
WHERE ranked.rn <= 5
ORDER BY ranked.started_at DESC
"""

# Lesson notes for one student, newest first.
STUDENT_LESSON_NOTES = """
SELECT ln.id, ln.lesson_date, ln.body, p.title AS piece_title
FROM lesson_notes ln
LEFT JOIN student_pieces sp ON sp.id = ln.student_piece_id
LEFT JOIN pieces p          ON p.id = sp.piece_id
WHERE ln.student_id = %(student_id)s
ORDER BY ln.lesson_date DESC, ln.id DESC
LIMIT 20
"""

# ---------------------------------------------------------------- tags

# All of this teacher's tags, presets first.
TEACHER_TAGS = """
SELECT id, name, applies_to, is_preset
FROM tags
WHERE teacher_id = %(teacher_id)s
ORDER BY applies_to, is_preset DESC, lower(name)
"""

# Student tags for every student in the studio (dashboard rows).
STUDIO_STUDENT_TAGS = """
SELECT stg.student_id, t.id, t.name, t.is_preset
FROM student_tags stg
JOIN tags t ON t.id = stg.tag_id
WHERE t.teacher_id = %(teacher_id)s
ORDER BY lower(t.name)
"""

# This teacher's piece tags on one student's active pieces.
STUDENT_PIECE_TAGS = """
SELECT sp.id AS student_piece_id, t.id, t.name
FROM student_pieces sp
JOIN piece_tags pt ON pt.piece_id = sp.piece_id
JOIN tags t        ON t.id = pt.tag_id
WHERE sp.student_id = %(student_id)s
  AND t.teacher_id = %(teacher_id)s
ORDER BY lower(t.name)
"""

TAG_CREATE = """
INSERT INTO tags (teacher_id, name, applies_to)
VALUES (%(teacher_id)s, %(name)s, %(applies_to)s)
RETURNING id
"""

# Presets can't be deleted (the UI shows a lock; this WHERE enforces it).
TAG_DELETE = """
DELETE FROM tags
WHERE id = %(tag_id)s
  AND teacher_id = %(teacher_id)s
  AND NOT is_preset
RETURNING name
"""

# The tag must be this teacher's and the right kind (Flask rule from the schema notes).
STUDENT_TAG_ADD = """
INSERT INTO student_tags (student_id, tag_id)
SELECT %(student_id)s, t.id
FROM tags t
WHERE t.id = %(tag_id)s
  AND t.teacher_id = %(teacher_id)s
  AND t.applies_to = 'student'
ON CONFLICT DO NOTHING
RETURNING tag_id
"""

STUDENT_TAG_REMOVE = """
DELETE FROM student_tags stg
USING tags t
WHERE stg.tag_id = t.id
  AND stg.student_id = %(student_id)s
  AND t.id = %(tag_id)s
  AND t.teacher_id = %(teacher_id)s
"""

PIECE_TAG_ADD = """
INSERT INTO piece_tags (piece_id, tag_id)
SELECT %(piece_id)s, t.id
FROM tags t
WHERE t.id = %(tag_id)s
  AND t.teacher_id = %(teacher_id)s
  AND t.applies_to = 'piece'
ON CONFLICT DO NOTHING
RETURNING tag_id
"""

PIECE_TAG_REMOVE = """
DELETE FROM piece_tags pt
USING tags t
WHERE pt.tag_id = t.id
  AND pt.piece_id = %(piece_id)s
  AND t.id = %(tag_id)s
  AND t.teacher_id = %(teacher_id)s
"""

# The 3 locked default student tags, copied to every new teacher.
PRESET_TAGS_CREATE = """
INSERT INTO tags (teacher_id, name, applies_to, is_preset)
VALUES (%(teacher_id)s, 'Beginner', 'student', true),
       (%(teacher_id)s, 'Adult',    'student', true),
       (%(teacher_id)s, 'RCM 4',    'student', true)
"""

# ---------------------------------------------------------------- repertoire writes (teacher)

# Find the piece, or create it. ON CONFLICT ... DO UPDATE is a no-op that makes RETURNING work
# for both new and existing rows (UNIQUE (title, composer)).
PIECE_FIND_OR_CREATE = """
INSERT INTO pieces (title, composer, rcm_level_id, henle_level)
VALUES (%(title)s, %(composer)s, %(rcm_level_id)s, %(henle_level)s)
ON CONFLICT (title, composer) DO UPDATE
  SET rcm_level_id = COALESCE(pieces.rcm_level_id, EXCLUDED.rcm_level_id),  -- fill gaps, never overwrite
      henle_level  = COALESCE(pieces.henle_level,  EXCLUDED.henle_level)
RETURNING id
"""

# New piece goes to the end of the student's list, at stage 1.
STUDENT_PIECE_CREATE = """
INSERT INTO student_pieces (student_id, piece_id, seq_order, current_stage_id, started_on)
SELECT %(student_id)s, %(piece_id)s,
       COALESCE(MAX(seq_order), 0) + 1,
       (SELECT id FROM stages WHERE position = 1),
       (now() AT TIME ZONE 'America/Denver')::date
FROM student_pieces
WHERE student_id = %(student_id)s
RETURNING id
"""

STAGE_CHANGE_CREATE = """
INSERT INTO stage_changes (student_piece_id, from_stage_id, to_stage_id, changed_by)
VALUES (%(student_piece_id)s, %(from_stage_id)s, %(to_stage_id)s, %(teacher_id)s)
"""

# Keep current_stage_id in step with stage_changes (same transaction, see schema notes).
SET_CURRENT_STAGE = """
UPDATE student_pieces
SET current_stage_id = %(to_stage_id)s
WHERE id = %(student_piece_id)s
"""

# Saving an assignment adds a new row; the newest row is "the" assignment (history kept).
ASSIGNMENT_CREATE = """
INSERT INTO assignments (student_piece_id, title, body, minutes_per_day)
VALUES (%(student_piece_id)s, %(title)s, %(body)s, %(minutes_per_day)s)
"""

# The active piece just above or below (for the up/down buttons).
NEIGHBOR_PIECE = """
SELECT id, seq_order
FROM student_pieces
WHERE student_id = %(student_id)s
  AND completed_on IS NULL
  AND CASE WHEN %(direction)s = 'up' THEN seq_order < %(seq_order)s
           ELSE seq_order > %(seq_order)s END
ORDER BY CASE WHEN %(direction)s = 'up' THEN -seq_order ELSE seq_order END
LIMIT 1
"""

# The UNIQUE (student_id, seq_order) is DEFERRABLE INITIALLY DEFERRED, so two updates in one
# transaction can swap positions without a temporary clash.
SET_SEQ_ORDER = "UPDATE student_pieces SET seq_order = %(seq_order)s WHERE id = %(student_piece_id)s"

FINISH_PIECE = """
UPDATE student_pieces
SET completed_on = GREATEST((now() AT TIME ZONE 'America/Denver')::date, started_on)
WHERE id = %(student_piece_id)s
  AND completed_on IS NULL
"""

LESSON_NOTE_CREATE = """
INSERT INTO lesson_notes (student_id, body, student_piece_id, lesson_date)
VALUES (%(student_id)s, %(body)s, %(student_piece_id)s, (now() AT TIME ZONE 'America/Denver')::date)
"""

# Share link with the 5 "what viewers see" checkboxes. created_by = whoever made it.
SHARE_LINK_CREATE_WITH_FIELDS = """
INSERT INTO share_links (student_id, created_by, token, week_start,
                         show_name, show_pieces, show_stages, show_minutes, show_teacher_notes)
VALUES (
  %(student_id)s, %(user_id)s, %(token)s,
  date_trunc('week', now() AT TIME ZONE 'America/Denver')::date,
  %(show_name)s, %(show_pieces)s, %(show_stages)s, %(show_minutes)s, %(show_teacher_notes)s
)
RETURNING id
"""

# ---------------------------------------------------------------- invites + join code

STUDIO_JOIN_CODE = "SELECT join_code FROM studios WHERE teacher_id = %(teacher_id)s"

SET_JOIN_CODE = """
UPDATE studios SET join_code = %(code)s
WHERE teacher_id = %(teacher_id)s
"""

# Is this email already a student in my studio?
STUDENT_IN_STUDIO_BY_EMAIL = """
SELECT 1
FROM users u
JOIN students st ON st.user_id = u.id
JOIN studios s   ON s.id = st.studio_id
WHERE u.email = %(email)s
  AND s.teacher_id = %(teacher_id)s
"""

INVITE_CREATE = """
INSERT INTO invites (studio_id, email)
SELECT s.id, %(email)s
FROM studios s
WHERE s.teacher_id = %(teacher_id)s
RETURNING id
"""

INVITE_REMOVE = """
DELETE FROM invites i
USING studios s
WHERE i.studio_id = s.id
  AND i.id = %(invite_id)s
  AND s.teacher_id = %(teacher_id)s
  AND i.status = 'pending'
RETURNING i.email
"""

# The student answers an invite sent to THEIR email (checked in the WHERE).
INVITE_RESPOND = """
UPDATE invites i
SET status = %(status)s, responded_at = now()
FROM users u
WHERE i.id = %(invite_id)s
  AND u.id = %(user_id)s
  AND i.email = u.email
  AND i.status = 'pending'
RETURNING i.studio_id
"""

SET_STUDENT_STUDIO = """
UPDATE students SET studio_id = %(studio_id)s
WHERE user_id = %(user_id)s
"""

STUDIO_BY_JOIN_CODE = "SELECT id, name FROM studios WHERE join_code = %(code)s"

# The student's current studio + teacher name (log page, card).
STUDENT_STUDIO = """
SELECT s.name AS studio_name, t.display_name AS teacher_name
FROM students st
JOIN studios s ON s.id = st.studio_id
JOIN users t   ON t.id = s.teacher_id
WHERE st.user_id = %(user_id)s
"""

# The student's newest active link for this week's card.
STUDENT_ACTIVE_LINK = """
SELECT token, expires_at
FROM share_links
WHERE student_id = %(student_id)s
  AND revoked_at IS NULL
  AND expires_at > now()
  AND week_start = date_trunc('week', now() AT TIME ZONE 'America/Denver')::date
ORDER BY created_at DESC
LIMIT 1
"""


# ================================================================ Nov 19 (2): difficulty, goals, profile pages

RCM_LEVELS = "SELECT id, name FROM rcm_levels ORDER BY sort_order"

# Difficulty belongs to the piece itself (pieces is shared by every studio), so this changes it everywhere.
SET_PIECE_LEVELS = """
UPDATE pieces p
SET rcm_level_id = %(rcm_level_id)s, henle_level = %(henle_level)s
FROM student_pieces sp
WHERE sp.id = %(student_piece_id)s
  AND p.id = sp.piece_id
"""

# ---------------------------------------------------------------- goals (student)

# This period's goals for one tab ('general' goals have no period_start).
GOALS_FOR_PERIOD = """
SELECT id, body, kind, target_count, done_count, completed_at
FROM goals
WHERE student_id = %(student_id)s
  AND period = %(period)s
  AND (period_start IS NOT DISTINCT FROM %(period_start)s)
ORDER BY completed_at IS NOT NULL, created_at
"""

GOALS_COMPLETED = """
SELECT id, body, kind, target_count, done_count, completed_at, period
FROM goals
WHERE student_id = %(student_id)s
  AND completed_at IS NOT NULL
ORDER BY completed_at DESC
LIMIT 30
"""

GOAL_CREATE = """
INSERT INTO goals (student_id, period, period_start, body, kind, target_count)
VALUES (%(student_id)s, %(period)s, %(period_start)s, %(body)s, %(kind)s, %(target_count)s)
"""

# Check goals: done <-> not done.
GOAL_TOGGLE = """
UPDATE goals
SET completed_at = CASE WHEN completed_at IS NULL THEN now() ELSE NULL END
WHERE id = %(goal_id)s
  AND student_id = %(student_id)s
  AND kind = 'check'
"""

# Count goals: +1 / -1, kept between 0 and the target; completed exactly when full
# (the CHECK in migration 002 requires that).
GOAL_STEP = """
UPDATE goals
SET done_count   = LEAST(GREATEST(done_count + %(delta)s, 0), target_count),
    completed_at = CASE WHEN LEAST(GREATEST(done_count + %(delta)s, 0), target_count) = target_count
                        THEN COALESCE(completed_at, now()) END
WHERE id = %(goal_id)s
  AND student_id = %(student_id)s
  AND kind = 'count'
"""

GOAL_DELETE = "DELETE FROM goals WHERE id = %(goal_id)s AND student_id = %(student_id)s"

# ---------------------------------------------------------------- profiles

STUDENT_PROFILE_SELF = """
SELECT u.display_name, u.email, st.parent_email, s.name AS studio_name, t.display_name AS teacher_name
FROM users u
JOIN students st    ON st.user_id = u.id
LEFT JOIN studios s ON s.id = st.studio_id
LEFT JOIN users t   ON t.id = s.teacher_id
WHERE u.id = %(user_id)s
"""

SET_CONTACT_EMAIL = "UPDATE students SET parent_email = %(email)s WHERE user_id = %(user_id)s"

TEACHER_PROFILE = """
SELECT u.display_name, u.email, s.name AS studio_name, s.join_code, c.name AS city, c.state,
       (SELECT COUNT(*) FROM students st WHERE st.studio_id = s.id) AS student_count
FROM users u
JOIN studios s ON s.teacher_id = u.id
JOIN cities c  ON c.id = s.city_id
WHERE u.id = %(teacher_id)s
"""

SET_STUDIO_NAME = "UPDATE studios SET name = %(name)s WHERE teacher_id = %(teacher_id)s"
