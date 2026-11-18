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

    @app.route("/health")
    def health():
        """does it work?"""
        return "ok", 200

    return app