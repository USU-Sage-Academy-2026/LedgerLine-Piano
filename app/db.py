def get_db(exc=None):
    """Open database connection if its not open"""
    if "db" not in g: 
        g.db = psycopg.connect(current_app.config["DATABASE_URL"])
    return g.db
def close_db(exc=None):
    """Close this request's connection, if one was opened."""
    db = g.pop("db", None)
    if db is not None:
        db.close()