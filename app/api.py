from flask import Blueprint, jsonify, session

from app.auth import role_required
from app.db import get_db

bp = Blueprint("api", __name__, url_prefix="/api")

MINUTES_THIS_WEEK_SQL = """
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
"""

@bp.get("/teacher/minutes-this-week")
@role_required("teacher")
def minutes_this_week():
    """Bar chart data: [{student_id, display_name, total_minutes}, ...] for this week."""
    rows = get_db().execute(MINUTES_THIS_WEEK_SQL, (session["user_id"],)).fetchall()
    return jsonify(rows)

STUDIO_MINUTES_DAILY_SQL = """
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
    WHERE st.teacher_id = %s
)
SELECT d.day, COALESCE(SUM(sl.minutes), 0) AS total_minutes
FROM days d
LEFT JOIN studio_logs sl ON d.day = sl.log_day
GROUP BY d.day
ORDER BY d.day"""


@bp.get("/teacher/studio-minutes-daily")
@role_required("teacher")
def studio_minutes_daily():
    """Line chart data: [{day: 'YYYY-MM-DD', total_minutes}, ...], 56 days, oldest first."""
    rows = get_db().execute(STUDIO_MINUTES_DAILY_SQL, (session["user_id"],)).fetchall()
    return jsonify([{"day": r["day"].isoformat(), "total_minutes": r["total_minutes"]} for r in rows])
