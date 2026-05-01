import functools
import re
from bs4 import BeautifulSoup
from src.network import fetch_text


@functools.lru_cache(maxsize=128)
def get_html(url):
    return fetch_text(url, timeout=10)


def parse_isbn(html):
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("input", {"id": "lid_isbn"})
    if tag:
        val = re.sub(r"\D", "", tag.get("value", ""))
        if len(val) in [10, 13]:
            return val
    meta = soup.find("meta", {"property": "books:isbn"})
    if meta and meta.get("content"):
        val = re.sub(r"\D", "", meta.get("content"))
        if len(val) in [10, 13]:
            return val
    text = soup.get_text()
    m = re.search(r"(97[89]\d{10}|\b\d{9}[\dX]\b)", text)
    return m.group(0) if m else ""


def extract_image_url(html):
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", property="og:image")
    if meta and meta.get("content"):
        return meta.get("content").strip()
    meta = soup.find("meta", attrs={"name": "twitter:image"})
    if meta and meta.get("content"):
        return meta.get("content").strip()
    img = soup.find("img", {"id": "coverImage"})
    if not img:
        img = soup.find("img", {"class": "cover"})
    if not img:
        img = soup.find("img", {"class": "book-cover"})
    if img and img.get("src"):
        return img.get("src").strip()
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src and any(
            keyword in src.lower() for keyword in ("cover", "thumbnail", "book")
        ):
            return src.strip()
    return ""


@functools.lru_cache(maxsize=256)
def get_isbn(url, html=None):
    if not url:
        return ""
    m = re.search(r"isbn=(97[89]\d{10}|\d{9}[\dX])", url, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    if html is None:
        html = get_html(url)
    return parse_isbn(html)
