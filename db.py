import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

def get_connection():
    """Return a new connection to the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create required tables if they don't already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            priority TEXT NOT NULL,
            color TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS habit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY(habit_id) REFERENCES habits(id)
        )
        """
    )

    conn.commit()
    conn.close()


def migrate_db():
    """Upgrade existing tables to the latest schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check existing columns in the habits table
    cursor.execute('PRAGMA table_info(habits)')
    columns = [row['name'] for row in cursor.fetchall()]

    if 'priority' not in columns:
        cursor.execute("ALTER TABLE habits ADD COLUMN priority TEXT NOT NULL DEFAULT 'low'")

    if 'color' not in columns:
        cursor.execute("ALTER TABLE habits ADD COLUMN color TEXT NOT NULL DEFAULT '#ffffff'")

    conn.commit()
    conn.close()

