"""Register, login and logout routes."""
from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash #basic security uses password hashing
from .db import get_db
import functools

bp = Blueprint("auth", __name__, url_prefix="/auth")

def login_required(view): # wrapper function to ensure that the user is logged in before accessing certain routes
    """Send anonymous users to the login page."""
    @functools.wraps(view)
    def wrapped(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped

def role_required(role): # usually require teacher role
    """Send users without the required role to the login page."""
    def decorator(view):
        @functools.wraps(view)
        def wrapped(**kwargs):
            if session.get("role") != role:
                abort(403) # forbidden
            return view(**kwargs)
        return wrapped
    return decorator


@bp.route("/login", methods=["GET", "POST"]) # ensures both get and post requests work
def login():
    """Show the login form (GET) or log the user in (POST)."""
    if request.method == "POST":
        email = request.form["email"].strip().lower() # prevents case sensitivity and whitespace issues
        password = request.form["password"]
        user = get_db().execute(
            "SELECT id, password_hash, role FROM users WHERE email = %s", # selects the user with the given email from the database
            (email,), # prevents bobby tables joke from happening
        ).fetchone() # (email,) is a tuple with one element, the comma is necessary or else it would just be a string
        if user is None or not check_password_hash(user["password_hash"], password): # None prevents crash
            flash("Wrong email or password.") # generic ahh login message to prevent enumeration attacks
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            return redirect(url_for("health")) # redirects to the health check route after successful login for now at least
    return render_template("auth/login.html") # renders the login form if the request method is GET or if the login failed

@bp.route("/logout", methods=["GET"]) # only get request
@login_required # ensures that the user is logged in before logging out
def logout():
    """Log the user out."""
    session.clear() # clears the session
    flash("You have been logged out.") # generic ahh logout message
    return redirect(url_for("auth.login")) # redirects to the login page after logging out

@bp.route("/teacher-only", methods=["GET"]) # only get request
@role_required("teacher") # test teacher only route
def teacher_only():
    """Temporary test route; delete after testing."""
    return "teacher ok"

