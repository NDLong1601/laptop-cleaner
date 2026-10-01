from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from qfluentwidgets import (
    TitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    PrimaryPushButton, PushButton, SwitchButton, CheckBox, ComboBox,
    CardWidget, FluentIcon as FI, InfoBar, InfoBarPosition
)

from core.scheduler_manager import SchedulerManager


class SchedulerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SchedulerTab")
        self.sm = SchedulerManager()
        self.config = self.sm.load_config()

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 24, 36, 24)
        main_layout.setSpacing(18)

        # 1. Header
        title_box = QVBoxLayout()
        title_box.addWidget(TitleLabel("Lên Lịch Tự Động Tối Ưu (Auto-Clean Scheduler)", self))
        sub = BodyLabel("Thiết lập tự động dọn dẹp định kỳ và nhận cảnh báo khi ổ đĩa hệ thống sắp đầy dung lượng.", self)
        sub.setStyleSheet("color: #888888;")
        title_box.addWidget(sub)
        main_layout.addLayout(title_box)

        # 2. Main Auto-switches Card
        switches_card = CardWidget(self)
        sw_layout = QVBoxLayout(switches_card)
        sw_layout.setContentsMargins(22, 16, 22, 16)
        sw_layout.setSpacing(16)

        # Switch 1: Startup Auto-Clean
        row1 = QHBoxLayout()
        vbox1 = QVBoxLayout()
        vbox1.addWidget(StrongBodyLabel("Tự động dọn rác khi khởi động Windows", switches_card))
        desc1 = CaptionLabel("Tự động quét và dọn sạch file tạm thời khi người dùng vừa đăng nhập vào máy tính.", switches_card)
        desc1.setStyleSheet("color: #888888;")
        vbox1.addWidget(desc1)
        row1.addLayout(vbox1, stretch=1)

        self.sw_startup = SwitchButton(switches_card)
        self.sw_startup.setChecked(self.config.get("auto_clean_on_startup", False))
        row1.addWidget(self.sw_startup)
        sw_layout.addLayout(row1)

        # Switch 2: Low Disk Alert
        row2 = QHBoxLayout()
        vbox2 = QVBoxLayout()
        vbox2.addWidget(StrongBodyLabel("Cảnh báo khi ổ đĩa hệ thống (C:) sắp đầy", switches_card))
        desc2 = CaptionLabel("Hiển thị thông báo khi dung lượng trống của ổ C: tụt xuống dưới ngưỡng cho phép.", switches_card)
        desc2.setStyleSheet("color: #888888;")
        vbox2.addWidget(desc2)
        row2.addLayout(vbox2, stretch=1)

        self.sw_low_disk = SwitchButton(switches_card)
        self.sw_low_disk.setChecked(self.config.get("low_disk_alert", True))
        row2.addWidget(self.sw_low_disk)
        sw_layout.addLayout(row2)

        main_layout.addWidget(switches_card)

        # 3. Parameters Card
        params_card = CardWidget(self)
        p_layout = QGridLayout(params_card)
        p_layout.setContentsMargins(22, 16, 22, 16)
        p_layout.setSpacing(14)

        p_layout.addWidget(StrongBodyLabel("Ngưỡng cảnh báo ổ đĩa C:"), 0, 0)
        self.combo_disk_threshold = ComboBox(params_card)
        self.combo_disk_threshold.addItems(["Dưới 10% dung lượng trống", "Dưới 15% dung lượng trống", "Dưới 20% dung lượng trống"])
        thresh_map = {10: 0, 15: 1, 20: 2}
        self.combo_disk_threshold.setCurrentIndex(thresh_map.get(self.config.get("low_disk_threshold_pct", 15), 1))
        p_layout.addWidget(self.combo_disk_threshold, 0, 1)

        p_layout.addWidget(StrongBodyLabel("Tần suất dọn dẹp khuyến nghị:"), 1, 0)
        self.combo_freq = ComboBox(params_card)
        self.combo_freq.addItems(["Hàng tuần (Khuyến nghị)", "Hàng ngày", "Mỗi khi khởi động máy", "Chỉ dọn thủ công"])
        freq_map = {"weekly": 0, "daily": 1, "startup": 2, "manual": 3}
        self.combo_freq.setCurrentIndex(freq_map.get(self.config.get("schedule_frequency", "weekly"), 0))
        p_layout.addWidget(self.combo_freq, 1, 1)

        main_layout.addWidget(params_card)

        # 4. Target Categories for Auto-Clean
        targets_card = CardWidget(self)
        t_layout = QVBoxLayout(targets_card)
        t_layout.setContentsMargins(22, 16, 22, 16)
        t_layout.setSpacing(10)

        t_layout.addWidget(StrongBodyLabel("Hạng mục cho phép tự động dọn dẹp:", targets_card))

        self.chk_temp = CheckBox("File tạm thời hệ thống (%TEMP%, Windows Temp)", targets_card)
        self.chk_temp.setChecked(self.config.get("clean_temp", True))

        self.chk_logs = CheckBox("Nhật ký lỗi & Crash dumps cũ (.log, .dmp)", targets_card)
        self.chk_logs.setChecked(self.config.get("clean_logs", True))

        self.chk_recycle = CheckBox("Thùng rác hệ thống (Recycle Bin)", targets_card)
        self.chk_recycle.setChecked(self.config.get("clean_recycle_bin", False))

        t_layout.addWidget(self.chk_temp)
        t_layout.addWidget(self.chk_logs)
        t_layout.addWidget(self.chk_recycle)

        main_layout.addWidget(targets_card)

        # 5. Save Button
        btn_row = QHBoxLayout()
        btn_save = PrimaryPushButton(FI.SAVE, "💾 Lưu Cấu Hình Lên Lịch", self)
        btn_save.setFixedSize(220, 42)
        btn_save.clicked.connect(self._save_settings)
        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        main_layout.addLayout(btn_row)

        main_layout.addStretch()

    def _save_settings(self):
        thresh_values = [10, 15, 20]
        freq_values = ["weekly", "daily", "startup", "manual"]

        new_cfg = {
            "auto_clean_on_startup": self.sw_startup.isChecked(),
            "low_disk_alert": self.sw_low_disk.isChecked(),
            "low_disk_threshold_pct": thresh_values[self.combo_disk_threshold.currentIndex()],
            "schedule_frequency": freq_values[self.combo_freq.currentIndex()],
            "clean_temp": self.chk_temp.isChecked(),
            "clean_logs": self.chk_logs.isChecked(),
            "clean_recycle_bin": self.chk_recycle.isChecked()
        }

        success, note = self.sm.save_config(new_cfg)

        # Sync startup entry if user changed startup auto-clean
        self.sm.sync_startup_registration(self.sw_startup.isChecked())

        if success:
            InfoBar.success(
                title="Đã lưu cài đặt!",
                content="Lịch tự động và các cấu hình cảnh báo đã được áp dụng.",
                position=InfoBarPosition.TOP,
                duration=3500,
                parent=self
            )
        else:
            InfoBar.error(
                title="Lỗi lưu cấu hình",
                content=note,
                position=InfoBarPosition.TOP,
                duration=3500,
                parent=self
            )
