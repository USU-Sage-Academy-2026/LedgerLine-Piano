"""Database helpers: one psycopg connection per request."""
import psycopg
from psycopg.rows import dict_row
from flask import current_app, g


def get_db():
    """Return this request's DB connection, only opens if not opened already."""
    if "db" not in g:
        g.db = psycopg.connect(
            current_app.config["DATABASE_URL"],
            row_factory=dict_row,
        )
    return g.db
def close_db(exc=None):
    """Close this request's connection, if one was opened."""
    db = g.pop("db", None)
    if db is not None:
        db.close()