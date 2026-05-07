import threading
import time
import requests

_thread_local = threading.local()
_rate_lock = threading.Lock()
_last_request_time = 0.0
REQUEST_INTERVAL = 0.6
DEFAULT_HEADERS = {"User-Agent": "hon-log-app/1.0"}


def session():
    if not hasattr(_thread_local, "session"):
        s = requests.Session()
        s.headers.update(DEFAULT_HEADERS)
        _thread_local.session = s
    return _thread_local.session


def _wait():
    global _last_request_time
    with _rate_lock:
        now = time.monotonic()
        wait_time = max(0, REQUEST_INTERVAL - (now - _last_request_time))
        time.sleep(wait_time)
        _last_request_time = time.monotonic()


def fetch(url, timeout=5, headers=None, **kwargs):
    if not url:
        return None
    try:
        _wait()
        h = {**DEFAULT_HEADERS, **(headers or {})}
        r = session().get(url, headers=h, timeout=timeout, **kwargs)
        return r if r.status_code == 200 else None
    except Exception:
        return None


def fetch_text(url, timeout=10):
    r = fetch(url, timeout=timeout)
    return r.text if r else ""


def fetch_content(url, timeout=5):
    r = fetch(url, timeout=timeout)
    return r.content if r else None


def fetch_json(url, timeout=10):
    r = fetch(url, timeout=timeout)
    return r.json() if r and r.status_code == 200 else None
