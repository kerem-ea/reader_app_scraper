import os
import webview

from .keep_awake import register_user_activity, keep_awake_mgr
from .window_manager import get_current_screen, get_screen_bounds, apply_window_bounds


# JS <-> Python bridge exposed to the pywebview window.
class Api:
    def __init__(self):
        self._window = None
        self._is_maximized = False
        self._restored_bounds = None
        self._has_taskbar = True

    def set_window(self, window):
        self._window = window

    def close(self):
        if self._window:
            try:
                self._window.destroy()
            except Exception:
                pass
        os._exit(0)

    def minimize(self):
        if self._window:
            try:
                self._window.minimize()
            except Exception:
                pass

    def ping_activity(self):
        register_user_activity()
        return True

    def set_keep_awake(self, enabled):
        keep_awake_mgr.set_enabled(enabled)
        return True

    def set_taskbar_mode(self, has_taskbar):
        self._has_taskbar = bool(has_taskbar)
        self._apply_taskbar_bounds()
        return self._has_taskbar

    def toggle_taskbar_mode(self):
        self._has_taskbar = not self._has_taskbar
        self._apply_taskbar_bounds()
        return self._has_taskbar

    def _apply_taskbar_bounds(self):
        if not self._window:
            return
        try:
            include_taskbar_fullscreen = not self._has_taskbar
            wx, wy, ww, wh = get_screen_bounds(self._window, include_taskbar=include_taskbar_fullscreen)
            apply_window_bounds(self._window, wx, wy, ww, wh)
        except Exception:
            pass

    def maximize(self):
        if not self._window:
            return

        try:
            scr = get_current_screen(self._window)
            if not scr and getattr(webview, 'screens', None):
                scr = webview.screens[0]

            if self._is_maximized:
                if self._restored_bounds:
                    rx, ry, rw, rh = self._restored_bounds
                    apply_window_bounds(self._window, rx, ry, rw, rh)
                else:
                    if scr:
                        rw, rh = int(scr.width * 0.8), int(scr.height * 0.8)
                        rx = scr.x + (scr.width - rw) // 2
                        ry = scr.y + (scr.height - rh) // 2
                        apply_window_bounds(self._window, rx, ry, rw, rh)
                self._is_maximized = False
                try:
                    self._window.evaluate_js('if (window.setWindowMaximizedState) window.setWindowMaximizedState(false);')
                except Exception:
                    pass
            else:
                if getattr(self._window, 'width', 0) and getattr(self._window, 'height', 0):
                    if self._window.width > 200 and self._window.height > 200:
                        self._restored_bounds = (self._window.x, self._window.y, self._window.width, self._window.height)

                self._apply_taskbar_bounds()
                self._is_maximized = True
                try:
                    self._window.evaluate_js('if (window.setWindowMaximizedState) window.setWindowMaximizedState(true);')
                except Exception:
                    pass
        except Exception:
            pass