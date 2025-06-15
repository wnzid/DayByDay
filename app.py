from flask import Flask, render_template, g
import sqlite3
import os
from db import init_db

DATABASE = os.path.join(os.path.dirname(__file__), 'app.db')

app = Flask(__name__)

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




@app.route('/')
def index():
    db = get_db()
    habits = db.execute('SELECT name, color FROM habits').fetchall()
    return render_template('index.html', habits=habits)


if __name__ == '__main__':
    app.run(debug=True)
