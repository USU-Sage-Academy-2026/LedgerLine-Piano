"""Public weekly progress card, opened by share-link token. No login required."""
from flask import Blueprint, render_template

from app import queries
from app.db import get_db

bp = Blueprint("card", __name__, url_prefix="/card")


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

    params = {"student_id": link["student_id"], "week_start": link["week_start"]}
    student = db.execute(queries.CARD_STUDENT, params).fetchone()
    days = weeks = pieces = notes = []
    if link["show_minutes"]:
        days = db.execute(queries.CARD_DAILY_MINUTES, params).fetchall()
        weeks = db.execute(queries.CARD_WEEKLY_TOTALS, params).fetchall()
    if link["show_pieces"] or link["show_stages"]:
        pieces = db.execute(queries.CARD_PIECES, params).fetchall()
    if link["show_teacher_notes"]:
        notes = db.execute(queries.CARD_NOTES, params).fetchall()
    return render_template(
        "card/card.html",
        link=link, student=student, days=days, weeks=weeks, pieces=pieces, notes=notes,
        week_total=sum(day["minutes"] for day in days),
    )
