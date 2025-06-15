from flask import Flask, render_template, g, request, redirect, url_for, session
import sqlite3
import os
from db import init_db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

DATABASE = os.path.join(os.path.dirname(__file__), 'app.db')

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")

with app.app_context():
    init_db()


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




@app.route('/')
@login_required
def index():
    db = get_db()
    habits = db.execute(
        'SELECT name, color FROM habits WHERE user_id = ?',
        (session['user_id'],)
    ).fetchall()
    return render_template('index.html', habits=habits)


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
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Username already taken')
        return redirect(url_for('login'))
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
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
