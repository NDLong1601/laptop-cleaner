import threading
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    TitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    PrimaryPushButton, PushButton, CheckBox, CardWidget,
    ProgressBar, FluentIcon as FI, InfoBar, InfoBarPosition, MessageBox
)

from core.privacy_cleaner import PrivacyCleaner
from core.cleaner import format_size
from .animations import SmoothAnimationHelper, animate_button_bounce


class PrivacySignals(QObject):
    progress = pyqtSignal(str, int)
    scan_done = pyqtSignal(dict)
    clean_done = pyqtSignal(int, int)


class PrivacyTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("PrivacyTab")
        self.cleaner = PrivacyCleaner()
        self.signals = PrivacySignals()
        self.signals.progress.connect(self._on_progress)
        self.signals.scan_done.connect(self._on_scan_done)
        self.signals.clean_done.connect(self._on_clean_done)

        self.category_widgets = {}
        self._init_ui()
        self.start_scan()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 24, 36, 24)
        main_layout.setSpacing(16)

        # 1. Header
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.addWidget(TitleLabel("Bảo Mật & Dấu Vết Riêng Tư (Privacy Cleaner)", self))
        sub = BodyLabel("Xóa lịch sử mở tệp gần đây, lệnh Run, JumpLists và bộ nhớ đệm hình ảnh để bảo vệ quyền riêng tư.", self)
        sub.setStyleSheet("color: #888888;")
        title_box.addWidget(sub)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.btn_scan = PushButton(FI.SYNC, "Quét Dấu Vết", self)
        self.btn_scan.setFixedHeight(38)
        self.btn_scan.clicked.connect(self.start_scan)

        self.btn_clean = PrimaryPushButton(FI.DELETE, "Dọn Dẹp Riêng Tư", self)
        self.btn_clean.setFixedHeight(38)
        self.btn_clean.clicked.connect(self._confirm_and_clean)

        header_row.addWidget(self.btn_scan)
        header_row.addWidget(self.btn_clean)
        main_layout.addLayout(header_row)

        # 2. Progress
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.status_label = CaptionLabel("Đang chuẩn bị quét...", self)
        self.status_label.setStyleSheet("color: #888888;")
        main_layout.addWidget(self.status_label)

        # 3. Privacy Category Cards
        items_def = [
            ("recent_files", "📋 Tệp Tin Mở Gần Đây (Recent Items)", "Lịch sử các tài liệu, ảnh, tệp tin vừa mở trên File Explorer"),
            ("jumplists", "📑 Lịch Sử JumpLists Trên Taskbar", "Danh sách các tệp ghim hoặc vừa mở khi chuột phải vào icon trên thanh Taskbar"),
            ("run_mru", "📜 Lịch Sử Hộp Thoại Run (Win + R)", "Lịch sử các câu lệnh và đường dẫn người dùng đã gõ trong hộp thoại Run"),
            ("typed_paths", "🌐 Đường Dẫn Đã Gõ Trong File Explorer", "Lịch sử thanh địa chỉ của Windows Explorer (TypedPaths)"),
            ("thumbnail_cache", "🖼️ Bộ Nhớ Đệm Hình Thu Nhỏ (Thumbnail Cache)", "Các file thumbcache_*.db lưu ảnh thu nhỏ của tài liệu, video và ảnh"),
            ("clipboard", "✂️ Bộ Nhớ Tạm Clipboard", "Nội dung văn bản, hình ảnh đang lưu trong bộ nhớ copy/paste")
        ]

        for cat_id, title, desc in items_def:
            card = CardWidget(self)
            card.setFixedHeight(68)
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(18, 10, 18, 10)
            c_layout.setSpacing(12)

            chk = CheckBox(title, card)
            chk.setChecked(True)

            desc_label = CaptionLabel(desc, card)
            desc_label.setStyleSheet("color: #888888;")

            vbox = QVBoxLayout()
            vbox.setSpacing(2)
            vbox.addWidget(chk)
            vbox.addWidget(desc_label)

            count_label = StrongBodyLabel("Đang quét...", card)
            count_label.setStyleSheet("color: #0078D4; font-size: 14px;")

            c_layout.addLayout(vbox, stretch=1)
            c_layout.addWidget(count_label)

            self.category_widgets[cat_id] = {
                "checkbox": chk,
                "count_label": count_label
            }
            main_layout.addWidget(card)

        main_layout.addStretch()

    def start_scan(self):
        animate_button_bounce(self.btn_scan)
        self.btn_scan.setEnabled(False)
        self.progress_bar.setValue(0)

        for w in self.category_widgets.values():
            w["count_label"].setText("Đang quét...")

        def _worker():
            results = self.cleaner.scan_privacy_items()
            self.signals.scan_done.emit(results)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_progress(self, msg, pct):
        self.status_label.setText(msg)
        SmoothAnimationHelper.animate_progress_bar(self.progress_bar, pct, duration=200)

    def _on_scan_done(self, results):
        self.btn_scan.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_label.setText("Hoàn tất quét dấu vết riêng tư.")

        total_items = 0
        for cat_id, data in results.items():
            if cat_id in self.category_widgets:
                count = data["count"]
                size = data["size"]
                total_items += count
                text = f"{count} mục"
                if size > 0:
                    text += f" ({format_size(size)})"
                self.category_widgets[cat_id]["count_label"].setText(text)

        self.btn_clean.setEnabled(total_items > 0)

    def _confirm_and_clean(self):
        selected_ids = [
            cat_id for cat_id, w in self.category_widgets.items()
            if w["checkbox"].isChecked()
        ]
        if not selected_ids:
            InfoBar.warning(
                title="Chưa chọn danh mục",
                content="Vui lòng tích chọn ít nhất 1 danh mục để dọn dẹp.",
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self
            )
            return

        w = MessageBox(
            "Xác nhận xóa dấu vết",
            "Bạn có chắc muốn dọn sạch lịch sử và các dấu vết riêng tư đã chọn không?",
            self.window()
        )
        if not w.exec():
            return

        animate_button_bounce(self.btn_clean)
        self.btn_clean.setEnabled(False)
        self.btn_scan.setEnabled(False)

        def _worker():
            def cb(m, p):
                self.signals.progress.emit(m, p)

            cleaned_count, freed_bytes = self.cleaner.clean_privacy_categories(selected_ids, progress_callback=cb)
            self.signals.clean_done.emit(cleaned_count, freed_bytes)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_clean_done(self, count, freed_bytes):
        self.btn_scan.setEnabled(True)
        self.btn_clean.setEnabled(True)
        InfoBar.success(
            title="Đã xóa dấu vết riêng tư!",
            content=f"Đã dọn dẹp {count} mục lịch sử ({format_size(freed_bytes)}).",
            position=InfoBarPosition.TOP,
            duration=3500,
            parent=self
        )
        self.start_scan()
