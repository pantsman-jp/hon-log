import threading
import time

import requests

_thread_local = threading.local()
_rate_lock = threading.Lock()
_last_request_time = 0.0
REQUEST_INTERVAL = 0.6
DEFAULT_HEADERS = {"User-Agent": "hon-log-app/1.0"}


def session():
    if getattr(_thread_local, "session", None) is None:
        s = requests.Session()
        s.headers.update(DEFAULT_HEADERS)
        _thread_local.session = s
    return _thread_local.session


def _wait_for_rate_limit():
    global _last_request_time
    with _rate_lock:
        now = time.monotonic()
        elapsed = now - _last_request_time
        if elapsed < REQUEST_INTERVAL:
            time.sleep(REQUEST_INTERVAL - elapsed)
            now = time.monotonic()
        _last_request_time = now


def fetch(url, timeout=5, headers=None, **kwargs):
    if not url:
        return None
    try:
        _wait_for_rate_limit()
        sess = session()
        request_headers = dict(DEFAULT_HEADERS)
        if headers:
            request_headers.update(headers)
        response = sess.get(url, headers=request_headers, timeout=timeout, **kwargs)
        if response.status_code != 200:
            return None
        return response
    except Exception:
        return None


def fetch_text(url, timeout=10):
    response = fetch(url, timeout=timeout)
    return response.text if response else ""


def fetch_content(url, timeout=5):
    response = fetch(url, timeout=timeout)
    return response.content if response else None


def fetch_json(url, timeout=10):
    response = fetch(url, timeout=timeout)
    if not response:
        return None
    try:
        return response.json()
    except ValueError:
        return None
