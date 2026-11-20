# register app and blueprints here
from flask import Flask
from .config import Config
from . import db

def create_app():
    """build the app here such that it doesn't build on every import"""
    app = Flask(__name__)
    app.config.from_object(Config)
    app.teardown_appcontext(db.close_db)

    from . import auth
    app.register_blueprint(auth.bp)
    from . import teacher
    app.register_blueprint(teacher.bp)
    from app import student
    app.register_blueprint(student.bp)
    from app import api
    app.register_blueprint(api.bp)
    from app import card
    app.register_blueprint(card.bp)


    @app.route("/")
    def home():
        """Landing page with the 3D piano. Logged-in users get an 'Open the app' button."""
        from flask import render_template, session
        from .auth import home_url_for
        app_home = home_url_for(session["role"]) if session.get("role") else None
        return render_template("home.html", app_home=app_home)

    @app.route("/health")
    def health():
        """does it work?"""
        return "ok", 200

    return app