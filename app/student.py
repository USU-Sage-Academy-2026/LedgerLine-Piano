"""Student-only pages: log practice, my pieces, my weekly card, invites and join code."""
import secrets
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from app import queries
from app.auth import current_student_or_404, role_required
from app.card import ALL_FIELDS, STUDIO_TZ, load_card, this_monday
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
    studio = db.execute(queries.STUDENT_STUDIO, {"user_id": session["user_id"]}).fetchone()
    return render_template(
        "student/log.html",
        form=form, pieces=pieces, week_total=week_total,
        goal=student["weekly_goal_minutes"], invite=invite, studio=studio,
    )


@bp.get("/pieces")
@role_required("student")
def pieces():
    """My current pieces (in my teacher's order) and finished pieces."""
    student = current_student_or_404()
    db = get_db()
    params = {"student_id": student["id"]}
    stage_of = {r["student_piece_id"]: r for r in db.execute(queries.STUDENT_PIECE_STAGES, params)}
    return render_template(
        "student/pieces.html",
        pieces=db.execute(queries.STUDENT_PIECES_DETAIL, params).fetchall(),
        stage_of=stage_of,
        finished=db.execute(queries.STUDENT_FINISHED_PIECES, params).fetchall(),
    )


@bp.get("/card")
@role_required("student")
def card():
    """My card for this week, plus my newest share link."""
    student = current_student_or_404()
    db = get_db()
    return render_template(
        "student/card.html",
        card=load_card(db, student["id"], this_monday(), dict(ALL_FIELDS)),
        link=db.execute(queries.STUDENT_ACTIVE_LINK, {"student_id": student["id"]}).fetchone(),
    )


@bp.post("/share")
@role_required("student")
def share():
    """Students can share their own card too (same 5 checkboxes as the teacher)."""
    student = current_student_or_404()
    fields = {key: key in request.form for key in ALL_FIELDS}
    if not any(fields.values()):
        flash("Tick at least one thing to share.")
        return redirect(url_for("student.card"))
    db = get_db()
    db.execute(queries.SHARE_LINK_CREATE_WITH_FIELDS,
               {"student_id": student["id"], "user_id": session["user_id"],
                "token": secrets.token_urlsafe(24), **fields})
    db.commit()
    flash("Share link created. It works for 30 days.")
    return redirect(url_for("student.card"))


@bp.post("/invites/<int:invite_id>")
@role_required("student")
def respond_invite(invite_id):
    """Accept (join the studio) or decline an invite sent to my email."""
    answer = request.form.get("answer")
    if answer not in ("accepted", "declined"):
        abort(400)
    db = get_db()
    params = {"invite_id": invite_id, "user_id": session["user_id"], "status": answer}
    with db.transaction():
        row = db.execute(queries.INVITE_RESPOND, params).fetchone()
        if row is None:
            abort(404)
        if answer == "accepted":
            db.execute(queries.SET_STUDENT_STUDIO, {"studio_id": row["studio_id"], "user_id": session["user_id"]})
    db.commit()
    flash("You joined the studio." if answer == "accepted" else "Invite declined.")
    return redirect(url_for("student.log_practice"))


@bp.post("/join")
@role_required("student")
def join():
    """Join a studio with the teacher's 6-digit code."""
    code = request.form.get("code", "").replace(" ", "")
    db = get_db()
    studio = db.execute(queries.STUDIO_BY_JOIN_CODE, {"code": code}).fetchone() if code.isdigit() else None
    if studio is None:
        flash("That code didn't match a studio. Check it with your teacher.")
    else:
        db.execute(queries.SET_STUDENT_STUDIO, {"studio_id": studio["id"], "user_id": session["user_id"]})
        db.commit()
        flash(f"You joined {studio['name']}.")
    return redirect(url_for("student.log_practice"))


# ---------------------------------------------------------------- Goals and Profile tabs

GOAL_TABS = ["week", "month", "year", "general", "completed"]


def period_start(period):
    """First day of the current week/month/year (Denver); None for general goals."""
    monday = this_monday()
    today = datetime.now(STUDIO_TZ).date()
    return {"week": monday, "month": today.replace(day=1),
            "year": today.replace(month=1, day=1), "general": None}[period]


@bp.route("/goals", methods=["GET", "POST"])
@role_required("student")
def goals():
    """GET: one tab of goals (?tab=week). POST: add a goal to that tab."""
    student = current_student_or_404()
    db = get_db()
    tab = request.args.get("tab", "week")
    if tab not in GOAL_TABS:
        tab = "week"
    if request.method == "POST":
        body = request.form.get("body", "").strip()
        target = request.form.get("target_count", "").strip()
        counted = "counted" in request.form
        if tab == "completed" or not 1 <= len(body) <= 140:
            flash("A goal needs 1 to 140 characters.")
        elif counted and not (target.isdigit() and 1 <= int(target) <= 50):
            flash("The target must be a whole number from 1 to 50.")
        else:
            db.execute(queries.GOAL_CREATE, {
                "student_id": student["id"], "period": tab, "period_start": period_start(tab),
                "body": body, "kind": "count" if counted else "check",
                "target_count": int(target) if counted else None})
            db.commit()
            flash("Goal added.")
        return redirect(url_for("student.goals", tab=tab))
    if tab == "completed":
        rows = db.execute(queries.GOALS_COMPLETED, {"student_id": student["id"]}).fetchall()
    else:
        rows = db.execute(queries.GOALS_FOR_PERIOD, {"student_id": student["id"], "period": tab,
                                                     "period_start": period_start(tab)}).fetchall()
    return render_template("student/goals.html", goals=rows, tab=tab, tabs=GOAL_TABS)


@bp.post("/goals/<int:goal_id>/<action>")
@role_required("student")
def goal_action(goal_id, action):
    """toggle (check goals), plus / minus (count goals), delete. Ownership is in every WHERE."""
    student = current_student_or_404()
    params = {"goal_id": goal_id, "student_id": student["id"]}
    sql = {"toggle": queries.GOAL_TOGGLE, "plus": queries.GOAL_STEP, "minus": queries.GOAL_STEP,
           "delete": queries.GOAL_DELETE}.get(action)
    if sql is None:
        abort(404)
    db = get_db()
    db.execute(sql, {**params, "delta": 1 if action == "plus" else -1})
    db.commit()
    if action == "delete":
        flash("Goal deleted.")
    return redirect(url_for("student.goals", tab=request.form.get("tab", "week")))


@bp.route("/profile", methods=["GET", "POST"])
@role_required("student")
def profile():
    """Account details; the contact email can be changed or cleared."""
    from app.auth import is_valid_email
    db = get_db()
    if request.method == "POST":
        email = request.form.get("contact_email", "").strip().lower()
        if email and not is_valid_email(email):
            flash("Enter a valid contact email, or leave it empty.")
        else:
            db.execute(queries.SET_CONTACT_EMAIL, {"email": email or None, "user_id": session["user_id"]})
            db.commit()
            flash("Contact email saved." if email else "Contact email removed.")
        return redirect(url_for("student.profile"))
    return render_template("student/profile.html",
                           me=db.execute(queries.STUDENT_PROFILE_SELF, {"user_id": session["user_id"]}).fetchone())
