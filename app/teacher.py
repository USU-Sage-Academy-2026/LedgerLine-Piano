"""Teacher-only pages: dashboard, student detail, weekly goal, share links."""
import secrets

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from app import queries
from app.auth import role_required, teacher_student_or_404
from app.db import get_db

bp = Blueprint("teacher", __name__, url_prefix="/teacher")


@bp.get("/dashboard")
@role_required("teacher")
def dashboard():
    """Studio overview: minutes vs goal (a), who needs attention (d), pending invites (f)."""
    db = get_db()
    params = {"teacher_id": session["user_id"]}  # always the session, never the URL
    studio = db.execute(queries.TEACHER_STUDIO, params).fetchone()
    if studio is None:
        abort(404)  # every teacher account is created with a studio
    students = db.execute(queries.STUDIO_WEEK_MINUTES, params).fetchall()
    attention = db.execute(queries.STUDIO_LAST_PRACTICE, params).fetchall()
    invites = db.execute(queries.STUDIO_PENDING_INVITES, params).fetchall()
    return render_template(
        "teacher/dashboard.html",
        studio=studio, students=students, attention=attention, invites=invites,
    )


@bp.get("/students/<int:student_id>")
@role_required("teacher")
def student_detail(student_id):
    """One student: pieces (b), this week by piece (c), goal form, share links."""
    student = teacher_student_or_404(student_id)  # ownership check BEFORE any query
    db = get_db()
    params = {"student_id": student_id}
    pieces = db.execute(queries.STUDENT_PIECES_DETAIL, params).fetchall()
    week_by_piece = db.execute(queries.STUDENT_WEEK_BY_PIECE, params).fetchall()
    links = db.execute(queries.SHARE_LINKS_FOR_STUDENT, params).fetchall()
    return render_template(
        "teacher/student.html",
        student=student, pieces=pieces, week_by_piece=week_by_piece,
        week_total=sum(row["minutes_this_week"] for row in week_by_piece),
        links=links,
    )


@bp.post("/students/<int:student_id>/goal")
@role_required("teacher")
def set_weekly_goal(student_id):
    """Set or clear (blank) a student's weekly minutes goal."""
    teacher_student_or_404(student_id)
    raw = request.form.get("weekly_goal_minutes", "").strip()
    if raw and not (raw.isdigit() and 1 <= int(raw) <= 5000):
        flash("Goal must be a whole number from 1 to 5000, or blank for no goal.")
    else:
        db = get_db()
        db.execute(
            queries.SET_WEEKLY_GOAL,
            {"goal": int(raw) if raw else None,
             "student_id": student_id, "teacher_id": session["user_id"]},
        )
        db.commit()
        flash("Weekly goal saved." if raw else "Weekly goal cleared.")
    return redirect(url_for("teacher.student_detail", student_id=student_id))


@bp.post("/students/<int:student_id>/share")
@role_required("teacher")
def create_share_link(student_id):
    """Create a 30-day share link for this week's progress card."""
    teacher_student_or_404(student_id)
    db = get_db()
    db.execute(
        queries.SHARE_LINK_CREATE,
        {"student_id": student_id, "teacher_id": session["user_id"],
         "token": secrets.token_urlsafe(24)},  # ~32 random URL-safe chars
    )
    db.commit()
    flash("Share link created.")
    return redirect(url_for("teacher.student_detail", student_id=student_id))


@bp.post("/share/<int:link_id>/revoke")
@role_required("teacher")
def revoke_share_link(link_id):
    """Turn off a share link (ownership is checked inside the UPDATE)."""
    db = get_db()
    row = db.execute(
        queries.SHARE_LINK_REVOKE,
        {"link_id": link_id, "teacher_id": session["user_id"]},
    ).fetchone()
    if row is None:
        abort(404)  # not this teacher's link, or already revoked
    db.commit()
    flash("Share link turned off.")
    return redirect(url_for("teacher.student_detail", student_id=row["student_id"]))
