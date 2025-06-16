DROP TABLE IF EXISTS habit_log;
DROP TABLE IF EXISTS planner_tasks;
DROP TABLE IF EXISTS habits;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    display_name TEXT
);

CREATE TABLE habits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    priority TEXT NOT NULL,
    color TEXT NOT NULL
);

CREATE TABLE habit_log (
    id SERIAL PRIMARY KEY,
    habit_id INTEGER NOT NULL REFERENCES habits(id),
    date DATE NOT NULL
);

CREATE TABLE planner_tasks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    task TEXT NOT NULL,
    date DATE NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE
);
