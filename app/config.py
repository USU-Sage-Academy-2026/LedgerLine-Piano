#All the constants
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Config variables"""
    SECRET_KEY = os.environ["SECRET_KEY"]
    DATABASE_URL = os.environ["DATABASE_URL"]
    INSIGHTS_MIN_GROUP = 10