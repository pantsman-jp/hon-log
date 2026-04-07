import requests
from bs4 import BeautifulSoup


def fetch_html(url):
    return requests.get(url).text


def parse_html(html):
    return BeautifulSoup(html, "html.parser")


def find_isbn_tag(soup):
    return soup.find("input", {"id": "lid_isbn"})


def get_value_attr(tag):
    return tag["value"] if tag and "value" in tag.attrs else None


def extract_isbn(soup):
    return get_value_attr(find_isbn_tag(soup))


def fetch_isbn(url):
    return extract_isbn(parse_html(fetch_html(url)))
