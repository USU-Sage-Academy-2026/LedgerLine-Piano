"""Weekly progress card: the public page (by share-link token) and a shared loader
that the student's and teacher's own card pages reuse."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import Blueprint, render_template

from app import queries
from app.db import get_db

bp = Blueprint("card", __name__, url_prefix="/card")

STUDIO_TZ = ZoneInfo("America/Denver")


def this_monday():
    """Monday of the current week in Denver (weeks start Monday)."""
    today = datetime.now(STUDIO_TZ).date()
    return today - timedelta(days=today.weekday())


ALL_FIELDS = {"show_name": True, "show_pieces": True, "show_stages": True,
              "show_minutes": True, "show_teacher_notes": True}


def load_card(db, student_id, week_start, fields):
    """Everything the card template needs for one student and one week.

    fields: dict of the 5 show_* flags. Data for a hidden field is never queried,
    so it can't leak into the page.
    """
    params = {"student_id": student_id, "week_start": week_start}
    days = weeks = pieces = notes = []
    if fields["show_minutes"]:
        days = db.execute(queries.CARD_DAILY_MINUTES, params).fetchall()
        weeks = db.execute(queries.CARD_WEEKLY_TOTALS, params).fetchall()
    if fields["show_pieces"] or fields["show_stages"]:
        pieces = db.execute(queries.CARD_PIECES, params).fetchall()
    if fields["show_teacher_notes"]:
        notes = db.execute(queries.CARD_NOTES, params).fetchall()
    return {
        "fields": fields,
        "week_start": week_start,
        "student": db.execute(queries.CARD_STUDENT, params).fetchone(),
        "days": days, "weeks": weeks, "pieces": pieces, "notes": notes,
        "week_total": sum(day["minutes"] for day in days),
        "max_day": max([day["minutes"] for day in days] + [1]),
        "max_week": max([week["minutes"] for week in weeks] + [1]),
    }


@bp.get("/<token>")
def view_card(token):
    """Show the card if the link is active; otherwise one generic 'unavailable' page.

    The token is the only key, so unknown, expired and revoked links all get the
    same 404 page: the response never reveals which tokens exist.
    """
    db = get_db()
    link = db.execute(queries.SHARE_LINK_BY_TOKEN, {"token": token}).fetchone()
    if link is None or link["state"] != "active":
        return render_template("card/unavailable.html"), 404
    fields = {key: link[key] for key in ALL_FIELDS}
    card = load_card(db, link["student_id"], link["week_start"], fields)
    return render_template("card/card.html", card=card)
