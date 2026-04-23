import os
import requests
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


def fetch_ndl(isbn):
    try:
        r = requests.get(
            f"https://ndlsearch.ndl.go.jp/thumbnail/{isbn}.jpg",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5,
        )
        return r.content if r.status_code == 200 else None
    except Exception:
        return None


def fetch_google(isbn):
    try:
        r = requests.get(
            f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}", timeout=5
        )
        data = r.json()
        url = (
            data.get("items", [{}])[0]
            .get("volumeInfo", {})
            .get("imageLinks", {})
            .get("thumbnail")
        )
        return (
            requests.get(url.replace("http://", "https://"), timeout=5).content
            if url
            else None
        )
    except Exception:
        return None


def fetch_openlibrary(isbn):
    try:
        r = requests.get(
            f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg", timeout=5
        )
        if r.status_code == 200 and len(r.content) > 1000:
            return r.content
        return None
    except Exception:
        return None


def download_image(isbn):
    return next(
        filter(None, [fetch_ndl(isbn), fetch_google(isbn), fetch_openlibrary(isbn)]),
        None,
    )


def process_thumbnail(isbn):
    if isbn == "":
        return ""
    path = os.path.join(get_image_dir(), f"{isbn}.jpeg")
    if os.path.exists(path):
        return path
    data = download_image(isbn)
    if data is None:
        return ""
    try:
        Image.open(BytesIO(data)).convert("RGB").save(path, "JPEG")
        return path
    except Exception:
        return ""
