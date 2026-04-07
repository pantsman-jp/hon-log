import os
import sqlite3
from csv import DictReader

from isbn import get_isbn
from thumbnail import process_url


def connect(db_path):
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
        return "img/no-image.png"
    path = "img/" + isbn + ".jpg"
    if os.path.exists(path):
        return path
    return "img/no-image.png"


def fetch_and_store_image(url):
    try:
        process_url(url)
    except Exception:
        return


def record_exists(conn, material_id, loan_date):
    cursor = conn.execute(
        "SELECT 1 FROM loans WHERE material_id = ? AND loan_date = ?",
        (material_id, loan_date),
    )
    return cursor.fetchone() is not None


def insert_row(conn, row):
    row = normalize_row(row)
    material_id = row.get("資料ID", "")
    loan_date = row.get("貸出日", "")
    if record_exists(conn, material_id, loan_date):
        return
    url = row.get("URL", "")
    isbn = get_isbn(url)
    fetch_and_store_image(url)
    image_path = build_image_path(isbn)
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
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row in DictReader(f):
            insert_row(conn, row)


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


def initialize_db(db_path, csv_path):
    with connect(db_path) as conn:
        create_table(conn)
        import_csv(conn, csv_path)
        conn.commit()


def enrich_isbn(db_path):
    with connect(db_path) as conn:
        fill_isbn(conn)
        conn.commit()


# initialize_db("loans.db", "loan_history.csv")
