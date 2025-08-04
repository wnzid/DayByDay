from flask import Flask, render_template, g, request, redirect, url_for, session, flash
import os
from bson.objectid import ObjectId
from db import get_connection
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import calendar

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


def get_db():
    if 'db' not in g:
        g.db = get_connection()
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    g.pop('db', None)


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
    used = {h["color"] for h in db.habits.find({"user_id": ObjectId(user_id)})}
    for color in COLOR_PALETTE:
        if color not in used:
            return color
    # fallback if all colors are used
    return COLOR_PALETTE[0]


def ensure_planner_table():
    return


def ensure_display_name_column():
    return



@app.route('/')
def index():
    """Show welcome page or redirect logged-in users to the calendar."""
    if 'user_id' in session:
        now = datetime.now()
        return redirect(url_for('calendar_view', year=now.year, month=now.month))
    return render_template('welcome.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')


@app.route('/habit-tracker')
def habit_tracker():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    now = datetime.now()
    return redirect(url_for('calendar_view', year=now.year, month=now.month))


@app.route('/planner')
def planner_root():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    now = datetime.now()
    return redirect(url_for('planner_view', year=now.year, month=now.month))


@app.route('/planner/add', methods=['POST'])
@login_required
def add_planner_task():
    ensure_planner_table()
    db = get_db()
    task = request.form.get('task', '').strip()
    date = request.form.get('date')
    if task and date:
        db.planner_tasks.insert_one({
            'user_id': ObjectId(session['user_id']),
            'task': task,
            'date': date,
            'completed': False,
        })
    year, month, _ = [int(x) for x in date.split('-')]
    return redirect(url_for('planner_view', year=year, month=month))


@app.route('/planner/<int:year>/<int:month>')
@login_required
def planner_view(year, month):
    ensure_planner_table()
    db = get_db()
    rows = db.planner_tasks.find({
        'user_id': ObjectId(session['user_id']),
        'date': {'$regex': f'^{year:04d}-{month:02d}-'}
    })
    tasks_by_day = {}
    for row in rows:
        day = int(row['date'].split('-')[2])
        tasks_by_day.setdefault(day, []).append({
            'id': str(row['_id']),
            'task': row['task'],
            'completed': row.get('completed', False)
        })

    cal = calendar.Calendar()
    weeks = cal.monthdayscalendar(year, month)
    month_name = calendar.month_name[month]

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

    return render_template(
        'planner.html',
        month_name=month_name,
        year=year,
        month=month,
        weeks=weeks,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
        tasks_by_day=tasks_by_day,
    )


@app.route('/planner/<int:year>/<int:month>/<int:day>', methods=['GET', 'POST'])
@login_required
def planner_day(year, month, day):
    ensure_planner_table()
    db = get_db()
    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    if request.method == 'POST':
        task = request.form.get('task', '').strip()
        if task:
            db.planner_tasks.insert_one({
                'user_id': ObjectId(session['user_id']),
                'task': task,
                'date': date_str,
                'completed': False,
            })
        return redirect(url_for('planner_day', year=year, month=month, day=day))

    tasks = [
        {
            'id': str(t['_id']),
            'task': t['task'],
            'completed': t.get('completed', False),
        }
        for t in db.planner_tasks.find({'user_id': ObjectId(session['user_id']), 'date': date_str})
    ]
    return render_template(
        'planner_day.html',
        tasks=tasks,
        date_str=date_str,
        year=year,
        month=month,
        day=day,
    )


