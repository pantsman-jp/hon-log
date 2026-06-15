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
    QStyle,
)
from PySide6.QtCore import QSize, Qt, QThread, Signal
from PySide6.QtGui import QFont, QPixmap
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

APP_STYLE = """
QWidget#AppRoot,
QDialog {
    background: #f7f3ec;
    color: #232a27;
    font-size: 14px;
}

QFrame#Toolbar,
QFrame#UpdateInfoBar {
    background: #fffdf8;
    border: 1px solid #e2dacd;
    border-radius: 8px;
}

QFrame#UpdateInfoBar {
    background: #fff5d8;
    border-color: #ebcf7a;
}

QLabel#AppTitle {
    color: #17211d;
    font-size: 24px;
    font-weight: 700;
}

QLabel#MutedLabel,
QLabel#BookAuthor,
QLabel#CountLabel {
    color: #69746f;
}

QLabel#DialogTitle {
    color: #17211d;
    font-size: 21px;
    font-weight: 700;
}

QLabel#SectionLabel {
    color: #303b36;
    font-weight: 700;
}

QLabel#MetaValue {
    color: #3f4945;
}

QPushButton {
    background: #23635f;
    color: white;
    border: 1px solid #23635f;
    border-radius: 6px;
    padding: 7px 12px;
    min-height: 28px;
    font-weight: 700;
}

QPushButton:hover {
    background: #2f756d;
    border-color: #2f756d;
}

QPushButton:pressed {
    background: #184c49;
    border-color: #184c49;
}

QPushButton#SecondaryButton {
    background: #fffdf8;
    color: #26312d;
    border-color: #cfc5b6;
}

QPushButton#SecondaryButton:hover {
    background: #f0e9df;
}

QPushButton#DangerButton {
    background: #b64b45;
    border-color: #b64b45;
}

QPushButton#DangerButton:hover {
    background: #9f3d39;
    border-color: #9f3d39;
}

QComboBox,
QLineEdit,
QTextEdit {
    background: #fffdf8;
    border: 1px solid #cfc5b6;
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: #2f756d;
}

QComboBox:focus,
QLineEdit:focus,
QTextEdit:focus {
    border-color: #2f756d;
}

QComboBox {
    min-height: 30px;
}

QTextEdit {
    min-height: 160px;
}

QProgressBar {
    background: #e8dfd2;
    border: none;
    border-radius: 5px;
    height: 10px;
    color: transparent;
}

QProgressBar::chunk {
    background: #2f756d;
    border-radius: 5px;
}

QScrollArea {
    background: transparent;
    border: none;
}

QWidget#GridContainer {
    background: transparent;
}

QFrame#BookCard {
    background: #fffdf8;
    border: 1px solid #e2dacd;
    border-radius: 8px;
}

QFrame#BookCard:hover {
    border-color: #9dbdb4;
    background: #ffffff;
}

QLabel#CoverImage {
    background: #eee7dc;
    border: 1px solid #ded3c3;
    border-radius: 5px;
}

QLabel#BookTitle {
    color: #1d2723;
    font-weight: 700;
}

QLabel#BookRating {
    color: #b57724;
    font-weight: 700;
}

QLabel#EmptyState {
    color: #69746f;
    font-size: 17px;
    padding: 80px;
}

QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #c8bcae;
    border-radius: 6px;
    min-height: 34px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}
"""


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


