# Gunicorn WSGI entry point for render, this links the web server to the flask app

from app import create_app

app = create_app()