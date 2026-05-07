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
import matplotlib as mpl
import matplotlib.font_manager as font_manager
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from src.db import clear_database, connect_db, init_database, insert_loans_parallel
from src.stats import get_author_loan_counts, get_monthly_loan_counts
from src.utils import get_latest_version, resource_path


def choose_japanese_font():
    installed = set(font_manager.get_font_names())
    candidates = [
        "MS Gothic",
        "Yu Gothic",
        "Meiryo",
        "Hiragino Sans",
        "IPAexGothic",
        "Noto Sans CJK JP",
        "DejaVu Sans",
    ]
    return next((f for f in candidates if f in installed), "sans-serif")


JAPANESE_FONT = choose_japanese_font()
mpl.rcParams["font.family"] = JAPANESE_FONT
mpl.rcParams["axes.unicode_minus"] = False
VERSION = "v2.2.1"
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
                insert_loans_parallel(
                    list(csv.DictReader(f)), lambda p: self.progress.emit(p)
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
        img_label = QLabel()
        path = (
            self.row[9]
            if self.row[9] and os.path.exists(self.row[9])
            else resource_path("assets", "img", "no-image.png")
        )
        pix = QPixmap(path).scaled(
            120, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        img_label.setPixmap(pix)
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
        self.star_layout = QHBoxLayout(self)
        self.star_layout.setContentsMargins(0, 0, 0, 0)
        self.refresh_stars()

    def refresh_stars(self):
        [
            self.star_layout.takeAt(0).widget().deleteLater()
            for _ in range(self.star_layout.count())
            if self.star_layout.itemAt(0).widget()
        ]
        [self.star_layout.addWidget(self.create_star(i)) for i in range(1, 6)]

    def create_star(self, index):
        star = QLabel()
        path = resource_path(
            "assets", "img", "star-on.png" if index <= self.rating else "star-off.png"
        )
        star.setPixmap(
            QPixmap(path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        star.setCursor(Qt.PointingHandCursor)
        star.mousePressEvent = lambda e: (
            setattr(self, "rating", 0 if index == self.rating else index),
            self.refresh_stars(),
        )
        return star


class App(QWidget):
    def __init__(self):
        super().__init__()
        init_database(connect_db())
        self.setWindowTitle(f"ほんろぐ {VERSION}")
        self.resize(1100, 800)
        self.main_layout = QVBoxLayout(self)
        self.init_ui()
        self.check_updates()

    def init_ui(self):
        self.update_info_bar = QFrame()
        self.update_info_bar.setVisible(False)
        self.update_info_bar.setStyleSheet("background-color: #fff3cd;")
        up_layout = QHBoxLayout(self.update_info_bar)
        self.update_label = QLabel()
        up_layout.addWidget(self.update_label)
        btn_dl = QPushButton("ダウンロード")
        btn_dl.clicked.connect(
            lambda: webbrowser.open(f"https://github.com/{REPO_URL}/releases/latest")
        )
        up_layout.addWidget(btn_dl)
        self.main_layout.addWidget(self.update_info_bar)
        self.control_layout = QHBoxLayout()
        self.btn_update = QPushButton("新規追加 / 更新")
        self.btn_update.clicked.connect(self.select_csv)
        self.control_layout.addWidget(self.btn_update)
        self.btn_clear = QPushButton("全削除")
        self.btn_clear.clicked.connect(self.confirm_clear_db)
        self.control_layout.addWidget(self.btn_clear)
        self.btn_stats = QPushButton("統計")
        self.btn_stats.clicked.connect(self.show_statistics)
        self.control_layout.addWidget(self.btn_stats)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["すべて表示", "感想あり", "未入力のみ"])
        self.filter_combo.currentIndexChanged.connect(self.refresh_grid)
        self.control_layout.addWidget(self.filter_combo)
        self.tag_combo = QComboBox()
        self.tag_combo.currentIndexChanged.connect(self.refresh_grid)
        self.control_layout.addWidget(self.tag_combo)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(
            ["日付が新しい順", "日付が古い順", "評価が高い順", "タイトル順"]
        )
        self.sort_combo.currentIndexChanged.connect(self.refresh_grid)
        self.control_layout.addWidget(self.sort_combo)
        self.main_layout.addLayout(self.control_layout)
        self.progress_bar = QProgressBar()
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

    def check_updates(self):
        self.update_checker = UpdateChecker()
        self.update_checker.new_version_found.connect(
            lambda v: (
                self.update_label.setText(f"新バージョン {v} があります"),
                self.update_info_bar.setVisible(True),
            )
        )
        self.update_checker.start()

    def refresh_tag_combo(self):
        self.tag_combo.blockSignals(True)
        self.tag_combo.clear()
        self.tag_combo.addItem("すべてのタグ")
        conn = connect_db()
        tags = set(
            t.strip()
            for r in conn.execute("SELECT tags FROM loans WHERE tags != ''").fetchall()
            for t in r[0].split(",")
        )
        conn.close()
        self.tag_combo.addItems(sorted(list(tags)))
        self.tag_combo.blockSignals(False)

    def select_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "CSV選択", "", "CSV (*.csv)")
        if path:
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.worker = ImportWorker(path)
            self.worker.progress.connect(self.progress_bar.setValue)
            self.worker.finished.connect(
                lambda: (
                    self.progress_bar.setVisible(False),
                    self.refresh_tag_combo(),
                    self.refresh_grid(),
                )
            )
            self.worker.start()

    def confirm_clear_db(self):
        if QMessageBox.Yes == QMessageBox.question(
            self, "確認", "全記録を削除しますか？"
        ):
            clear_database()
            self.refresh_tag_combo()
            self.refresh_grid()

    def refresh_grid(self):
        [
            self.grid_layout.takeAt(0).widget().deleteLater()
            for _ in range(self.grid_layout.count())
            if self.grid_layout.itemAt(0).widget()
        ]
        conds = (
            ["(review != '')"]
            if self.filter_combo.currentIndex() == 1
            else ["(review = '' OR review IS NULL)"]
            if self.filter_combo.currentIndex() == 2
            else []
        ) + (["tags LIKE ?"] if self.tag_combo.currentIndex() > 0 else [])
        params = (
            [f"%{self.tag_combo.currentText()}%"]
            if self.tag_combo.currentIndex() > 0
            else []
        )
        sort = {
            0: "MAX(loan_date) DESC",
            1: "MAX(loan_date) ASC",
            2: "rating DESC, MAX(loan_date) DESC",
            3: "title ASC",
        }[self.sort_combo.currentIndex()]
        conn = connect_db()
        rows = conn.execute(
            f"SELECT * FROM loans {'WHERE ' + ' AND '.join(conds) if conds else ''} GROUP BY material_id ORDER BY {sort}",
            params,
        ).fetchall()
        conn.close()
        [
            self.grid_layout.addWidget(BookWidget(r, self.show_detail), i // 5, i % 5)
            for i, r in enumerate(rows)
        ]

    def show_detail(self, mid):
        conn = connect_db()
        book = conn.execute(
            "SELECT title, author, publisher, loan_date, isbn, review, material_id, url, image_path, rating, tags FROM loans WHERE material_id=?",
            (mid,),
        ).fetchone()
        dates = [
            r[0]
            for r in conn.execute(
                "SELECT loan_date FROM loans WHERE material_id=? ORDER BY loan_date DESC",
                (mid,),
            ).fetchall()
        ]
        conn.close()
        if not book:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("書籍詳細")
        dialog.setMinimumWidth(600)
        layout = QHBoxLayout(dialog)
        img_l = QLabel()
        img_l.setPixmap(
            QPixmap(
                book[8]
                if book[8] and os.path.exists(book[8])
                else resource_path("assets", "img", "no-image.png")
            ).scaled(200, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        layout.addWidget(img_l, alignment=Qt.AlignTop)
        right = QVBoxLayout()
        form = QFormLayout()
        star = StarRatingWidget(book[9] or 0)
        tag_e = QLineEdit(book[10] or "")
        text_e = QTextEdit(book[5] or "")
        [
            form.addRow(k, QLabel(str(v)))
            for k, v in zip(
                ["タイトル:", "著者:", "貸出履歴:"],
                [book[0], book[1], ", ".join(dates)],
            )
        ]
        form.addRow("評価:", star)
        form.addRow("タグ:", tag_e)
        right.addLayout(form)
        right.addWidget(text_e)
        save_b = QPushButton("変更を保存")
        save_b.clicked.connect(
            lambda: self.save_data(
                dialog, mid, text_e.toPlainText(), star.rating, tag_e.text()
            )
        )
        right.addWidget(save_b)
        layout.addLayout(right)
        dialog.exec()

    def save_data(self, diag, mid, txt, rate, tags):
        conn = connect_db()
        conn.execute(
            "UPDATE loans SET review=?, rating=?, tags=? WHERE material_id=?",
            (txt, rate, tags, mid),
        )
        conn.commit()
        conn.close()
        diag.accept()
        self.refresh_tag_combo()
        self.refresh_grid()

    def show_statistics(self):
        conn = connect_db()
        auth, mon = get_author_loan_counts(conn), get_monthly_loan_counts(conn)
        conn.close()
        if not auth and not mon:
            return
        diag = QDialog(self)
        diag.resize(900, 700)
        lay = QVBoxLayout(diag)
        if auth:
            fig = Figure(figsize=(8, 4))
            ax = fig.add_subplot(111)
            ax.barh(*zip(*auth), color="#648fff")
            ax.invert_yaxis()
            lay.addWidget(FigureCanvas(fig))
        if mon:
            fig = Figure(figsize=(8, 4))
            ax = fig.add_subplot(111)
            ax.plot(range(len(mon)), [c for m, c in mon], marker="o")
            ax.set_xticks(range(len(mon)))
            ax.set_xticklabels([m for m, c in mon], rotation=45)
            lay.addWidget(FigureCanvas(fig))
        diag.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
