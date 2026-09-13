<div align="center">

# DayByDay

**Habit tracking and monthly planning in one focused workspace.**

`Flask` · `MongoDB` · `Jinja` · `Bootstrap`

</div>

DayByDay combines recurring habits with a day-by-day planner. Each account owns its habits, completion history, and scheduled tasks, with monthly views that keep progress and upcoming work in the same context.

## Features

- Registration, sign-in, account editing, and account deletion
- Habit creation, editing, priority, color, and removal
- Daily completion tracking
- Monthly habit calendar
- Planner tasks with completion toggles and day-level views
- User-scoped MongoDB records
- Server-rendered responsive interface

## Local setup

Python 3.10 or newer and a reachable MongoDB instance are required.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Configure the environment:

```text
MONGO_URI=mongodb://localhost:27017
MONGO_DBNAME=DayByDay
SECRET_KEY=replace-with-a-long-random-value
```

Then start the app:

```bash
python app.py
```

For a WSGI deployment, the included `Procfile` runs `gunicorn app:app`.

## Project map

```text
app.py       Routes, authentication, habits, and planner workflows
db.py        MongoDB connection factory
templates/   Jinja page templates
static/      Styles and assets
utils/       Supporting utilities
```

`schema.sql` is a legacy relational schema reference; the current application uses MongoDB through PyMongo.

## Security note

Set a strong `SECRET_KEY`, keep `MONGO_URI` out of source control, and deploy behind HTTPS before exposing accounts publicly.

## License

Licensed under the [MIT License](LICENSE).
