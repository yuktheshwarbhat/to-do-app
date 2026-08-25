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
    """Anonymous client (not logged in)."""
    return app.test_client()


@pytest.fixture
def auth_client(app):
    """Client registered and logged in as 'tester'."""
    c = app.test_client()
    register(c, "tester", "secret123")
    login(c, "tester", "secret123")
    return c


@pytest.fixture
def add_todo(auth_client):
    """Fixture factory: create todos with less repetition."""
    def _add(title, priority="medium"):
        resp = auth_client.post("/todos", json={"title": title, "priority": priority})
        assert resp.status_code == 201
        return resp.get_json()
    return _add


# ---------- helpers ----------

def register(c, username, password):
    return c.post("/register", data={"username": username, "password": password})


def login(c, username, password):
    return c.post("/login", data={"username": username, "password": password})


def logged_in_client(app, username, password="secret123"):
    c = app.test_client()
    register(c, username, password)
    login(c, username, password)
    return c


# ---------- auth: pages ----------

def test_login_page_loads(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Login" in resp.data


def test_register_page_loads(client):
    assert b"Register" in client.get("/register").data


# ---------- auth: register ----------

def test_register_creates_user(client):
    register(client, "alice", "secret123")
    resp = login(client, "alice", "secret123")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"


def test_register_rejects_duplicate_username(client):
    register(client, "alice", "secret123")
    resp = register(client, "alice", "anotherpass")
    assert "/register" in resp.headers["Location"]


def test_register_rejects_short_password(client):
    register(client, "alice", "123")
    resp = login(client, "alice", "123")
    assert "/login" in resp.headers["Location"]   # login fails: user was never created


# ---------- auth: login / logout ----------

def test_login_with_wrong_password(client):
    register(client, "alice", "secret123")
    resp = login(client, "alice", "wrongpass")
    assert "/login" in resp.headers["Location"]


def test_login_with_unknown_user(client):
    resp = login(client, "ghost", "secret123")
    assert "/login" in resp.headers["Location"]


def test_logout_clears_session(auth_client):
    auth_client.post("/logout")
    assert auth_client.get("/todos").status_code == 302


# ---------- auth: protection ----------

def test_home_redirects_when_not_logged_in(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_todos_api_requires_login(client):
    assert client.get("/todos").status_code == 302
    assert client.post("/todos", json={"title": "x"}).status_code == 302


# ---------- auth: user isolation ----------

def test_users_see_only_their_own_todos(app):
    alice = logged_in_client(app, "alice")
    alice.post("/todos", json={"title": "alice task"})

    bob = logged_in_client(app, "bob")
    bob.post("/todos", json={"title": "bob task"})

    assert [t["title"] for t in alice.get("/todos").get_json()] == ["alice task"]
    assert [t["title"] for t in bob.get("/todos").get_json()] == ["bob task"]


def test_user_cannot_delete_another_users_todo(app):
    alice = logged_in_client(app, "alice")
    todo = alice.post("/todos", json={"title": "private"}).get_json()

    bob = logged_in_client(app, "bob")
    assert bob.delete(f"/todos/{todo['id']}").status_code == 404
    assert len(alice.get("/todos").get_json()) == 1


def test_user_cannot_toggle_another_users_todo(app):
    alice = logged_in_client(app, "alice")
    todo = alice.post("/todos", json={"title": "private"}).get_json()

    bob = logged_in_client(app, "bob")
    assert bob.patch(f"/todos/{todo['id']}/done").status_code == 404
    assert alice.get("/todos").get_json()[0]["done"] == 0


# ---------- home page (logged in) ----------

def test_home_page_serves_html(auth_client):
    resp = auth_client.get("/")
    assert resp.status_code == 200
    assert b"Pi ToDo Pro" in resp.data


def test_home_page_shows_username(auth_client):
    assert b"Hi, tester" in auth_client.get("/").data


def test_home_page_has_form_and_script(auth_client):
    html = auth_client.get("/").data.decode()
    assert "<form" in html
    assert "fetch('/todos')" in html


def test_priority_css_classes_exist(auth_client):
    html = auth_client.get("/").data.decode()
    for p in ["high", "medium", "low"]:
        assert f"badge-{p}" in html


# ---------- listing ----------

def test_api_returns_json_content_type(auth_client):
    assert auth_client.get("/todos").content_type.startswith("application/json")


def test_list_starts_empty(auth_client):
    assert auth_client.get("/todos").get_json() == []


def test_added_todo_appears_in_list(auth_client, add_todo):
    add_todo("buy milk")
    titles = [t["title"] for t in auth_client.get("/todos").get_json()]
    assert "buy milk" in titles


def test_todos_returned_newest_first(auth_client, add_todo):
    for title in ["first", "second", "third"]:
        add_todo(title)
    titles = [t["title"] for t in auth_client.get("/todos").get_json()]
    assert titles == ["third", "second", "first"]


def test_each_todo_gets_unique_id(add_todo):
    ids = [add_todo(f"todo {i}")["id"] for i in range(5)]
    assert len(set(ids)) == 5


# ---------- adding ----------

def test_add_todo(auth_client):
    resp = auth_client.post("/todos", json={"title": "learn pytest"})
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
def test_add_todo_rejects_bad_input(auth_client, payload):
    resp = auth_client.post("/todos", json=payload)
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "title is required"


def test_add_todo_without_json_body(auth_client):
    assert auth_client.post("/todos").status_code == 400


def test_add_todo_with_unicode(add_todo):
    todo = add_todo("cafe naive resume - weekend tasks")
    assert todo["title"] == "cafe naive resume - weekend tasks"


def test_add_long_title(add_todo):
    title = "x" * 500
    assert add_todo(title)["title"] == title


# ---------- priorities ----------

def test_add_todo_with_priority(add_todo):
    todo = add_todo("urgent task", priority="high")
    assert todo["priority"] == "high"


def test_invalid_priority_defaults_to_medium(auth_client):
    resp = auth_client.post("/todos", json={"title": "test", "priority": "ultra-mega"})
    assert resp.get_json()["priority"] == "medium"


# ---------- toggling ----------

def test_toggle_done(add_todo, auth_client):
    todo = add_todo("task")
    resp = auth_client.patch(f"/todos/{todo['id']}/done")
    assert resp.get_json()["done"] == 1


def test_toggle_twice_returns_to_original(add_todo, auth_client):
    todo = add_todo("flip flop")
    auth_client.patch(f"/todos/{todo['id']}/done")
    resp = auth_client.patch(f"/todos/{todo['id']}/done")
    assert resp.get_json()["done"] == 0


def test_done_state_persists_in_list(add_todo, auth_client):
    todo = add_todo("persistent")
    auth_client.patch(f"/todos/{todo['id']}/done")
    todos = auth_client.get("/todos").get_json()
    match = next(t for t in todos if t["id"] == todo["id"])
    assert match["done"] == 1


def test_toggle_missing_todo_returns_404(auth_client):
    assert auth_client.patch("/todos/999/done").status_code == 404


# ---------- editing ----------

def test_update_todo_title(add_todo, auth_client):
    todo = add_todo("old title")
    resp = auth_client.patch(f"/todos/{todo['id']}", json={"title": "new title"})
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "new title"


def test_update_missing_todo_returns_404(auth_client):
    assert auth_client.patch("/todos/999", json={"title": "x"}).status_code == 404


# ---------- deleting ----------

def test_delete_todo(add_todo, auth_client):
    todo = add_todo("temp")
    resp = auth_client.delete(f"/todos/{todo['id']}")
    assert resp.status_code == 200
    remaining = [t["id"] for t in auth_client.get("/todos").get_json()]
    assert todo["id"] not in remaining


def test_delete_only_removes_target(add_todo, auth_client):
    keep = add_todo("keep me")
    remove = add_todo("delete me")
    auth_client.delete(f"/todos/{remove['id']}")
    remaining = auth_client.get("/todos").get_json()
    assert len(remaining) == 1
    assert remaining[0]["id"] == keep["id"]


def test_delete_missing_todo_returns_404(auth_client):
    assert auth_client.delete("/todos/999").status_code == 404


# ---------- clear completed ----------

def test_clear_completed(add_todo, auth_client):
    t1 = add_todo("done 1")
    t2 = add_todo("active")
    auth_client.patch(f"/todos/{t1['id']}/done")

    resp = auth_client.delete("/todos/clear-completed")
    assert resp.status_code == 200
    assert resp.get_json()["cleared"] == 1

    remaining = auth_client.get("/todos").get_json()
    assert len(remaining) == 1
    assert remaining[0]["id"] == t2["id"]