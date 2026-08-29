import os
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, flash, g, jsonify, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = Path(os.environ.get("DB_PATH", str(Path(__file__).parent / "todos.db")))


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = str(db_path or DB_PATH)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        db = get_db()
        db.execute(
            """CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT UNIQUE NOT NULL,
                   password_hash TEXT NOT NULL
               )"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS todos (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   title TEXT NOT NULL,
                   done INTEGER DEFAULT 0,
                   priority TEXT DEFAULT 'medium',
                   user_id INTEGER
               )"""
        )
        todo_cols = [row[1] for row in db.execute("PRAGMA table_info(todos)").fetchall()]
        if "priority" not in todo_cols:
            db.execute("ALTER TABLE todos ADD COLUMN priority TEXT DEFAULT 'medium'")
        if "user_id" not in todo_cols:
            db.execute("ALTER TABLE todos ADD COLUMN user_id INTEGER")
        db.commit()

    with app.app_context():
        init_db()

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect("/login")
            return view(*args, **kwargs)
        return wrapped

    def current_user_id():
        return session["user_id"]

    # ---------- HTML AUTH ROUTES (Original App) ----------
    @app.get("/register")
    def register_page(): return render_template("register.html")

    @app.post("/register")
    def register():
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if len(username) < 3: flash("Username too short"); return redirect("/register")
        if len(password) < 6: flash("Password too short"); return redirect("/register")
        db = get_db()
        if db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
            flash("Taken"); return redirect("/register")
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, generate_password_hash(password)))
        db.commit()
        return redirect("/login")

    @app.get("/login")
    def login_page(): return render_template("login.html")

    @app.post("/login")
    def login():
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Bad login"); return redirect("/login")
        session["user_id"] = user["id"]
        return redirect("/")

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect("/login")

    # ---------- JSON AUTH ROUTES FOR REACT ----------
    @app.post("/api/register")
    def api_register():
        data = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        password = data.get("password", "")
        if len(username) < 3: return jsonify({"error": "Username must be at least 3 characters"}), 400
        if len(password) < 6: return jsonify({"error": "Password must be at least 6 characters"}), 400
        db = get_db()
        if db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
            return jsonify({"error": "Username already taken"}), 400
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, generate_password_hash(password)))
        db.commit()
        return jsonify({"message": "Account created"}), 201

    @app.post("/api/login")
    def api_login():
        data = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        password = data.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid username or password"}), 401
        session["user_id"] = user["id"]
        return jsonify({"username": user["username"]})

    @app.post("/api/logout")
    def api_logout():
        session.clear()
        return jsonify({"message": "Logged out"})

    @app.get("/api/me")
    def api_me():
        if "user_id" not in session: return jsonify({"username": None})
        user = get_db().execute("SELECT username FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        return jsonify({"username": user["username"]})

    @app.get("/api/health")
    def health(): return jsonify({"status": "ok"})

    # ---------- TODO API ----------
    @app.get("/")
    @login_required
    def home():
        user = get_db().execute("SELECT username FROM users WHERE id = ?", (current_user_id(),)).fetchone()
        return render_template("index.html", username=user["username"])

    @app.get("/todos")
    @login_required
    def list_todos():
        rows = get_db().execute("SELECT * FROM todos WHERE user_id = ? ORDER BY id DESC", (current_user_id(),)).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.post("/todos")
    @login_required
    def add_todo():
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        priority = data.get("priority", "medium")
        if not title: return jsonify({"error": "title is required"}), 400
        db = get_db()
        cur = db.execute("INSERT INTO todos (title, priority, user_id) VALUES (?, ?, ?)", (title, priority, current_user_id()))
        db.commit()
        return jsonify(dict(db.execute("SELECT * FROM todos WHERE id = ?", (cur.lastrowid,)).fetchone())), 201

    @app.patch("/todos/<int:todo_id>")
    @login_required
    def update_todo(todo_id):
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        priority = data.get("priority")
        row = get_db().execute("SELECT * FROM todos WHERE id = ? AND user_id = ?", (todo_id, current_user_id())).fetchone()
        if not row: return jsonify({"error": "not found"}), 404
        updates, params = [], []
        if title: updates.append("title = ?"); params.append(title)
        if priority in ["low", "medium", "high"]: updates.append("priority = ?"); params.append(priority)
        if updates:
            params.extend([todo_id, current_user_id()])
            get_db().execute(f"UPDATE todos SET {', '.join(updates)} WHERE id = ? AND user_id = ?", params)
            get_db().commit()
        return jsonify(dict(get_db().execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()))

    @app.patch("/todos/<int:todo_id>/done")
    @login_required
    def toggle_done(todo_id):
        row = get_db().execute("SELECT * FROM todos WHERE id = ? AND user_id = ?", (todo_id, current_user_id())).fetchone()
        if not row: return jsonify({"error": "not found"}), 404
        get_db().execute("UPDATE todos SET done = ? WHERE id = ?", (not row["done"], todo_id))
        get_db().commit()
        return jsonify(dict(get_db().execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()))

    @app.delete("/todos/<int:todo_id>")
    @login_required
    def delete_todo(todo_id):
        row = get_db().execute("SELECT * FROM todos WHERE id = ? AND user_id = ?", (todo_id, current_user_id())).fetchone()
        if not row: return jsonify({"error": "not found"}), 404
        get_db().execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        get_db().commit()
        return jsonify({"deleted": todo_id})

    @app.delete("/todos/clear-completed")
    @login_required
    def clear_completed():
        c = get_db().execute("DELETE FROM todos WHERE done = 1 AND user_id = ?", (current_user_id(),))
        get_db().commit()
        return jsonify({"cleared": c.rowcount})

    return app

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)