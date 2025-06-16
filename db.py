import psycopg2
import os


def get_connection():
    """Return a new connection to the PostgreSQL database."""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn



