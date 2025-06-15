# Habit Tracker

Habit Tracker is a Flask-based web application that helps you build and maintain good habits. Create an account, set up custom habits, and log your progress on an easy-to-use calendar interface. Data is stored in a lightweight SQLite database and the application includes a simple migration mechanism so your schema stays up to date.

## Features

- **User Accounts** – Register, log in and manage your own habit list
- **Calendar View** – Visualize your progress with a monthly calendar
- **Habit Management** – Add, edit and delete habits with priority levels and custom colors
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

3. (Optional) Set a `SECRET_KEY` environment variable before running the app.

### Running the Application

Start the development server with:

```bash
python app.py
```

The application will create `app.db` in the project directory. Existing databases are migrated to the latest schema on startup.

### Deployment

A simple `Procfile` is included for platforms such as Render or Heroku. It uses Gunicorn to serve the Flask app:

```bash
gunicorn app:app
```

## License

This project is licensed under the MIT License. Feel free to use it as a starting point for your own habit tracking tools. Don't forget to give credits.

---

### @wnizd

