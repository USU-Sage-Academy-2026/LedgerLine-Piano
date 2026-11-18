from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from app.auth import role_required
from app.db import get_db

STUDIO_TZ = ZoneInfo("America/Denver")
MAX_DAYS_BACK = 7


def compute_started_at(minutes, earlier_local=""):
    """Timezone calc (calc is short for calculator, i'm just using slang)
    """
    now = datetime.now(timezone.utc)
    if not earlier_local:
        return now - timedelta(minutes=minutes)
    try:
        naive = datetime.fromisoformat(earlier_local)
    except ValueError:
        return None
    started = naive.replace(tzinfo=STUDIO_TZ).astimezone(timezone.utc)
    if started < now - timedelta(days=MAX_DAYS_BACK):
        return None
    if started + timedelta(minutes=minutes) > now:
        return None
    return started

bp = Blueprint("student", __name__, url_prefix="/student")



@bp.route("/log", methods=["GET", "POST"])
@role_required("student")
def log_practice():
    """GET: show the log form. POST: validate and save one practice log."""
    db = get_db()
    form = request.form if request.method == "POST" else {}
    if request.method == "POST":
        piece_id = form.get("student_piece_id", "")
        minutes = form.get("minutes", "")
        note = form.get("note", "").strip()

        error, started_at = None, None
        if not piece_id.isdigit():
            error = "Choose a piece."
        elif not minutes.isdigit() or not 1 <= int(minutes) <= 300:
            error = "Minutes must be a whole number from 1 to 300."
        elif len(note) > 500:
            error = "Notes can be up to 500 characters."
        else:
            started_at = compute_started_at(int(minutes), form.get("earlier_local", ""))
            if started_at is None:
                error = "Start time must be in the last 7 days, and the session can't end in the future."

        if error is None: #no errors so insert practtice log
            row = db.execute(
                """
                INSERT INTO practice_logs (student_piece_id, started_at, minutes, note)
                SELECT sp.id, %s, %s, %s
                FROM student_pieces sp
                JOIN students s ON s.id = sp.student_id
                WHERE sp.id = %s
                AND s.user_id = %s
                AND sp.completed_on IS NULL
                RETURNING id
                """, (started_at, int(minutes), note or None, int(piece_id), session["user_id"]),
            ).fetchone()
            if row is None:
                error = "Choose one of your active pieces."
            else:
                db.commit()
                flash("Practice logged.")
                return redirect(url_for("student.log_practice"))
        flash(error)

    pieces = db.execute( #list of valid pieces
        """
        SELECT sp.id AS student_piece_id, p.title, sp.seq_order
        FROM student_pieces sp
        JOIN pieces p ON p.id = sp.piece_id
        JOIN students s ON s.id = sp.student_id
        WHERE s.user_id = %s
        AND sp.completed_on IS NULL
        ORDER BY sp.seq_order
        """, (session["user_id"],)).fetchall()
    return render_template("student/log.html", form=form, pieces=pieces)