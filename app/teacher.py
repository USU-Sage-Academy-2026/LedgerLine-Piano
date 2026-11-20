"""Teacher-only pages: dashboard, student page (pieces, stages, assignments, notes, tags,
weekly goal, share links), the teacher's view of a card, tags and adding students."""
import secrets

import psycopg
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from app import queries
from app.auth import role_required, teacher_student_or_404
from app.card import ALL_FIELDS, load_card, this_monday
from app.db import get_db

bp = Blueprint("teacher", __name__, url_prefix="/teacher")

SHARE_FIELDS = list(ALL_FIELDS)          # show_name, show_pieces, show_stages, show_minutes, show_teacher_notes


def teacher_piece_or_404(student_piece_id):
    """Return the student_piece only if it belongs to one of this teacher's students."""
    piece = get_db().execute(
        queries.TEACHER_PIECE,
        {"student_piece_id": student_piece_id, "teacher_id": session["user_id"]},
    ).fetchone()
    if piece is None:
        abort(404)
    return piece


def parse_levels(form):
    """Read the optional RCM level id and Henle level (1-9) from a form. Returns (rcm, henle, error)."""
    rcm, henle = form.get("rcm_level_id", ""), form.get("henle_level", "")
    if (rcm and not rcm.isdigit()) or (henle and not (henle.isdigit() and 1 <= int(henle) <= 9)):
        return None, None, "Choose a difficulty from the lists."
    return (int(rcm) if rcm else None), (int(henle) if henle else None), None


def back_to_student(student_id):
    """Every student-page form returns to the student page."""
    return redirect(url_for("teacher.student_detail", student_id=student_id))


# ---------------------------------------------------------------- dashboard

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
    # Look-up tables so each student row can show its last-practice info and tags.
    last = {row["student_id"]: row for row in attention}
    tags = {}
    for row in db.execute(queries.STUDIO_STUDENT_TAGS, params).fetchall():
        tags.setdefault(row["student_id"], []).append(row["name"])
    week_total = sum(row["minutes_this_week"] for row in students)
    return render_template(
        "teacher/dashboard.html",
        studio=studio, students=students, attention=attention, invites=invites,
        last=last, tags=tags, week_total=week_total,
    )


# ---------------------------------------------------------------- one student

