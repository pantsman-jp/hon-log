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


def extract_image_url(html):
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    og = soup.find("meta", property="og:image")
    tw = soup.find("meta", attrs={"name": "twitter:image"})
    if og and og.get("content"):
        return og.get("content").strip()
    if tw and tw.get("content"):
        return tw.get("content").strip()
    img = (
        soup.find("img", {"id": "coverImage"})
        or soup.find("img", {"class": "cover"})
        or soup.find("img", {"class": "book-cover"})
    )
    if img and img.get("src"):
        return img.get("src").strip()
    return next(
        (
            i.get("src") or i.get("data-src")
            for i in soup.find_all("img")
            if any(
                k in (i.get("src") or "").lower()
                for k in ("cover", "thumbnail", "book")
            )
        ),
        "",
    )


@functools.lru_cache(maxsize=256)
def get_isbn(url, html=None):
    m = re.search(r"isbn=(97[89]\d{10}|\d{9}[\dX])", url or "", flags=re.IGNORECASE)
    return m.group(1) if m else parse_isbn(html or get_html(url))
