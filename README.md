# Habit Tracker

This is a simple Flask application for tracking habits. It uses SQLite for data storage.

## Setup

Create a virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

Run the application locally:

```bash
python app.py
```

The application will automatically upgrade the database schema if an older
version is detected. If you previously ran the app before the `color` column was
added, simply restart the app and it will migrate the existing database to the
latest schema.
