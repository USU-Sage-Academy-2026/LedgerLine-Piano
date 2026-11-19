"""Student-only pages: log practice (with pieces, weekly goal and invite banner)."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app import queries
from app.auth import current_student_or_404, role_required
from app.db import get_db

STUDIO_TZ = ZoneInfo("America/Denver")
MAX_DAYS_BACK = 7

bp = Blueprint("student", __name__, url_prefix="/student")


def compute_started_at(minutes, earlier_local=""):
    """Return the session's UTC start time, or None if it's out of range.

    Blank earlier_local = the session just ended now. Otherwise it's a
    datetime-local string in Denver time, at most 7 days back, not ending in the future.
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


def last_time_text(piece):
    """'Last time: 45 min, 2 days ago' or 'Not practiced yet' (Denver calendar days)."""
    if piece["last_started_at"] is None:
        return "Not practiced yet"
    today = datetime.now(STUDIO_TZ).date()
    days = (today - piece["last_started_at"].astimezone(STUDIO_TZ).date()).days
    when = "today" if days == 0 else "yesterday" if days == 1 else f"{days} days ago"
    return f"Last time: {piece['last_minutes']} min, {when}"


@bp.route("/log", methods=["GET", "POST"])
@role_required("student")
def log_practice():
    """GET: show the log form. POST: validate and save one practice log."""
    db = get_db()
    student = current_student_or_404()
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

        if error is None:
            row = db.execute(
                queries.INSERT_PRACTICE_LOG,
                {"started_at": started_at, "minutes": int(minutes), "note": note or None,
                 "student_piece_id": int(piece_id), "user_id": session["user_id"]},
            ).fetchone()
            if row is None:
                error = "Choose one of your active pieces."
            else:
                db.commit()
                flash("Practice logged.")
                return redirect(url_for("student.log_practice"))
        flash(error)

    params = {"student_id": student["id"]}
    pieces = [
        dict(piece, last_text=last_time_text(piece))
        for piece in db.execute(queries.STUDENT_PIECES_DETAIL, params).fetchall()
    ]
    week_total = sum(
        row["minutes_this_week"]
        for row in db.execute(queries.STUDENT_WEEK_BY_PIECE, params).fetchall()
    )
    invite = db.execute(
        queries.STUDENT_PENDING_INVITE, {"user_id": session["user_id"]}
    ).fetchone()
    return render_template(
        "student/log.html",
        form=form, pieces=pieces, week_total=week_total,
        goal=student["weekly_goal_minutes"], invite=invite,
    )
