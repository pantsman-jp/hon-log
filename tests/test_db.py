import sqlite3
import unittest

from src.db import LOAN_INSERT_SQL, init_database


class DatabaseTests(unittest.TestCase):
    def test_reimport_updates_an_existing_cover_path(self):
        row = (
            "書名",
            "著者",
            "出版社",
            "2026-10-01",
            "9784003101018",
            "",
            "material-1",
            "https://opac.example.test/book/1",
            "/tmp/old.jpeg",
            0,
            "",
            "",
            "",
        )
        conn = sqlite3.connect(":memory:")
        init_database(conn)
        conn.execute(LOAN_INSERT_SQL, row)
        conn.execute(LOAN_INSERT_SQL, (*row[:8], "/tmp/new-v2.jpeg", *row[9:]))

        image_path = conn.execute("SELECT image_path FROM loans").fetchone()[0]
        self.assertEqual(image_path, "/tmp/new-v2.jpeg")


if __name__ == "__main__":
    unittest.main()
