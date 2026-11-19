-- LedgerLine queries (PostgreSQL 17 on Supabase). Flask passes %(name)s parameters via psycopg 3.
-- "This week" = Monday 00:00 to next Monday 00:00 in America/Denver, converted to timestamptz.
-- Bounds are computed in local time, then converted, so a DST change can't shift them by an hour.

-- =====================================================================
-- a. Business question: How many minutes has each of my students practiced
--    this week, compared with their weekly goal? (dashboard rows + bar chart)
-- =====================================================================
WITH week AS (
  SELECT
    date_trunc('week', now() AT TIME ZONE 'America/Denver') AT TIME ZONE 'America/Denver'
      AS week_start,
    (date_trunc('week', now() AT TIME ZONE 'America/Denver') + interval '7 days') AT TIME ZONE 'America/Denver'
      AS week_end
)
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
ORDER BY u.display_name;

-- =====================================================================
-- b. Business question: For each piece a student is working on, what is the
--    current assignment, the last practice session, and the current stage?
--    (log page: "Last time: 45 min, 2 days ago")
-- =====================================================================
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
ORDER BY sp.seq_order;

-- =====================================================================
-- c. Business question: How were one student's minutes this week split
--    across their pieces? (student detail chart; pieces with 0 minutes included)
-- =====================================================================
WITH week AS (
  SELECT
    date_trunc('week', now() AT TIME ZONE 'America/Denver') AT TIME ZONE 'America/Denver'
      AS week_start,
    (date_trunc('week', now() AT TIME ZONE 'America/Denver') + interval '7 days') AT TIME ZONE 'America/Denver'
      AS week_end
)
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
ORDER BY sp.seq_order;

-- =====================================================================
-- d. Business question: When did each of my students last practice, and who
--    needs attention (no practice in 4+ days, or never)?
-- =====================================================================
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
ORDER BY needs_attention DESC, last_practiced_at NULLS FIRST;

-- =====================================================================
-- e. Business question: Is this share link active, expired or turned off,
--    and what may the public page show? (public progress card)
-- =====================================================================
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
WHERE sl.token = %(token)s;

-- =====================================================================
-- f. Business question: Which invitations has my studio sent that are still
--    waiting for an answer? (teacher's "Sent invitations", newest first)
-- =====================================================================
SELECT i.id, i.email, i.created_at
FROM invites i
JOIN studios s ON s.id = i.studio_id
WHERE s.teacher_id = %(teacher_id)s
  AND i.status = 'pending'
ORDER BY i.created_at DESC;

-- =====================================================================
-- g. Business question: Does the logged-in student have a pending invite?
--    (banner on the log page)
-- =====================================================================
SELECT i.id, s.name AS studio_name, i.created_at
FROM invites i
JOIN studios s ON s.id = i.studio_id
JOIN users u   ON u.email = i.email
WHERE u.id = %(user_id)s
  AND i.status = 'pending'
ORDER BY i.created_at DESC
LIMIT 1;