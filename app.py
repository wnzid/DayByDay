from flask import Flask, render_template, g, request, redirect, url_for, session, flash
import os
import psycopg2
import psycopg2.extras
from db import get_connection
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import calendar

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")


def get_db():
    if 'db' not in g:
        g.db = get_connection()
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

# Mapping priorities to sortable ranks
PRIORITY_RANK = {"High": 1, "Medium": 2, "Low": 3}


def get_next_color(db, user_id):
    """Return the first color from the palette that isn't used by the user."""
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        "SELECT color FROM habits WHERE user_id = %s",
        (user_id,),
    )
    rows = cur.fetchall()
    used = {row["color"] for row in rows}
    for color in COLOR_PALETTE:
        if color not in used:
            return color
    # fallback if all colors are used
    return COLOR_PALETTE[0]



@app.route('/')
@login_required
def index():
    now = datetime.now()
    return redirect(url_for('calendar_view', year=now.year, month=now.month))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')


@app.route('/habit-tracker')
def habit_tracker():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('index'))


@app.route('/planner')
def planner():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('planner.html')


@app.route('/calendar/<int:year>/<int:month>')
@login_required
def calendar_view(year, month):
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        'SELECT id, name, color FROM habits WHERE user_id = %s',
        (session['user_id'],)
    )
    habits = cur.fetchall()
    now = datetime.now()
    is_future = (year > now.year) or (year == now.year and month > now.month)
    cal = calendar.Calendar()
    weeks = cal.monthdayscalendar(year, month)
    month_name = calendar.month_name[month]
    # navigation months
    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1
    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1
    # completed logs for month with associated habit info
    cur.execute(
        """
        SELECT habit_log.habit_id, habits.color, habits.name, habits.priority, habit_log.date
        FROM habit_log
        JOIN habits ON habit_log.habit_id = habits.id
        WHERE habits.user_id = %s
          AND EXTRACT(YEAR FROM habit_log.date) = %s
          AND EXTRACT(MONTH FROM habit_log.date) = %s
        """,
        (session['user_id'], year, month)
    )
    logs = cur.fetchall()

    # Map day number to list of habit dicts and sort by priority
    day_colors = {}
    for row in logs:
        day = row['date'].day
        entry = {
            'color': row['color'],
            'name': row['name'],
            'priority': row['priority']
        }
        day_colors.setdefault(day, []).append(entry)

    for habits_list in day_colors.values():
        habits_list.sort(key=lambda h: PRIORITY_RANK.get(h['priority'].capitalize(), 4))

    completed = {f"{row['habit_id']}_{row['date']}" for row in logs}
    return render_template(
        'index.html',
        habits=habits,
        month_name=month_name,
        year=year,
        month=month,
        weeks=weeks,
        is_future=is_future,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
        completed=completed,
        day_colors=day_colors,
    )




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        try:
            cur = db.cursor()
            cur.execute(
                'INSERT INTO users (username, password) VALUES (%s, %s)',
                (username, generate_password_hash(password)),
            )
            db.commit()
            flash('Account created. Please log in.', 'success')
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            flash('Username already taken', 'danger')
            return render_template('register.html')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            'SELECT id, password FROM users WHERE username = %s', (username,)
        )
        user = cur.fetchone()
        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
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
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        'SELECT id, name, priority, color FROM habits WHERE user_id = %s',
        (session['user_id'],),
    )
    habits = cur.fetchall()
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
        cur = db.cursor()
        cur.execute(
            'INSERT INTO habits (user_id, name, priority, color) VALUES (%s, %s, %s, %s)',
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
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        'SELECT * FROM habits WHERE id = %s AND user_id = %s',
        (habit_id, session['user_id']),
    )
    habit = cur.fetchone()
    if habit is None:
        return redirect(url_for('manage_habits'))
    if request.method == 'POST':
        name = request.form['name']
        priority = request.form['priority']
        color = request.form.get('color', '').strip()
        if not color:
            color = get_next_color(db, session['user_id'])
        cur.execute(
            'UPDATE habits SET name = %s, priority = %s, color = %s WHERE id = %s AND user_id = %s',
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
    cur = db.cursor()
    # Delete logs first
    cur.execute(
        'DELETE FROM habit_log WHERE habit_id = %s AND user_id = %s',
        (habit_id, session['user_id'])
    )

    # Then delete habit
    cur.execute(
        'DELETE FROM habits WHERE id = %s AND user_id = %s',
        (habit_id, session['user_id'])
    )

    db.commit()
    flash('Habit deleted', 'success')
    return redirect(url_for('manage_habits'))


@app.route('/complete', methods=['POST'])
@login_required
def complete():
    habit_id = int(request.form['habit_id'])
    date_str = request.form['date']
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        'SELECT id FROM habit_log WHERE habit_id = %s AND date = %s',
        (habit_id, date_str)
    )
    existing = cur.fetchone()
    if existing:
        cur.execute('DELETE FROM habit_log WHERE id = %s', (existing['id'],))
    else:
        cur.execute('INSERT INTO habit_log (habit_id, date) VALUES (%s, %s)', (habit_id, date_str))
    db.commit()
    year, month, _ = [int(x) for x in date_str.split('-')]
    return redirect(url_for('calendar_view', year=year, month=month))


@app.route('/track/<int:year>/<int:month>/<int:day>', methods=['GET', 'POST'])
@login_required
def track_day(year, month, day):
    db = get_db()
    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    now = datetime.now()
    is_future = (year, month, day) > (now.year, now.month, now.day)
    if request.method == 'POST':
        if is_future:
            flash('Cannot track habits for a future date.', 'danger')
            return redirect(url_for('track_day', year=year, month=month, day=day))
        selected = request.form.getlist('habit_ids')
        # Remove old records for this user and date
        cur = db.cursor()
        cur.execute(
            """
            DELETE FROM habit_log
            WHERE id IN (
                SELECT habit_log.id FROM habit_log
                JOIN habits ON habit_log.habit_id = habits.id
                WHERE habits.user_id = %s AND habit_log.date = %s
            )
            """,
            (session['user_id'], date_str),
        )
        # Insert new records
        for hid in selected:
            cur.execute(
                'INSERT INTO habit_log (habit_id, date) VALUES (%s, %s)',
                (int(hid), date_str),
            )
        db.commit()
        return redirect(url_for('calendar_view', year=year, month=month))

    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        'SELECT id, name, color FROM habits WHERE user_id = %s',
        (session['user_id'],),
    )
    habits = cur.fetchall()
    cur.execute(
        """
        SELECT habit_log.habit_id
        FROM habit_log
        JOIN habits ON habit_log.habit_id = habits.id
        WHERE habits.user_id = %s AND habit_log.date = %s
        """,
        (session['user_id'], date_str),
    )
    logs = cur.fetchall()
    completed = {row['habit_id'] for row in logs}
    return render_template(
        'track_day.html',
        habits=habits,
        completed=completed,
        date_str=date_str,
        year=year,
        month=month,
        day=day,
        is_future=is_future,
    )

if __name__ == '__main__':
    # Run the app on all network interfaces with a fixed port for Render
    app.run(host='0.0.0.0', port=10000)
