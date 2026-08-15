import os
import sqlite3
from pathlib import Path
from flask import Flask, g, jsonify, render_template, request

# DB location configurable via environment variable (needed for Docker)
DB_PATH = Path(os.environ.get("DB_PATH", str(Path(__file__).parent / "todos.db")))


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = str(db_path or DB_PATH)

    # ---------- database helpers ----------
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
            """CREATE TABLE IF NOT EXISTS todos (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   title TEXT NOT NULL,
                   done INTEGER DEFAULT 0,
                   priority TEXT DEFAULT 'medium'
               )"""
        )
        # Migration: add 'priority' column to older databases
        cols = [row[1] for row in db.execute("PRAGMA table_info(todos)").fetchall()]
        if "priority" not in cols:
            db.execute("ALTER TABLE todos ADD COLUMN priority TEXT DEFAULT 'medium'")
        db.commit()

    with app.app_context():
        init_db()

    # ---------- web page ----------
    @app.get("/")
    def home():
        return render_template("index.html")

    # ---------- API: list (newest first) ----------
    @app.get("/todos")
    def list_todos():
        rows = get_db().execute("SELECT * FROM todos ORDER BY id DESC").fetchall()
        return jsonify([dict(r) for r in rows])

    # ---------- API: add ----------
    @app.post("/todos")
    def add_todo():
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        priority = data.get("priority", "medium")

        if not title:
            return jsonify({"error": "title is required"}), 400
        if priority not in ["low", "medium", "high"]:
            priority = "medium"

        db = get_db()
        cur = db.execute(
            "INSERT INTO todos (title, priority) VALUES (?, ?)",
            (title, priority),
        )
        db.commit()
        row = db.execute("SELECT * FROM todos WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(dict(row)), 201

    # ---------- API: edit title / priority ----------
    @app.patch("/todos/<int:todo_id>")
    def update_todo(todo_id):
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        priority = data.get("priority")

        db = get_db()
        row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        if row is None:
            return jsonify({"error": "not found"}), 404

        updates, params = [], []
        if title:
            updates.append("title = ?")
            params.append(title)
        if priority in ["low", "medium", "high"]:
            updates.append("priority = ?")
            params.append(priority)

        if updates:
            params.append(todo_id)
            db.execute(f"UPDATE todos SET {', '.join(updates)} WHERE id = ?", params)
            db.commit()

        row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        return jsonify(dict(row))

    # ---------- API: toggle done ----------
    @app.patch("/todos/<int:todo_id>/done")
    def toggle_done(todo_id):
        db = get_db()
        row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        if row is None:
            return jsonify({"error": "not found"}), 404
        db.execute("UPDATE todos SET done = ? WHERE id = ?", (not row["done"], todo_id))
        db.commit()
        row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        return jsonify(dict(row))

    # ---------- API: delete one ----------
    @app.delete("/todos/<int:todo_id>")
    def delete_todo(todo_id):
        db = get_db()
        row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        if row is None:
            return jsonify({"error": "not found"}), 404
        db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        db.commit()
        return jsonify({"deleted": todo_id})

    # ---------- API: clear all completed ----------
    @app.delete("/todos/clear-completed")
    def clear_completed():
        db = get_db()
        cursor = db.execute("DELETE FROM todos WHERE done = 1")
        db.commit()
        return jsonify({"cleared": cursor.rowcount})

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)