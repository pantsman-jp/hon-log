import re
from collections import Counter
from datetime import datetime


def parse_loan_date(date_str):
    if not date_str:
        return None
    date_str = date_str.strip()
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    m = re.search(r"(\d{4})[^0-9]?(\d{1,2})[^0-9]?(\d{1,2})", date_str)
    if m:
        year, month, day = map(int, m.groups())
        try:
            return datetime(year, month, day).date()
        except ValueError:
            pass
    return None


def get_author_loan_counts(conn, limit=20):
    rows = conn.execute(
        "SELECT author FROM loans WHERE author IS NOT NULL AND author != ''"
    ).fetchall()
    authors = [row[0].strip() for row in rows if row[0].strip()]
    counts = Counter(authors)
    most_common = counts.most_common(limit)
    return most_common


def get_monthly_loan_counts(conn):
    rows = conn.execute(
        "SELECT loan_date FROM loans WHERE loan_date IS NOT NULL AND loan_date != ''"
    ).fetchall()
    months = []
    for row in rows:
        date = parse_loan_date(row[0])
        if date is not None:
            months.append(date.strftime("%Y-%m"))
    counts = Counter(months)
    items = sorted(counts.items())
    return items