@bp.get("/students/<int:student_id>")
@role_required("teacher")
def student_detail(student_id):
    """One student: pieces with stages and assignments, notes, tags, goal, share links."""
    student = teacher_student_or_404(student_id)  # ownership check BEFORE any query
    db = get_db()
    params = {"student_id": student_id}
    tparams = {"student_id": student_id, "teacher_id": session["user_id"]}
    pieces = db.execute(queries.STUDENT_PIECES_DETAIL, params).fetchall()
    week_by_piece = db.execute(queries.STUDENT_WEEK_BY_PIECE, params).fetchall()

    stage_of = {r["student_piece_id"]: r for r in db.execute(queries.STUDENT_PIECE_STAGES, params)}
    logs, piece_tags = {}, {}
    for r in db.execute(queries.STUDENT_RECENT_LOGS, params).fetchall():
        logs.setdefault(r["student_piece_id"], []).append(r)
    for r in db.execute(queries.STUDENT_PIECE_TAGS, tparams).fetchall():
        piece_tags.setdefault(r["student_piece_id"], []).append(r)
    # Week minutes come back in the same order as pieces (both ORDER BY seq_order).
    minutes = [row["minutes_this_week"] for row in week_by_piece]

    all_tags = db.execute(queries.TEACHER_TAGS, {"teacher_id": session["user_id"]}).fetchall()
    student_tags = [r for r in db.execute(queries.STUDIO_STUDENT_TAGS, {"teacher_id": session["user_id"]})
                    if r["student_id"] == student_id]
    return render_template(
        "teacher/student.html",
        student=student,
        profile=db.execute(queries.STUDENT_PROFILE, params).fetchone(),
        pieces=pieces, stage_of=stage_of, logs=logs, piece_tags=piece_tags,
        minutes=minutes, max_minutes=max(minutes + [1]),
        week_by_piece=week_by_piece, week_total=sum(minutes),
        stages=db.execute(queries.STAGES).fetchall(),
        rcm_levels=db.execute(queries.RCM_LEVELS).fetchall(),
        finished=db.execute(queries.STUDENT_FINISHED_PIECES, params).fetchall(),
        notes=db.execute(queries.STUDENT_LESSON_NOTES, params).fetchall(),
        links=db.execute(queries.SHARE_LINKS_FOR_STUDENT, params).fetchall(),
        student_tags=student_tags,
        student_tag_options=[t for t in all_tags if t["applies_to"] == "student"
                             and t["id"] not in {s["id"] for s in student_tags}],
        piece_tag_options=[t for t in all_tags if t["applies_to"] == "piece"],
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
    return back_to_student(student_id)


@bp.post("/students/<int:student_id>/pieces")
@role_required("teacher")
def add_piece(student_id):
    """Assign a new piece: it goes to the end of the list at stage 1, with its first assignment."""
    teacher_student_or_404(student_id)
    form = request.form
    title = form.get("title", "").strip()
    composer = form.get("composer", "").strip() or "Unknown"
    a_title = form.get("assignment_title", "").strip()
    a_body = form.get("assignment_body", "").strip()
    per_day = form.get("minutes_per_day", "").strip()
    if not title or not a_title:
        flash("Enter the piece title and an assignment title.")
        return back_to_student(student_id)
    if per_day and not (per_day.isdigit() and 1 <= int(per_day) <= 300):
        flash("Minutes per day must be a whole number from 1 to 300, or blank.")
        return back_to_student(student_id)
    rcm, henle, error = parse_levels(form)
    if error:
        flash(error)
        return back_to_student(student_id)
    db = get_db()
    try:
        with db.transaction():           # piece + student_piece + first stage + assignment, all or nothing
            piece_id = db.execute(queries.PIECE_FIND_OR_CREATE,
                                  {"title": title, "composer": composer,
                                   "rcm_level_id": rcm, "henle_level": henle}).fetchone()["id"]
            sp_id = db.execute(queries.STUDENT_PIECE_CREATE,
                               {"student_id": student_id, "piece_id": piece_id}).fetchone()["id"]
            first = db.execute("SELECT id FROM stages WHERE position = 1").fetchone()["id"]
            db.execute(queries.STAGE_CHANGE_CREATE,
                       {"student_piece_id": sp_id, "from_stage_id": None, "to_stage_id": first,
                        "teacher_id": session["user_id"]})
            db.execute(queries.ASSIGNMENT_CREATE,
                       {"student_piece_id": sp_id, "title": a_title, "body": a_body or None,
                        "minutes_per_day": int(per_day) if per_day else None})
    except psycopg.errors.UniqueViolation:
        flash("This student already has that piece (current or finished).")
        return back_to_student(student_id)
    except psycopg.errors.ForeignKeyViolation:
        flash("Choose an RCM level from the list.")
        return back_to_student(student_id)
    db.commit()
    flash(f"{title} added at stage 1.")
    return back_to_student(student_id)


@bp.post("/pieces/<int:student_piece_id>/stage")
@role_required("teacher")
def set_stage(student_piece_id):
    """Change a piece's stage: log it in stage_changes AND update current_stage_id together."""
    piece = teacher_piece_or_404(student_piece_id)
    to_stage = request.form.get("stage_id", "")
    db = get_db()
    valid = {row["id"] for row in db.execute(queries.STAGES)}
    if not to_stage.isdigit() or int(to_stage) not in valid:
        flash("Choose one of the six stages.")
    elif int(to_stage) != piece["current_stage_id"]:
        params = {"student_piece_id": student_piece_id, "from_stage_id": piece["current_stage_id"],
                  "to_stage_id": int(to_stage), "teacher_id": session["user_id"]}
        with db.transaction():
            db.execute(queries.STAGE_CHANGE_CREATE, params)
            db.execute(queries.SET_CURRENT_STAGE, params)
        db.commit()
        flash("Stage updated.")
    return back_to_student(piece["student_id"])


@bp.post("/pieces/<int:student_piece_id>/difficulty")
@role_required("teacher")
def set_difficulty(student_piece_id):
    """Set a piece's RCM level and Henle level (read-only labels everywhere else)."""
    piece = teacher_piece_or_404(student_piece_id)
    rcm, henle, error = parse_levels(request.form)
    if error:
        flash(error)
    else:
        db = get_db()
        try:
            db.execute(queries.SET_PIECE_LEVELS,
                       {"rcm_level_id": rcm, "henle_level": henle, "student_piece_id": student_piece_id})
            db.commit()
            flash("Difficulty saved.")
        except psycopg.errors.ForeignKeyViolation:
            db.rollback()
            flash("Choose an RCM level from the list.")
    return back_to_student(piece["student_id"])


@bp.post("/pieces/<int:student_piece_id>/move")
@role_required("teacher")
def move_piece(student_piece_id):
    """Swap a piece with the one above or below it."""
    piece = teacher_piece_or_404(student_piece_id)
    direction = request.form.get("direction")
    if direction not in ("up", "down"):
        abort(400)
    db = get_db()
    other = db.execute(queries.NEIGHBOR_PIECE,
                       {"student_id": piece["student_id"], "seq_order": piece["seq_order"],
                        "direction": direction}).fetchone()
    if other is not None:
        with db.transaction():           # the UNIQUE on seq_order is checked at COMMIT, after both updates
            db.execute(queries.SET_SEQ_ORDER, {"seq_order": other["seq_order"], "student_piece_id": piece["id"]})
            db.execute(queries.SET_SEQ_ORDER, {"seq_order": piece["seq_order"], "student_piece_id": other["id"]})
        db.commit()
    return back_to_student(piece["student_id"])


@bp.post("/pieces/<int:student_piece_id>/finish")
@role_required("teacher")
def finish_piece(student_piece_id):
    """Move a piece to Finished (sets completed_on; logs are kept)."""
    piece = teacher_piece_or_404(student_piece_id)
    db = get_db()
    db.execute(queries.FINISH_PIECE, {"student_piece_id": student_piece_id})
    db.commit()
    flash("Piece moved to Finished.")
    return back_to_student(piece["student_id"])


@bp.post("/pieces/<int:student_piece_id>/assignment")
@role_required("teacher")
def save_assignment(student_piece_id):
    """Save a new version of the piece's assignment (title required)."""
    piece = teacher_piece_or_404(student_piece_id)
    title = request.form.get("assignment_title", "").strip()
    body = request.form.get("assignment_body", "").strip()
    per_day = request.form.get("minutes_per_day", "").strip()
    if not title:
        flash("The assignment needs a title.")
    elif per_day and not (per_day.isdigit() and 1 <= int(per_day) <= 300):
        flash("Minutes per day must be a whole number from 1 to 300, or blank.")
    else:
        db = get_db()
        db.execute(queries.ASSIGNMENT_CREATE,
                   {"student_piece_id": student_piece_id, "title": title, "body": body or None,
                    "minutes_per_day": int(per_day) if per_day else None})
        db.commit()
        flash("Assignment saved.")
    return back_to_student(piece["student_id"])


@bp.post("/students/<int:student_id>/notes")
@role_required("teacher")
def add_lesson_note(student_id):
    """Add a lesson note (whole lesson, or about one of the student's pieces)."""
    teacher_student_or_404(student_id)
    body = request.form.get("body", "").strip()
    about = request.form.get("student_piece_id", "")
    piece_id = None
    if about:
        if not about.isdigit():
            abort(400)
        piece = teacher_piece_or_404(int(about))
        if piece["student_id"] != student_id:   # the piece must belong to THIS student
            abort(400)
        piece_id = piece["id"]
    if not 1 <= len(body) <= 2000:
        flash("A lesson note needs 1 to 2,000 characters.")
    else:
        db = get_db()
        db.execute(queries.LESSON_NOTE_CREATE,
                   {"student_id": student_id, "body": body, "student_piece_id": piece_id})
        db.commit()
        flash("Lesson note added. It shows on the student's card.")
    return back_to_student(student_id)


@bp.post("/students/<int:student_id>/tags")
@role_required("teacher")
def add_student_tag(student_id):
    teacher_student_or_404(student_id)
    tag_id = request.form.get("tag_id", "")
    if tag_id.isdigit():
        db = get_db()
        db.execute(queries.STUDENT_TAG_ADD,
                   {"student_id": student_id, "tag_id": int(tag_id), "teacher_id": session["user_id"]})
        db.commit()
    return back_to_student(student_id)


@bp.post("/students/<int:student_id>/tags/<int:tag_id>/remove")
@role_required("teacher")
def remove_student_tag(student_id, tag_id):
    teacher_student_or_404(student_id)
    db = get_db()
    db.execute(queries.STUDENT_TAG_REMOVE,
               {"student_id": student_id, "tag_id": tag_id, "teacher_id": session["user_id"]})
    db.commit()
    return back_to_student(student_id)


@bp.post("/pieces/<int:student_piece_id>/tags")
@role_required("teacher")
def add_piece_tag(student_piece_id):
    piece = teacher_piece_or_404(student_piece_id)
    tag_id = request.form.get("tag_id", "")
    if tag_id.isdigit():
        db = get_db()
        piece_id = db.execute("SELECT piece_id FROM student_pieces WHERE id = %s",
                              (student_piece_id,)).fetchone()["piece_id"]
        db.execute(queries.PIECE_TAG_ADD,
                   {"piece_id": piece_id, "tag_id": int(tag_id), "teacher_id": session["user_id"]})
        db.commit()
    return back_to_student(piece["student_id"])


@bp.post("/pieces/<int:student_piece_id>/tags/<int:tag_id>/remove")
@role_required("teacher")
def remove_piece_tag(student_piece_id, tag_id):
    piece = teacher_piece_or_404(student_piece_id)
    db = get_db()
    piece_id = db.execute("SELECT piece_id FROM student_pieces WHERE id = %s",
                          (student_piece_id,)).fetchone()["piece_id"]
    db.execute(queries.PIECE_TAG_REMOVE,
               {"piece_id": piece_id, "tag_id": tag_id, "teacher_id": session["user_id"]})
    db.commit()
    return back_to_student(piece["student_id"])


# ---------------------------------------------------------------- cards and share links

@bp.get("/students/<int:student_id>/card")
@role_required("teacher")
def student_card(student_id):
    """The teacher's preview of this week's card (everything shown)."""
    student = teacher_student_or_404(student_id)
    card = load_card(get_db(), student_id, this_monday(), dict(ALL_FIELDS))
    return render_template("teacher/card.html", student=student, card=card)


@bp.post("/students/<int:student_id>/share")
@role_required("teacher")
def create_share_link(student_id):
    """Create a 30-day share link for this week's card, showing only the ticked fields."""
    teacher_student_or_404(student_id)
    fields = {key: key in request.form for key in SHARE_FIELDS}   # unticked boxes aren't sent at all
    if not any(fields.values()):
        flash("Tick at least one thing to share.")
        return back_to_student(student_id)
    db = get_db()
    db.execute(queries.SHARE_LINK_CREATE_WITH_FIELDS,
               {"student_id": student_id, "user_id": session["user_id"],
                "token": secrets.token_urlsafe(24), **fields})  # ~32 random URL-safe chars
    db.commit()
    flash("Share link created. Copy it from the list below.")
    return back_to_student(student_id)


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
    return back_to_student(row["student_id"])


# ---------------------------------------------------------------- tags page

@bp.route("/tags", methods=["GET", "POST"])
@role_required("teacher")
def tags():
    """GET: list my tags. POST: create a tag (case-insensitive unique per kind)."""
    db = get_db()
    params = {"teacher_id": session["user_id"]}
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        applies_to = request.form.get("applies_to", "")
        if applies_to not in ("student", "piece"):
            abort(400)
        if not 1 <= len(name) <= 24:
            flash("A tag name needs 1 to 24 characters.")
        else:
            try:
                db.execute(queries.TAG_CREATE, {**params, "name": name, "applies_to": applies_to})
                db.commit()
                flash(f"Tag “{name}” added.")
            except psycopg.errors.UniqueViolation:
                db.rollback()
                flash("You already have a tag with this name.")
        return redirect(url_for("teacher.tags"))
    all_tags = db.execute(queries.TEACHER_TAGS, params).fetchall()
    return render_template(
        "teacher/tags.html",
        piece_tags=[t for t in all_tags if t["applies_to"] == "piece"],
        student_tags=[t for t in all_tags if t["applies_to"] == "student"],
    )


@bp.post("/tags/<int:tag_id>/delete")
@role_required("teacher")
def delete_tag(tag_id):
    db = get_db()
    row = db.execute(queries.TAG_DELETE, {"tag_id": tag_id, "teacher_id": session["user_id"]}).fetchone()
    db.commit()
    flash(f"Tag “{row['name']}” deleted." if row else "Preset tags can't be deleted.")
    return redirect(url_for("teacher.tags"))


# ---------------------------------------------------------------- add student (invites + join code)

@bp.route("/invite", methods=["GET", "POST"])
@role_required("teacher")
def invite():
    """GET: invite form, join code, pending invites. POST: send an invite by email."""
    db = get_db()
    params = {"teacher_id": session["user_id"]}
    if request.method == "POST":
        from app.auth import is_valid_email      # imported here to keep the top of the file short
        email = request.form.get("email", "").strip().lower()
        if not is_valid_email(email):
            flash("Enter a valid email address.")
        elif db.execute(queries.STUDENT_IN_STUDIO_BY_EMAIL, {**params, "email": email}).fetchone():
            flash("That student is already in your studio.")
        else:
            try:
                db.execute(queries.INVITE_CREATE, {**params, "email": email})
                db.commit()
                flash(f"Invite sent to {email}. They'll see it when they log in.")
            except psycopg.errors.UniqueViolation:   # partial unique index: one pending invite per email
                db.rollback()
                flash("You already invited this email. It's in the list below.")
        return redirect(url_for("teacher.invite"))
    return render_template(
        "teacher/invite.html",
        code=db.execute(queries.STUDIO_JOIN_CODE, params).fetchone()["join_code"],
        invites=db.execute(queries.STUDIO_PENDING_INVITES, params).fetchall(),
    )


@bp.post("/invites/<int:invite_id>/remove")
@role_required("teacher")
def remove_invite(invite_id):
    db = get_db()
    row = db.execute(queries.INVITE_REMOVE, {"invite_id": invite_id, "teacher_id": session["user_id"]}).fetchone()
    db.commit()
    if row:
        flash(f"Invite to {row['email']} removed.")
    return redirect(url_for("teacher.invite"))


@bp.post("/join-code")
@role_required("teacher")
def new_join_code():
    """Make a new 6-digit code; the old one stops working. Retries if a code is taken."""
    db = get_db()
    for _ in range(5):
        try:
            with db.transaction():
                db.execute(queries.SET_JOIN_CODE,
                           {"code": f"{secrets.randbelow(1_000_000):06d}", "teacher_id": session["user_id"]})
            db.commit()
            flash("New join code made. The old one no longer works.")
            break
        except psycopg.errors.UniqueViolation:
            continue
    return redirect(url_for("teacher.invite"))


# ---------------------------------------------------------------- Students, Cards, Profile tabs

@bp.get("/students")
@role_required("teacher")
def students():
    """All students with search (?q=) and a tag filter (?tag=)."""
    db = get_db()
    params = {"teacher_id": session["user_id"]}
    rows = db.execute(queries.STUDIO_WEEK_MINUTES, params).fetchall()
    last = {r["student_id"]: r for r in db.execute(queries.STUDIO_LAST_PRACTICE, params)}
    tags = {}
    for r in db.execute(queries.STUDIO_STUDENT_TAGS, params):
        tags.setdefault(r["student_id"], []).append(r["name"])
    q = request.args.get("q", "").strip()
    tag = request.args.get("tag", "")
    shown = [r for r in rows
             if q.lower() in r["display_name"].lower()
             and (not tag or (tag == "attention" and last[r["student_id"]]["needs_attention"])
                  or tag in tags.get(r["student_id"], []))]
    all_tags = [t["name"] for t in db.execute(queries.TEACHER_TAGS, params) if t["applies_to"] == "student"]
    return render_template("teacher/students.html", students=shown, total=len(rows),
                           last=last, tags=tags, q=q, tag=tag, all_tags=all_tags)


@bp.get("/cards")
@role_required("teacher")
def cards():
    """Pick a student and see this week's card (same card as the share link, all fields)."""
    db = get_db()
    roster = db.execute(queries.STUDIO_WEEK_MINUTES, {"teacher_id": session["user_id"]}).fetchall()
    chosen = request.args.get("student_id", "")
    card = student = None
    if roster:
        student_id = int(chosen) if chosen.isdigit() else roster[0]["student_id"]
        student = teacher_student_or_404(student_id)        # also stops other teachers' ids
        card = load_card(db, student_id, this_monday(), dict(ALL_FIELDS))
    return render_template("teacher/cards.html", roster=roster, student=student, card=card)


@bp.route("/profile", methods=["GET", "POST"])
@role_required("teacher")
def profile():
    """Account details; the studio name can be changed."""
    db = get_db()
    params = {"teacher_id": session["user_id"]}
    if request.method == "POST":
        name = request.form.get("studio_name", "").strip()
        if not 1 <= len(name) <= 80:
            flash("The studio name needs 1 to 80 characters.")
        else:
            db.execute(queries.SET_STUDIO_NAME, {**params, "name": name})
            db.commit()
            flash("Studio name saved.")
        return redirect(url_for("teacher.profile"))
    return render_template("teacher/profile.html", me=db.execute(queries.TEACHER_PROFILE, params).fetchone())
