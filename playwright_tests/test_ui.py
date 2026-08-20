import threading
import time

import pytest
from playwright.sync_api import expect

from app import create_app

PORT = 5555


@pytest.fixture(scope="session")
def live_server_url():
    app = create_app(db_path="/tmp/e2e-todo.db")
    thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=PORT, use_reloader=False),
        daemon=True,
    )
    thread.start()
    time.sleep(1)
    yield f"http://127.0.0.1:{PORT}"


def register_and_login(page, base_url, username, password="secret123"):
    page.goto(f"{base_url}/register")
    page.fill("input[name=username]", username)
    page.fill("input[name=password]", password)
    page.click("button[type=submit]")
    # redirected to /login
    page.fill("input[name=username]", username)
    page.fill("input[name=password]", password)
    page.click("button[type=submit]")


def test_login_page_loads(page, live_server_url):
    page.goto(f"{live_server_url}/login")
    expect(page.locator("h1")).to_contain_text("Pi ToDo Pro")


def test_home_redirects_to_login(page, live_server_url):
    page.goto(live_server_url)
    expect(page).to_have_url(f"{live_server_url}/login")


def test_register_and_add_todo(page, live_server_url):
    register_and_login(page, live_server_url, "e2e_add")
    expect(page.locator(".hello")).to_contain_text("e2e_add")
    page.fill("#title-input", "Playwright was here")
    page.click(".btn-primary")
    expect(page.locator(".title", has_text="Playwright was here")).to_be_visible()


def test_toggle_dark_mode(page, live_server_url):
    register_and_login(page, live_server_url, "e2e_theme")
    page.click("#theme-btn")
    assert page.locator("html").get_attribute("data-theme") == "dark"


def test_complete_todo_updates_stats(page, live_server_url):
    register_and_login(page, live_server_url, "e2e_stats")
    page.fill("#title-input", "stats test")
    page.click(".btn-primary")
    page.locator(".todo").first.locator(".check").click()
    expect(page.locator("#stat-done")).not_to_have_text("0")