import os
import time
import platform
import getpass
import threading
import psutil
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame
)
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    PrimaryPushButton, PushButton, CardWidget, ElevatedCardWidget,
    ProgressBar, ProgressRing, FluentIcon as FI, InfoBar, InfoBarPosition,
    SmoothScrollArea
)

from core.cleaner import Cleaner, format_size
from core.ram_optimizer import RAMOptimizer
from core.admin import is_admin
from core.battery_power_manager import BatteryPowerManager
from .animations import (
    SmoothAnimationHelper, MiniWaveWidget, PulseEffect,
    NumberRollAnimation, animate_button_bounce, StaggeredCardEntrance
)


class WorkerSignals(QObject):
    junk_scanned = pyqtSignal(int)
    optimized = pyqtSignal(bool, int, object)


class DashboardTab(SmoothScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("DashboardTab")
        self.setWidgetResizable(True)
        self.setStyleSheet("background-color: transparent; border: none;")

        self.cleaner = Cleaner()
        self.ram_opt = RAMOptimizer()
        self.signals = WorkerSignals()
        self.signals.junk_scanned.connect(self._on_junk_scanned)
        self.signals.optimized.connect(self._on_optimized)

        self.current_junk_bytes = 0

        self.container = QWidget()
        self.container.setStyleSheet("background-color: transparent;")
        self.setWidget(self.container)

        self._init_ui()

        # Timer to auto-update CPU and RAM metrics periodically
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_metrics)
        self.timer.start(2500)

        # Initial metric load
        self.refresh_metrics()
        self.quick_scan_junk()

    def _init_ui(self):
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(36, 20, 36, 30)
        main_layout.setSpacing(18)

        # -------------------------------------------------------------
        # 1. HERO BANNER: HEALTH SCORE & 1-CLICK OPTIMIZATION
        # -------------------------------------------------------------
        hero_card = ElevatedCardWidget(self.container)
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(28, 20, 28, 20)
        hero_layout.setSpacing(20)

        # Health Ring Graphic
        self.health_ring = ProgressRing(hero_card)
        self.health_ring.setFixedSize(85, 85)
        self.health_ring.setValue(85)
        self.health_ring.setStrokeWidth(8)
        hero_layout.addWidget(self.health_ring)

        # Health info text
        health_text_vbox = QVBoxLayout()
        health_text_vbox.setSpacing(4)

        score_title_row = QHBoxLayout()
        score_title_row.setSpacing(10)
        self.health_title = TitleLabel("Trạng Thái: Tốt", hero_card)

        # Separate colored dot indicator (not embedded in text to avoid emoji layout bugs)
        self.health_status_dot = StrongBodyLabel("●", hero_card)
        self.health_status_dot.setStyleSheet("color: #107C41; font-size: 18px;")

        self.health_score_badge = StrongBodyLabel("85 / 100", hero_card)
        self.health_score_badge.setStyleSheet(
            "background-color: #107C41; color: white; padding: 2px 10px; border-radius: 10px; font-size: 13px;"
        )
        self.pulse_effect = PulseEffect(self.health_score_badge)

        score_title_row.addWidget(self.health_title)
        score_title_row.addWidget(self.health_status_dot)
        score_title_row.addWidget(self.health_score_badge)
        score_title_row.addStretch()
        health_text_vbox.addLayout(score_title_row)

        self.health_desc = BodyLabel(
            "Hệ thống đang hoạt động ổn định. Khuyến nghị quét rác và tối ưu RAM định kỳ.",
            hero_card
        )
        self.health_desc.setStyleSheet("color: #888888;")
        health_text_vbox.addWidget(self.health_desc)

        hero_layout.addLayout(health_text_vbox, stretch=1)

        # Big 1-Click Optimize Button — NO emoji in string to prevent icon collision
        self.btn_quick_optimize = PrimaryPushButton(FI.SPEED_HIGH, "Tối Ưu Nhanh 1-Click", hero_card)
        self.btn_quick_optimize.setFixedSize(210, 48)
        self.btn_quick_optimize.clicked.connect(self.quick_optimize_all)
        hero_layout.addWidget(self.btn_quick_optimize)

        main_layout.addWidget(hero_card)

        # -------------------------------------------------------------
        # 2. SYSTEM RESOURCE METRICS (4 CARDS GRID)
        # -------------------------------------------------------------
        cards_grid = QGridLayout()
        cards_grid.setSpacing(16)

        # === Card 1: RAM ===
        self.ram_card = CardWidget(self.container)
        ram_layout = QVBoxLayout(self.ram_card)
        ram_layout.setContentsMargins(20, 16, 20, 16)
        ram_layout.setSpacing(8)

        ram_header = QHBoxLayout()
        ram_header.addWidget(StrongBodyLabel("🧠 Bộ Nhớ RAM", self.ram_card))
        ram_header.addStretch()
        self.ram_percent_label = StrongBodyLabel("0%", self.ram_card)
        self.ram_percent_label.setStyleSheet("color: #0078D4; font-size: 18px; font-weight: bold;")
        ram_header.addWidget(self.ram_percent_label)
        ram_layout.addLayout(ram_header)

        self.ram_bar = ProgressBar(self.ram_card)
        self.ram_bar.setFixedHeight(8)
        ram_layout.addWidget(self.ram_bar)

        # Live Real-Time Mini Wave Graph for RAM
        self.ram_wave = MiniWaveWidget(color_hex="#0078D4", parent=self.ram_card)
        ram_layout.addWidget(self.ram_wave)

        self.ram_detail_label = CaptionLabel("Đang tải dữ liệu...", self.ram_card)
        self.ram_detail_label.setStyleSheet("color: #888888;")
        ram_layout.addWidget(self.ram_detail_label)

        self.ram_top_app_label = CaptionLabel("🔥 Đang đọc tiến trình ngốn RAM...", self.ram_card)
        self.ram_top_app_label.setStyleSheet("color: #D83B01; font-weight: bold;")
        ram_layout.addWidget(self.ram_top_app_label)

        btn_flush_ram = PushButton(FI.SPEED_HIGH, "Thu Hồi RAM", self.ram_card)
        btn_flush_ram.setFixedHeight(30)
        btn_flush_ram.clicked.connect(self._flush_ram_only)
        ram_layout.addWidget(btn_flush_ram, alignment=Qt.AlignmentFlag.AlignLeft)

        cards_grid.addWidget(self.ram_card, 0, 0)

        # === Card 2: CPU & Processes ===
        self.cpu_card = CardWidget(self.container)
        cpu_layout = QVBoxLayout(self.cpu_card)
        cpu_layout.setContentsMargins(20, 16, 20, 16)
        cpu_layout.setSpacing(8)

        cpu_header = QHBoxLayout()
        cpu_header.addWidget(StrongBodyLabel("⚡ Bộ Xử Lý (CPU)", self.cpu_card))
        cpu_header.addStretch()
        self.cpu_percent_label = StrongBodyLabel("0%", self.cpu_card)
        self.cpu_percent_label.setStyleSheet("color: #107C41; font-size: 18px; font-weight: bold;")
        cpu_header.addWidget(self.cpu_percent_label)
        cpu_layout.addLayout(cpu_header)

        self.cpu_bar = ProgressBar(self.cpu_card)
        self.cpu_bar.setFixedHeight(8)
        cpu_layout.addWidget(self.cpu_bar)

        # Live Real-Time Mini Wave Graph for CPU
        self.cpu_wave = MiniWaveWidget(color_hex="#107C41", parent=self.cpu_card)
        cpu_layout.addWidget(self.cpu_wave)

        cores = psutil.cpu_count(logical=True)
        self.cpu_detail_label = CaptionLabel(f"0 tiến trình | {cores} Luồng xử lý", self.cpu_card)
        self.cpu_detail_label.setStyleSheet("color: #888888;")
        cpu_layout.addWidget(self.cpu_detail_label)

        self.cpu_freq_label = CaptionLabel("Tần số hoạt động: Đang cập nhật...", self.cpu_card)
        self.cpu_freq_label.setStyleSheet("color: #107C41;")
        cpu_layout.addWidget(self.cpu_freq_label)

        btn_view_proc = PushButton(FI.APPLICATION, "Xem Tiến Trình", self.cpu_card)
        btn_view_proc.setFixedHeight(30)
        btn_view_proc.clicked.connect(lambda: self._jump_tab("processes_tab"))
        cpu_layout.addWidget(btn_view_proc, alignment=Qt.AlignmentFlag.AlignLeft)

        cards_grid.addWidget(self.cpu_card, 0, 1)

        # === Card 3: Disk C: (System Drive) ===
        self.disk_card = CardWidget(self.container)
        disk_layout = QVBoxLayout(self.disk_card)
        disk_layout.setContentsMargins(20, 16, 20, 16)
        disk_layout.setSpacing(8)

        disk_header = QHBoxLayout()
        disk_header.addWidget(StrongBodyLabel("💾 Ổ Đĩa Hệ Thống (C:)", self.disk_card))
        disk_header.addStretch()
        self.disk_percent_label = StrongBodyLabel("0%", self.disk_card)
        self.disk_percent_label.setStyleSheet("color: #8764B8; font-size: 18px; font-weight: bold;")
        disk_header.addWidget(self.disk_percent_label)
        disk_layout.addLayout(disk_header)

        self.disk_bar = ProgressBar(self.disk_card)
        self.disk_bar.setFixedHeight(8)
        disk_layout.addWidget(self.disk_bar)

        self.disk_detail_label = CaptionLabel("Đang đọc ổ đĩa...", self.disk_card)
        self.disk_detail_label.setStyleSheet("color: #888888;")
        disk_layout.addWidget(self.disk_detail_label)

        self.disk_status_label = CaptionLabel("🟢 Không gian ổ đĩa đang ở mức an toàn", self.disk_card)
        self.disk_status_label.setStyleSheet("color: #107C41;")
        disk_layout.addWidget(self.disk_status_label)

        btn_analyze_disk = PushButton(FI.FOLDER, "Phân Tích Thư Mục", self.disk_card)
        btn_analyze_disk.setFixedHeight(30)
        btn_analyze_disk.clicked.connect(lambda: self._jump_tab("folder_analyzer_tab"))
        disk_layout.addWidget(btn_analyze_disk, alignment=Qt.AlignmentFlag.AlignLeft)

        cards_grid.addWidget(self.disk_card, 1, 0)

        # === Card 4: Junk Files Estimate ===
        self.junk_card = CardWidget(self.container)
        junk_layout = QVBoxLayout(self.junk_card)
        junk_layout.setContentsMargins(20, 16, 20, 16)
        junk_layout.setSpacing(8)

        junk_header = QHBoxLayout()
        junk_header.addWidget(StrongBodyLabel("🗑️ Tệp Rác Có Thể Dọn", self.junk_card))
        junk_header.addStretch()
        self.junk_size_label = StrongBodyLabel("Đang quét...", self.junk_card)
        self.junk_size_label.setStyleSheet("color: #D83B01; font-size: 18px; font-weight: bold;")
        junk_header.addWidget(self.junk_size_label)
        junk_layout.addLayout(junk_header)

        self.junk_bar = ProgressBar(self.junk_card)
        self.junk_bar.setFixedHeight(8)
        self.junk_bar.setValue(0)
        junk_layout.addWidget(self.junk_bar)

        self.junk_desc_label = CaptionLabel("Bao gồm temp, browser cache, logs & crash dumps", self.junk_card)
        self.junk_desc_label.setStyleSheet("color: #888888;")
        junk_layout.addWidget(self.junk_desc_label)

        self.junk_hint_label = CaptionLabel("⚡ Có thể dọn ngay bằng nút 'Tối Ưu Nhanh'", self.junk_card)
        self.junk_hint_label.setStyleSheet("color: #0078D4;")
        junk_layout.addWidget(self.junk_hint_label)

        btn_row = QHBoxLayout()
        btn_clean_now = PushButton(FI.DELETE, "Dọn Rác Chi Tiết", self.junk_card)
        btn_clean_now.setFixedHeight(30)
        btn_clean_now.clicked.connect(lambda: self._jump_tab("cleaner_tab"))

        btn_rescan = PushButton(FI.SYNC, "Quét Lại", self.junk_card)
        btn_rescan.setFixedHeight(30)
        btn_rescan.clicked.connect(self.quick_scan_junk)

        btn_row.addWidget(btn_clean_now)
        btn_row.addWidget(btn_rescan)
        btn_row.addStretch()
        junk_layout.addLayout(btn_row)

        cards_grid.addWidget(self.junk_card, 1, 1)

        main_layout.addLayout(cards_grid)

        # -------------------------------------------------------------
        # 3. SYSTEM HARDWARE & LAPTOP POWER STATUS
        # -------------------------------------------------------------
        specs_card = CardWidget(self.container)
        specs_layout = QVBoxLayout(specs_card)
        specs_layout.setContentsMargins(22, 16, 22, 16)
        specs_layout.setSpacing(10)

        specs_header = QHBoxLayout()
        specs_header.addWidget(StrongBodyLabel("🖥️ Thông Tin Thiết Bị & Trạng Thái Laptop", specs_card))
        specs_header.addStretch()
        self.uptime_label = CaptionLabel("Thời gian chạy: Đang tính...", specs_card)
        self.uptime_label.setStyleSheet("color: #0078D4; font-weight: bold;")
        specs_header.addWidget(self.uptime_label)
        specs_layout.addLayout(specs_header)

        specs_grid = QGridLayout()
        specs_grid.setSpacing(8)

        os_name = f"{platform.system()} {platform.release()} ({platform.architecture()[0]})"
        comp_name = f"{os.environ.get('COMPUTERNAME', 'Windows-PC')} / {getpass.getuser()}"
        admin_status = "Đang chạy quyền Administrator" if is_admin() else "Chế độ Standard User"

        specs_grid.addWidget(CaptionLabel("Hệ điều hành:"), 0, 0)
        specs_grid.addWidget(StrongBodyLabel(os_name, specs_card), 0, 1)

        specs_grid.addWidget(CaptionLabel("Tên máy / Người dùng:"), 0, 2)
        specs_grid.addWidget(StrongBodyLabel(comp_name, specs_card), 0, 3)

        specs_grid.addWidget(CaptionLabel("Quyền thực thi:"), 1, 0)
        specs_grid.addWidget(StrongBodyLabel(admin_status, specs_card), 1, 1)

        specs_grid.addWidget(CaptionLabel("Vi xử lý (CPU):"), 1, 2)
        specs_grid.addWidget(StrongBodyLabel(platform.processor() or "Intel/AMD x64 Processor", specs_card), 1, 3)

        # Laptop Battery Status Row
        specs_grid.addWidget(CaptionLabel("Trạng thái Nguồn / Pin:"), 2, 0)
        self.battery_status_lbl = StrongBodyLabel("Đang đọc dữ liệu pin...", specs_card)
        specs_grid.addWidget(self.battery_status_lbl, 2, 1)

        specs_grid.addWidget(CaptionLabel("Chế độ nguồn hiện tại:"), 2, 2)
        self.active_plan_lbl = StrongBodyLabel("Đang đọc...", specs_card)
        specs_grid.addWidget(self.active_plan_lbl, 2, 3)

        specs_layout.addLayout(specs_grid)
        main_layout.addWidget(specs_card)

        # -------------------------------------------------------------
        # 4. QUICK ACTION SHORTCUT HUB (2 Rows of Clean Tools)
        # -------------------------------------------------------------
        quick_hub = CardWidget(self.container)
        hub_layout = QVBoxLayout(quick_hub)
        hub_layout.setContentsMargins(22, 16, 22, 16)
        hub_layout.setSpacing(12)

        hub_layout.addWidget(StrongBodyLabel("⚡ Truy Cập Nhanh Toàn Bộ Công Cụ", quick_hub))

        # Row 1
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        btn_c1 = PushButton(FI.DELETE, "Dọn Rác Hệ Thống", quick_hub)
        btn_c1.setFixedHeight(36)
        btn_c1.clicked.connect(lambda: self._jump_tab("cleaner_tab"))

        btn_c2 = PushButton(FI.FOLDER, "Phân Tích AppData", quick_hub)
        btn_c2.setFixedHeight(36)
        btn_c2.clicked.connect(lambda: self._jump_tab("folder_analyzer_tab"))

        btn_c3 = PushButton(FI.COPY, "Tìm Tệp Trùng Lặp", quick_hub)
        btn_c3.setFixedHeight(36)
        btn_c3.clicked.connect(lambda: self._jump_tab("duplicate_tab"))

        btn_c4 = PushButton(FI.PIE_SINGLE, "Tệp Dung Lượng Khủng", quick_hub)
        btn_c4.setFixedHeight(36)
        btn_c4.clicked.connect(lambda: self._jump_tab("large_files_tab"))

        row1.addWidget(btn_c1)
        row1.addWidget(btn_c2)
        row1.addWidget(btn_c3)
        row1.addWidget(btn_c4)
        hub_layout.addLayout(row1)

        # Row 2
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        btn_c5 = PushButton(FI.FINGERPRINT, "Dấu Vết Riêng Tư", quick_hub)
        btn_c5.setFixedHeight(36)
        btn_c5.clicked.connect(lambda: self._jump_tab("privacy_tab"))

        btn_c6 = PushButton(FI.APPLICATION, "Gỡ Ứng Dụng", quick_hub)
        btn_c6.setFixedHeight(36)
        btn_c6.clicked.connect(lambda: self._jump_tab("uninstaller_tab"))

        btn_c7 = PushButton(FI.POWER_BUTTON, "Khởi Động Cùng Win", quick_hub)
        btn_c7.setFixedHeight(36)
        btn_c7.clicked.connect(lambda: self._jump_tab("startup_tab"))

        btn_c8 = PushButton(FI.BRIGHTNESS, "Pin & Hiệu Năng", quick_hub)
        btn_c8.setFixedHeight(36)
        btn_c8.clicked.connect(lambda: self._jump_tab("battery_tab"))

        row2.addWidget(btn_c5)
        row2.addWidget(btn_c6)
        row2.addWidget(btn_c7)
        row2.addWidget(btn_c8)
        hub_layout.addLayout(row2)

        main_layout.addWidget(quick_hub)

        # Staggered card entrance animation on load (Phương án 8)
        StaggeredCardEntrance.animate_cards([
            hero_card, self.ram_card, self.cpu_card, self.disk_card, self.junk_card, specs_card, quick_hub
        ])

    def _jump_tab(self, tab_attr_name):
        win = self.window()
        if hasattr(win, tab_attr_name):
            target_widget = getattr(win, tab_attr_name)
            if hasattr(win, "switchTo"):
                win.switchTo(target_widget)

    def refresh_metrics(self):
        """Update live CPU, RAM, Disk, Uptime, Battery and Health Score."""
        try:
            # 1. RAM
            mem = self.ram_opt.get_memory_info()
            used_gb = mem['used'] / (1024 ** 3)
            total_gb = mem['total'] / (1024 ** 3)
            free_gb = mem['available'] / (1024 ** 3)
            ram_pct = int(mem['percent'])

            # 1. RAM Animation & Wave update
            self.ram_percent_label.setText(f"{ram_pct}%")
            SmoothAnimationHelper.animate_progress_bar(self.ram_bar, ram_pct)
            self.ram_wave.add_point(ram_pct)
            self.ram_detail_label.setText(f"Đã dùng: {used_gb:.1f} GB / {total_gb:.1f} GB (Còn trống: {free_gb:.1f} GB)")

            # Find top RAM process
            try:
                top_p = None
                max_m = 0
                for p in psutil.process_iter(['name', 'memory_info']):
                    m = p.info['memory_info'].rss
                    if m > max_m:
                        max_m = m
                        top_p = p.info['name']
                if top_p:
                    self.ram_top_app_label.setText(f"🔥 Ngốn RAM nhất: {top_p} ({format_size(max_m)})")
            except Exception:
                pass

            # 2. CPU Animation & Wave update
            cpu = psutil.cpu_percent()
            cpu_pct = int(cpu)
            self.cpu_percent_label.setText(f"{cpu_pct}%")
            SmoothAnimationHelper.animate_progress_bar(self.cpu_bar, cpu_pct)
            self.cpu_wave.add_point(cpu_pct)
            num_proc = len(psutil.pids())
            cores = psutil.cpu_count(logical=True)
            self.cpu_detail_label.setText(f"{num_proc} tiến trình đang chạy ngầm | {cores} luồng")

            # CPU frequency
            try:
                freq = psutil.cpu_freq()
                if freq and freq.current:
                    self.cpu_freq_label.setText(f"Xung nhịp hiện tại: {freq.current / 1000:.2f} GHz")
            except Exception:
                pass

            # 3. Disk C: Animation
            du = psutil.disk_usage("C:")
            disk_pct = int(du.percent)
            disk_free_gb = du.free / (1024 ** 3)
            disk_total_gb = du.total / (1024 ** 3)
            disk_used_gb = du.used / (1024 ** 3)

            self.disk_percent_label.setText(f"{disk_pct}%")
            SmoothAnimationHelper.animate_progress_bar(self.disk_bar, disk_pct)
            self.disk_detail_label.setText(f"Đã dùng: {disk_used_gb:.1f} GB / {disk_total_gb:.1f} GB (Còn trống: {disk_free_gb:.1f} GB)")

            if disk_pct >= 90:
                self.disk_status_label.setText("🔴 Ổ C: Đang sắp đầy! Hãy dọn dẹp ngay.")
                self.disk_status_label.setStyleSheet("color: #E81123; font-weight: bold;")
            elif disk_pct >= 80:
                self.disk_status_label.setText("🟡 Ổ C: Cần chú ý dọn dẹp bớt tệp không cần thiết.")
                self.disk_status_label.setStyleSheet("color: #D83B01;")
            else:
                self.disk_status_label.setText("🟢 Ổ C: Không gian lưu trữ đang rất thoải mái.")
                self.disk_status_label.setStyleSheet("color: #107C41;")

            # 4. System Uptime
            uptime_sec = time.time() - psutil.boot_time()
            hours = int(uptime_sec // 3600)
            mins = int((uptime_sec % 3600) // 60)
            self.uptime_label.setText(f"Thời gian hoạt động liên tục: {hours} giờ {mins} phút")

            # 5. Laptop Battery & Power Plan Status
            batt_info = BatteryPowerManager.get_battery_info()
            self.battery_status_lbl.setText(batt_info["status_text"])

            plans = BatteryPowerManager.get_power_plans()
            active_plan = next((p["name"] for p in plans if p["is_active"]), "Tiêu chuẩn Windows")
            self.active_plan_lbl.setText(active_plan)

            # 6. Evaluate Health Score with Spring Animation
            score = 100
            reasons = []
            if ram_pct > 85:
                score -= 20
                reasons.append(f"RAM đang dùng cao ({ram_pct}%)")
            elif ram_pct > 70:
                score -= 10

            if cpu_pct > 80:
                score -= 20
                reasons.append(f"CPU tải nặng ({cpu_pct}%)")
            elif cpu_pct > 50:
                score -= 10

            if disk_pct > 90:
                score -= 25
                reasons.append("Ổ C: sắp đầy")
            elif disk_pct > 80:
                score -= 10

            if self.current_junk_bytes > 3 * 1024 ** 3:
                score -= 15
                reasons.append(f"Tệp rác nhiều (~{format_size(self.current_junk_bytes)})")
            elif self.current_junk_bytes > 500 * 1024 ** 2:
                score -= 8
                reasons.append(f"Có ~{format_size(self.current_junk_bytes)} rác")

            score = max(20, min(100, score))
            SmoothAnimationHelper.animate_progress_ring(self.health_ring, score)
            self.health_score_badge.setText(f"{score} / 100")

            if score >= 85:
                self.pulse_effect.stop()
                self.health_title.setText("Trạng Thái: Rất Tốt")
                self.health_status_dot.setStyleSheet("color: #107C41; font-size: 18px;")
                self.health_score_badge.setStyleSheet(
                    "background-color: #107C41; color: white; padding: 2px 10px; border-radius: 10px; font-size: 13px;"
                )
                self.health_desc.setText("Máy tính hoạt động trơn tru, tài nguyên RAM & ổ đĩa ở trạng thái dồi dào.")
            elif score >= 65:
                self.pulse_effect.start()  # Breathing pulse glow when attention is needed
                self.health_title.setText("Trạng Thái: Cần Tối Ưu")
                self.health_status_dot.setStyleSheet("color: #D83B01; font-size: 18px;")
                self.health_score_badge.setStyleSheet(
                    "background-color: #D83B01; color: white; padding: 2px 10px; border-radius: 10px; font-size: 13px;"
                )
                reason_str = " | ".join(reasons) if reasons else "Khuyến nghị chạy Tối Ưu Nhanh"
                self.health_desc.setText(f"Cảnh báo: {reason_str}. Bấm nút bên phải để xử lý ngay.")
            else:
                self.pulse_effect.start()  # Breathing pulse glow on overload
                self.health_title.setText("Trạng Thái: Quá Tải")
                self.health_status_dot.setStyleSheet("color: #E81123; font-size: 18px;")
                self.health_score_badge.setStyleSheet(
                    "background-color: #E81123; color: white; padding: 2px 10px; border-radius: 10px; font-size: 13px;"
                )
                self.health_desc.setText("Bộ nhớ RAM hoặc ổ cứng đang tiệm cận mức đầy. Hãy dọn dẹp ngay để tránh giật lag.")

        except Exception:
            pass

    def quick_scan_junk(self):
        self.junk_size_label.setText("Đang tính toán...")

        def _worker():
            _, total = self.cleaner.scan_junk()
            self.signals.junk_scanned.emit(total)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_junk_scanned(self, total):
        self.current_junk_bytes = total
        self.junk_size_label.setText(format_size(total))
        pct = min(100, int((total / (10 * 1024 ** 3)) * 100))
        SmoothAnimationHelper.animate_progress_bar(self.junk_bar, pct)
        self.refresh_metrics()

    def _flush_ram_only(self):
        success, freed, after = self.ram_opt.optimize()
        self.refresh_metrics()
        if success and freed > 0:
            InfoBar.success(
                title="Đã giải phóng RAM",
                content=f"Đã thu hồi thành công ~{format_size(freed)} bộ nhớ đệm.",
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            InfoBar.info(
                title="RAM đã tối ưu",
                content="Bộ nhớ hiện tại đã ở trạng thái tối ưu.",
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self
            )

    def quick_optimize_all(self):
        """1-Click quick optimization: cleans temp + frees RAM."""
        animate_button_bounce(self.btn_quick_optimize)
        self.btn_quick_optimize.setEnabled(False)
        self.btn_quick_optimize.setText("Đang tối ưu...")

        def _worker():
            cats = self.cleaner.scan_categories()
            items_to_clean = cats['windows_temp']['items'] + cats['logs_dumps']['items']
            cleaned_bytes = self.cleaner.clean_all(items_to_clean)
            success, freed_ram, after_mem = self.ram_opt.optimize()
            self.signals.optimized.emit(success, cleaned_bytes + freed_ram, after_mem)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_optimized(self, success, total_freed, after_mem):
        self.btn_quick_optimize.setEnabled(True)
        self.btn_quick_optimize.setText("Tối Ưu Nhanh 1-Click")

        # Rolling counter animation from current junk down to 0 (Phương án 1)
        if self.current_junk_bytes > 0:
            NumberRollAnimation(self.junk_size_label, self.current_junk_bytes, 0, duration=800).start()
            self.current_junk_bytes = 0

        self.refresh_metrics()
        self.quick_scan_junk()

        # Celebration spring bounce animation on health ring (Phương án 15)
        SmoothAnimationHelper.animate_progress_ring(self.health_ring, 95, duration=1000)
        self.pulse_effect.stop()

        InfoBar.success(
            title="✨ Tối Ưu Hoàn Tất!",
            content=f"Đã dọn dẹp file rác & tối ưu bộ nhớ working set! (Tổng giải phóng ~{format_size(total_freed)})",
            position=InfoBarPosition.TOP,
            duration=3500,
            parent=self
        )
