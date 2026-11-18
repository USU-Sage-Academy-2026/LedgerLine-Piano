# Teacher only dashboard
from flask import Blueprint, abort, render_template, session

from app.auth import role_required
from app.db import get_db

bp = Blueprint("teacher", __name__, url_prefix="/teacher") # teacher blueprint for dashboard and other teacher-only routes


@bp.get("/dashboard")
@role_required("teacher") # see auth.py
def dashboard():
    """Teacher home: their studio now, their students next."""
    studio = get_db().execute(
        """
        SELECT s.id, s.name, c.name AS city, c.state
        FROM studios s
        JOIN cities c ON c.id = s.city_id
        WHERE s.teacher_id = %s
        """, # measures by session user_id, not url
        (session["user_id"],),
    ).fetchone()
    if studio is None:
        abort(404) # shouldn't happen since acc creation requires a studio
    return render_template("teacher/dashboard.html", studio=studio)