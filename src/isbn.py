import functools
import re
from bs4 import BeautifulSoup
from src.network import fetch_text

PLACEHOLDER_IMAGE_MARKERS = (
    "bookimage-",
    "no-image",
    "no_image",
    "noimage",
    "placeholder",
    "default-cover",
)


@functools.lru_cache(maxsize=128)
def get_html(url):
    return fetch_text(url, timeout=10)


def parse_isbn(html):
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("input", {"id": "lid_isbn"})
    if tag and len(re.sub(r"\D", "", tag.get("value", ""))) in [10, 13]:
        return re.sub(r"\D", "", tag.get("value", ""))
    meta = soup.find("meta", {"property": "books:isbn"})
    if (
        meta
        and meta.get("content")
        and len(re.sub(r"\D", "", meta.get("content"))) in [10, 13]
    ):
        return re.sub(r"\D", "", meta.get("content"))
    m = re.search(r"(97[89]\d{10}|\b\d{9}[\dX]\b)", soup.get_text())
    return m.group(0) if m else ""


def is_placeholder_image_url(url):
    return any(marker in (url or "").lower() for marker in PLACEHOLDER_IMAGE_MARKERS)


def _image_url(tag):
    if not tag:
        return ""
    url = (
        tag.get("data-src")
        or tag.get("data-original")
        or tag.get("src")
        or tag.get("value")
        or ""
    ).strip()
    return "" if is_placeholder_image_url(url) else url


def extract_image_url(html):
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    og = soup.find("meta", property="og:image")
    tw = soup.find("meta", attrs={"name": "twitter:image"})
    for tag in (og, tw):
        url = _image_url(tag)
        if url:
            return url
    for tag in (
        soup.select_one("input.l_limedio_thumbnail_url"),
        soup.find("img", {"id": "coverImage"}),
        soup.find("img", {"class": "cover"}),
        soup.find("img", {"class": "book-cover"}),
    ):
        url = _image_url(tag)
        if url:
            return url
    for image in soup.find_all("img"):
        url = _image_url(image)
        if url and any(key in url.lower() for key in ("cover", "thumbnail", "book")):
            return url
    return ""


@functools.lru_cache(maxsize=256)
def get_isbn(url, html=None):
    m = re.search(r"isbn=(97[89]\d{10}|\d{9}[\dX])", url or "", flags=re.IGNORECASE)
    return m.group(1) if m else parse_isbn(html or get_html(url))
