import sys
import os
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QGridLayout,
    QLabel,
    QFileDialog,
    QDialog,
    QTextEdit,
    QProgressBar,
    QScrollArea,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from src.db import (
    connect_db,
    create_table,
    fetch_all_loans,
    get_db_path,
    insert_loans_parallel,
)
import csv
from src.thumbnail import get_image_dir

VERSION = "v1.3.1"


def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


class ImportWorker(QThread):
    progress = Signal(int, int)
    finished = Signal()

    def __init__(self, csv_path):
        super().__init__()
        self.csv_path = csv_path

    def run(self):
        rows = list(csv.DictReader(open(self.csv_path, encoding="utf-8-sig")))
        insert_loans_parallel(rows, self.progress.emit)
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
        no_image = resource_path(os.path.join("assets", "img", "no-image.png"))
        isbn = self.row[5]
        img_path = no_image
        if isbn:
            for ext in [".jpeg", ".jpg"]:
                p = os.path.join(get_image_dir(), f"{isbn}{ext}")
                if os.path.exists(p):
                    img_path = p
                    break
        pix = QPixmap(img_path)
        if pix.isNull():
            pix = QPixmap(no_image)
        img_label.setPixmap(
            pix.scaled(120, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        img_label.mousePressEvent = lambda e: on_click(self.row[0], self.row[6])
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
        if path:
            self.start_import(path)

    def start_import(self, path):
        self.progress_bar.setVisible(True)
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
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        conn = connect_db()
        create_table(conn)
        for i, row in enumerate(fetch_all_loans(conn)):
            self.grid_layout.addWidget(BookWidget(row, self.edit_review), i // 5, i % 5)
        conn.close()

    def edit_review(self, db_id, current_review):
        dialog = QDialog(self)
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        if current_review:
            text_edit.setText(current_review)
        else:
            text_edit.setText("")
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(
            lambda: self.save_review(dialog, db_id, text_edit.toPlainText())
        )
        layout.addWidget(text_edit)
        layout.addWidget(save_btn)
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
