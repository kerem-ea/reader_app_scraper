import socket
import time
import threading
import webview
from .routes import app
from .keep_awake import keep_awake_mgr
from .window_manager import get_free_port
from .api import Api

# Start the Flask server + pywebview desktop window.
def _wait_for_server(port: int, timeout: float = 10.0) -> None:
    """Block until the Flask server on 127.0.0.1:port accepts connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)


def main():
    port = 5000
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 5000))
        s.close()
    except OSError:
        port = get_free_port()

    def start_flask():
        app.run(debug=False, use_reloader=False, host='127.0.0.1', port=port, threaded=True)

    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    _wait_for_server(port)

    keep_awake_mgr.start()

    api_instance = Api()
    win = webview.create_window(
        'Weaver Reader',
        f'http://127.0.0.1:{port}',
        width=1280,
        height=850,
        min_size=(480, 360),
        resizable=True,
        maximized=False,
        frameless=True,
        easy_drag=False,
        js_api=api_instance
    )
    api_instance.set_window(win)

    def init_maximized():
        time.sleep(0.5)
        api_instance.maximize()

    threading.Thread(target=init_maximized, daemon=True).start()
    webview.start()

if __name__ == '__main__':
    main()