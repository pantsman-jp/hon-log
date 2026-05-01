import os
import re
import time
import requests
from io import BytesIO
from PIL import Image

USER_AGENT = "hon-log-app/1.0"


def get_app_dir():
    app_dir = os.path.join(os.path.expanduser("~"), ".hon-log")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


def get_image_dir():
    image_dir = os.path.join(get_app_dir(), "img")
    os.makedirs(image_dir, exist_ok=True)
    return image_dir


def safe_get(url, timeout=5):
    try:
        time.sleep(0.2)
        headers = {"User-Agent": USER_AGENT}
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code != 200:
            return None
        return r
    except Exception:
        return None


def fetch_url(url):
    response = safe_get(url)
    return response.content if response else None


def fetch_ndl(isbn):
    if not isbn:
        return None
    response = safe_get(
        f"https://ndlsearch.ndl.go.jp/thumbnail/{isbn}.jpg"
    )
    if response is None or len(response.content) < 1000:
        return None
    return response.content


def fetch_google(isbn):
    if not isbn:
        return None
    response = safe_get(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}")
    if response is None:
        return None
    try:
        data = response.json()
    except ValueError:
        return None
    for item in data.get("items", []):
        info = item.get("volumeInfo", {})
        links = info.get("imageLinks", {})
        url = links.get("thumbnail") or links.get("smallThumbnail")
        if url:
            return fetch_url(url.replace("http://", "https://"))
    return None


def fetch_google_query(query):
    if not query:
        return None
    response = safe_get(f"https://www.googleapis.com/books/v1/volumes?q=intitle:{query}")
    if response is None:
        return None
    try:
        data = response.json()
    except ValueError:
        return None
    for item in data.get("items", []):
        info = item.get("volumeInfo", {})
        links = info.get("imageLinks", {})
        url = links.get("thumbnail") or links.get("smallThumbnail")
        if url:
            return fetch_url(url.replace("http://", "https://"))
    return None


def fetch_openlibrary(isbn):
    if not isbn:
        return None
    response = safe_get(f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg")
    if response is None or len(response.content) <= 200:
        return None
    return response.content


def download_image(isbn, query, image_url=None):
    if image_url:
        data = fetch_url(image_url)
        if data:
            return data

    if isbn:
        for fetcher in (fetch_google, fetch_openlibrary, fetch_ndl):
            data = fetcher(isbn)
            if data:
                return data

    if query:
        return fetch_google_query(query)

    return None


def _safe_filename(key):
    safe_key = re.sub(r"[^\w\-_.]+", "_", key)
    return safe_key[:240]


def process_thumbnail(isbn, query, image_url=None):
    key = isbn or query or (image_url or "")
    if not key:
        return ""
    safe_key = _safe_filename(key)
    path = os.path.join(get_image_dir(), f"{safe_key}.jpeg")
    if os.path.exists(path):
        return path

    data = download_image(isbn, query, image_url)
    if not data:
        return ""
    try:
        with Image.open(BytesIO(data)) as img:
            img.convert("RGB").save(path, "JPEG")
        return path
    except Exception:
        return ""
