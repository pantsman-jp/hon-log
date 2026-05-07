import os
import re
from io import BytesIO
from PIL import Image
from src.network import fetch_content, fetch_json


def get_app_dir():
    d = os.path.join(os.path.expanduser("~"), ".hon-log")
    os.makedirs(d, exist_ok=True)
    return d


def get_image_dir():
    d = os.path.join(get_app_dir(), "img")
    os.makedirs(d, exist_ok=True)
    return d


def fetch_ndl(isbn):
    r = fetch_content(f"https://ndlsearch.ndl.go.jp/thumbnail/{isbn}.jpg")
    return r if r and len(r) > 1000 else None


def fetch_google(isbn):
    d = fetch_json(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}")
    url = (
        next(
            (
                i.get("volumeInfo", {}).get("imageLinks", {}).get("thumbnail")
                for i in d.get("items", [])
                if i.get("volumeInfo", {}).get("imageLinks")
            ),
            None,
        )
        if d
        else None
    )
    return fetch_content(url.replace("http://", "https://")) if url else None


def process_thumbnail(isbn, query, url=None):
    path = os.path.join(
        get_image_dir(),
        f"{re.sub(r'[^\w\-_.]+', '_', isbn or query or 'none')[:240]}.jpeg",
    )
    if os.path.exists(path):
        return path
    data = fetch_content(url) if url else (fetch_google(isbn) or fetch_ndl(isbn))
    try:
        if data:
            Image.open(BytesIO(data)).convert("RGB").save(path, "JPEG")
            return path
    except Exception:
        pass
    return ""
