import os
import sqlite3
from csv import DictReader
from concurrent.futures import ThreadPoolExecutor

from src.isbn import get_isbn
from src.thumbnail import process_url
from src.utils import get_data_path, resource_path


IMG_DIR = get_data_path("assets", "img")


def connect(db_path):
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(db_path)


def create_table(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, loan_date TEXT, volume TEXT, author TEXT, publisher TEXT, published_at TEXT, material_id TEXT, url TEXT, isbn TEXT, image_path TEXT, review TEXT, UNIQUE(material_id, loan_date))"
    )


def normalize_row(row):
    normalized = {}
    for [k, v] in row.items():
        key = k.replace("\ufeff", "").strip()
        normalized[key] = v
    return normalized


def build_image_path(isbn):
    if isbn == "":
        return resource_path("assets/img/no-image.png")
    path = os.path.join(IMG_DIR, f"{isbn}.jpg")
    if os.path.exists(path):
        return path
    return resource_path("assets/img/no-image.png")


def fetch_and_store_image(url, isbn=None):
    try:
        process_url(url, isbn=isbn)
    except Exception:
        return


def download_missing_images(items):
    if not items:
        return
    unique_items = set(items)
    with ThreadPoolExecutor(max_workers=5) as executor:
        for [url, isbn] in unique_items:
            executor.submit(fetch_and_store_image, url, isbn)


def record_exists(conn, material_id, loan_date):
    cursor = conn.execute(
        "SELECT 1 FROM loans WHERE material_id = ? AND loan_date = ?",
        (material_id, loan_date),
    )
    return cursor.fetchone() is not None


def insert_row(conn, row, missing_images):
    row = normalize_row(row)
    material_id = row.get("資料ID", "")
    loan_date = row.get("貸出日", "")
    if record_exists(conn, material_id, loan_date):
        return
    url = row.get("URL", "")
    isbn = get_isbn(url)
    image_path = build_image_path(isbn)
    if (os.path.basename(image_path) == "no-image.png") and (isbn != ""):
        missing_images.append((url, isbn))
    conn.execute(
        "INSERT INTO loans (title, loan_date, volume, author, publisher, published_at, material_id, url, isbn, image_path, review) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            row.get("タイトル", ""),
            loan_date,
            row.get("巻情報", ""),
            row.get("著者", ""),
            row.get("出版社", ""),
            row.get("年月情報", ""),
            material_id,
            url,
            isbn,
            image_path,
            "",
        ),
    )


def import_csv(conn, csv_path):
    missing_images = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row in DictReader(f):
            insert_row(conn, row, missing_images)
    download_missing_images(missing_images)


def update_isbn(conn, row_id, url):
    isbn = get_isbn(url)
    fetch_and_store_image(url)
    image_path = build_image_path(isbn)
    conn.execute(
        "UPDATE loans SET isbn = ?, image_path = ? WHERE id = ?",
        (isbn, image_path, row_id),
    )


def fill_isbn(conn):
    cursor = conn.execute("SELECT id, url FROM loans")
    for [row_id, url] in cursor:
        update_isbn(conn, row_id, url)


def update_review(conn, row_id, review):
    conn.execute("UPDATE loans SET review = ? WHERE id = ?", (review, row_id))


def fetch_rows(conn):
    cursor = conn.execute(
        "SELECT id, title, author, publisher, loan_date, image_path, review FROM loans ORDER BY loan_date DESC"
    )
    return list(cursor)


def initialize_db(db_path, csv_path):
    with connect(db_path) as conn:
        create_table(conn)
        import_csv(conn, csv_path)
        conn.commit()


def enrich_isbn(db_path):
    with connect(db_path) as conn:
        fill_isbn(conn)
        conn.commit()
