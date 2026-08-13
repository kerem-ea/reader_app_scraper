import sys
import time
import threading
import ctypes


def set_thread_execution_state(flags):
    if sys.platform == 'win32':
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(flags)
        except Exception:
            pass


def send_synthetic_user_input():
    if sys.platform == 'win32':
        try:
            ctypes.windll.user32.mouse_event(0x0001, 0, 0, 0, 0)
        except Exception:
            pass


def register_user_activity():
    ES_CONTINUOUS = 0x80000000
    ES_DISPLAY_REQUIRED = 0x00000002
    ES_SYSTEM_REQUIRED = 0x00000001
    set_thread_execution_state(ES_CONTINUOUS | ES_DISPLAY_REQUIRED | ES_SYSTEM_REQUIRED)
    send_synthetic_user_input()


class KeepAwakeManager:
    def __init__(self):
        self.enabled = True
        self._thread = None
        self._running = False

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while self._running:
            if self.enabled:
                register_user_activity()
            time.sleep(15)

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        ES_CONTINUOUS = 0x80000000
        if self.enabled:
            register_user_activity()
        else:
            set_thread_execution_state(ES_CONTINUOUS)


keep_awake_mgr = KeepAwakeManager()
