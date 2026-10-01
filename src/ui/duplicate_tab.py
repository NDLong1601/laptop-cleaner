import os
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

from core.duplicate_finder import DuplicateFinder
from core.cleaner import format_size
from .animations import (
    SmoothAnimationHelper, NumberRollAnimation,
    animate_button_bounce, TableFadeOutHelper
)


class DuplicateSignals(QObject):
    progress = pyqtSignal(str, int)
    scan_done = pyqtSignal(list)
    delete_done = pyqtSignal(int, list)


class DuplicateTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("DuplicateTab")
        self.finder = DuplicateFinder()
        self.signals = DuplicateSignals()
        self.signals.progress.connect(self._on_progress)
        self.signals.scan_done.connect(self._on_scan_done)
        self.signals.delete_done.connect(self._on_delete_done)

        self.duplicate_groups = []
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 24, 36, 24)
        main_layout.setSpacing(14)

        # 1. Header
        title_box = QVBoxLayout()
        title_box.addWidget(TitleLabel("Tìm & Dọn Dẹp Tệp Trùng Lặp (Duplicate Finder)", self))
        sub = BodyLabel("Quét băm chính xác nội dung (MD5) để tìm các tệp tin nhân bản giống hệt nhau chiếm dung lượng.", self)
        sub.setStyleSheet("color: #888888;")
        title_box.addWidget(sub)
        main_layout.addLayout(title_box)

        # 2. Controls Card
        ctrl_card = CardWidget(self)
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(18, 14, 18, 14)
        ctrl_layout.setSpacing(10)

        row1 = QHBoxLayout()
        user_downloads = os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")
        self.path_input = LineEdit(ctrl_card)
        self.path_input.setText(user_downloads if os.path.exists(user_downloads) else os.environ.get("USERPROFILE", ""))
        self.path_input.setPlaceholderText("Chọn hoặc dán thư mục cần quét...")

        btn_browse = PushButton(FI.FOLDER, "Duyệt...", ctrl_card)
        btn_browse.clicked.connect(self._browse)

        row1.addWidget(self.path_input, stretch=1)
        row1.addWidget(btn_browse)

        row2 = QHBoxLayout()
        row2.addWidget(CaptionLabel("Lọc kích thước tối thiểu:", ctrl_card))

        self.size_combo = ComboBox(ctrl_card)
        self.size_combo.addItems([">= 1 MB", ">= 5 MB", ">= 10 MB", ">= 50 MB", ">= 100 MB"])
        self.size_combo.setCurrentIndex(1)  # Default >= 5 MB
        row2.addWidget(self.size_combo)

        row2.addStretch()

        self.btn_scan = PrimaryPushButton(FI.SEARCH, "Bắt Đầu Quét Trùng Lặp", ctrl_card)
        self.btn_scan.clicked.connect(self.start_scan)
        row2.addWidget(self.btn_scan)

        ctrl_layout.addLayout(row1)
        ctrl_layout.addLayout(row2)
        main_layout.addWidget(ctrl_card)

        # 3. Stats & Progress
        stats_row = QHBoxLayout()
        self.stat_groups_label = StrongBodyLabel("Số nhóm trùng: 0", self)
        self.stat_wasted_label = StrongBodyLabel("Dung lượng lãng phí: 0 MB", self)
        self.stat_wasted_label.setStyleSheet("color: #D83B01; font-weight: bold;")
        stats_row.addWidget(self.stat_groups_label)
        stats_row.addSpacing(20)
        stats_row.addWidget(self.stat_wasted_label)
        stats_row.addStretch()
        main_layout.addLayout(stats_row)

        self.progress_bar = ProgressBar(self)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.status_label = CaptionLabel("Sẵn sàng quét thư mục.", self)
        self.status_label.setStyleSheet("color: #888888;")
        main_layout.addWidget(self.status_label)

        # 4. Action buttons
        btn_row = QHBoxLayout()
        btn_row.addWidget(StrongBodyLabel("Danh sách tệp trùng lặp:", self))
        btn_row.addStretch()

        btn_auto_select = PushButton("⚡ Tự Động Chọn Bản Sao", self)
        btn_auto_select.setToolTip("Giữ lại 1 bản gốc duy nhất trong mỗi nhóm và chọn tất cả các bản copy còn lại để xóa")
        btn_auto_select.clicked.connect(self._auto_select_duplicates)
        btn_row.addWidget(btn_auto_select)

        btn_deselect = PushButton("Bỏ Chọn", self)
        btn_deselect.clicked.connect(self._deselect_all)
        btn_row.addWidget(btn_deselect)

        self.btn_delete = PrimaryPushButton("🗑️ Xóa Bản Sao Đã Chọn", self)
        self.btn_delete.setEnabled(False)
        self.btn_delete.setStyleSheet("background-color: #D83B01; border-color: #D83B01;")
        self.btn_delete.clicked.connect(self._confirm_and_delete)
        btn_row.addWidget(self.btn_delete)

        main_layout.addLayout(btn_row)

        # 5. Table
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Chọn", "Tên Tệp Tin", "Dung Lượng", "Nhóm Trùng", "Đường Dẫn Đầy Đủ"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(1, 220)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(2, 95)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(3, 110)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.table)

    def _browse(self):
        f = QFileDialog.getExistingDirectory(self, "Chọn thư mục", self.path_input.text())
        if f:
            self.path_input.setText(f)

    def _get_min_size(self):
        idx = self.size_combo.currentIndex()
        sizes = [1, 5, 10, 50, 100]
        return sizes[idx] * 1024 * 1024

    def start_scan(self):
        animate_button_bounce(self.btn_scan)
        target = self.path_input.text().strip()
        if not target or not os.path.exists(target):
            InfoBar.warning(
                title="Thư mục không tồn tại",
                content="Vui lòng kiểm tra lại đường dẫn thư mục cần quét.",
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        self.btn_scan.setEnabled(False)
        self.btn_delete.setEnabled(False)
        self.progress_bar.setValue(0)
        min_bytes = self._get_min_size()

        def _worker():
            def cb(m, p):
                self.signals.progress.emit(m, p)

            groups = self.finder.find_duplicates(target, min_size_bytes=min_bytes, progress_callback=cb)
            self.signals.scan_done.emit(groups)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_progress(self, msg, pct):
        self.status_label.setText(msg)
        SmoothAnimationHelper.animate_progress_bar(self.progress_bar, pct, duration=200)

    def _on_scan_done(self, groups):
        self.btn_scan.setEnabled(True)
        self.duplicate_groups = groups
        self.progress_bar.setValue(100)

        total_wasted = sum(g["wasted_size"] for g in groups)
        total_files = sum(len(g["files"]) for g in groups)

        self.stat_groups_label.setText(f"Số nhóm trùng: {len(groups)} ({total_files} tệp)")
        self.stat_wasted_label.setText(f"Dung lượng lãng phí: {format_size(total_wasted)}")
        self.status_label.setText(f"Hoàn tất quét! Phát hiện {len(groups)} nhóm tệp trùng lặp.")

        self._render_table()
        if groups:
            self._auto_select_duplicates()

    def _render_table(self):
        # Flatten groups into rows
        rows = []
        for g_idx, g in enumerate(self.duplicate_groups):
            for f_idx, filepath in enumerate(g["files"]):
                is_original = (f_idx == 0)
                rows.append({
                    "group_idx": g_idx + 1,
                    "filepath": filepath,
                    "name": os.path.basename(filepath),
                    "size_str": g["size_str"],
                    "is_original": is_original
                })

        self.table.setRowCount(len(rows))
        for r_idx, r_data in enumerate(rows):
            # Col 0: Checkbox
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Unchecked)
            chk.setData(Qt.ItemDataRole.UserRole, r_data["filepath"])
            chk.setData(Qt.ItemDataRole.UserRole + 1, r_data["is_original"])
            self.table.setItem(r_idx, 0, chk)

            # Col 1: Name
            badge = " (Gốc)" if r_data["is_original"] else " (Bản sao)"
            name_item = QTableWidgetItem(r_data["name"] + badge)
            if r_data["is_original"]:
                name_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(r_idx, 1, name_item)

            # Col 2: Size
            self.table.setItem(r_idx, 2, QTableWidgetItem(r_data["size_str"]))

            # Col 3: Group
            grp_item = QTableWidgetItem(f"Nhóm #{r_data['group_idx']}")
            grp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r_idx, 3, grp_item)

            # Col 4: Path
            path_item = QTableWidgetItem(r_data["filepath"])
            path_item.setToolTip(r_data["filepath"])
            self.table.setItem(r_idx, 4, path_item)

        try:
            self.table.itemChanged.disconnect(self._on_item_changed)
        except Exception:
            pass
        self.table.itemChanged.connect(self._on_item_changed)
        self._update_btn_state()

    def _on_item_changed(self, item):
        if item.column() == 0:
            self._update_btn_state()

    def _auto_select_duplicates(self):
        """Keep the original (first) file in each group, check all other duplicates."""
        for r in range(self.table.rowCount()):
            chk = self.table.item(r, 0)
            if chk:
                is_orig = chk.data(Qt.ItemDataRole.UserRole + 1)
                chk.setCheckState(Qt.CheckState.Unchecked if is_orig else Qt.CheckState.Checked)
        self._update_btn_state()

    def _deselect_all(self):
        for r in range(self.table.rowCount()):
            chk = self.table.item(r, 0)
            if chk:
                chk.setCheckState(Qt.CheckState.Unchecked)
        self._update_btn_state()

    def _get_selected_files(self):
        files = []
        for r in range(self.table.rowCount()):
            chk = self.table.item(r, 0)
            if chk and chk.checkState() == Qt.CheckState.Checked:
                fp = chk.data(Qt.ItemDataRole.UserRole)
                if fp:
                    files.append(fp)
        return files

    def _update_btn_state(self):
        selected = self._get_selected_files()
        self.btn_delete.setEnabled(len(selected) > 0)

    def _confirm_and_delete(self):
        animate_button_bounce(self.btn_delete)
        selected = self._get_selected_files()
        if not selected:
            return

        msg = f"Bạn có chắc muốn xóa vĩnh viễn {len(selected)} tệp bản sao đã chọn không?\n(Mỗi nhóm vẫn được giữ lại 1 bản gốc)."
        w = MessageBox("Xác nhận xóa tệp trùng", msg, self.window())
        if not w.exec():
            return

        self.btn_delete.setEnabled(False)
        self.btn_scan.setEnabled(False)

        def _worker():
            freed, failed = self.finder.delete_files(selected)
            self.signals.delete_done.emit(freed, failed)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_delete_done(self, freed, failed):
        self.btn_scan.setEnabled(True)
        # Smooth fade-out of table before reloading (Phương án 3)
        TableFadeOutHelper.fade_out_table(self.table, duration=250, on_finished=self.start_scan)

        InfoBar.success(
            title="Đã dọn dẹp tệp trùng",
            content=f"Đã giải phóng thành công {format_size(freed)} dung lượng ổ đĩa.",
            position=InfoBarPosition.TOP,
            duration=3500,
            parent=self
        )