@app.route('/planner/delete/<task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    ensure_planner_table()
    db = get_db()
    db.planner_tasks.delete_one({'_id': ObjectId(task_id), 'user_id': ObjectId(session['user_id'])})
    return redirect(request.referrer or url_for('planner_root'))


@app.route('/planner/toggle/<task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    ensure_planner_table()
    db = get_db()
    task = db.planner_tasks.find_one({'_id': ObjectId(task_id), 'user_id': ObjectId(session['user_id'])})
    if task:
        db.planner_tasks.update_one(
            {'_id': task['_id']},
            {'$set': {'completed': not task.get('completed', False)}}
        )
        if request.form.get('redirect') == 'day':
            year, month, day = [int(x) for x in task['date'].split('-')]
            return redirect(url_for('planner_day', year=year, month=month, day=day))
    return redirect(request.referrer or url_for('planner_root'))


@app.route('/calendar/<int:year>/<int:month>')
@login_required
def calendar_view(year, month):
    db = get_db()
    user_id = ObjectId(session['user_id'])
    habits = list(db.habits.find({'user_id': user_id}))
    for h in habits:
        h['id'] = str(h['_id'])
    now = datetime.now()
    is_future = (year > now.year) or (year == now.year and month > now.month)
    cal = calendar.Calendar()
    weeks = cal.monthdayscalendar(year, month)
    month_name = calendar.month_name[month]
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
    habit_map = {h['_id']: h for h in habits}
    habit_ids = list(habit_map.keys())
    prefix = f"{year:04d}-{month:02d}-"
    logs = list(db.habit_log.find({'habit_id': {'$in': habit_ids}, 'date': {'$regex': f'^{prefix}'}}))
    day_colors = {}
    completed = set()
    for row in logs:
        habit = habit_map.get(row['habit_id'])
        if not habit:
            continue
        day = int(row['date'].split('-')[2])
        entry = {'color': habit['color'], 'name': habit['name'], 'priority': habit['priority']}
        day_colors.setdefault(day, []).append(entry)
        completed.add(f"{str(habit['_id'])}_{row['date']}")
    for habits_list in day_colors.values():
        habits_list.sort(key=lambda h: PRIORITY_RANK.get(h['priority'].capitalize(), 4))
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
        ensure_display_name_column()
        if db.users.find_one({'username': username}):
            flash('Username already taken', 'danger')
            return render_template('register.html')
        db.users.insert_one({
            'username': username,
            'password': generate_password_hash(password),
            'display_name': username,
        })
        flash('Account created. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = str(user['_id'])
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


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account_settings():
    ensure_display_name_column()
    db = get_db()
    user = db.users.find_one({'_id': ObjectId(session['user_id'])})
    if request.method == 'POST':
        display_name = request.form.get('display_name', '').strip()
        current = request.form.get('current_password', '')
        new_pw = request.form.get('new_password', '')
        updates = {}
        if display_name and display_name != user.get('display_name'):
            updates['display_name'] = display_name
        if new_pw:
            if check_password_hash(user['password'], current):
                updates['password'] = generate_password_hash(new_pw)
            else:
                flash('Incorrect current password', 'danger')
                return redirect(url_for('account_settings'))
        if updates:
            db.users.update_one({'_id': user['_id']}, {'$set': updates})
        flash('Account updated', 'success')
        return redirect(url_for('account_settings'))
    return render_template('account_settings.html', user=user)


@app.route('/account/delete', methods=['POST'])
@login_required
def delete_account():
    ensure_display_name_column()
    password = request.form.get('password', '')
    db = get_db()
    user = db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or not check_password_hash(user['password'], password):
        flash('Incorrect password. Account not deleted.', 'danger')
        return redirect(url_for('account_settings'))
    user_id = ObjectId(session['user_id'])
    habit_ids = [h['_id'] for h in db.habits.find({'user_id': user_id})]
    if habit_ids:
        db.habit_log.delete_many({'habit_id': {'$in': habit_ids}})
    db.habits.delete_many({'user_id': user_id})
    db.planner_tasks.delete_many({'user_id': user_id})
    db.users.delete_one({'_id': user_id})
    session.clear()
    flash('Account deleted', 'info')
    return redirect(url_for('index'))


# ---------------- Habit management -----------------

@app.route('/habits')
@login_required
def manage_habits():
    db = get_db()
    habits = list(db.habits.find({'user_id': ObjectId(session['user_id'])}))
    for h in habits:
        h['id'] = str(h['_id'])
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
        db.habits.insert_one({
            'user_id': ObjectId(session['user_id']),
            'name': name,
            'priority': priority,
            'color': color,
        })
        flash('Habit added', 'success')
        return redirect(url_for('manage_habits'))
    return render_template('habit_form.html', habit=None)


@app.route('/habits/edit/<habit_id>', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    db = get_db()
    habit = db.habits.find_one({'_id': ObjectId(habit_id), 'user_id': ObjectId(session['user_id'])})
    if habit is None:
        return redirect(url_for('manage_habits'))
    if request.method == 'POST':
        name = request.form['name']
        priority = request.form['priority']
        color = request.form.get('color', '').strip()
        if not color:
            color = get_next_color(db, session['user_id'])
        db.habits.update_one(
            {'_id': habit['_id']},
            {'$set': {'name': name, 'priority': priority, 'color': color}},
        )
        flash('Habit updated', 'success')
        return redirect(url_for('manage_habits'))
    habit['id'] = str(habit['_id'])
    return render_template('habit_form.html', habit=habit)


@app.route('/habits/delete/<habit_id>', methods=['POST'])
@login_required
def delete_habit(habit_id):
    db = get_db()
    user_id = ObjectId(session['user_id'])
    db.habit_log.delete_many({'habit_id': ObjectId(habit_id)})
    db.habits.delete_one({'_id': ObjectId(habit_id), 'user_id': user_id})
    flash('Habit deleted', 'success')
    return redirect(url_for('manage_habits'))


@app.route('/complete', methods=['POST'])
@login_required
def complete():
    habit_id = request.form['habit_id']
    date_str = request.form['date']
    db = get_db()
    existing = db.habit_log.find_one({'habit_id': ObjectId(habit_id), 'date': date_str})
    if existing:
        db.habit_log.delete_one({'_id': existing['_id']})
    else:
        db.habit_log.insert_one({'habit_id': ObjectId(habit_id), 'date': date_str})
    year, month, _ = [int(x) for x in date_str.split('-')]
    return redirect(url_for('calendar_view', year=year, month=month))


@app.route('/track/<int:year>/<int:month>/<int:day>', methods=['GET', 'POST'])
@login_required
def track_day(year, month, day):
    db = get_db()
    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    now = datetime.now()
    is_future = (year, month, day) > (now.year, now.month, now.day)
    user_id = ObjectId(session['user_id'])
    if request.method == 'POST':
        if is_future:
            flash('Cannot track habits for a future date.', 'danger')
            return redirect(url_for('track_day', year=year, month=month, day=day))
        selected = request.form.getlist('habit_ids')
        habit_ids = [h['_id'] for h in db.habits.find({'user_id': user_id})]
        if habit_ids:
            db.habit_log.delete_many({'habit_id': {'$in': habit_ids}, 'date': date_str})
        for hid in selected:
            db.habit_log.insert_one({'habit_id': ObjectId(hid), 'date': date_str})
        return redirect(url_for('calendar_view', year=year, month=month))

    habits = list(db.habits.find({'user_id': user_id}))
    for h in habits:
        h['id'] = str(h['_id'])
    logs = db.habit_log.find({'habit_id': {'$in': [h['_id'] for h in habits]}, 'date': date_str})
    completed = {str(row['habit_id']) for row in logs}
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


