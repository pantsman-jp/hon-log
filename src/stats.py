import re
from collections import Counter
from datetime import datetime


def parse_loan_date(s):
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"]:
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    m = re.search(r"(\d{4})[^0-9]?(\d{1,2})[^0-9]?(\d{1,2})", str(s))
    return datetime(*map(int, m.groups())).date() if m else None


def get_author_loan_counts(conn, limit=20):
    rows = conn.execute("SELECT author FROM loans WHERE author != ''").fetchall()
    return Counter(r[0].strip() for r in rows).most_common(limit)


def get_monthly_loan_counts(conn):
    rows = conn.execute("SELECT loan_date FROM loans WHERE loan_date != ''").fetchall()
    dates = filter(None, (parse_loan_date(r[0]) for r in rows))
    return sorted(Counter(d.strftime("%Y-%m") for d in dates).items())
