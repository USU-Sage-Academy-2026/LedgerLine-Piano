"""JSON endpoints for Plotly.js charts. All scoped to the logged-in teacher."""
from flask import Blueprint, jsonify, session

from app import queries
from app.auth import role_required, teacher_student_or_404
from app.db import get_db

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.get("/teacher/minutes-this-week")
@role_required("teacher")
def minutes_this_week():
    """Bar chart: [{student_id, display_name, minutes_this_week, weekly_goal_minutes|null}]."""
    rows = get_db().execute(
        queries.STUDIO_WEEK_MINUTES, {"teacher_id": session["user_id"]}
    ).fetchall()
    return jsonify(rows)


@bp.get("/teacher/studio-minutes-daily")
@role_required("teacher")
def studio_minutes_daily():
    """Line chart: [{day: 'YYYY-MM-DD', total_minutes}], 56 days, oldest first."""
    rows = get_db().execute(
        queries.STUDIO_DAILY_MINUTES, {"teacher_id": session["user_id"]}
    ).fetchall()
    return jsonify([{"day": r["day"].isoformat(), "total_minutes": r["total_minutes"]} for r in rows])


@bp.get("/teacher/students/<int:student_id>/week-by-piece")
@role_required("teacher")
def student_week_by_piece(student_id):
    """Student detail chart: [{title, minutes_this_week}] for this week (query c)."""
    teacher_student_or_404(student_id)
    rows = get_db().execute(
        queries.STUDENT_WEEK_BY_PIECE, {"student_id": student_id}
    ).fetchall()
    return jsonify(rows)
