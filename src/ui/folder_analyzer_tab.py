import os
import threading
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem,
    QFileDialog, QAbstractItemView
)
from qfluentwidgets import (
    TitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    PrimaryPushButton, PushButton, LineEdit, TableWidget, CheckBox,
    ProgressBar, FluentIcon as FI, InfoBar, InfoBarPosition, MessageBox,
    CardWidget, ComboBox
)

from core.folder_analyzer import (
    FolderAnalyzer, LEVEL_SAFE, LEVEL_CAUTION, LEVEL_DANGER
)
from core.cleaner import format_size
from .animations import (
    SmoothAnimationHelper, animate_button_bounce, TableFadeOutHelper, NumberRollAnimation
)


class AnalyzerSignals(QObject):
    progress = pyqtSignal(str, int)
    scan_done = pyqtSignal(list)
    delete_done = pyqtSignal(int, list)


class FolderAnalyzerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("FolderAnalyzerTab")
        self.analyzer = FolderAnalyzer()
        self.signals = AnalyzerSignals()
        self.signals.progress.connect(self._on_progress)
        self.signals.scan_done.connect(self._on_scan_done)
        self.signals.delete_done.connect(self._on_delete_done)

        self.analysis_results = []
        self.appdata_paths = self.analyzer.get_appdata_paths()

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 24, 36, 24)
        main_layout.setSpacing(14)

        # 1. Header
        title_box = QVBoxLayout()
        title_box.addWidget(TitleLabel("Phân Tích & Dọn Dẹp Thư Mục / AppData", self))
        sub = BodyLabel(
            "Dán đường dẫn bất kỳ hoặc chọn AppData để tự động phân tích các nhóm: "
            "An toàn để xóa, Cần cân nhắc hoặc Chứa cấu hình máy.", self
        )
        sub.setStyleSheet("color: #888888;")
        title_box.addWidget(sub)
        main_layout.addLayout(title_box)

        # 2. Path Input & Shortcuts Card
        path_card = CardWidget(self)
        path_card_layout = QVBoxLayout(path_card)
        path_card_layout.setContentsMargins(18, 14, 18, 14)
        path_card_layout.setSpacing(10)

        # Input row
        input_row = QHBoxLayout()
        self.path_input = LineEdit(path_card)
        self.path_input.setPlaceholderText("Dán hoặc nhập đường dẫn thư mục cần quét (Ví dụ: C:\\Users\\...\\AppData)...")
        self.path_input.setText(self.appdata_paths.get("Local", ""))

        btn_browse = PushButton(FI.FOLDER, "Duyệt Thư Mục...", path_card)
        btn_browse.clicked.connect(self._browse_folder)

        self.btn_scan = PrimaryPushButton(FI.SEARCH, "Phân Tích Thư Mục", path_card)
        self.btn_scan.clicked.connect(self.start_analysis)

        input_row.addWidget(self.path_input, stretch=1)
        input_row.addWidget(btn_browse)
        input_row.addWidget(self.btn_scan)
        path_card_layout.addLayout(input_row)

        # Quick preset buttons row
        presets_row = QHBoxLayout()
        presets_row.addWidget(CaptionLabel("Lối tắt quét nhanh:", path_card))

        btn_appdata_local = PushButton("⚡ AppData Local (Cache/Temp)", path_card)
        btn_appdata_local.clicked.connect(lambda: self._set_and_scan(self.appdata_paths.get("Local", "")))

        btn_appdata_roaming = PushButton("⚡ AppData Roaming (App Data)", path_card)
        btn_appdata_roaming.clicked.connect(lambda: self._set_and_scan(self.appdata_paths.get("Roaming", "")))

        btn_user_profile = PushButton("⚡ Thư Mục Người Dùng (%USERPROFILE%)", path_card)
        btn_user_profile.clicked.connect(lambda: self._set_and_scan(os.environ.get("USERPROFILE", "")))

        presets_row.addWidget(btn_appdata_local)
        presets_row.addWidget(btn_appdata_roaming)
        presets_row.addWidget(btn_user_profile)
        presets_row.addStretch()
        path_card_layout.addLayout(presets_row)

        main_layout.addWidget(path_card)

        # 3. Summary Cards (Total, Safe, Caution, Danger)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.card_total = self._create_metric_card("Tổng Dung Lượng", "0 MB", "#0078D4")
        self.card_safe = self._create_metric_card("🟢 An Toàn Để Xóa", "0 MB", "#107C41")
        self.card_caution = self._create_metric_card("🟡 Cần Cân Nhắc", "0 MB", "#D83B01")
        self.card_danger = self._create_metric_card("🔴 Giữ Lại (Cấu Hình)", "0 MB", "#E81123")

        stats_layout.addWidget(self.card_total['card'])
        stats_layout.addWidget(self.card_safe['card'])
        stats_layout.addWidget(self.card_caution['card'])
        stats_layout.addWidget(self.card_danger['card'])
        main_layout.addLayout(stats_layout)

        # 4. Progress bar & status
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.status_label = CaptionLabel("Nhập đường dẫn và nhấn 'Phân Tích Thư Mục' để bắt đầu.", self)
        self.status_label.setStyleSheet("color: #888888;")
        main_layout.addWidget(self.status_label)

        # 5. Table actions & Filter
        action_row = QHBoxLayout()
        action_row.addWidget(StrongBodyLabel("Danh mục được phân loại:", self))
        action_row.addStretch()

        self.filter_combo = ComboBox(self)
        self.filter_combo.addItems(["Tất Cả Mức Độ", "🟢 Chỉ An Toàn", "🟡 Chỉ Cân Nhắc", "🔴 Chỉ Chứa Cấu Hình"])
        self.filter_combo.currentIndexChanged.connect(self._render_table)
        action_row.addWidget(self.filter_combo)

        btn_select_safe = PushButton("Chọn Mục An Toàn", self)
        btn_select_safe.clicked.connect(self._select_safe_only)
        action_row.addWidget(btn_select_safe)

        btn_deselect_all = PushButton("Bỏ Chọn Hết", self)
        btn_deselect_all.clicked.connect(self._deselect_all)
        action_row.addWidget(btn_deselect_all)

        self.btn_delete = PrimaryPushButton("🗑️ Xóa Mục Đã Chọn", self)
        self.btn_delete.setEnabled(False)
        self.btn_delete.setStyleSheet("background-color: #D83B01; border-color: #D83B01;")
        self.btn_delete.clicked.connect(self._confirm_and_delete)
        action_row.addWidget(self.btn_delete)

        main_layout.addLayout(action_row)

        # 6. Result Table
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Chọn", "Tên Thư Mục / Tệp", "Mức Độ An Toàn", "Dung Lượng", "Đánh Giá & Tác Động Khi Xóa"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)

        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(1, 210)

        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(2, 190)

        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(3, 100)

        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.table)

    def _create_metric_card(self, title, default_val, color):
        card = CardWidget(self)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        lbl_title = CaptionLabel(title, card)
        lbl_title.setStyleSheet("color: #888888;")
        lbl_val = StrongBodyLabel(default_val, card)
        lbl_val.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        return {'card': card, 'val_label': lbl_val}

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục cần phân tích", self.path_input.text())
        if folder:
            self.path_input.setText(folder)

    def _set_and_scan(self, path):
        if path and os.path.exists(path):
            self.path_input.setText(path)
            self.start_analysis()

    def start_analysis(self):
        animate_button_bounce(self.btn_scan)
        target = self.path_input.text().strip()
        if not target or not os.path.exists(target):
            InfoBar.warning(
                title="Đường dẫn không hợp lệ",
                content="Vui lòng kiểm tra lại đường dẫn thư mục vừa nhập.",
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        self.btn_scan.setEnabled(False)
        self.btn_delete.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Đang bắt đầu quét {target}...")

        def _worker():
            def cb(msg, pct):
                self.signals.progress.emit(msg, pct)

            results = self.analyzer.scan_path(target, progress_callback=cb)
            self.signals.scan_done.emit(results)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_progress(self, msg, pct):
        self.status_label.setText(msg)
        SmoothAnimationHelper.animate_progress_bar(self.progress_bar, pct, duration=200)

    def _on_scan_done(self, results):
        self.btn_scan.setEnabled(True)
        self.analysis_results = results
        self.progress_bar.setValue(100)
        self.status_label.setText(f"Phân tích hoàn tất! Phát hiện {len(results)} mục.")

        # Calculate metrics
        total_size = sum(r['size'] for r in results)
        safe_size = sum(r['size'] for r in results if r['level'] == LEVEL_SAFE)
        caution_size = sum(r['size'] for r in results if r['level'] == LEVEL_CAUTION)
        danger_size = sum(r['size'] for r in results if r['level'] == LEVEL_DANGER)

        self.card_total['val_label'].setText(format_size(total_size))
        self.card_safe['val_label'].setText(format_size(safe_size))
        self.card_caution['val_label'].setText(format_size(caution_size))
        self.card_danger['val_label'].setText(format_size(danger_size))

        self._render_table()
        # By default, check only safe items
        self._select_safe_only()

        InfoBar.success(
            title="Đã phân tích xong",
            content=f"Tổng dung lượng: {format_size(total_size)} ({format_size(safe_size)} có thể xóa an toàn).",
            position=InfoBarPosition.TOP,
            duration=3500,
            parent=self
        )

    def _render_table(self):
        filter_idx = self.filter_combo.currentIndex()
        # 0: All, 1: Safe, 2: Caution, 3: Danger

        filtered = []
        for r in self.analysis_results:
            if filter_idx == 1 and r['level'] != LEVEL_SAFE:
                continue
            elif filter_idx == 2 and r['level'] != LEVEL_CAUTION:
                continue
            elif filter_idx == 3 and r['level'] != LEVEL_DANGER:
                continue
            filtered.append(r)

        self.table.setRowCount(len(filtered))

        for row, item in enumerate(filtered):
            # Column 0: Checkbox
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_item.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(row, 0, chk_item)

            # Store the data path in col 0 UserRole
            chk_item.setData(Qt.ItemDataRole.UserRole, item['path'])
            chk_item.setData(Qt.ItemDataRole.UserRole + 1, item['level'])

            # Column 1: Name
            name_text = f"📁 {item['name']}" if item.get('is_dir') else f"📄 {item['name']}"
            name_item = QTableWidgetItem(name_text)
            self.table.setItem(row, 1, name_item)

            # Column 2: Safety Level
            if item['level'] == LEVEL_SAFE:
                badge = "🟢 An toàn (Cache/Temp)"
            elif item['level'] == LEVEL_CAUTION:
                badge = "🟡 Cần cân nhắc"
            else:
                badge = "🔴 Không nên xóa (Cấu hình)"

            lvl_item = QTableWidgetItem(badge)
            lvl_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, lvl_item)

            # Column 3: Size
            size_item = QTableWidgetItem(format_size(item['size']))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, size_item)

            # Column 4: Impact & Reason
            desc_text = f"{item['reason']} — {item['impact']}"
            desc_item = QTableWidgetItem(desc_text)
            desc_item.setToolTip(desc_text)
            self.table.setItem(row, 4, desc_item)

        try:
            self.table.itemChanged.disconnect(self._on_table_item_changed)
        except Exception:
            pass
        self.table.itemChanged.connect(self._on_table_item_changed)
        self._update_delete_btn_state()

    def _on_table_item_changed(self, item):
        if item.column() == 0:
            self._update_delete_btn_state()

    def _select_safe_only(self):
        for r in range(self.table.rowCount()):
            chk = self.table.item(r, 0)
            if chk:
                level = chk.data(Qt.ItemDataRole.UserRole + 1)
                chk.setCheckState(Qt.CheckState.Checked if level == LEVEL_SAFE else Qt.CheckState.Unchecked)
        self._update_delete_btn_state()

    def _deselect_all(self):
        for r in range(self.table.rowCount()):
            chk = self.table.item(r, 0)
            if chk:
                chk.setCheckState(Qt.CheckState.Unchecked)
        self._update_delete_btn_state()

    def _get_checked_paths(self):
        checked_paths = []
        has_danger = False

        for r in range(self.table.rowCount()):
            chk = self.table.item(r, 0)
            if chk and chk.checkState() == Qt.CheckState.Checked:
                path = chk.data(Qt.ItemDataRole.UserRole)
                level = chk.data(Qt.ItemDataRole.UserRole + 1)
                if path:
                    checked_paths.append(path)
                    if level == LEVEL_DANGER:
                        has_danger = True

        return checked_paths, has_danger

    def _update_delete_btn_state(self):
        paths, _ = self._get_checked_paths()
        self.btn_delete.setEnabled(len(paths) > 0)

    def _confirm_and_delete(self):
        paths, has_danger = self._get_checked_paths()
        if not paths:
            return

        warning_extra = ""
        if has_danger:
            warning_extra = (
                "\n\n⚠️ CẢNH BÁO ĐẶC BIỆT:\n"
                "Bạn đã chọn một hoặc nhiều thư mục thuộc nhóm [🔴 Không nên xóa (Cấu hình)].\n"
                "Xóa các mục này có thể làm mất thiết lập, tài khoản hoặc làm lỗi ứng dụng tương ứng!"
            )

        msg = (
            f"Bạn có chắc chắn muốn xóa vĩnh viễn {len(paths)} mục đã chọn không?{warning_extra}\n\n"
            "Hành động này không thể hoàn tác!"
        )

        w = MessageBox("Xác nhận dọn dẹp thư mục", msg, self.window())
        if not w.exec():
            return

        animate_button_bounce(self.btn_delete)
        self.btn_delete.setEnabled(False)
        self.btn_scan.setEnabled(False)
        self.progress_bar.setValue(0)

        def _worker():
            def cb(m, p):
                self.signals.progress.emit(m, p)

            freed, failed = self.analyzer.delete_items(paths, progress_callback=cb)
            self.signals.delete_done.emit(freed, failed)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_delete_done(self, freed, failed):
        self.btn_scan.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_label.setText(f"Dọn dẹp xong! Đã giải phóng {format_size(freed)}.")

        if failed:
            InfoBar.warning(
                title="Dọn dẹp một phần",
                content=f"Đã giải phóng {format_size(freed)}, nhưng có {len(failed)} tệp đang bị khóa hoặc cần quyền Admin.",
                position=InfoBarPosition.TOP,
                duration=4500,
                parent=self
            )
        else:
            InfoBar.success(
                title="Xóa thành công!",
                content=f"Đã giải phóng thành công {format_size(freed)} dung lượng ổ đĩa.",
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self
            )

        # Smooth fade-out of table before re-scanning (Phương án 3)
        TableFadeOutHelper.fade_out_table(self.table, duration=220, on_finished=self.start_analysis)
