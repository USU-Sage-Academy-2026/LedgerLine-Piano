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
