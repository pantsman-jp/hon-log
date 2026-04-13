import os
import requests
from io import BytesIO
from PIL import Image


def get_app_dir():
    dir = os.path.join(os.path.expanduser("~"), ".hon-log")
    os.makedirs(dir, exist_ok=True)
    return dir


def get_image_dir():
    dir = os.path.join(get_app_dir(), "img")
    os.makedirs(dir, exist_ok=True)
    return dir


def download_image(isbn):
    try:
        img = requests.get(
            f"https://ndlsearch.ndl.go.jp/thumbnail/{isbn}.jpg",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://ndlsearch.ndl.go.jp/",
            },
            timeout=10,
        )
        if img.status_code == 200:
            return img.content
        else:
            None
    except Exception:
        return None


def process_thumbnail(isbn):
    if not isbn:
        return ""
    path = os.path.join(get_image_dir(), f"{isbn}.jpeg")
    if os.path.exists(path):
        return path
    img_data = download_image(isbn)
    if not img_data:
        return ""
    try:
        Image.open(BytesIO(img_data)).save(path, "JPEG")
        return path
    except Exception:
        return ""
