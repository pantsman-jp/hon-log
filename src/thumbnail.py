from io import BytesIO
import os
import threading

from PIL import Image
import requests

from src.isbn import get_isbn
from src.utils import get_data_path

IMG_DIR = get_data_path("assets", "img")

_thread_local = threading.local()


def get_session():
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update(
            {"User-Agent": "Mozilla/5.0", "Referer": "https://ndlsearch.ndl.go.jp/"}
        )
        _thread_local.session = session
    return session


def build_thumbnail_url(isbn):
    return "https://ndlsearch.ndl.go.jp/thumbnail/" + isbn + ".jpg"


def get_image(url):
    response = get_session().get(url, timeout=5)
    response.raise_for_status()
    return response.content


def open_image(image_bytes):
    return Image.open(BytesIO(image_bytes))


def save_image(img, isbn):
    os.makedirs(IMG_DIR, exist_ok=True)
    path = os.path.join(IMG_DIR, f"{isbn}.jpg")
    img.save(path)
    return path


def process_url(url, isbn=None):
    if isbn is None:
        isbn = get_isbn(url)
    if isbn == "":
        return
    return save_image(open_image(get_image(build_thumbnail_url(isbn))), isbn)
