"""
config.py

Loads environment variables from .env into a Config class read by the Flask
app factory.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    DB_HOST = os.environ["DB_HOST"]
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_USER = os.environ["DB_USER"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
    DB_NAME = os.environ.get("DB_NAME", "club_organizations")
