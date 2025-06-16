import psycopg2

def get_connection():
    """Return a new connection to the PostgreSQL database."""
    from app import DATABASE_URL
    conn = psycopg2.connect(DATABASE_URL)
    return conn



