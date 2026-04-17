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


def download_image(isbn):
    try:
        r = requests.get(
            f"https://ndlsearch.ndl.go.jp/thumbnail/{isbn}.jpg",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://ndlsearch.ndl.go.jp/",
            },
            timeout=10,
        )
        if r.status_code == 200:
            return r.content
        return None
    except Exception:
        return None


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
        Image.open(BytesIO(data)).save(path, "JPEG")
        return path
    except Exception:
        return ""
