from io import BytesIO
from os import makedirs

from PIL import Image
from requests import get

from isbn import get_isbn


def build_thumbnail_url(isbn):
    return "https://ndlsearch.ndl.go.jp/thumbnail/" + isbn + ".jpg"


def get_image(url):
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://ndlsearch.ndl.go.jp/"}
    response = get(url, headers=headers, timeout=5)
    response.raise_for_status()
    return response.content


def open_image(image_bytes):
    return Image.open(BytesIO(image_bytes))


def save_image(img, isbn):
    makedirs("img", exist_ok=True)
    path = "img/" + isbn + ".jpg"
    img.save(path)
    return path


def process_url(url):
    isbn = get_isbn(url)
    if isbn == "":
        return
    return save_image(open_image(get_image(build_thumbnail_url(isbn))), isbn)


# process_url("https://www.lib.kyutech.ac.jp/opac/volume/887096")
