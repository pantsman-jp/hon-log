import csv
import os
import sys
import webbrowser
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
    QLineEdit,
    QMessageBox,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from src.db import (
    clear_database,
    connect_db,
    init_database,
    insert_loans_parallel,
)
from src.utils import get_latest_version, resource_path

VERSION = "v2.1.2"
REPO_URL = "pantsman-jp/hon-log"


class UpdateChecker(QThread):
    new_version_found = Signal(str)

    def run(self):
        latest = get_latest_version(REPO_URL)
        if latest and latest != VERSION:
            self.new_version_found.emit(latest)


class ImportWorker(QThread):
    progress = Signal(int)
    finished = Signal()

    def __init__(self, csv_path):
        super().__init__()
        self.csv_path = csv_path

    def run(self):
        try:
            with open(self.csv_path, encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
            insert_loans_parallel(
                rows, lambda c, t: self.progress.emit(int(c / t * 100))
            )
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
        if self.row[9] and os.path.exists(self.row[9]):
            img_path = self.row[9]
        pix = QPixmap(img_path)
        if pix.isNull():
            pix = QPixmap(resource_path("assets", "img", "no-image.png"))
        img_label.setPixmap(
            pix.scaled(120, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        img_label.mousePressEvent = lambda e: on_click(self.row[7])
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
            pix = QPixmap(resource_path("assets", "img", icon_name))
            if pix.isNull():
                pix = QPixmap(32, 32)
                pix.fill(Qt.transparent)
            star.setPixmap(
                pix.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            star.setCursor(Qt.PointingHandCursor)
            star.mousePressEvent = lambda e, val=i: self.set_rating(val)
            self.star_layout.addWidget(star)
            self.stars.append(star)

    def set_rating(self, val):
        self.rating = 0 if val == self.rating else val
        self.refresh_stars()

    def get_rating(self):
        return self.rating


class App(QWidget):
    def __init__(self):
        super().__init__()
        conn = connect_db()
        init_database(conn)
        conn.close()
        self.setWindowTitle(f"ほんろぐ {VERSION}")
        self.resize(1100, 800)
        self.main_layout = QVBoxLayout(self)
        self.update_info_bar = QFrame()
        self.update_info_bar.setVisible(False)
        self.update_info_bar.setStyleSheet(
            "background-color: #fff3cd; border-bottom: 1px solid #ffeeba;"
        )
        update_layout = QHBoxLayout(self.update_info_bar)
        self.update_label = QLabel()
        update_layout.addWidget(self.update_label)
        btn_download = QPushButton("ダウンロード")
        btn_download.clicked.connect(
            lambda: webbrowser.open(f"https://github.com/{REPO_URL}/releases/latest")
        )
        update_layout.addWidget(btn_download)
        update_layout.addStretch()
        self.main_layout.addWidget(self.update_info_bar)
        self.control_layout = QHBoxLayout()
        self.btn_update = QPushButton("新規追加 / 更新")
        self.btn_update.clicked.connect(self.select_csv)
        self.control_layout.addWidget(self.btn_update)
        self.btn_clear = QPushButton("全削除")
        self.btn_clear.clicked.connect(self.confirm_clear_db)
        self.control_layout.addWidget(self.btn_clear)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["すべて表示", "感想あり", "未入力のみ"])
        self.filter_combo.currentIndexChanged.connect(self.refresh_grid)
        self.control_layout.addWidget(QLabel(" 絞り込み:"))
        self.control_layout.addWidget(self.filter_combo)
        self.tag_combo = QComboBox()
        self.tag_combo.currentIndexChanged.connect(self.refresh_grid)
        self.control_layout.addWidget(QLabel(" タグ:"))
        self.control_layout.addWidget(self.tag_combo)
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
        self.refresh_tag_combo()
        self.refresh_grid()
        self.check_updates()

    def check_updates(self):
        self.update_checker = UpdateChecker()
        self.update_checker.new_version_found.connect(self.show_update_bar)
        self.update_checker.start()

    def show_update_bar(self, latest_version):
        self.update_label.setText(f"新しいバージョン {latest_version} が利用可能です。")
        self.update_info_bar.setVisible(True)

    def refresh_tag_combo(self):
        self.tag_combo.blockSignals(True)
        self.tag_combo.clear()
        self.tag_combo.addItem("すべてのタグ")
        conn = connect_db()
        rows = conn.execute(
            "SELECT tags FROM loans WHERE tags IS NOT NULL AND tags != ''"
        ).fetchall()
        conn.close()
        unique_tags = sorted(
            list(set(t.strip() for r in rows for t in r[0].split(",") if t.strip()))
        )
        self.tag_combo.addItems(unique_tags)
        self.tag_combo.blockSignals(False)

    def select_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "CSV選択", "", "CSV (*.csv)")
        if path != "":
            self.start_import(path)

    def start_import(self, path):
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        QApplication.processEvents()
        self.worker = ImportWorker(path)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_import_finished)
        self.worker.start()

    def on_import_finished(self):
        self.progress_bar.setVisible(False)
        self.refresh_tag_combo()
        self.refresh_grid()

    def confirm_clear_db(self):
        reply = QMessageBox.question(
            self,
            "確認",
            "データベース内のすべての貸出記録を削除しますか？\n（取得した書影画像は削除されません）",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            clear_database()
            self.refresh_tag_combo()
            self.refresh_grid()

    def clear_layout(self, layout):
        while layout.count() > 0:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def refresh_grid(self):
        self.clear_layout(self.grid_layout)
        query = "SELECT id, title, author, publisher, loan_date, isbn, review, material_id, url, image_path, rating, volume, published_at, tags FROM loans"
        conds = []
        params = []
        if self.filter_combo.currentIndex() == 1:
            conds.append("(review IS NOT NULL AND review != '')")
        elif self.filter_combo.currentIndex() == 2:
            conds.append("(review IS NULL OR review = '')")
        if self.tag_combo.currentIndex() > 0:
            conds.append("tags LIKE ?")
            params.append(f"%{self.tag_combo.currentText()}%")
        if conds:
            query += " WHERE " + " AND ".join(conds)
        query += " GROUP BY material_id"
        sort_map = {
            0: "MAX(loan_date) DESC",
            1: "MAX(loan_date) ASC",
            2: "rating DESC, MAX(loan_date) DESC",
            3: "title ASC",
        }
        query += f" ORDER BY {sort_map.get(self.sort_combo.currentIndex(), 'MAX(loan_date) DESC')}"
        conn = connect_db()
        rows = conn.execute(query, params).fetchall()
        conn.close()
        for i, row in enumerate(rows):
            self.grid_layout.addWidget(BookWidget(row, self.show_detail), i // 5, i % 5)

    def show_detail(self, material_id):
        conn = connect_db()
        book = conn.execute(
            "SELECT title, author, publisher, loan_date, isbn, review, material_id, url, image_path, rating, tags, volume, published_at FROM loans WHERE material_id=?",
            (material_id,),
        ).fetchone()
        dates_rows = conn.execute(
            "SELECT loan_date FROM loans WHERE material_id=? ORDER BY loan_date DESC",
            (material_id,),
        ).fetchall()
        dates = [r[0] for r in dates_rows]
        conn.close()
        if book is None:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("書籍詳細")
        dialog.setMinimumWidth(600)
        main_h = QHBoxLayout(dialog)
        left = QVBoxLayout()
        img_l = QLabel()
        img_p = resource_path("assets", "img", "no-image.png")
        if book[8] and os.path.exists(book[8]):
            img_p = book[8]
        pix = QPixmap(img_p)
        if pix.isNull():
            pix = QPixmap(resource_path("assets", "img", "no-image.png"))
        img_l.setPixmap(
            pix.scaled(200, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        left.addWidget(img_l, alignment=Qt.AlignTop)
        left.addStretch()
        main_h.addLayout(left)
        right = QVBoxLayout()
        form_f = QFrame()
        form_l = QFormLayout(form_f)
        form_l.addRow("タイトル:", QLabel(book[0]))
        form_l.addRow("著者:", QLabel(book[1]))
        form_l.addRow("出版社:", QLabel(book[2]))
        form_l.addRow("巻情報:", QLabel(book[11] if book[11] else "-"))
        form_l.addRow("出版年月:", QLabel(book[12] if book[12] else "-"))
        form_l.addRow("貸出履歴:", QLabel(", ".join(dates)))
        form_l.addRow("ISBN:", QLabel(book[4] if book[4] else "なし"))
        form_l.addRow("資料ID:", QLabel(book[6]))
        url_l = QLabel(f'<a href="{book[7]}">図書館詳細ページへ</a>')
        url_l.setOpenExternalLinks(True)
        form_l.addRow("URL:", url_l)
        star = StarRatingWidget(book[9] if book[9] is not None else 0)
        form_l.addRow("評価:", star)
        tag_e = QLineEdit()
        tag_e.setPlaceholderText("コンマ区切り (例: 技術書, Python)")
        tag_e.setText(book[10] if book[10] else "")
        form_l.addRow("タグ:", tag_e)
        right.addWidget(form_f)
        right.addWidget(QLabel("感想 / レビュー:"))
        text_e = QTextEdit()
        text_e.setText(book[5] if book[5] else "")
        right.addWidget(text_e)
        save_b = QPushButton("変更を保存")
        save_b.clicked.connect(
            lambda: self.save_data(
                dialog,
                material_id,
                text_e.toPlainText(),
                star.get_rating(),
                tag_e.text(),
            )
        )
        right.addWidget(save_b)
        main_h.addLayout(right)
        dialog.exec()

    def save_data(self, dialog, material_id, text, rating, tags):
        conn = connect_db()
        conn.execute(
            "UPDATE loans SET review=?, rating=?, tags=? WHERE material_id=?",
            (text, rating, tags, material_id),
        )
        conn.commit()
        conn.close()
        dialog.accept()
        self.refresh_tag_combo()
        self.refresh_grid()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
