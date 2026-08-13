import sqlite3
from pathlib import Path
from flask import Flask, g, jsonify, request

DB_PATH = Path(__file__).parent / "todos.db"


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = str(db_path or DB_PATH)

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
        get_db().execute(
            """CREATE TABLE IF NOT EXISTS todos (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   title TEXT NOT NULL,
                   done INTEGER DEFAULT 0
               )"""
        )
        g.db.commit()

    with app.app_context():
        init_db()

    @app.get("/todos")
    def list_todos():
        rows = get_db().execute("SELECT * FROM todos ORDER BY id").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.post("/todos")
    def add_todo():
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"error": "title is required"}), 400
        db = get_db()
        cur = db.execute("INSERT INTO todos (title) VALUES (?)", (title,))
        db.commit()
        row = db.execute("SELECT * FROM todos WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(dict(row)), 201

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

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)