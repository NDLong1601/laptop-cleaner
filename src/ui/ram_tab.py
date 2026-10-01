import threading
import psutil
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from qfluentwidgets import (
    TitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    PrimaryPushButton, CardWidget, ElevatedCardWidget,
    ProgressBar, FluentIcon as FI, InfoBar, InfoBarPosition
)

from core.ram_optimizer import RAMOptimizer
from core.cleaner import format_size
from .animations import (
    SmoothAnimationHelper, MiniWaveWidget,
    animate_button_bounce, NumberRollAnimation
)


class RAMSignals(QObject):
    optimized = pyqtSignal(bool, int, object)


class RAMTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("RAMTab")
        self.ram_opt = RAMOptimizer()
        self.signals = RAMSignals()
        self.signals.optimized.connect(self._on_optimized)

        self._init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_info)
        self.timer.start(2000)
        self.update_info()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 24, 36, 24)
        main_layout.setSpacing(20)

        # 1. Header
        title_box = QVBoxLayout()
        title_box.addWidget(TitleLabel("Tối Ưu Hóa Bộ Nhớ RAM", self))
        sub = BodyLabel("Giải phóng bộ nhớ đệm (Working Set) không cần thiết để tăng tốc độ phản hồi cho máy tính.", self)
        sub.setStyleSheet("color: #888888;")
        title_box.addWidget(sub)
        main_layout.addLayout(title_box)

        # 2. Main RAM Card
        ram_main_card = ElevatedCardWidget(self)
        ram_card_layout = QVBoxLayout(ram_main_card)
        ram_card_layout.setContentsMargins(28, 24, 28, 24)
        ram_card_layout.setSpacing(16)

        top_row = QHBoxLayout()
        top_row.addWidget(StrongBodyLabel("Mức Tiêu Thụ RAM Hiện Tại", ram_main_card))
        top_row.addStretch()
        self.percent_big = StrongBodyLabel("0%", ram_main_card)
        self.percent_big.setStyleSheet("font-size: 32px; color: #0078D4; font-weight: bold;")
        top_row.addWidget(self.percent_big)
        ram_card_layout.addLayout(top_row)

        self.progress_bar = ProgressBar(ram_main_card)
        self.progress_bar.setFixedHeight(12)
        ram_card_layout.addWidget(self.progress_bar)

        # Sub info grid
        grid = QGridLayout()
        grid.setSpacing(12)

        self.lbl_total = StrongBodyLabel("0 GB", ram_main_card)
        self.lbl_used = StrongBodyLabel("0 GB", ram_main_card)
        self.lbl_avail = StrongBodyLabel("0 GB", ram_main_card)

        grid.addWidget(CaptionLabel("Tổng Dung Lượng:"), 0, 0)
        grid.addWidget(self.lbl_total, 0, 1)

        grid.addWidget(CaptionLabel("Đang Sử Dụng:"), 1, 0)
        grid.addWidget(self.lbl_used, 1, 1)

        grid.addWidget(CaptionLabel("Còn Khả Dụng:"), 2, 0)
        grid.addWidget(self.lbl_avail, 2, 1)

        ram_card_layout.addLayout(grid)

        # Real-time memory sparkline wave
        self.wave_widget = MiniWaveWidget(color_hex="#0078D4", parent=ram_main_card)
        ram_card_layout.addWidget(self.wave_widget)

        # Action button
        self.btn_optimize = PrimaryPushButton(FI.SPEED_HIGH, "Thu Hồi & Giải Phóng RAM Ngay", ram_main_card)
        self.btn_optimize.setFixedHeight(45)
        self.btn_optimize.clicked.connect(self.start_optimize)
        ram_card_layout.addWidget(self.btn_optimize)

        main_layout.addWidget(ram_main_card)

        # 3. Informational card
        info_card = CardWidget(self)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(20, 16, 20, 16)

        info_layout.addWidget(StrongBodyLabel("💡 Cơ chế hoạt động của RAM Optimizer:", info_card))
        desc = CaptionLabel(
            "Công cụ sử dụng Windows API (SetProcessWorkingSetSize với quyền PROCESS_SET_QUOTA) "
            "để yêu cầu hệ điều hành thu hồi các trang bộ nhớ không còn tích cực sử dụng của các tiến trình ngầm. "
            "Điều này giúp nhường tài nguyên ngay lập tức cho các ứng dụng nặng như Game, Trình duyệt hoặc Đồ họa.",
            info_card
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #888888; line-height: 1.4;")
        info_layout.addWidget(desc)

        main_layout.addWidget(info_card)
        main_layout.addStretch(1)

    def update_info(self):
        try:
            mem = self.ram_opt.get_memory_info()
            pct = int(mem['percent'])
            self.percent_big.setText(f"{pct}%")
            SmoothAnimationHelper.animate_progress_bar(self.progress_bar, pct)
            self.wave_widget.add_point(pct)

            total_gb = mem['total'] / (1024 ** 3)
            used_gb = mem['used'] / (1024 ** 3)
            avail_gb = mem['available'] / (1024 ** 3)

            self.lbl_total.setText(f"{total_gb:.2f} GB")
            self.lbl_used.setText(f"{used_gb:.2f} GB ({pct}%)")
            self.lbl_avail.setText(f"{avail_gb:.2f} GB")
        except Exception:
            pass

    def start_optimize(self):
        animate_button_bounce(self.btn_optimize)
        self.btn_optimize.setEnabled(False)
        self.btn_optimize.setText("Đang giải phóng bộ nhớ...")

        def _worker():
            success, freed, after = self.ram_opt.optimize()
            self.signals.optimized.emit(success, freed, after)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_optimized(self, success, freed, after):
        self.btn_optimize.setEnabled(True)
        self.btn_optimize.setText("Thu Hồi & Giải Phóng RAM Ngay")

        if success and freed > 0 and after:
            try:
                old_pct = int(self.percent_big.text().replace("%", ""))
                new_pct = int(after.percent)
                # Rolling counter down to new percentage (Phương án 1)
                NumberRollAnimation(self.percent_big, old_pct, new_pct, duration=800, is_size=False, suffix="%").start()
            except Exception:
                pass
            self.update_info()
            InfoBar.success(
                title="Tối ưu thành công!",
                content=f"Đã giải phóng ~{format_size(freed)} bộ nhớ RAM.",
                position=InfoBarPosition.TOP,
                duration=3500,
                parent=self
            )
        else:
            self.update_info()
            InfoBar.info(
                title="Bộ nhớ đã ở mức tối ưu",
                content="RAM hiện tại đã được Windows quản lý tốt, không có bộ nhớ thừa cần thu hồi.",
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
