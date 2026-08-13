import pytest
from app import create_app


# ---------- fixtures ----------

@pytest.fixture
def app(tmp_path):
    app = create_app(db_path=tmp_path / "test.db")
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def add_todo(client):
    """Fixture factory: a little helper to create todos with less repetition."""
    def _add(title):
        resp = client.post("/todos", json={"title": title})
        assert resp.status_code == 201
        return resp.get_json()
    return _add


# ---------- home page ----------

def test_home_page_serves_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Pi ToDo" in resp.data


def test_home_page_has_form_and_script(client):
    html = client.get("/").data.decode()
    assert "<form" in html
    assert "fetch('/todos')" in html


def test_api_returns_json_content_type(client):
    resp = client.get("/todos")
    assert resp.content_type.startswith("application/json")


# ---------- listing ----------

def test_list_starts_empty(client):
    assert client.get("/todos").get_json() == []


def test_added_todo_appears_in_list(client, add_todo):
    add_todo("buy milk")
    titles = [t["title"] for t in client.get("/todos").get_json()]
    assert "buy milk" in titles


def test_todos_returned_in_insertion_order(client, add_todo):
    for title in ["first", "second", "third"]:
        add_todo(title)
    titles = [t["title"] for t in client.get("/todos").get_json()]
    assert titles == ["first", "second", "third"]


def test_each_todo_gets_unique_id(client, add_todo):
    ids = [add_todo(f"todo {i}")["id"] for i in range(5)]
    assert len(set(ids)) == 5


# ---------- adding ----------

def test_add_todo(client):
    resp = client.post("/todos", json={"title": "learn pytest"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["title"] == "learn pytest"
    assert data["done"] == 0


@pytest.mark.parametrize("payload", [
    {"title": ""},
    {"title": "   "},
    {"title": None},
    {},
], ids=["empty", "spaces", "null", "missing"])
def test_add_todo_rejects_bad_input(client, payload):
    resp = client.post("/todos", json=payload)
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "title is required"


def test_add_todo_without_json_body(client):
    resp = client.post("/todos")
    assert resp.status_code == 400


def test_add_todo_with_emoji(client, add_todo):
    todo = add_todo("🍓 water the plants 🌱")
    assert todo["title"] == "🍓 water the plants 🌱"


def test_add_long_title(client, add_todo):
    title = "x" * 500
    assert add_todo(title)["title"] == title


# ---------- toggling ----------

def test_toggle_done(client, add_todo):
    todo = add_todo("task")
    resp = client.patch(f"/todos/{todo['id']}/done")
    assert resp.get_json()["done"] == 1


def test_toggle_twice_returns_to_original(client, add_todo):
    todo = add_todo("flip flop")
    client.patch(f"/todos/{todo['id']}/done")
    resp = client.patch(f"/todos/{todo['id']}/done")
    assert resp.get_json()["done"] == 0


def test_done_state_persists_in_list(client, add_todo):
    todo = add_todo("persistent")
    client.patch(f"/todos/{todo['id']}/done")
    todos = client.get("/todos").get_json()
    match = next(t for t in todos if t["id"] == todo["id"])
    assert match["done"] == 1


def test_toggle_missing_todo_returns_404(client):
    assert client.patch("/todos/999/done").status_code == 404


# ---------- deleting ----------

def test_delete_todo(client, add_todo):
    todo = add_todo("temp")
    resp = client.delete(f"/todos/{todo['id']}")
    assert resp.status_code == 200
    remaining = [t["id"] for t in client.get("/todos").get_json()]
    assert todo["id"] not in remaining


def test_delete_only_removes_target(client, add_todo):
    keep = add_todo("keep me")
    remove = add_todo("delete me")
    client.delete(f"/todos/{remove['id']}")
    remaining = client.get("/todos").get_json()
    assert len(remaining) == 1
    assert remaining[0]["id"] == keep["id"]


def test_delete_missing_todo_returns_404(client):
    assert client.delete("/todos/999").status_code == 404