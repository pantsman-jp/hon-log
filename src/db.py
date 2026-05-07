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
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_database(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS loans("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "title TEXT, author TEXT, publisher TEXT, loan_date TEXT,"
        "isbn TEXT, review TEXT, material_id TEXT, url TEXT,"
        "image_path TEXT, rating INTEGER, volume TEXT,"
        "published_at TEXT, tags TEXT, UNIQUE(material_id,loan_date))"
    )
    columns = [row[1] for row in conn.execute("PRAGMA table_info(loans)").fetchall()]
    [
        conn.execute(f"ALTER TABLE loans ADD COLUMN {c} {t}")
        for c, t in [
            ("rating", "INTEGER DEFAULT 0"),
            ("volume", "TEXT"),
            ("published_at", "TEXT"),
            ("tags", "TEXT"),
        ]
        if c not in columns
    ]


def normalize_row(row):
    return {k.replace("\ufeff", "").strip(): (v or "").strip() for k, v in row.items()}


def process_single_loan(row):
    data = normalize_row(row)
    if not data.get("資料ID"):
        return None
    html = get_html(data.get("URL", ""))
    isbn = get_isbn(data.get("URL", ""), html)
    img_path = process_thumbnail(
        isbn,
        " ".join(
            filter(None, [data.get("タイトル", ""), data.get("著者", "")])
        ).strip(),
        extract_image_url(html),
    )
    return (
        data.get("タイトル", ""),
        data.get("著者", ""),
        data.get("出版社", ""),
        data.get("貸出日", ""),
        isbn,
        "",
        data.get("資料ID", ""),
        data.get("URL", ""),
        img_path,
        0,
        data.get("巻情報", ""),
        data.get("年月情報", ""),
        "",
    )


def insert_loans_parallel(rows, callback):
    conn = connect_db()
    init_database(conn)
    if not rows:
        conn.close()
        return
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_single_loan, row) for row in rows]
        results = [
            f.result()
            for i, f in enumerate(as_completed(futures), 1)
            if (callback(int(i / len(rows) * 100)) or True) and f.result()
        ]
    if results:
        conn.executemany(LOAN_INSERT_SQL, results)
    conn.commit()
    conn.close()


def clear_database():
    conn = connect_db()
    conn.execute("DELETE FROM loans")
    conn.commit()
    conn.close()
