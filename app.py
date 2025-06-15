from flask import Flask, render_template, g, request, redirect, url_for, session, flash
import sqlite3
import os
from db import init_db, migrate_db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import calendar

DATABASE = os.path.join(os.path.dirname(__file__), 'app.db')

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")

with app.app_context():
    init_db()
    migrate_db()


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def login_required(view):
    """Decorator that redirects to the login page if the user is not authenticated."""
    @wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view(**kwargs)

    return wrapped_view

# Preset list of colors used when no color is provided
COLOR_PALETTE = [
    "#e6194b", "#3cb44b", "#ffe119", "#0082c8", "#f58231", "#911eb4",
    "#46f0f0", "#f032e6", "#d2f53c", "#fabebe", "#008080", "#e6beff",
    "#aa6e28", "#fffac8", "#800000", "#aaffc3", "#808000", "#ffd8b1",
    "#000080", "#808080",
]


def get_next_color(db, user_id):
    """Return the first color from the palette that isn't used by the user."""
    rows = db.execute(
        "SELECT color FROM habits WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    used = {row["color"] for row in rows}
    for color in COLOR_PALETTE:
        if color not in used:
            return color
    # fallback if all colors are used
    return COLOR_PALETTE[0]




@app.route('/')
@login_required
def index():
    db = get_db()
    habits = db.execute(
        'SELECT name, color FROM habits WHERE user_id = ?',
        (session['user_id'],)
    ).fetchall()
    now = datetime.now()
    year = now.year
    month = now.month
    cal = calendar.Calendar()
    weeks = cal.monthdayscalendar(year, month)
    month_name = calendar.month_name[month]
    return render_template(
        'index.html',
        habits=habits,
        month_name=month_name,
        year=year,
        weeks=weeks,
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        try:
            db.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, generate_password_hash(password)),
            )
            db.commit()
            flash('Account created. Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already taken', 'danger')
            return render_template('register.html')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute(
            'SELECT id, password FROM users WHERE username = ?', (username,)
        ).fetchone()
        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        flash('Invalid username or password', 'danger')
        return render_template('login.html')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You were logged out', 'info')
    return redirect(url_for('login'))


# ---------------- Habit management -----------------

@app.route('/habits')
@login_required
def manage_habits():
    db = get_db()
    habits = db.execute(
        'SELECT id, name, priority, color FROM habits WHERE user_id = ?',
        (session['user_id'],),
    ).fetchall()
    return render_template('habits.html', habits=habits)


@app.route('/habits/add', methods=['GET', 'POST'])
@login_required
def add_habit():
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        priority = request.form['priority']
        color = request.form.get('color', '').strip()
        if not color:
            color = get_next_color(db, session['user_id'])
        db.execute(
            'INSERT INTO habits (user_id, name, priority, color) VALUES (?, ?, ?, ?)',
            (session['user_id'], name, priority, color),
        )
        db.commit()
        flash('Habit added', 'success')
        return redirect(url_for('manage_habits'))
    return render_template('habit_form.html', habit=None)


@app.route('/habits/edit/<int:habit_id>', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    db = get_db()
    habit = db.execute(
        'SELECT * FROM habits WHERE id = ? AND user_id = ?',
        (habit_id, session['user_id']),
    ).fetchone()
    if habit is None:
        return redirect(url_for('manage_habits'))
    if request.method == 'POST':
        name = request.form['name']
        priority = request.form['priority']
        color = request.form.get('color', '').strip()
        if not color:
            color = get_next_color(db, session['user_id'])
        db.execute(
            'UPDATE habits SET name = ?, priority = ?, color = ? WHERE id = ? AND user_id = ?',
            (name, priority, color, habit_id, session['user_id']),
        )
        db.commit()
        flash('Habit updated', 'success')
        return redirect(url_for('manage_habits'))
    return render_template('habit_form.html', habit=habit)


@app.route('/habits/delete/<int:habit_id>', methods=['POST'])
@login_required
def delete_habit(habit_id):
    db = get_db()
    db.execute(
        'DELETE FROM habits WHERE id = ? AND user_id = ?',
        (habit_id, session['user_id']),
    )
    db.commit()
    flash('Habit deleted', 'success')
    return redirect(url_for('manage_habits'))


if __name__ == '__main__':
    app.run(debug=True)
