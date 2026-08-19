from playwright.sync_api import expect

live_server_url = "127.0.0.1"

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
