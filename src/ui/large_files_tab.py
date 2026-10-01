import os
import subprocess
import threading
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem,
    QFileDialog, QAbstractItemView
)
from qfluentwidgets import (
    TitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    PrimaryPushButton, PushButton, LineEdit, TableWidget, ComboBox,
    ProgressBar, FluentIcon as FI, InfoBar, InfoBarPosition, MessageBox,
    CardWidget
)

from core.large_files_hunter import LargeFilesHunter
from core.cleaner import format_size
from .animations import (
    SmoothAnimationHelper, animate_button_bounce, TableFadeOutHelper
)


class LargeFilesSignals(QObject):
    progress = pyqtSignal(str, int)
    scan_done = pyqtSignal(list)
    file_deleted = pyqtSignal(bool, str)


class LargeFilesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("LargeFilesTab")
        self.hunter = LargeFilesHunter()
        self.signals = LargeFilesSignals()
        self.signals.progress.connect(self._on_progress)
        self.signals.scan_done.connect(self._on_scan_done)
        self.signals.file_deleted.connect(self._on_file_deleted)

        self.large_files = []
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 24, 36, 24)
        main_layout.setSpacing(14)

        # 1. Header
        title_box = QVBoxLayout()
        title_box.addWidget(TitleLabel("Truy Tìm Tệp Dung Lượng Khủng (Large Files Hunter)", self))
        sub = BodyLabel("Quét nhanh toàn bộ các tệp tin có dung lượng lớn bị lãng quên (ISO, nén cũ, video, installer...).", self)
        sub.setStyleSheet("color: #888888;")
        title_box.addWidget(sub)
        main_layout.addLayout(title_box)

        # 2. Controls
        ctrl_card = CardWidget(self)
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(18, 14, 18, 14)
        ctrl_layout.setSpacing(10)

        row1 = QHBoxLayout()
        self.path_input = LineEdit(ctrl_card)
        self.path_input.setText(os.environ.get("USERPROFILE", "C:\\"))
        self.path_input.setPlaceholderText("Chọn ổ đĩa hoặc thư mục (Ví dụ: C:\\ hoặc D:\\)...")

        btn_browse = PushButton(FI.FOLDER, "Duyệt...", ctrl_card)
        btn_browse.clicked.connect(self._browse)

        row1.addWidget(self.path_input, stretch=1)
        row1.addWidget(btn_browse)

        row2 = QHBoxLayout()
        row2.addWidget(CaptionLabel("Lọc kích thước lớn hơn:", ctrl_card))

        self.size_combo = ComboBox(ctrl_card)
        self.size_combo.addItems([">= 100 MB", ">= 250 MB", ">= 500 MB", ">= 1 GB", ">= 2 GB"])
        self.size_combo.setCurrentIndex(2)  # Default >= 500 MB
        row2.addWidget(self.size_combo)

        btn_c_drive = PushButton("⚡ Quét Ổ C:", ctrl_card)
        btn_c_drive.clicked.connect(lambda: self._set_and_scan("C:\\"))

        btn_user_drive = PushButton("⚡ Quét Thư Mục User", ctrl_card)
        btn_user_drive.clicked.connect(lambda: self._set_and_scan(os.environ.get("USERPROFILE", "C:\\")))

        row2.addWidget(btn_c_drive)
        row2.addWidget(btn_user_drive)
        row2.addStretch()

        self.btn_scan = PrimaryPushButton(FI.SEARCH, "Tìm Tệp Dung Lượng Lớn", ctrl_card)
        self.btn_scan.clicked.connect(self.start_scan)
        row2.addWidget(self.btn_scan)

        ctrl_layout.addLayout(row1)
        ctrl_layout.addLayout(row2)
        main_layout.addWidget(ctrl_card)

        # 3. Progress bar & status
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.status_label = CaptionLabel("Chọn thư mục và nhấn 'Tìm Tệp Dung Lượng Lớn'.", self)
        self.status_label.setStyleSheet("color: #888888;")
        main_layout.addWidget(self.status_label)

        # 4. Actions row
        act_row = QHBoxLayout()
        self.count_label = StrongBodyLabel("Tìm thấy: 0 tệp tin lớn", self)
        act_row.addWidget(self.count_label)
        act_row.addStretch()

        self.btn_open_folder = PushButton(FI.FOLDER, "Mở Vị Trí Tệp", self)
        self.btn_open_folder.clicked.connect(self._open_file_location)

        self.btn_delete = PrimaryPushButton("🗑️ Xóa Tệp Đã Chọn", self)
        self.btn_delete.setStyleSheet("background-color: #D83B01; border-color: #D83B01;")
        self.btn_delete.clicked.connect(self._confirm_and_delete)

        act_row.addWidget(self.btn_open_folder)
        act_row.addWidget(self.btn_delete)
        main_layout.addLayout(act_row)

        # 5. Table
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Tên Tệp Tin", "Dung Lượng", "Định Dạng", "Ngày Chỉnh Sửa", "Thư Mục Chứa"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 240)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(1, 100)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(2, 90)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(3, 140)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        main_layout.addWidget(self.table)

    def _browse(self):
        f = QFileDialog.getExistingDirectory(self, "Chọn thư mục", self.path_input.text())
        if f:
            self.path_input.setText(f)

    def _set_and_scan(self, path):
        self.path_input.setText(path)
        self.start_scan()

    def _get_min_size(self):
        idx = self.size_combo.currentIndex()
        sizes = [100, 250, 500, 1024, 2048]
        return sizes[idx] * 1024 * 1024

    def start_scan(self):
        animate_button_bounce(self.btn_scan)
        target = self.path_input.text().strip()
        if not target or not os.path.exists(target):
            InfoBar.warning(
                title="Đường dẫn không hợp lệ",
                content="Vui lòng kiểm tra lại đường dẫn ổ đĩa/thư mục.",
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        self.btn_scan.setEnabled(False)
        self.progress_bar.setValue(0)
        min_bytes = self._get_min_size()

        def _worker():
            def cb(m, p):
                self.signals.progress.emit(m, p)

            files = self.hunter.scan_large_files(target, min_size_bytes=min_bytes, progress_callback=cb)
            self.signals.scan_done.emit(files)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_progress(self, msg, pct):
        self.status_label.setText(msg)
        SmoothAnimationHelper.animate_progress_bar(self.progress_bar, pct, duration=200)

    def _on_scan_done(self, files):
        self.btn_scan.setEnabled(True)
        self.large_files = files
        self.progress_bar.setValue(100)
        total_size = sum(f["size"] for f in files)
        self.count_label.setText(f"Tìm thấy: {len(files)} tệp tin lớn (Tổng cộng ~{format_size(total_size)})")
        self.status_label.setText("Hoàn tất quét tệp tin lớn.")

        self.table.setRowCount(len(files))
        for row, f in enumerate(files):
            name_item = QTableWidgetItem(f"📄 {f['name']}")
            name_item.setData(Qt.ItemDataRole.UserRole, f["path"])
            self.table.setItem(row, 0, name_item)

            size_item = QTableWidgetItem(f["size_str"])
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, size_item)

            ext_item = QTableWidgetItem(f["ext"])
            ext_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, ext_item)

            date_item = QTableWidgetItem(f["mtime"])
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, date_item)

            path_item = QTableWidgetItem(f["dir"])
            path_item.setToolTip(f["path"])
            self.table.setItem(row, 4, path_item)

    def _get_selected_file(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            InfoBar.warning(
                title="Chưa chọn tệp tin",
                content="Vui lòng nhấp chọn một dòng trong bảng.",
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self
            )
            return None
        row = selected_rows[0].row()
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _open_file_location(self):
        filepath = self._get_selected_file()
        if filepath and os.path.exists(filepath):
            subprocess.run(f'explorer /select,"{os.path.abspath(filepath)}"', shell=True)

    def _confirm_and_delete(self):
        animate_button_bounce(self.btn_delete)
        filepath = self._get_selected_file()
        if not filepath:
            return

        msg = f"Bạn có chắc muốn xóa vĩnh viễn tệp tin này không?\n\n📄 {os.path.basename(filepath)}\nĐường dẫn: {filepath}"
        w = MessageBox("Xác nhận xóa tệp lớn", msg, self.window())
        if not w.exec():
            return

        success, note = self.hunter.delete_file(filepath)
        self.signals.file_deleted.emit(success, note)

    def _on_file_deleted(self, success, note):
        if success:
            InfoBar.success(
                title="Đã xóa tệp tin",
                content="Tệp tin đã được giải phóng khỏi ổ đĩa.",
                position=InfoBarPosition.TOP,
                duration=3500,
                parent=self
            )
            TableFadeOutHelper.fade_out_table(self.table, duration=220, on_finished=self.start_scan)
        else:
            InfoBar.error(
                title="Lỗi xóa tệp",
                content=note,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self
            )
