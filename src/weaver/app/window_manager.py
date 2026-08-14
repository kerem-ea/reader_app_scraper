import sys
import socket
import ctypes
from ctypes import wintypes
import webview


# Pick an available localhost TCP port for the Flask server.
def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


# Determine which monitor the window currently sits on.
def get_current_screen(win):
    if not win or not getattr(webview, 'screens', None):
        return None
    try:
        cx = 0
        cy = 0
        if getattr(win, 'x', None) is not None and getattr(win, 'width', None) is not None:
            cx = win.x + win.width // 2
            cy = win.y + win.height // 2
        elif webview.screens:
            cx = webview.screens[0].x + webview.screens[0].width // 2
            cy = webview.screens[0].y + webview.screens[0].height // 2

        for s in webview.screens:
            if (s.x <= cx < s.x + s.width) and (s.y <= cy < s.y + s.height):
                return s
        return webview.screens[0]
    except Exception:
        return None


# Get the monitor bounds (optionally including the taskbar area).
def get_screen_bounds(win, include_taskbar=False):
    scr = get_current_screen(win)
    if not scr and getattr(webview, 'screens', None):
        scr = webview.screens[0]

    if sys.platform == 'win32':
        try:
            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ('cbSize', wintypes.DWORD),
                    ('rcMonitor', wintypes.RECT),
                    ('rcWork', wintypes.RECT),
                    ('dwFlags', wintypes.DWORD),
                ]

            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)

            cx, cy = 0, 0
            if win and getattr(win, 'x', None) is not None and getattr(win, 'width', None) is not None:
                cx = win.x + win.width // 2
                cy = win.y + win.height // 2
            elif scr:
                cx = scr.x + scr.width // 2
                cy = scr.y + scr.height // 2

            pt = wintypes.POINT(cx, cy)
            hMon = ctypes.windll.user32.MonitorFromPoint(pt, 1)
            if hMon and ctypes.windll.user32.GetMonitorInfoW(hMon, ctypes.byref(mi)):
                full_w = mi.rcMonitor.right - mi.rcMonitor.left
                full_h = mi.rcMonitor.bottom - mi.rcMonitor.top
                wx = mi.rcMonitor.left
                wy = mi.rcMonitor.top

                if include_taskbar:
                    return wx, wy, full_w, full_h
                else:
                    work_w = mi.rcWork.right - mi.rcWork.left
                    work_h = mi.rcWork.bottom - mi.rcWork.top
                    work_x = mi.rcWork.left
                    work_y = mi.rcWork.top

                    if work_h < full_h:
                        return work_x, work_y, work_w, work_h
                    else:
                        return wx, wy, full_w, max(300, full_h - 48)
        except Exception:
            pass

    if scr:
        if include_taskbar:
            return scr.x, scr.y, scr.width, scr.height
        else:
            return scr.x, scr.y, scr.width, max(300, scr.height - 48)

    return 0, 0, 1280, 850


# Extract the native Win32 HWND from a pywebview window without relying on
# pywebview's internal attribute layout (version-agnostic getattr chain).
def _native_hwnd(win):
    if sys.platform != 'win32':
        return None
    try:
        native = getattr(win, 'native', None)
        if native is None:
            return None
        handle = getattr(native, 'Handle', None)
        if handle is None:
            handle = native
        raw = int(handle)
        if raw:
            return wintypes.HWND(raw)
    except Exception:
        pass
    return None


# Move/resize the window via the public API, then confirm with the Win32 API.
def apply_window_bounds(win, x, y, w, h):
    if not win:
        return
    try:
        win.move(int(x), int(y))
        win.resize(int(w), int(h))
    except Exception:
        pass

    if sys.platform == 'win32':
        try:
            hwnd = _native_hwnd(win)
            if hwnd:
                user32 = ctypes.windll.user32
                user32.SetWindowPos.argtypes = [
                    wintypes.HWND, wintypes.HWND,
                    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                    ctypes.c_uint,
                ]
                user32.SetWindowPos(hwnd, 0, int(x), int(y), int(w), int(h), 0x0040 | 0x0004 | 0x0010)
        except Exception:
            pass


# Convenience alias for the work-area (taskbar-excluded) bounds.
def get_screen_work_area(win):
    return get_screen_bounds(win, include_taskbar=False)