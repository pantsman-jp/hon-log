import os
import sqlite3
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
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

from db import connect, initialize_db, update_review

DB_PATH = "loans.db"


def db_exists():
    return os.path.exists(DB_PATH)


def select_csv():
    dialog = QFileDialog()
    path, _ = dialog.getOpenFileName(filter="CSV Files (*.csv)")
    return path


def load_db():
    return connect(DB_PATH)


def fetch_rows(conn):
    cursor = conn.execute(
        "SELECT id, title, author, publisher, loan_date, image_path, review FROM loans ORDER BY loan_date DESC"
    )
    return list(cursor)


def create_image_label(path):
    label = QLabel()
    pixmap = QPixmap(path)
    label.setPixmap(pixmap.scaled(120, 160, Qt.KeepAspectRatio))
    return label


def create_title_label(title):
    label = QLabel(title)
    label.setWordWrap(True)
    label.setFixedWidth(120)
    return label


def build_tooltip(row):
    return f"{row[1]}\n{row[2]}\n{row[3]}\n{row[4]}"


def open_review_dialog(row_id, current_review):
    dialog = QDialog()
    layout = QVBoxLayout()
    text = QTextEdit()
    text.setText(current_review)
    btn = QPushButton("保存")

    def save():
        with connect(DB_PATH) as conn:
            update_review(conn, row_id, text.toPlainText())
            conn.commit()
        dialog.accept()

    btn.clicked.connect(save)
    layout.addWidget(text)
    layout.addWidget(btn)
    dialog.setLayout(layout)
    dialog.exec()


def create_book_widget(row):
    widget = QWidget()
    layout = QVBoxLayout()
    img = create_image_label(row[5])
    title = create_title_label(row[1])
    img.setToolTip(build_tooltip(row))
    img.mousePressEvent = lambda event: open_review_dialog(row[0], row[6])
    layout.addWidget(img)
    layout.addWidget(title)
    widget.setLayout(layout)
    return widget


def populate_grid(grid, rows):
    for i, row in enumerate(rows):
        widget = create_book_widget(row)
        grid.addWidget(widget, i // 5, i % 5)


def create_main_widget(rows):
    main = QWidget()
    layout = QVBoxLayout()
    scroll = QScrollArea()
    container = QWidget()
    grid = QGridLayout()
    populate_grid(grid, rows)
    container.setLayout(grid)
    scroll.setWidget(container)
    scroll.setWidgetResizable(True)
    update_btn = QPushButton("更新")

    def update_action():
        csv_path = select_csv()
        if csv_path != "":
            initialize_db(DB_PATH, csv_path)
            reload_ui(main)

    update_btn.clicked.connect(update_action)
    layout.addWidget(update_btn)
    layout.addWidget(scroll)
    main.setLayout(layout)
    return main


def reload_ui(main_widget):
    conn = load_db()
    rows = fetch_rows(conn)

    new_widget = create_main_widget(rows)
    main_widget.layout().addWidget(new_widget)


def initialize_if_needed():
    if db_exists():
        return
    csv_path = select_csv()
    if csv_path != "":
        initialize_db(DB_PATH, csv_path)


def main():
    app = QApplication([])
    initialize_if_needed()
    conn = load_db()
    rows = fetch_rows(conn)
    widget = create_main_widget(rows)
    widget.resize(800, 600)
    widget.show()
    app.exec()


if __name__ == "__main__":
    main()
