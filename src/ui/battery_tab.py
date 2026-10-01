from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from qfluentwidgets import (
    TitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    PrimaryPushButton, PushButton, CardWidget, ElevatedCardWidget,
    ProgressBar, ProgressRing, FluentIcon as FI, InfoBar, InfoBarPosition
)

from core.battery_power_manager import BatteryPowerManager
from .animations import SmoothAnimationHelper, animate_button_bounce, StaggeredCardEntrance


class BatteryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("BatteryTab")
        self.pm = BatteryPowerManager()

        self._init_ui()

        # Update battery every 3 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_battery_info)
        self.timer.start(3000)

        self.update_battery_info()
        self.refresh_power_plans()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 24, 36, 24)
        main_layout.setSpacing(18)

        # 1. Header
        title_box = QVBoxLayout()
        title_box.addWidget(TitleLabel("Quản Lý Pin & Chế Độ Nguồn (Battery & Power)", self))
        sub = BodyLabel("Theo dõi trạng thái pin laptop và chuyển đổi nhanh các chế độ hiệu năng hoặc tiết kiệm pin.", self)
        sub.setStyleSheet("color: #888888;")
        title_box.addWidget(sub)
        main_layout.addLayout(title_box)

        # 2. Battery State Card
        self.batt_card = ElevatedCardWidget(self)
        batt_layout = QHBoxLayout(self.batt_card)
        batt_layout.setContentsMargins(28, 20, 28, 20)
        batt_layout.setSpacing(24)

        self.batt_ring = ProgressRing(self.batt_card)
        self.batt_ring.setFixedSize(85, 85)
        self.batt_ring.setValue(100)
        self.batt_ring.setStrokeWidth(8)
        batt_layout.addWidget(self.batt_ring)

        text_vbox = QVBoxLayout()
        text_vbox.setSpacing(4)
        self.batt_pct_title = TitleLabel("100%", self.batt_card)
        self.batt_status_desc = BodyLabel("Đang đọc trạng thái nguồn...", self.batt_card)
        self.batt_status_desc.setStyleSheet("color: #888888;")

        text_vbox.addWidget(self.batt_pct_title)
        text_vbox.addWidget(self.batt_status_desc)
        batt_layout.addLayout(text_vbox, stretch=1)

        main_layout.addWidget(self.batt_card)

        # 3. Power Mode Selector Section
        main_layout.addWidget(StrongBodyLabel("⚡ Chọn Chế Độ Hiệu Năng Hoạt Động:", self))

        self.plans_container = QVBoxLayout()
        self.plans_container.setSpacing(10)
        main_layout.addLayout(self.plans_container)

        # 4. Tips Card
        tips_card = CardWidget(self)
        tips_layout = QVBoxLayout(tips_card)
        tips_layout.setContentsMargins(20, 14, 20, 14)
        tips_layout.addWidget(StrongBodyLabel("💡 Mẹo tối ưu hóa pin laptop:", tips_card))
        t_desc = CaptionLabel(
            "• Khi làm việc di động ngoài trời: Hãy chuyển sang chế độ 'Tiết Kiệm Pin' (Power Saver) để giảm tải xung nhịp CPU.\n"
            "• Khi cắm sạc AC chơi game hoặc làm đồ họa: Chọn chế độ 'Hiệu Năng Cao' (High Performance) để máy phát huy 100% công suất.\n"
            "• Đóng các tiến trình chạy ngầm không cần thiết trong tab 'Tiến Trình Chạy Ngầm' để tránh hao pin vô ích.",
            tips_card
        )
        t_desc.setStyleSheet("color: #888888; line-height: 1.5;")
        tips_layout.addWidget(t_desc)
        main_layout.addWidget(tips_card)

        main_layout.addStretch()

    def update_battery_info(self):
        info = self.pm.get_battery_info()
        pct = info["percent"]
        SmoothAnimationHelper.animate_progress_ring(self.batt_ring, pct)
        self.batt_pct_title.setText(f"{pct}%")
        self.batt_status_desc.setText(info["status_text"])

    def refresh_power_plans(self):
        # Clear existing cards
        while self.plans_container.count():
            item = self.plans_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        plans = self.pm.get_power_plans()

        if not plans:
            lbl = CaptionLabel("Không tìm thấy cấu hình nguồn trên hệ thống.", self)
            self.plans_container.addWidget(lbl)
            return

        for p in plans:
            card = CardWidget(self)
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(20, 12, 20, 12)

            name = p["name"]
            guid = p["guid"]
            is_active = p["is_active"]

            # Icon & title
            icon_tag = "⚡" if "high" in name.lower() or "hiệu năng" in name.lower() else ("🍃" if "saver" in name.lower() or "tiết kiệm" in name.lower() else "⚖️")

            title_lbl = StrongBodyLabel(f"{icon_tag} {name}", card)
            c_layout.addWidget(title_lbl)
            c_layout.addStretch()

            if is_active:
                active_badge = StrongBodyLabel("🟢 ĐANG HOẠT ĐỘNG", card)
                active_badge.setStyleSheet("color: #107C41; font-weight: bold;")
                c_layout.addWidget(active_badge)
            else:
                btn_activate = PrimaryPushButton("Kích Hoạt", card)
                btn_activate.setFixedHeight(32)
                btn_activate.clicked.connect(lambda checked, b=btn_activate, g=guid: (animate_button_bounce(b), self._activate_plan(g)))
                c_layout.addWidget(btn_activate)

            self.plans_container.addWidget(card)

        # Power mode transition animation (Phương án 9)
        cards = [self.plans_container.itemAt(i).widget() for i in range(self.plans_container.count()) if self.plans_container.itemAt(i).widget()]
        StaggeredCardEntrance.animate_cards(cards, base_delay=30, step_delay=40, duration=260)

    def _activate_plan(self, guid):
        success, note = self.pm.set_active_plan(guid)
        if success:
            InfoBar.success(
                title="Đã chuyển chế độ nguồn",
                content=note,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            self.refresh_power_plans()
        else:
            InfoBar.error(
                title="Lỗi kích hoạt",
                content=note,
                position=InfoBarPosition.TOP,
                duration=3500,
                parent=self
            )
