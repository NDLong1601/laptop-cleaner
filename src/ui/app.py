from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon as FI,
    setTheme, Theme, toggleTheme
)

from .dashboard_tab import DashboardTab
from .cleaner_tab import CleanerTab
from .folder_analyzer_tab import FolderAnalyzerTab
from .duplicate_tab import DuplicateTab
from .large_files_tab import LargeFilesTab
from .privacy_tab import PrivacyTab
from .uninstaller_tab import UninstallerTab
from .processes_tab import ProcessesTab
from .ram_tab import RAMTab
from .startup_tab import StartupTab
from .battery_tab import BatteryTab
from .scheduler_tab import SchedulerTab
from core.admin import is_admin


class LaptopCleanerApp(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Laptop Cleaner & Optimizer - Windows 11 Fluent")
        self.resize(1120, 750)
        self.setMinimumSize(920, 620)

        # Center on screen if screen geometry is available
        screen = QApplication.primaryScreen()
        if screen:
            desktop = screen.availableGeometry()
            w, h = desktop.width(), desktop.height()
            self.move(int((w - self.width()) / 2), int((h - self.height()) / 2))

        # Default dark mode
        setTheme(Theme.DARK)

        # Enable Windows 11 Mica translucent blur effect (Phương án 14)
        self.setMicaEffectEnabled(True)

        # Enable smooth animated page transitions (Phương án 11)
        if hasattr(self, 'stackedWidget') and hasattr(self.stackedWidget, 'setAnimationEnabled'):
            self.stackedWidget.setAnimationEnabled(True)

        # Initialize all Tabs
        self.dashboard_tab = DashboardTab(self)
        self.cleaner_tab = CleanerTab(self)
        self.folder_analyzer_tab = FolderAnalyzerTab(self)
        self.duplicate_tab = DuplicateTab(self)
        self.large_files_tab = LargeFilesTab(self)
        self.privacy_tab = PrivacyTab(self)
        self.uninstaller_tab = UninstallerTab(self)
        self.processes_tab = ProcessesTab(self)
        self.ram_tab = RAMTab(self)
        self.startup_tab = StartupTab(self)
        self.battery_tab = BatteryTab(self)
        self.scheduler_tab = SchedulerTab(self)

        self._init_navigation()

    def _init_navigation(self):
        # 1. Main Navigation Items (Categorized for clean workflow)
        self.addSubInterface(
            self.dashboard_tab,
            FI.HOME,
            "Tổng Quan",
            NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.cleaner_tab,
            FI.DELETE,
            "Dọn Rác Hệ Thống",
            NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.folder_analyzer_tab,
            FI.FOLDER,
            "Phân Tích AppData / Thư Mục",
            NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.duplicate_tab,
            FI.COPY,
            "Tìm Tệp Trùng Lặp",
            NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.large_files_tab,
            FI.PIE_SINGLE,
            "Tệp Dung Lượng Khủng",
            NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.privacy_tab,
            FI.FINGERPRINT,
            "Dấu Vết Riêng Tư",
            NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.uninstaller_tab,
            FI.APPLICATION,
            "Gỡ Ứng Dụng",
            NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.processes_tab,
            FI.COMMAND_PROMPT,
            "Tiến Trình Chạy Ngầm",
            NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.ram_tab,
            FI.SPEED_HIGH,
            "Tối Ưu RAM",
            NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.startup_tab,
            FI.POWER_BUTTON,
            "Khởi Động Cùng Win",
            NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.battery_tab,
            FI.BRIGHTNESS,
            "Pin & Hiệu Năng Laptop",
            NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.scheduler_tab,
            FI.DATE_TIME,
            "Lên Lịch Tự Động",
            NavigationItemPosition.TOP
        )

        # 2. Bottom Navigation Items
        admin_text = "Quyền: Quản Trị Viên (Admin)" if is_admin() else "Quyền: Người Dùng (User)"
        self.navigationInterface.addItem(
            routeKey="admin_status",
            icon=FI.CERTIFICATE if is_admin() else FI.INFO,
            text=admin_text,
            onClick=None,
            selectable=False,
            position=NavigationItemPosition.BOTTOM
        )

        self.navigationInterface.addItem(
            routeKey="theme_switch",
            icon=FI.CONSTRACT,
            text="Giao diện Sáng/Tối",
            onClick=lambda: toggleTheme(),
            selectable=False,
            position=NavigationItemPosition.BOTTOM
        )
