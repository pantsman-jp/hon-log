import os
import requests
import time
from io import BytesIO
from PIL import Image


def get_app_dir():
    dir = os.path.join(os.path.expanduser("~"), ".hon-log")
    if os.path.exists(dir) is False:
        os.makedirs(dir, exist_ok=True)
    return dir


def get_image_dir():
    dir = os.path.join(get_app_dir(), "img")
    if os.path.exists(dir) is False:
        os.makedirs(dir, exist_ok=True)
    return dir


def safe_get(url, timeout=5):
    try:
        time.sleep(0.2)
        r = requests.get(url, timeout=timeout)
        if r.status_code != 200:
            return None
        return r
    except Exception:
        return None


def fetch_ndl(isbn):
    try:
        time.sleep(0.2)
        r = requests.get(
            f"https://ndlsearch.ndl.go.jp/thumbnail/{isbn}.jpg",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://ndlsearch.ndl.go.jp/",
            },
            timeout=5,
        )
        if r.status_code != 200:
            return None
        if len(r.content) < 1000:
            return None
        return r.content
    except Exception:
        return None


def fetch_google(isbn):
    r = safe_get(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}")
    if r is None:
        return None
    data = r.json()
    items = data.get("items")
    if not items:
        return None
    for item in items:
        info = item.get("volumeInfo", {})
        links = info.get("imageLinks", {})
        url = links.get("thumbnail") or links.get("smallThumbnail")
        if url:
            img = safe_get(url.replace("http://", "https://"))
            return img.content if img else None
    return None


def fetch_google_query(query):
    r = safe_get(f"https://www.googleapis.com/books/v1/volumes?q=intitle:{query}")
    if r is None:
        return None
    data = r.json()
    items = data.get("items")
    if not items:
        return None
    for item in items:
        info = item.get("volumeInfo", {})
        links = info.get("imageLinks", {})
        url = links.get("thumbnail") or links.get("smallThumbnail")
        if url:
            img = safe_get(url.replace("http://", "https://"))
            return img.content if img else None
    return None


def fetch_openlibrary(isbn):
    r = safe_get(f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg")
    if r and len(r.content) > 200:
        return r.content
    return None


def download_image(isbn, query):
    if isbn != "":
        data = next(
            filter(
                None, [fetch_google(isbn), fetch_openlibrary(isbn), fetch_ndl(isbn)]
            ),
            None,
        )
        if data:
            return data
    if query != "":
        return fetch_google_query(query)
    return None


def process_thumbnail(isbn, query):
    key = isbn if isbn != "" else query
    if key == "":
        return ""
    safe_key = key.replace("/", "_")
    path = os.path.join(get_image_dir(), f"{safe_key}.jpeg")
    if os.path.exists(path):
        return path
    data = download_image(isbn, query)
    if data is None:
        return ""
    try:
        Image.open(BytesIO(data)).convert("RGB").save(path, "JPEG")
        return path
    except Exception:
        return ""
