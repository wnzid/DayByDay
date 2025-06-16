# DayByDay

DayByDay is a Flask-based web application that combines a habit tracker and monthly planner. Create an account, manage your daily habits, and organize upcoming tasks in one place. Data is stored in a PostgreSQL database and the application includes a simple migration mechanism so that schema stays up to date.

## Features

- **User Accounts** – Register, log in and manage your own habit list
- **Calendar View** – Visualize your progress with a monthly calendar
- **Habit Management** – Add, edit and delete habits with priority levels and custom colors
- **Monthly Planner** – Organize daily tasks alongside your habit tracking
- **Automatic Migrations** – The database schema is upgraded automatically on launch

Try the hosted version here: [https://habit-tracker-1sq5.onrender.com](https://habit-tracker-1sq5.onrender.com).

## Getting Started

Follow the steps below if you want to run the application locally.

### Installation

1. Clone this repository and navigate into the project directory.
2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and edit `DATABASE_URL` with your PostgreSQL connection string. Set `SECRET_KEY` to any random value.

### Running the Application

Start the development server with:

```bash
python app.py
```

Ensure your PostgreSQL database is reachable via `DATABASE_URL`. If this is a new database run:

```bash
psql "$DATABASE_URL" -f schema.sql
```

This creates the initial tables used by the app.

### Deployment

A simple `Procfile` is included for platforms such as Render or Heroku. It uses Gunicorn to serve the Flask app:

```bash
gunicorn app:app
```

## License

This project is licensed under the MIT License. Feel free to use it as a starting point for your own habit tracking tools. Don't forget to give credits.

---

### @wnizd

