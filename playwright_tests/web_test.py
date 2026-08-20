
import threading
import time
import pytest
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