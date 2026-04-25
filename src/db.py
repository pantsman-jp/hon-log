import sqlite3
import os
from concurrent.futures import ThreadPoolExecutor
from src.isbn import get_isbn
from src.thumbnail import process_thumbnail, get_app_dir


def get_db_path():
    return os.path.join(get_app_dir(), "loans.db")


def connect_db():
    return sqlite3.connect(get_db_path())


def init_database(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS loans(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,author TEXT,publisher TEXT,loan_date TEXT,isbn TEXT,review TEXT,material_id TEXT,url TEXT,image_path TEXT,rating INTEGER,volume TEXT,published_at TEXT,tags TEXT,UNIQUE(material_id,loan_date))"
    )
    cursor = conn.execute("PRAGMA table_info(loans)")
    columns = [row[1] for row in cursor.fetchall()]
    if "rating" not in columns:
        conn.execute("ALTER TABLE loans ADD COLUMN rating INTEGER DEFAULT 0")
    if "volume" not in columns:
        conn.execute("ALTER TABLE loans ADD COLUMN volume TEXT")
    if "published_at" not in columns:
        conn.execute("ALTER TABLE loans ADD COLUMN published_at TEXT")
    if "tags" not in columns:
        conn.execute("ALTER TABLE loans ADD COLUMN tags TEXT")


def normalize_row(row):
    return {k.replace("\ufeff", "").strip(): v.strip() for [k, v] in row.items()}


def process_single_loan(row):
    data = normalize_row(row)
    mid = data.get("資料ID", "")
    date = data.get("貸出日", "")
    if mid == "":
        return None
    url = data.get("URL", "")
    isbn = get_isbn(url)
    query = data.get("タイトル", "") + " " + data.get("著者", "")
    img_path = process_thumbnail(isbn, query)
    return (
        data.get("タイトル", ""),
        data.get("著者", ""),
        data.get("出版社", ""),
        date,
        isbn,
        "",
        mid,
        url,
        img_path,
        0,
        data.get("巻情報", ""),
        data.get("年月情報", ""),
        "",
    )


def insert_loans_parallel(rows, callback):
    conn = connect_db()
    init_database(conn)
    total = len(rows)
    if total == 0:
        conn.close()
        return
    with ThreadPoolExecutor(max_workers=3) as executor:
        try:
            for [i, result] in enumerate(executor.map(process_single_loan, rows)):
                if result is not None:
                    conn.execute(
                        "INSERT OR IGNORE INTO loans(title,author,publisher,loan_date,isbn,review,material_id,url,image_path,rating,volume,published_at,tags) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        result,
                    )
                callback(i + 1, total)
        except Exception:
            pass
    conn.commit()
    conn.close()


def clear_database():
    conn = connect_db()
    conn.execute("DELETE FROM loans")
    conn.commit()
    conn.close()
