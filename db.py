import os
import psycopg2
from urllib.parse import urlparse

def get_connection():
    """Return a new connection to the PostgreSQL database."""
    db_url = os.environ["DATABASE_URL"]
    result = urlparse(db_url)
    return psycopg2.connect(
        dbname=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port,
    )



