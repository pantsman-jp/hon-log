import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.isbn import extract_image_url, get_html, get_isbn
from src.thumbnail import get_app_dir, process_thumbnail

LOAN_INSERT_SQL = """INSERT OR IGNORE INTO loans(
    title, author, publisher, loan_date, isbn, review, material_id,
    url, image_path, rating, volume, published_at, tags
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""


def get_db_path():
    app_dir = get_app_dir()
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, "loans.db")


def connect_db():
    return sqlite3.connect(get_db_path())


def init_database(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS loans("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "title TEXT,"
        "author TEXT,"
        "publisher TEXT,"
        "loan_date TEXT,"
        "isbn TEXT,"
        "review TEXT,"
        "material_id TEXT,"
        "url TEXT,"
        "image_path TEXT,"
        "rating INTEGER,"
        "volume TEXT,"
        "published_at TEXT,"
        "tags TEXT,"
        "UNIQUE(material_id,loan_date)"
        ")"
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
    return {
        k.replace("\ufeff", "").strip(): (v or "").strip() for [k, v] in row.items()
    }


def process_single_loan(row):
    data = normalize_row(row)
    material_id = data.get("資料ID", "")
    if material_id == "":
        return None
    url = data.get("URL", "")
    html = get_html(url)
    isbn = get_isbn(url, html)
    query = " ".join(
        filter(None, [data.get("タイトル", ""), data.get("著者", "")])
    ).strip()
    img_url = extract_image_url(html)
    img_path = process_thumbnail(isbn, query, img_url)
    return (
        data.get("タイトル", ""),
        data.get("著者", ""),
        data.get("出版社", ""),
        data.get("貸出日", ""),
        isbn,
        "",
        material_id,
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
    with ThreadPoolExecutor(max_workers=min(3, total)) as executor:
        futures = [executor.submit(process_single_loan, row) for row in rows]
        completed = 0
        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception:
                result = None
            if result is not None:
                conn.execute(LOAN_INSERT_SQL, result)
            completed += 1
            callback(completed, total)
    conn.commit()
    conn.close()


def clear_database():
    conn = connect_db()
    conn.execute("DELETE FROM loans")
    conn.commit()
    conn.close()
