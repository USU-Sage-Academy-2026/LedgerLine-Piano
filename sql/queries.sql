-- how many generated teachers and students exist
-- 10 teachers, 112 students
SELECT role,
       count(*) AS users
FROM users
WHERE is_generated
GROUP BY role;


-- does each generated teacher have the right number of students
-- yes, 13/12 for all but the two demos
SELECT u.email,
       st.name,
       count(s.id) AS students
FROM studios st
JOIN users u ON u.id = st.teacher_id
LEFT JOIN students s ON s.studio_id = st.id
WHERE u.is_generated
GROUP BY u.email, st.name
ORDER BY students DESC;

-- how many logs and when was the first and last log for generated students
-- 6455 logs, from 9/24 to 11/18
SELECT count(*) AS logs,
       min(pl.started_at)::date AS first_day,
       max(pl.started_at) AS last_log
FROM practice_logs pl
JOIN student_pieces sp ON sp.id = pl.student_piece_id
JOIN students s ON s.id = sp.student_id
JOIN users u ON u.id = s.user_id
WHERE u.is_generated;

-- does registration update the db?
-- yes it does
SELECT u.id, u.email, u.role, s.name AS studio, c.name AS city
FROM users u
LEFT JOIN studios s ON s.teacher_id = u.id
LEFT JOIN cities c ON c.id = s.city_id
WHERE u.is_generated = false
ORDER BY u.id DESC;

-- for students
SELECT u.id, u.email, u.role, s.id AS student_row_id, s.studio_id
FROM users u
LEFT JOIN students s ON s.user_id = u.id
WHERE u.is_generated = false
  AND u.role = 'student'
ORDER BY u.id DESC;

-- which students are in this studio?
SELECT u.email, u.display_name, s.id AS student_row_id
FROM users u
JOIN students s ON s.user_id = u.id
WHERE s.studio_id = 8
ORDER BY u.display_name ASC;

-- which students are in this teacher's studio?
SELECT u.email, u.display_name, s.id AS student_row_id
FROM users u
JOIN students s ON s.user_id = u.id
JOIN studios st ON st.id = s.studio_id
WHERE st.teacher_id = 75
ORDER BY u.display_name ASC;

-- which active pieces are assigned to this student?
SELECT sp.id AS student_piece_id, p.title, sp.seq_order
FROM student_pieces sp
JOIN pieces p ON p.id = sp.piece_id
JOIN students s ON s.id = sp.student_id
WHERE s.user_id = %s
    AND sp.completed_on IS NULL
ORDER BY sp.seq_order


-- insert practice log
INSERT INTO practice_logs (student_piece_id, started_at, minutes, note)
SELECT sp.id, %s, %s, %s
FROM student_pieces sp
JOIN students s ON s.id = sp.student_id
WHERE sp.id = %s
    AND s.user_id = %s
    AND sp.completed_on IS NULL
RETURNING id

-- all students in studio's past week (starting monday) practice amounts
-- coalesce helps return 0 instead of null
SELECT s.id AS student_id, u.display_name, COALESCE(SUM(pl.minutes), 0) AS total_minutes
FROM studios st
JOIN students s ON s.studio_id = st.id
JOIN users u ON u.id = s.user_id
LEFT JOIN student_pieces sp ON sp.student_id = s.id
LEFT JOIN practice_logs pl
    ON pl.student_piece_id = sp.id
    AND date_trunc('week', pl.started_at AT TIME ZONE 'America/Denver')
        = date_trunc('week', now() AT TIME ZONE 'America/Denver')
WHERE st.teacher_id = %s
GROUP BY s.id, u.display_name
ORDER BY u.display_name;

-- select past 8 weeks of practice logs to find total practice time for each day
WITH days AS (
    SELECT generate_series(
        (now() AT TIME ZONE 'America/Denver')::date - 55,
        (now() AT TIME ZONE 'America/Denver')::date,
        interval '1 day'
    )::date AS day
),
studio_logs AS (
    SELECT (pl.started_at AT TIME ZONE 'America/Denver')::date AS log_day, pl.minutes -- select only the day of the log
    FROM practice_logs pl
    JOIN student_pieces sp ON sp.id = pl.student_piece_id
    JOIN students s ON s.id = sp.student_id
    JOIN studios st ON st.id = s.studio_id
    WHERE st.teacher_id = 75
)
SELECT d.day, COALESCE(SUM(sl.minutes), 0) AS total_minutes
FROM days d
LEFT JOIN studio_logs sl ON d.day = sl.log_day
GROUP BY d.day
ORDER BY d.day