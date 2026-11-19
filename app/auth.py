"""Controlls user registration, login, and logout.
Registration requries all forms to be filled out, and checks for valid email and minimum password length. 
Login checks for correct email and password. 
Logout clears the session."""
from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import generate_password_hash, check_password_hash #basic security uses password hashing
from .db import get_db
from . import queries
import functools
import psycopg
from email_validator import validate_email, EmailNotValidError


bp = Blueprint("auth", __name__, url_prefix="/auth") # auth blueprint for all logins

def is_valid_email(email):
    """True if the address has valid syntax. No DNS lookup (see notes)."""
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False

def home_url_for(role):
    """URL each role lands on after logging in or registering."""
    if role == "teacher":
        return url_for("teacher.dashboard")
    return url_for("student.log_practice")

def create_account(display_name, email, password, role, studio_name=None, city_id=None):
    """Insert a user plus their students or studios row atomically. Returns the new user id."""
    db = get_db()
    password_hash = generate_password_hash(password) # password hashing
    with db.transaction(): # allows for easier rollback if something goes wrong (eg bad city_id, but user info works)
        row = db.execute(
            """
            INSERT INTO users (email, password_hash, display_name, role)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (email, password_hash, display_name, role),
        ).fetchone() # send to db
        user_id = row["id"]
        if role == "student": # role logic
            db.execute("INSERT INTO students (user_id) VALUES (%s)", (user_id,))
        else:
            db.execute(
                "INSERT INTO studios (teacher_id, city_id, name) VALUES (%s, %s, %s)",
                (user_id, city_id, studio_name),
            )
    return user_id # log in automatically, no need to retype password

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
            if "user_id" not in session:
                return redirect(url_for("auth.login"))
            if session.get("role") != role:
                abort(403) # forbidden
            return view(**kwargs)
        return wrapped
    return decorator


def current_student_or_404():
    """The logged-in student's students row (id, weekly_goal_minutes)."""
    student = get_db().execute(
        queries.STUDENT_FOR_USER, {"user_id": session["user_id"]}
    ).fetchone()
    if student is None:
        abort(404)
    return student


def teacher_student_or_404(student_id):
    """Return the student only if they're in the logged-in teacher's studio.

    404 (not 403) so a teacher can't tell other studios' student ids exist.
    The DB connection bypasses RLS, so this is the only ownership guard.
    """
    student = get_db().execute(
        queries.TEACHER_STUDENT,
        {"student_id": student_id, "teacher_id": session["user_id"]},
    ).fetchone()
    if student is None:
        abort(404)
    return student


@bp.route("/register", methods=["GET", "POST"])
def register():
    """GET: show the form. POST: validate, create the account, log the user in."""
    minlength = current_app.config["MIN_PASSWORD_LENGTH"] # get the minimum password length from the config
    form = request.form if request.method == "POST" else {}
    if request.method == "POST":
        display_name = form.get("display_name", "").strip() # info from form is prepared
        email = form.get("email", "").strip().lower()
        password = form.get("password", "")
        role = form.get("role", "")
        studio_name = form.get("studio_name", "").strip()
        city_id = form.get("city_id", "")

        error = None
        if role not in ("teacher", "student"): # force role
            error = "Choose teacher or student."
        elif not display_name or not email or not password: # force required fields
            error = "Name, email and password are required."
        elif not is_valid_email(email): # force valid email
            error = "Enter a valid email address."
        elif len(password) < minlength: # force minimum password length
            error = f"Password must be at least {minlength} characters."
        elif role == "teacher" and (not studio_name or not city_id.isdigit()): # force required fields for teachers
            error = "Teachers need a studio name and a city."

        if error is None:
            try:
                user_id = create_account(
                    display_name, email, password, role,
                    studio_name if role == "teacher" else None,
                    int(city_id) if role == "teacher" else None,
                )
                get_db().commit() # commit the transaction if everything is successful
            except psycopg.errors.UniqueViolation: # prevent runtime errors
                error = "That email is already registered."
            except psycopg.errors.ForeignKeyViolation:
                error = "Choose a city from the list."
            else:
                session.clear()
                session["user_id"] = user_id
                session["role"] = role
                return redirect(home_url_for(role))
        flash(error) # shows user what went wrong

    cities = get_db().execute("SELECT id, name, state FROM cities ORDER BY name").fetchall()
    return render_template("auth/register.html", form=form, cities=cities)

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
            return redirect(home_url_for(session["role"])) # redirect to home page
    return render_template("auth/login.html") # renders the login form if the request method is GET or if the login failed

@bp.route("/logout", methods=["GET"]) # only get request
@login_required # ensures that the user is logged in before logging out
def logout():
    """Log the user out."""
    session.clear() # clears the session
    flash("You have been logged out.") # generic ahh logout message
    return redirect(url_for("auth.login")) # redirects to the login page after logging out



