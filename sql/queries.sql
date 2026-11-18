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