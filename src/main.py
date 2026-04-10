import sys
import os
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.db import (
    connect,
    fetch_rows,
    initialize_db,
    update_review,
)
from src.utils import get_data_path, resource_path

DB_PATH = get_data_path("loans.db")


class BookBrowser(QWidget):
    def __init__(self):
        super().__init__()
        self.conn = None
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.scroll_area = QScrollArea()
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_container.setLayout(self.grid_layout)
        self.scroll_area.setWidget(self.grid_container)
        self.scroll_area.setWidgetResizable(True)
        self.update_button = QPushButton("更新")
        self.update_button.clicked.connect(self.on_update)
        self.main_layout.addWidget(self.update_button)
        self.main_layout.addWidget(self.scroll_area)
        self.initialize_db_if_needed()
        self.load_db()
        self.reload_ui()

    def initialize_db_if_needed(self):
        if not os.path.exists(DB_PATH):
            csv_path = self.select_csv()
            if csv_path:
                initialize_db(DB_PATH, csv_path)

    def select_csv(self):
        dialog = QFileDialog()
        path, _ = dialog.getOpenFileName(filter="CSV Files (*.csv)")
        return path

    def load_db(self):
        self.conn = connect(DB_PATH)

    def reload_ui(self):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        rows = fetch_rows(self.conn)
        self.populate_grid(rows)

    def populate_grid(self, rows):
        for [i, row] in enumerate(rows):
            widget = self.create_book_widget(row)
            self.grid_layout.addWidget(widget, i // 5, i % 5)

    def create_book_widget(self, row):
        widget = QWidget()
        layout = QVBoxLayout()
        img_label = self.create_image_label(row[5])
        img_label.setToolTip(self.build_tooltip(row))
        img_label.mousePressEvent = lambda event, r=row: self.open_review_dialog(
            r[0], r[6]
        )
        title_label = QLabel(row[1])
        title_label.setWordWrap(True)
        title_label.setFixedWidth(120)
        layout.addWidget(img_label)
        layout.addWidget(title_label)
        widget.setLayout(layout)
        return widget

    def create_image_label(self, path):
        label = QLabel()
        full_path = resource_path(path)
        pixmap = QPixmap(full_path)
        if pixmap.isNull():
            fallback_path = resource_path("assets/img/no-image.png")
            pixmap = QPixmap(fallback_path)
        label.setPixmap(pixmap.scaled(120, 160, Qt.KeepAspectRatio))
        return label

    def build_tooltip(self, row):
        return f"{row[1]}\n{row[2]}\n{row[3]}\n{row[4]}"

    def open_review_dialog(self, row_id, current_review):
        dialog = QDialog(self)
        layout = QVBoxLayout(dialog)
        text = QTextEdit()
        text.setText(current_review)
        save_btn = QPushButton("保存")

        def save():
            update_review(self.conn, row_id, text.toPlainText())
            self.conn.commit()
            dialog.accept()
            self.reload_ui()

        save_btn.clicked.connect(save)
        layout.addWidget(text)
        layout.addWidget(save_btn)
        dialog.setLayout(layout)
        dialog.exec()

    def on_update(self):
        csv_path = self.select_csv()
        if csv_path:
            initialize_db(DB_PATH, csv_path)
            self.load_db()
            self.reload_ui()


def main():
    app = QApplication([])
    icon_path = resource_path(os.path.join("assets", "img", "favicon.ico"))
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
        app.setWindowIcon(icon)
    browser = BookBrowser()
    if os.path.exists(icon_path):
        browser.setWindowIcon(QIcon(icon_path))
    browser.resize(800, 600)
    browser.show()
    app.exec()


if __name__ == "__main__":
    main()
