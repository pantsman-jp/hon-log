import os
import re
from io import BytesIO
from urllib.parse import quote_plus, urljoin, urlparse
from PIL import Image
from src.isbn import is_placeholder_image_url
from src.network import fetch_content, fetch_json

NDL_HEADERS = {"Referer": "https://ndlsearch.ndl.go.jp/"}
COVER_CACHE_VERSION = "2"


def get_app_dir():
    d = os.path.join(os.path.expanduser("~"), ".hon-log")
    os.makedirs(d, exist_ok=True)
    return d


def get_image_dir():
    d = os.path.join(get_app_dir(), "img")
    os.makedirs(d, exist_ok=True)
    return d


def fetch_ndl(isbn):
    if not isbn:
        return None
    r = fetch_content(
        f"https://ndlsearch.ndl.go.jp/thumbnail/{isbn}.jpg", headers=NDL_HEADERS
    )
    return r if r and len(r) > 1000 else None


def _fetch_google(query):
    if not query:
        return None
    data = fetch_json(
        "https://www.googleapis.com/books/v1/volumes?q=" + quote_plus(query)
    )
    if not isinstance(data, dict):
        return None
    items = data.get("items", [])
    if not isinstance(items, list):
        return None
    for item in items:
        if not isinstance(item, dict):
            continue
        volume_info = item.get("volumeInfo", {})
        if not isinstance(volume_info, dict):
            continue
        links = volume_info.get("imageLinks", {})
        if not isinstance(links, dict):
            continue
        url = links.get("thumbnail") or links.get("smallThumbnail")
        if isinstance(url, str):
            return fetch_content(url.replace("http://", "https://"))
    return None


def fetch_google(isbn):
    return _fetch_google(f"isbn:{isbn}") if isbn else None


def fetch_google_query(query):
    return _fetch_google(f"intitle:{query}")


def fetch_openlibrary(isbn):
    if not isbn:
        return None
    # default=false makes the service return 404 instead of its generic
    # "cover not found" image, which must not be saved as a book cover.
    return fetch_content(
        f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg?default=false"
    )


def _is_image(data):
    if not data:
        return False
    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
        return True
    except (OSError, ValueError):
        return False


def _absolute_http_url(url, source_url):
    absolute_url = urljoin(source_url or "", url or "")
    parsed = urlparse(absolute_url)
    return absolute_url if parsed.scheme in {"http", "https"} and parsed.netloc else ""


def download_image(isbn, query, image_url=None, source_url=None):
    """Return the first valid image from the OPAC page or public cover APIs."""
    candidates = []
    direct_url = _absolute_http_url(image_url, source_url)
    if direct_url and not is_placeholder_image_url(direct_url):
        headers = {"Referer": source_url} if source_url else None
        candidates.append(lambda: fetch_content(direct_url, headers=headers))

    if isbn:
        # Google Books is preferred when available.  NDL is next because it is
        # especially complete for Japanese titles, then Open Library is used
        # as a final ISBN-based fallback.
        candidates.extend(
            [
                lambda: fetch_google(isbn),
                lambda: fetch_ndl(isbn),
                lambda: fetch_openlibrary(isbn),
            ]
        )
    elif query:
        candidates.append(lambda: fetch_google_query(query))

    for fetcher in candidates:
        data = fetcher()
        if _is_image(data):
            return data
    return None


def process_thumbnail(isbn, query, url=None, source_url=None):
    if not (isbn or query or url):
        return ""
    path = os.path.join(
        get_image_dir(),
        (
            f"{re.sub(r'[^\w\-_.]+', '_', isbn or query or 'none')[:236]}"
            f"-v{COVER_CACHE_VERSION}.jpeg"
        ),
    )
    if os.path.exists(path):
        return path
    data = download_image(isbn, query, url, source_url)
    try:
        if data:
            with Image.open(BytesIO(data)) as image:
                image.convert("RGB").save(path, "JPEG")
            return path
    except (OSError, ValueError):
        pass
    return ""
