import os
import threading
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QHeaderView, QTableWidgetItem
)
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    PrimaryPushButton, PushButton, CardWidget, CheckBox,
    ProgressBar, TableWidget, FluentIcon as FI, InfoBar, InfoBarPosition
)

from core.cleaner import Cleaner, format_size
from .animations import (
    SmoothAnimationHelper, NumberRollAnimation,
    animate_button_bounce, TableFadeOutHelper
)


class CleanerSignals(QObject):
    progress = pyqtSignal(str, int)
    scan_done = pyqtSignal(dict)
    clean_done = pyqtSignal(int)


class CleanerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("CleanerTab")
        self.cleaner = Cleaner()
        self.signals = CleanerSignals()
        self.signals.progress.connect(self._on_progress)
        self.signals.scan_done.connect(self._on_scan_done)
        self.signals.clean_done.connect(self._on_clean_done)

        self.scanned_categories = {}
        self.category_cards = {}

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 24, 36, 24)
        main_layout.setSpacing(16)

        # 1. Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.addWidget(TitleLabel("Dọn Dẹp Tệp Rác", self))
        sub = BodyLabel("Lựa chọn các danh mục để quét và dọn sạch không gian ổ đĩa.", self)
        sub.setStyleSheet("color: #888888;")
        title_box.addWidget(sub)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_scan = PushButton(FI.SEARCH, "Quét Rác", self)
        self.btn_scan.setFixedHeight(38)
        self.btn_scan.clicked.connect(self.start_scan)

        self.btn_clean = PrimaryPushButton(FI.DELETE, "Dọn Dẹp Ngay", self)
        self.btn_clean.setFixedHeight(38)
        self.btn_clean.setEnabled(False)
        self.btn_clean.clicked.connect(self.start_clean)

        header_layout.addWidget(self.btn_scan)
        header_layout.addWidget(self.btn_clean)
        main_layout.addLayout(header_layout)

        # 2. Progress section
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.status_label = CaptionLabel("Sẵn sàng quét hệ thống", self)
        self.status_label.setStyleSheet("color: #888888;")
        main_layout.addWidget(self.status_label)

        # 3. Category Selector Cards
        categories_container = QVBoxLayout()
        categories_container.setSpacing(10)

        self.category_configs = [
            ('windows_temp', 'Tệp tạm hệ thống & Windows Update', '%TEMP%, C:\\Windows\\Temp, thư mục tải về của Windows Update'),
            ('browser_cache', 'Bộ nhớ đệm trình duyệt (Chrome, Edge, Firefox)', 'Cache hình ảnh, css, web data tạm thời'),
            ('logs_dumps', 'Nhật ký lỗi & Crash Dumps (.log, .dmp)', 'Tệp log cũ của Windows và kết xuất lỗi ứng dụng crash'),
            ('recycle_bin', 'Thùng rác Windows (Recycle Bin)', 'Các file đã xóa tạm thời trong Recycle Bin')
        ]

        for cat_id, title, desc in self.category_configs:
            card = CardWidget(self)
            card.setFixedHeight(72)
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(18, 10, 18, 10)
            c_layout.setSpacing(12)

            chk = CheckBox(title, card)
            chk.setChecked(True)
            chk.stateChanged.connect(self._update_clean_button_state)

            desc_label = CaptionLabel(desc, card)
            desc_label.setStyleSheet("color: #888888;")
            desc_label.setWordWrap(False)

            text_vbox = QVBoxLayout()
            text_vbox.setSpacing(4)
            text_vbox.setContentsMargins(0, 0, 0, 0)
            text_vbox.addWidget(chk)
            text_vbox.addWidget(desc_label)

            size_label = StrongBodyLabel("Chưa quét", card)
            size_label.setStyleSheet("color: #0078D4; font-size: 15px;")
            size_label.setFixedWidth(110)
            size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            c_layout.addLayout(text_vbox, stretch=1)
            c_layout.addWidget(size_label)

            self.category_cards[cat_id] = {
                'card': card,
                'checkbox': chk,
                'size_label': size_label
            }
            categories_container.addWidget(card)

        main_layout.addLayout(categories_container)

        # 4. Scanned items table
        main_layout.addWidget(StrongBodyLabel("Chi tiết tệp tin phát hiện:", self))
        self.table = TableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Đường dẫn / Tên tệp", "Loại", "Dung lượng"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setMinimumHeight(160)
        main_layout.addWidget(self.table)

    def _on_progress(self, message, val):
        self.status_label.setText(message)
        SmoothAnimationHelper.animate_progress_bar(self.progress_bar, val, duration=250)

    def start_scan(self):
        animate_button_bounce(self.btn_scan)
        self.btn_scan.setEnabled(False)
        self.btn_clean.setEnabled(False)
        self.table.setRowCount(0)
        self.progress_bar.setValue(0)

        for card_info in self.category_cards.values():
            card_info['size_label'].setText("Đang quét...")

        def _worker():
            def cb(msg, val):
                self.signals.progress.emit(msg, int(val))

            cats = self.cleaner.scan_categories(progress_callback=cb)
            self.signals.scan_done.emit(cats)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_scan_done(self, cats):
        self.scanned_categories = cats
        self.btn_scan.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_label.setText("Quét hoàn tất!")

        total_scanned_bytes = 0
        all_items = []

        for cat_id, cat_data in cats.items():
            if cat_id in self.category_cards:
                size_str = format_size(cat_data['size'])
                self.category_cards[cat_id]['size_label'].setText(size_str)
                total_scanned_bytes += cat_data['size']
                all_items.extend(cat_data['items'])

        # Populate table (up to 500 items to keep UI ultra responsive)
        self.table.setRowCount(len(all_items))
        for row, item in enumerate(all_items):
            self.table.setItem(row, 0, QTableWidgetItem(str(item['path'])))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get('type', 'Tệp tin'))))
            self.table.setItem(row, 2, QTableWidgetItem(format_size(item['size'])))

        self._update_clean_button_state()

        if total_scanned_bytes > 0:
            InfoBar.info(
                title="Quét xong",
                content=f"Đã phát hiện tổng cộng {format_size(total_scanned_bytes)} tệp tin rác có thể dọn dẹp.",
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def _update_clean_button_state(self):
        has_selection = False
        for cat_id, info in self.category_cards.items():
            if info['checkbox'].isChecked():
                cat_data = self.scanned_categories.get(cat_id)
                if cat_data and cat_data['size'] > 0:
                    has_selection = True
                    break
        self.btn_clean.setEnabled(has_selection)

    def start_clean(self):
        animate_button_bounce(self.btn_clean)
        items_to_clean = []
        for cat_id, info in self.category_cards.items():
            if info['checkbox'].isChecked():
                cat_data = self.scanned_categories.get(cat_id)
                if cat_data:
                    items_to_clean.extend(cat_data['items'])

        if not items_to_clean:
            return

        self.btn_scan.setEnabled(False)
        self.btn_clean.setEnabled(False)
        self.progress_bar.setValue(0)

        def _worker():
            def cb(msg, val):
                self.signals.progress.emit(msg, int(val))

            cleaned = self.cleaner.clean_all(items_to_clean, progress_callback=cb)
            self.signals.clean_done.emit(cleaned)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_clean_done(self, cleaned_bytes):
        self.btn_scan.setEnabled(True)
        SmoothAnimationHelper.animate_progress_bar(self.progress_bar, 100)
        self.status_label.setText(f"Dọn dẹp hoàn tất! Đã giải phóng {format_size(cleaned_bytes)}.")

        # Rolling countdown animation on cleaned category sizes (Phương án 1)
        for cat_id, info in self.category_cards.items():
            if info['checkbox'].isChecked():
                cat_data = self.scanned_categories.get(cat_id)
                if cat_data and cat_data['size'] > 0:
                    NumberRollAnimation(info['size_label'], cat_data['size'], 0, duration=800).start()

        # Smooth fade-out of the results table before re-scanning (Phương án 3)
        TableFadeOutHelper.fade_out_table(self.table, duration=300, on_finished=self.start_scan)

        InfoBar.success(
            title="Dọn dẹp thành công!",
            content=f"Đã giải phóng thành công {format_size(cleaned_bytes)} không gian ổ đĩa.",
            position=InfoBarPosition.TOP,
            duration=4000,
            parent=self
        )