class BookWidget(QFrame):
    def __init__(self, row, on_click):
        super().__init__()
        self.row = row
        self.on_click = on_click
        self.init_ui()

    def init_ui(self):
        self.setObjectName("BookCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(176, 292)
        self.setAttribute(Qt.WA_Hover, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 12)
        layout.setSpacing(9)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        img_label = QLabel()
        img_label.setObjectName("CoverImage")
        img_label.setFixedSize(132, 176)
        img_label.setAlignment(Qt.AlignCenter)
        path = (
            self.row[9]
            if self.row[9] and os.path.exists(self.row[9])
            else resource_path("assets", "img", "no-image.png")
        )
        pix = QPixmap(path)
        if not pix.isNull():
            img_label.setPixmap(
                pix.scaled(124, 168, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        layout.addWidget(img_label, alignment=Qt.AlignCenter)

        title_label = QLabel(self.row[1])
        title_label.setObjectName("BookTitle")
        title_label.setFixedSize(148, 42)
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        title_label.setToolTip(self.row[1])
        layout.addWidget(title_label)

        author_label = QLabel(self.row[2] or "著者未登録")
        author_label.setObjectName("BookAuthor")
        author_label.setFixedSize(148, 32)
        author_label.setWordWrap(True)
        author_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        author_label.setToolTip(self.row[2] or "")
        layout.addWidget(author_label)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(6)
        rating = self.row[10] or 0
        rating_label = QLabel("★" * rating if rating else "未評価")
        rating_label.setObjectName("BookRating")
        rating_label.setFixedHeight(20)
        footer.addWidget(rating_label)
        footer.addStretch()
        date_label = QLabel(self.row[4] or "")
        date_label.setObjectName("MutedLabel")
        date_label.setFixedHeight(20)
        footer.addWidget(date_label)
        layout.addLayout(footer)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.on_click(self.row[7])
        super().mousePressEvent(event)


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
        self.setObjectName("AppRoot")
        self.setStyleSheet(APP_STYLE)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(22, 18, 22, 22)
        self.main_layout.setSpacing(16)
        self.init_ui()
        self.check_updates()

    def configure_button(self, button, icon=None, object_name=None, tooltip=None):
        if object_name:
            button.setObjectName(object_name)
        if icon is not None:
            button.setIcon(self.style().standardIcon(icon))
            button.setIconSize(QSize(16, 16))
        if tooltip:
            button.setToolTip(tooltip)
        return button

    def init_ui(self):
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(2, 0, 2, 0)
        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title = QLabel("ほんろぐ")
        title.setObjectName("AppTitle")
        version = QLabel(f"{VERSION}  読書履歴")
        version.setObjectName("MutedLabel")
        title_block.addWidget(title)
        title_block.addWidget(version)
        header_layout.addLayout(title_block)
        header_layout.addStretch()
        self.main_layout.addLayout(header_layout)

        self.update_info_bar = QFrame()
        self.update_info_bar.setObjectName("UpdateInfoBar")
        self.update_info_bar.setVisible(False)
        up_layout = QHBoxLayout(self.update_info_bar)
        up_layout.setContentsMargins(14, 10, 14, 10)
        up_layout.setSpacing(10)
        self.update_label = QLabel()
        self.update_label.setObjectName("SectionLabel")
        up_layout.addWidget(self.update_label)
        up_layout.addStretch()
        btn_dl = QPushButton("ダウンロード")
        self.configure_button(
            btn_dl,
            QStyle.StandardPixmap.SP_DialogSaveButton,
            "SecondaryButton",
            "最新リリースを開く",
        )
        btn_dl.clicked.connect(
            lambda: webbrowser.open(f"https://github.com/{REPO_URL}/releases/latest")
        )
        up_layout.addWidget(btn_dl)
        self.main_layout.addWidget(self.update_info_bar)

        self.control_frame = QFrame()
        self.control_frame.setObjectName("Toolbar")
        self.control_layout = QHBoxLayout(self.control_frame)
        self.control_layout.setContentsMargins(12, 10, 12, 10)
        self.control_layout.setSpacing(10)

        self.btn_update = QPushButton("新規追加 / 更新")
        self.configure_button(
            self.btn_update,
            QStyle.StandardPixmap.SP_DialogOpenButton,
            tooltip="CSVを選択",
        )
        self.btn_update.clicked.connect(self.select_csv)
        self.control_layout.addWidget(self.btn_update)

        self.btn_clear = QPushButton("全削除")
        self.configure_button(
            self.btn_clear,
            QStyle.StandardPixmap.SP_TrashIcon,
            "DangerButton",
            "保存済みの記録を削除",
        )
        self.btn_clear.clicked.connect(self.confirm_clear_db)
        self.control_layout.addWidget(self.btn_clear)

        self.btn_stats = QPushButton("統計")
        self.configure_button(
            self.btn_stats,
            QStyle.StandardPixmap.SP_FileDialogDetailedView,
            "SecondaryButton",
            "統計を表示",
        )
        self.btn_stats.clicked.connect(self.show_statistics)
        self.control_layout.addWidget(self.btn_stats)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("タイトル・著者・タグを検索")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumWidth(220)
        self.search_edit.textChanged.connect(lambda _: self.refresh_grid())
        self.control_layout.addWidget(self.search_edit, 1)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["すべて表示", "感想あり", "未入力のみ"])
        self.filter_combo.currentIndexChanged.connect(self.refresh_grid)
        self.control_layout.addWidget(self.filter_combo)

        self.tag_combo = QComboBox()
        self.tag_combo.setMinimumWidth(145)
        self.tag_combo.currentIndexChanged.connect(self.refresh_grid)
        self.control_layout.addWidget(self.tag_combo)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(
            ["日付が新しい順", "日付が古い順", "評価が高い順", "タイトル順"]
        )
        self.sort_combo.setMinimumWidth(145)
        self.sort_combo.currentIndexChanged.connect(self.refresh_grid)
        self.control_layout.addWidget(self.sort_combo)

        self.result_count = QLabel()
        self.result_count.setObjectName("CountLabel")
        self.result_count.setMinimumWidth(44)
        self.result_count.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.control_layout.addWidget(self.result_count)
        self.main_layout.addWidget(self.control_frame)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.grid_container = QWidget()
        self.grid_container.setObjectName("GridContainer")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.grid_layout.setHorizontalSpacing(18)
        self.grid_layout.setVerticalSpacing(18)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
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
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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
        search_text = self.search_edit.text().strip()
        if search_text:
            conds.append("(title LIKE ? OR author LIKE ? OR tags LIKE ?)")
            params.extend([f"%{search_text}%"] * 3)

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
        self.result_count.setText(f"{len(rows)}冊")

        if not rows:
            empty = QLabel("表示できる本がありません")
            empty.setObjectName("EmptyState")
            empty.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(empty, 0, 0, 1, 5)
            return

        for i, row in enumerate(rows):
            self.grid_layout.addWidget(BookWidget(row, self.show_detail), i // 5, i % 5)

    def show_detail(self, mid):
        conn = connect_db()
        book = conn.execute(
            "SELECT title, author, publisher, loan_date, isbn, review, material_id, url, image_path, rating, tags, volume, published_at FROM loans WHERE material_id=? ORDER BY loan_date DESC LIMIT 1",
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
        dialog.setStyleSheet(APP_STYLE)
        dialog.setMinimumSize(760, 560)
        dialog.resize(820, 600)
        layout = QHBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        img_l = QLabel()
        img_l.setObjectName("CoverImage")
        img_l.setFixedSize(220, 304)
        img_l.setAlignment(Qt.AlignCenter)
        cover = QPixmap(
            book[8]
            if book[8] and os.path.exists(book[8])
            else resource_path("assets", "img", "no-image.png")
        )
        if not cover.isNull():
            img_l.setPixmap(
                cover.scaled(204, 288, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        layout.addWidget(img_l, alignment=Qt.AlignTop)

        right = QVBoxLayout()
        right.setSpacing(14)

        title = QLabel(book[0])
        title.setObjectName("DialogTitle")
        title.setWordWrap(True)
        right.addWidget(title)

        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignTop)

        def meta_label(value):
            label = QLabel(str(value))
            label.setObjectName("MetaValue")
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            return label

        star = StarRatingWidget(book[9] or 0)
        tag_e = QLineEdit(book[10] or "")
        tag_e.setPlaceholderText("技術書, お気に入り")
        text_e = QTextEdit(book[5] or "")
        text_e.setPlaceholderText("感想やメモ")

        for label_text, value in [
            ("著者:", book[1] or "未登録"),
            ("出版社:", book[2]),
            ("巻情報:", book[11]),
            ("出版年:", book[12]),
            ("ISBN:", book[4]),
            ("貸出履歴:", "\n".join(dates)),
        ]:
            if value:
                form.addRow(label_text, meta_label(value))
        form.addRow("評価:", star)
        form.addRow("タグ:", tag_e)
        right.addLayout(form)

        review_label = QLabel("感想")
        review_label.setObjectName("SectionLabel")
        right.addWidget(review_label)
        right.addWidget(text_e)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 2, 0, 0)
        actions.setSpacing(10)
        if book[7]:
            open_b = QPushButton("OPACを開く")
            self.configure_button(
                open_b,
                QStyle.StandardPixmap.SP_DialogOpenButton,
                "SecondaryButton",
                "OPACページを開く",
            )
            open_b.clicked.connect(lambda: webbrowser.open(book[7]))
            actions.addWidget(open_b)
        actions.addStretch()
        close_b = QPushButton("閉じる")
        self.configure_button(
            close_b,
            QStyle.StandardPixmap.SP_DialogCloseButton,
            "SecondaryButton",
        )
        close_b.clicked.connect(dialog.reject)
        actions.addWidget(close_b)
        save_b = QPushButton("変更を保存")
        self.configure_button(save_b, QStyle.StandardPixmap.SP_DialogSaveButton)
        save_b.clicked.connect(
            lambda: self.save_data(
                dialog, mid, text_e.toPlainText(), star.rating, tag_e.text()
            )
        )
        actions.addWidget(save_b)
        right.addLayout(actions)
        layout.addLayout(right)
        dialog.exec()

    def save_data(self, diag, mid, txt, rate, tags):
        conn = connect_db()
        conn.execute(
            "UPDATE loans SET review=?, rating=?, tags=? WHERE material_id=?",
            (txt, rate, tags.strip(), mid),
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
            QMessageBox.information(self, "統計", "表示できる貸出記録がありません。")
            return
        diag = QDialog(self)
        diag.setWindowTitle("統計")
        diag.setStyleSheet(APP_STYLE)
        diag.resize(900, 700)
        lay = QVBoxLayout(diag)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(18)

        title = QLabel("読書統計")
        title.setObjectName("DialogTitle")
        lay.addWidget(title)

        if auth:
            fig = Figure(figsize=(8, 3.6), facecolor="#fffdf8")
            ax = fig.add_subplot(111)
            authors, counts = zip(*auth)
            ax.barh(authors, counts, color="#2f756d")
            ax.invert_yaxis()
            ax.set_title("著者別貸出冊数", fontweight="bold")
            ax.set_xlabel("冊数")
            ax.grid(axis="x", color="#e3d9ca", linewidth=0.8)
            ax.set_axisbelow(True)
            for spine in ax.spines.values():
                spine.set_visible(False)
            fig.tight_layout()
            lay.addWidget(FigureCanvas(fig))
        if mon:
            fig = Figure(figsize=(8, 3.6), facecolor="#fffdf8")
            ax = fig.add_subplot(111)
            ax.plot(
                range(len(mon)),
                [c for m, c in mon],
                marker="o",
                color="#b57724",
                linewidth=2.2,
            )
            ax.set_xticks(range(len(mon)))
            ax.set_xticklabels([m for m, c in mon], rotation=45)
            ax.set_title("月別貸出冊数", fontweight="bold")
            ax.set_ylabel("冊数")
            ax.grid(axis="y", color="#e3d9ca", linewidth=0.8)
            ax.set_axisbelow(True)
            for spine in ax.spines.values():
                spine.set_visible(False)
            fig.tight_layout()
            lay.addWidget(FigureCanvas(fig))
        diag.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont(JAPANESE_FONT, 10))
    window = App()
    window.show()
    sys.exit(app.exec())
