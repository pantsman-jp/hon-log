import sys
import os
import csv
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGridLayout,
    QLabel,
    QFileDialog,
    QDialog,
    QTextEdit,
    QProgressBar,
    QScrollArea,
    QFormLayout,
    QFrame,
    QComboBox,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from src.db import (
    connect_db,
    create_table,
    insert_loans_parallel,
    cleanup_duplicates,
)
from src.utils import resource_path

VERSION = "v1.7.1"
IMAGE_CACHE = {}


class ImportWorker(QThread):
    progress = Signal(int, int)
    finished = Signal()

    def __init__(self, csv_path):
        super().__init__()
        self.csv_path = csv_path

    def run(self):
        try:
            with open(self.csv_path, encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
            insert_loans_parallel(rows, self.progress.emit)
        except Exception:
            pass
        finally:
            self.finished.emit()


class BookWidget(QWidget):
    def __init__(self, row, on_click):
        super().__init__()
        self.row = row
        self.init_ui(on_click)

    def init_ui(self, on_click):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(10, 10, 10, 10)
        img_label = QLabel()
        img_path = resource_path("assets", "img", "no-image.png")
        if self.row[9] != "" and os.path.exists(self.row[9]):
            img_path = self.row[9]
        # キャッシュのチェック
        if img_path in IMAGE_CACHE:
            pix = IMAGE_CACHE[img_path]
        else:
            original_pix = QPixmap(img_path)
            if original_pix.isNull():
                original_pix = QPixmap(resource_path("assets", "img", "no-image.png"))
            pix = original_pix.scaled(
                120, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            IMAGE_CACHE[img_path] = pix
        img_label.setPixmap(pix)
        img_label.mousePressEvent = lambda e: on_click(self.row[0])
        layout.addWidget(img_label, alignment=Qt.AlignCenter)
        title_label = QLabel(self.row[1])
        title_label.setFixedWidth(120)
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label, alignment=Qt.AlignCenter)


class StarRatingWidget(QWidget):
    def __init__(self, initial_rating=0):
        super().__init__()
        self.rating = initial_rating
        self.stars = []
        self.init_ui()

    def init_ui(self):
        self.star_layout = QHBoxLayout(self)
        self.star_layout.setContentsMargins(0, 0, 0, 0)
        self.star_layout.setSpacing(5)
        self.refresh_stars()

    def refresh_stars(self):
        while self.star_layout.count() > 0:
            item = self.star_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.stars = []
        for i in range(1, 6):
            star = QLabel()
            icon_name = "star-on.png" if i <= self.rating else "star-off.png"
            icon_path = resource_path("assets", "img", icon_name)
            if icon_path in IMAGE_CACHE:
                pix = IMAGE_CACHE[icon_path]
            else:
                raw_pix = QPixmap(icon_path)
                if raw_pix.isNull():
                    raw_pix = QPixmap(32, 32)
                    raw_pix.fill(Qt.transparent)
                pix = raw_pix.scaled(
                    32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                IMAGE_CACHE[icon_path] = pix
            star.setPixmap(pix)
            star.setCursor(Qt.PointingHandCursor)
            star.mousePressEvent = lambda e, val=i: self.set_rating(val)
            self.star_layout.addWidget(star)
            self.stars.append(star)

    def set_rating(self, val):
        if val == self.rating:
            self.rating = 0
        else:
            self.rating = val
        self.refresh_stars()

    def get_rating(self):
        return self.rating


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.ensure_rating_column()
        self.setWindowTitle(f"ほんろぐ {VERSION}")
        self.resize(1100, 800)
        self.main_layout = QVBoxLayout(self)
        self.control_layout = QHBoxLayout()
        self.btn_update = QPushButton("新規追加 / 更新")
        self.btn_update.clicked.connect(self.select_csv)
        self.control_layout.addWidget(self.btn_update)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["すべて表示", "感想あり", "未入力のみ"])
        self.filter_combo.currentIndexChanged.connect(self.refresh_grid)
        self.control_layout.addWidget(QLabel(" 絞り込み:"))
        self.control_layout.addWidget(self.filter_combo)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(
            ["日付が新しい順", "日付が古い順", "評価が高い順", "タイトル順"]
        )
        self.sort_combo.currentIndexChanged.connect(self.refresh_grid)
        self.control_layout.addWidget(QLabel(" 並び替え:"))
        self.control_layout.addWidget(self.sort_combo)
        self.main_layout.addLayout(self.control_layout)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(20)
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.scroll.setWidget(self.grid_container)
        self.main_layout.addWidget(self.scroll)
        self.refresh_grid()

    def ensure_rating_column(self):
        conn = connect_db()
        create_table(conn)
        try:
            conn.execute("ALTER TABLE loans ADD COLUMN rating INTEGER DEFAULT 0")
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def select_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "CSV選択", "", "CSV (*.csv)")
        if path != "":
            self.start_import(path)

    def start_import(self, path):
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        QApplication.processEvents()
        self.worker = ImportWorker(path)
        self.worker.progress.connect(
            lambda c, t: self.progress_bar.setValue(int(c / t * 100))
        )
        self.worker.finished.connect(self.on_import_finished)
        self.worker.start()

    def on_import_finished(self):
        self.progress_bar.setVisible(False)
        self.refresh_grid()

    def refresh_grid(self):
        while self.grid_layout.count() > 0:
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        conn = connect_db()
        create_table(conn)
        conn.close()
        cleanup_duplicates()
        query = "SELECT id, title, author, publisher, loan_date, isbn, review, material_id, url, image_path, rating FROM loans"
        conditions = []
        if self.filter_combo.currentIndex() == 1:
            conditions.append("(review IS NOT NULL AND review != '')")
        elif self.filter_combo.currentIndex() == 2:
            conditions.append("(review IS NULL OR review = '')")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        sort_map = {
            0: "loan_date DESC",
            1: "loan_date ASC",
            2: "rating DESC, loan_date DESC",
            3: "title ASC",
        }
        query += f" ORDER BY {sort_map.get(self.sort_combo.currentIndex(), 'loan_date DESC')}"
        conn = connect_db()
        for [i, row] in enumerate(conn.execute(query).fetchall()):
            self.grid_layout.addWidget(BookWidget(row, self.show_detail), i // 5, i % 5)
        conn.close()

    def show_detail(self, db_id):
        conn = connect_db()
        book = conn.execute(
            "SELECT title, author, publisher, loan_date, isbn, review, material_id, url, image_path, rating FROM loans WHERE id=?",
            (db_id,),
        ).fetchone()
        conn.close()
        if book is None:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("書籍詳細")
        dialog.setMinimumWidth(600)
        main_h_layout = QHBoxLayout(dialog)
        left_layout = QVBoxLayout()
        img_label = QLabel()
        img_path = resource_path("assets", "img", "no-image.png")
        if (book[8] != "") and os.path.exists(book[8]):
            img_path = book[8]
        pix = QPixmap(img_path)
        if pix.isNull():
            pix = QPixmap(resource_path("assets", "img", "no-image.png"))
        img_label.setPixmap(
            pix.scaled(200, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        left_layout.addWidget(img_label, alignment=Qt.AlignTop)
        left_layout.addStretch()
        main_h_layout.addLayout(left_layout)
        right_layout = QVBoxLayout()
        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.addRow("タイトル:", QLabel(book[0]))
        form_layout.addRow("著者:", QLabel(book[1]))
        form_layout.addRow("出版社:", QLabel(book[2]))
        form_layout.addRow("貸出日:", QLabel(book[3]))
        isbn_val = book[4] if book[4] != "" else "なし"
        form_layout.addRow("ISBN:", QLabel(isbn_val))
        form_layout.addRow("資料ID:", QLabel(book[6]))
        url_label = QLabel(f'<a href="{book[7]}">図書館詳細ページへ</a>')
        url_label.setOpenExternalLinks(True)
        form_layout.addRow("URL:", url_label)
        star_rating = StarRatingWidget(book[9] if book[9] is not None else 0)
        form_layout.addRow("評価:", star_rating)
        right_layout.addWidget(form_frame)
        right_layout.addWidget(QLabel("感想 / レビュー:"))
        text_edit = QTextEdit()
        text_edit.setText(book[5] if book[5] is not None else "")
        right_layout.addWidget(text_edit)
        save_btn = QPushButton("変更を保存")
        save_btn.clicked.connect(
            lambda: self.save_data(
                dialog, db_id, text_edit.toPlainText(), star_rating.get_rating()
            )
        )
        right_layout.addWidget(save_btn)
        main_h_layout.addLayout(right_layout)
        dialog.exec()

    def save_data(self, dialog, db_id, text, rating):
        conn = connect_db()
        conn.execute(
            "UPDATE loans SET review=?, rating=? WHERE id=?", (text, rating, db_id)
        )
        conn.commit()
        conn.close()
        dialog.accept()
        self.refresh_grid()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
