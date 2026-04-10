import threading
import requests
from bs4 import BeautifulSoup

_thread_local = threading.local()


def get_session():
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        _thread_local.session = session
    return session


def get_html(url):
    response = get_session().get(url, timeout=5)
    response.raise_for_status()
    return response.text


def parse_html(html):
    return BeautifulSoup(html, "html.parser")


def find_isbn_tag(soup):
    return soup.find("input", {"id": "lid_isbn"})


def has_value_attr(tag):
    return (tag is not None) and ("value" in tag.attrs)


def get_value_attr(tag):
    if has_value_attr(tag):
        return tag["value"]
    return ""


def get_isbn(url):
    return get_value_attr(find_isbn_tag(parse_html(get_html(url))))
