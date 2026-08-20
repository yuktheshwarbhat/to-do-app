import threading
import time

import pytest
from playwright.sync_api import expect

from app import create_app

PORT = 5555


@pytest.fixture(scope="session")
def live_server_url():
    """Start a REAL server on port 5555 for the browser to visit."""
    app = create_app(db_path="/tmp/e2e-todo.db")
    thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=PORT, use_reloader=False),
        daemon=True,
    )
    thread.start()
    time.sleep(1)  # let the server boot
    yield f"http://127.0.0.1:{PORT}"


def test_page_loads(page, live_server_url):
    page.goto(live_server_url)
    assert page.title() == "Pi ToDo Pro"


def test_add_todo_via_ui(page, live_server_url):
    page.goto(live_server_url)
    page.fill("#title-input", "Playwright was here")
    page.click(".btn-primary")
    expect(page.locator(".title", has_text="Playwright was here")).to_be_visible()


def test_toggle_dark_mode(page, live_server_url):
    page.goto(live_server_url)
    page.click("#theme-btn")
    assert page.locator("html").get_attribute("data-theme") == "dark"


def test_complete_todo_updates_stats(page, live_server_url):
    page.goto(live_server_url)
    page.fill("#title-input", "stats test")
    page.click(".btn-primary")
    first_todo = page.locator(".todo").first
    first_todo.locator(".check").click()
    expect(page.locator("#stat-done")).not_to_have_text("0")