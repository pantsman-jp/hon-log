import threading
import requests
import re
from bs4 import BeautifulSoup

_thread_local = threading.local()


def session():
    if getattr(_thread_local, "session", None) is None:
        _thread_local.session = requests.Session()
        _thread_local.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
    return getattr(_thread_local, "session")


def get_html(url):
    try:
        r = session().get(url, timeout=10)
        return r.text
    except Exception:
        return ""


def parse_isbn(html):
    if html == "":
        return ""
    soup = BeautifulSoup(html, "html.parser")
    input_tag = soup.find("input", {"id": "lid_isbn"})
    if input_tag:
        val = re.sub(r"\D", "", input_tag.get("value", ""))
        if len(val) in [10, 13]:
            return val
    text = soup.get_text()
    m = re.search(r"(97[89]\d{10}|\b\d{9}[\dX]\b)", text)
    return m.group(0) if m else ""


def get_isbn(url):
    if url == "":
        return ""
    m = re.search(r"isbn=(97[89]\d{10}|\d{9}[\dX])", url)
    if m:
        return m.group(1)
    return parse_isbn(get_html(url))
