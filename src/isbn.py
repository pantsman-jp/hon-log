import re
import threading
import requests
from bs4 import BeautifulSoup

_thread_local = threading.local()


def session():
    if getattr(_thread_local, "session", None) is None:
        _thread_local.session = requests.Session()
        _thread_local.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
    return _thread_local.session


def get_html(url):
    if not url:
        return ""
    try:
        r = session().get(url, timeout=10)
        return r.text
    except Exception:
        return ""


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


def get_isbn(url, html=None):
    if not url:
        return ""
    m = re.search(r"isbn=(97[89]\d{10}|\d{9}[\dX])", url, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    if html is None:
        html = get_html(url)
    return parse_isbn(html)
