import threading
import re
import requests
from bs4 import BeautifulSoup

_thread_local = threading.local()
REQUEST_TIMEOUT = 10


def get_session():
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update(
            {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja-JP,ja;q=0.9"}
        )
        _thread_local.session = session
    return session


def get_html(url):
    if not url:
        return ""
    try:
        r = get_session().get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.text
    except requests.RequestException:
        return ""


def parse(html):
    return BeautifulSoup(html, "html.parser")


def extract_from_input(soup):
    tag = soup.find("input", {"id": "lid_isbn"})
    if tag and tag.get("value"):
        return tag["value"]
    return ""


def extract_from_text(text):
    patterns = [
        r"97[89][\-\s]?\d[\d\-\s]{10,17}\d",
        r"ISBN[\s]*[:：]?\s*(97[89][\d\-\s]+)",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1 if "ISBN" in p else 0).replace("-", "").replace(" ", "")
    return ""


def get_isbn(url):
    html = get_html(url)
    if not html:
        return ""
    soup = parse(html)
    isbn = extract_from_input(soup)
    if isbn:
        return isbn
    return extract_from_text(soup.get_text())
