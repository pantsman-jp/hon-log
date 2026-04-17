import sqlite3
import os
from concurrent.futures import ThreadPoolExecutor
from src.isbn import get_isbn
from src.thumbnail import process_thumbnail, get_app_dir


def get_db_path():
    return os.path.join(get_app_dir(), "loans.db")


def connect_db():
    return sqlite3.connect(get_db_path())


def create_table(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        author TEXT,
        publisher TEXT,
        loan_date TEXT,
        isbn TEXT,
        review TEXT,
        material_id TEXT,
        url TEXT,
        image_path TEXT,
        rating INTEGER DEFAULT 0
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_loan_date ON loans(loan_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rating ON loans(rating)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_review ON loans(review)")
    conn.commit()


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
    img_path = process_thumbnail(isbn)
    return (
        data.get("タイトル", ""),
        date,
        data.get("巻情報", ""),
        data.get("著者", ""),
        data.get("出版社", ""),
        data.get("年月情報", ""),
        mid,
        url,
        isbn,
        img_path,
        "",
    )


def insert_loans_parallel(rows, callback):
    conn = connect_db()
    create_table(conn)
    total = len(rows)
    if total == 0:
        conn.close()
        return
    with ThreadPoolExecutor(max_workers=10) as executor:
        try:
            for [i, result] in enumerate(executor.map(process_single_loan, rows)):
                if result is not None:
                    conn.execute(
                        "INSERT OR IGNORE INTO loans(title,loan_date,volume,author,publisher,published_at,material_id,url,isbn,image_path,review) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        result,
                    )
                callback(i + 1, total)
        except Exception:
            pass
    conn.commit()
    conn.close()
    cleanup_duplicates()


def cleanup_duplicates():
    conn = connect_db()
    conn.execute(
        "DELETE FROM loans WHERE id NOT IN (SELECT id FROM loans GROUP BY material_id HAVING MAX(loan_date))"
    )
    conn.commit()
    conn.close()


def fetch_all_loans(conn):
    return conn.execute(
        "SELECT id, title, author, publisher, loan_date, isbn, review, material_id, url, image_path FROM loans ORDER BY loan_date DESC"
    ).fetchall()
