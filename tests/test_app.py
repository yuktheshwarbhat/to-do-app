import pytest
from app import create_app

@pytest.fixture
def app(tmp_path):
    app = create_app(db_path=tmp_path / "test.db")
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app): return app.test_client()

@pytest.fixture
def auth_client(app):
    c = app.test_client()
    register(c, "tester", "secret123")
    login(c, "tester", "secret123")
    return c

@pytest.fixture
def add_todo(auth_client):
    def _add(title, priority="medium"):
        resp = auth_client.post("/todos", json={"title": title, "priority": priority})
        return resp.get_json()
    return _add

def register(c, username, password):
    return c.post("/register", data={"username": username, "password": password})

def login(c, username, password):
    return c.post("/login", data={"username": username, "password": password})

def logged_in_client(app, username, password="secret123"):
    c = app.test_client()
    register(c, username, password)
    login(c, username, password)
    return c

def test_login_page_loads(client): assert b"Login" in client.get("/login").data
def test_register_page_loads(client): assert b"Register" in client.get("/register").data
def test_register_creates_user(client):
    register(client, "alice", "secret123")
    assert login(client, "alice", "secret123").status_code == 302
def test_register_rejects_duplicate_username(client):
    register(client, "alice", "secret123")
    assert "/register" in register(client, "alice", "anotherpass").headers["Location"]
def test_register_rejects_short_password(client):
    register(client, "alice", "123")
    assert "/login" in login(client, "alice", "123").headers["Location"]
def test_login_with_wrong_password(client):
    register(client, "alice", "secret123")
    assert "/login" in login(client, "alice", "wrongpass").headers["Location"]
def test_login_with_unknown_user(client): assert "/login" in login(client, "ghost", "secret123").headers["Location"]
def test_logout_clears_session(auth_client):
    auth_client.post("/logout")
    assert auth_client.get("/todos").status_code == 302
def test_home_redirects_when_not_logged_in(client): assert "/login" in client.get("/").headers["Location"]
def test_todos_api_requires_login(client): assert client.get("/todos").status_code == 302
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
def test_home_page_serves_html(auth_client): assert b"Pi ToDo Pro" in auth_client.get("/").data
def test_home_page_shows_username(auth_client): assert b"Hi, tester" in auth_client.get("/").data
def test_priority_css_classes_exist(auth_client):
    html = auth_client.get("/").data.decode()
    for p in ["high", "medium", "low"]: assert f"badge-{p}" in html
def test_health_endpoint(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}

# JSON API Auth Tests
def test_api_register_success(client):
    resp = client.post("/api/register", json={"username": "reactuser", "password": "password123"})
    assert resp.status_code == 201
def test_api_register_duplicate(client):
    client.post("/api/register", json={"username": "reactuser", "password": "password123"})
    assert client.post("/api/register", json={"username": "reactuser", "password": "password123"}).status_code == 400
def test_api_login_success(client):
    client.post("/api/register", json={"username": "reactuser", "password": "password123"})
    assert client.post("/api/login", json={"username": "reactuser", "password": "password123"}).status_code == 200
def test_api_me_logged_out(client): assert client.get("/api/me").get_json()["username"] is None
def test_api_me_logged_in(client):
    client.post("/api/register", json={"username": "reactuser", "password": "password123"})
    client.post("/api/login", json={"username": "reactuser", "password": "password123"})
    assert client.get("/api/me").get_json()["username"] == "reactuser"

# Todo CRUD Tests
def test_list_starts_empty(auth_client): assert auth_client.get("/todos").get_json() == []
def test_added_todo_appears_in_list(auth_client, add_todo):
    add_todo("buy milk")
    assert "buy milk" in [t["title"] for t in auth_client.get("/todos").get_json()]
def test_todos_returned_newest_first(auth_client, add_todo):
    for title in ["first", "second", "third"]: add_todo(title)
    assert [t["title"] for t in auth_client.get("/todos").get_json()] == ["third", "second", "first"]
def test_add_todo(auth_client):
    assert auth_client.post("/todos", json={"title": "learn pytest"}).status_code == 201
@pytest.mark.parametrize("payload", [{"title": ""}, {"title": "   "}, {}, {"title": None}])
def test_add_todo_rejects_bad_input(auth_client, payload):
    assert auth_client.post("/todos", json=payload).status_code == 400
def test_toggle_done(add_todo, auth_client):
    todo = add_todo("task")
    assert auth_client.patch(f"/todos/{todo['id']}/done").get_json()["done"] == 1
def test_delete_todo(add_todo, auth_client):
    todo = add_todo("temp")
    auth_client.delete(f"/todos/{todo['id']}")
    assert todo["id"] not in [t["id"] for t in auth_client.get("/todos").get_json()]
def test_clear_completed(add_todo, auth_client):
    t1 = add_todo("done 1"); t2 = add_todo("active")
    auth_client.patch(f"/todos/{t1['id']}/done")
    auth_client.delete("/todos/clear-completed")
    assert len(auth_client.get("/todos").get_json()) == 1