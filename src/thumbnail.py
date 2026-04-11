import os
import requests
from io import BytesIO
from PIL import Image


def get_app_dir():
    d = os.path.join(os.path.expanduser("~"), ".hon-log")
    os.makedirs(d, exist_ok=True)
    return d


def get_image_dir():
    d = os.path.join(get_app_dir(), "img")
    os.makedirs(d, exist_ok=True)
    return d


def download_image(isbn):
    return requests.get(
        f"https://ndlsearch.ndl.go.jp/thumbnail/{isbn}.jpg",
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://ndlsearch.ndl.go.jp/",
        },
        timeout=10,
    ).content


def process_thumbnail(isbn):
    if not isbn:
        return ""
    path = os.path.join(get_image_dir(), f"{isbn}.jpeg")
    if os.path.exists(path):
        return path
    try:
        Image.open(BytesIO(download_image(isbn))).save(path)
        return path
    except Exception:
        return ""
