import os
import sqlite3
from csv import DictReader
from src.isbn import get_isbn
from src.thumbnail import process_url


def connect(db_path):
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(db_path)


def create_table(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, loan_date TEXT, volume TEXT, author TEXT, publisher TEXT, published_at TEXT, material_id TEXT, url TEXT, isbn TEXT, review TEXT, UNIQUE(material_id, loan_date))"
    )


def normalize_row(row):
    normalized = {}
    for k, v in row.items():
        key = k.replace("\ufeff", "").strip()
        normalized[key] = v
    return normalized


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
    process_url(url, isbn)
    conn.execute(
        "INSERT INTO loans (title, loan_date, volume, author, publisher, published_at, material_id, url, isbn, review) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
            "",
        ),
    )


def import_csv(conn, csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row in DictReader(f):
            insert_row(conn, row)


def update_review(conn, row_id, review):
    conn.execute("UPDATE loans SET review = ? WHERE id = ?", (review, row_id))


def fetch_rows(conn):
    cursor = conn.execute(
        "SELECT id, title, author, publisher, loan_date, isbn, review FROM loans ORDER BY loan_date DESC"
    )
    return list(cursor)


def initialize_db(db_path, csv_path):
    with connect(db_path) as conn:
        create_table(conn)
        import_csv(conn, csv_path)
        conn.commit()
