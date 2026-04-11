import sqlite3
import os
from src.isbn import get_isbn
from src.thumbnail import process_thumbnail, get_app_dir


def get_db_path():
    return os.path.join(get_app_dir(), "loans.db")


def connect_db():
    return sqlite3.connect(get_db_path())


def create_table(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS loans(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,loan_date TEXT,volume TEXT,author TEXT,publisher TEXT,published_at TEXT,material_id TEXT,url TEXT,isbn TEXT,image_path TEXT,review TEXT,UNIQUE(material_id,loan_date))"
    )


def normalize_row(row):
    return {k.replace("\ufeff", "").strip(): v.strip() for k, v in row.items()}


def record_exists(conn, mid, date):
    return (
        conn.execute(
            "SELECT 1 FROM loans WHERE material_id=? AND loan_date=?", (mid, date)
        ).fetchone()
        is not None
    )


def insert_loan(conn, row):
    data = normalize_row(row)
    if not data.get("資料ID", "") or record_exists(
        conn, data.get("資料ID", ""), data.get("貸出日", "")
    ):
        return False
    isbn = get_isbn(data.get("URL", ""))
    conn.execute(
        "INSERT INTO loans(title,loan_date,volume,author,publisher,published_at,material_id,url,isbn,image_path,review) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            data.get("タイトル", ""),
            data.get("貸出日", ""),
            data.get("巻情報", ""),
            data.get("著者", ""),
            data.get("出版社", ""),
            data.get("年月情報", ""),
            data.get("資料ID", ""),
            data.get("URL", ""),
            isbn,
            process_thumbnail(isbn),
            "",
        ),
    )
    return True


def fetch_all_loans(conn):
    return conn.execute(
        "SELECT id,title,author,publisher,loan_date,image_path,review FROM loans ORDER BY loan_date DESC"
    ).fetchall()
