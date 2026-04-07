import requests
from bs4 import BeautifulSoup


def get_html(url):
    return requests.get(url).text


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


# print(get_isbn("https://www.lib.kyutech.ac.jp/opac/ja/volume/891128"))
# print(get_isbn("https://www.lib.kyutech.ac.jp/opac/volume/231128"))
