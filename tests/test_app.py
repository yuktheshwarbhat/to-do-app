def test_list_starts_empty(client):
    resp = client.get("/todos")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_add_todo(client):
    resp = client.post("/todos", json={"title": "learn pytest"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["title"] == "learn pytest"
    assert data["done"] == 0


def test_add_todo_requires_title(client):
    resp = client.post("/todos", json={"title": "   "})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "title is required"


def test_added_todo_appears_in_list(client):
    client.post("/todos", json={"title": "buy milk"})
    titles = [t["title"] for t in client.get("/todos").get_json()]
    assert "buy milk" in titles


def test_toggle_done(client):
    created = client.post("/todos", json={"title": "task"}).get_json()
    resp = client.patch(f"/todos/{created['id']}/done")
    assert resp.get_json()["done"] == 1


def test_toggle_missing_todo_returns_404(client):
    resp = client.patch("/todos/999/done")
    assert resp.status_code == 404