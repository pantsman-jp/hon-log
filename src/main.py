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
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from src.db import (
    connect_db,
    create_table,
    fetch_all_loans,
    get_db_path,
    insert_loans_parallel,
    cleanup_duplicates,
)
from src.utils import resource_path

VERSION = "v1.4.0"


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
        no_image = resource_path("assets", "img", "no-image.png")
        path_in_row = self.row[9]
        img_path = no_image
        if path_in_row != "":
            if os.path.exists(path_in_row):
                img_path = path_in_row
        pix = QPixmap(img_path)
        if pix.isNull():
            pix = QPixmap(no_image)
        img_label.setPixmap(
            pix.scaled(120, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        img_label.mousePressEvent = lambda e: on_click(self.row[0])
        layout.addWidget(img_label, alignment=Qt.AlignCenter)
        title = QLabel(self.row[1])
        title.setFixedWidth(120)
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignCenter)


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"ほんろぐ {VERSION}")
        self.resize(1000, 700)
        self.main_layout = QVBoxLayout(self)
        self.btn_update = QPushButton("新規追加 / 更新")
        self.btn_update.clicked.connect(self.select_csv)
        self.main_layout.addWidget(self.btn_update)
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
        if os.path.exists(get_db_path()):
            self.refresh_grid()

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
        cleanup_duplicates()
        conn = connect_db()
        create_table(conn)
        rows = fetch_all_loans(conn)
        for [i, row] in enumerate(rows):
            self.grid_layout.addWidget(BookWidget(row, self.show_detail), i // 5, i % 5)
        conn.close()

    def show_detail(self, db_id):
        conn = connect_db()
        book = conn.execute(
            "SELECT title, author, publisher, loan_date, isbn, review, material_id, url, image_path FROM loans WHERE id=?",
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
        no_image = resource_path("assets", "img", "no-image.png")
        path_in_db = book[8]
        img_path = no_image
        if path_in_db != "":
            if os.path.exists(path_in_db):
                img_path = path_in_db
        pix = QPixmap(img_path)
        if pix.isNull():
            pix = QPixmap(no_image)
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
        isbn_val = book[4]
        if isbn_val == "":
            isbn_val = "なし"
        form_layout.addRow("ISBN:", QLabel(isbn_val))
        form_layout.addRow("資料ID:", QLabel(book[6]))
        url_label = QLabel(f'<a href="{book[7]}">図書館詳細ページへ</a>')
        url_label.setOpenExternalLinks(True)
        form_layout.addRow("URL:", url_label)
        right_layout.addWidget(form_frame)
        right_layout.addWidget(QLabel("感想 / レビュー:"))
        text_edit = QTextEdit()
        review_text = book[5]
        if review_text is None:
            review_text = ""
        text_edit.setText(review_text)
        right_layout.addWidget(text_edit)
        save_btn = QPushButton("変更を保存")
        save_btn.clicked.connect(
            lambda: self.save_review(dialog, db_id, text_edit.toPlainText())
        )
        right_layout.addWidget(save_btn)
        main_h_layout.addLayout(right_layout)
        dialog.exec()

    def save_review(self, dialog, db_id, text):
        conn = connect_db()
        conn.execute("UPDATE loans SET review=? WHERE id=?", (text, db_id))
        conn.commit()
        conn.close()
        dialog.accept()
        self.refresh_grid()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
