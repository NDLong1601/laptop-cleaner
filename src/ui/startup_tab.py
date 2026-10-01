import threading
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem
)
from qfluentwidgets import (
    TitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    PrimaryPushButton, PushButton, SearchLineEdit, TableWidget,
    FluentIcon as FI, InfoBar, InfoBarPosition
)

from core.startup_manager import StartupManager
from .animations import animate_button_bounce, TableFadeOutHelper


class StartupSignals(QObject):
    loaded = pyqtSignal(list)
    action_done = pyqtSignal(bool, str)


class StartupTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("StartupTab")
        self.sm = StartupManager()
        self.signals = StartupSignals()
        self.signals.loaded.connect(self._on_loaded)
        self.signals.action_done.connect(self._on_action_done)

        self.apps = []

        self._init_ui()
        self.refresh_list()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 24, 36, 24)
        main_layout.setSpacing(16)

        # 1. Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.addWidget(TitleLabel("Ứng Dụng Khởi Động Cùng Windows", self))
        self.sub_label = BodyLabel("Tắt các ứng dụng không cần thiết để tăng tốc độ bật máy laptop.", self)
        self.sub_label.setStyleSheet("color: #888888;")
        title_box.addWidget(self.sub_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_refresh = PushButton(FI.SYNC, "Làm Mới", self)
        self.btn_refresh.setFixedHeight(38)
        self.btn_refresh.clicked.connect(self.refresh_list)

        self.btn_disable = PushButton(FI.POWER_BUTTON, "Vô Hiệu Hóa", self)
        self.btn_disable.setFixedHeight(38)
        self.btn_disable.clicked.connect(self.disable_selected)

        self.btn_enable = PrimaryPushButton(FI.POWER_BUTTON, "Kích Hoạt Lại", self)
        self.btn_enable.setFixedHeight(38)
        self.btn_enable.clicked.connect(self.enable_selected)

        header_layout.addWidget(self.btn_refresh)
        header_layout.addWidget(self.btn_disable)
        header_layout.addWidget(self.btn_enable)
        main_layout.addLayout(header_layout)

        # 2. Search box
        self.search_box = SearchLineEdit(self)
        self.search_box.setPlaceholderText("Tìm kiếm ứng dụng khởi động...")
        self.search_box.textChanged.connect(self._filter_table)
        main_layout.addWidget(self.search_box)

        # 3. Table — column order: Tên | Trạng Thái | Phạm Vi | Lệnh/Đường Dẫn
        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Tên Ứng Dụng", "Trạng Thái", "Phạm Vi", "Lệnh / Đường Dẫn"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(TableWidget.SelectionMode.SingleSelection)
        main_layout.addWidget(self.table)

    def refresh_list(self):
        animate_button_bounce(self.btn_refresh)
        self.btn_refresh.setEnabled(False)
        self.sub_label.setText("Đang tải danh sách ứng dụng khởi động...")

        def _worker():
            apps = self.sm.get_startup_apps()
            self.signals.loaded.emit(apps)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_loaded(self, apps):
        self.btn_refresh.setEnabled(True)
        self.apps = apps
        enabled_count = sum(1 for a in apps if a['status'] == 'Enabled')
        disabled_count = sum(1 for a in apps if a['status'] == 'Disabled')
        self.sub_label.setText(f"Tìm thấy: {enabled_count} đang bật, {disabled_count} đã tắt")
        self._filter_table()

    def _filter_table(self):
        query = self.search_box.text().strip().lower()
        filtered = [
            a for a in self.apps
            if query in a['name'].lower() or query in a['command'].lower()
        ]

        self.table.setRowCount(len(filtered))
        for row, a in enumerate(filtered):
            name_item = QTableWidgetItem(a['name'])
            cmd_item = QTableWidgetItem(a['command'])
            loc_text = "Người dùng (HKCU)" if a['location'] == 'HKCU' else "Hệ thống (HKLM)"
            loc_item = QTableWidgetItem(loc_text)
            loc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if a['status'] == 'Enabled':
                status_text = "🟢 Đang Bật"
            else:
                status_text = "⚪ Đã Tắt"
                name_item.setForeground(Qt.GlobalColor.gray)
                cmd_item.setForeground(Qt.GlobalColor.gray)

            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, status_item)
            self.table.setItem(row, 2, loc_item)
            self.table.setItem(row, 3, cmd_item)

    def _get_selected_app(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            InfoBar.warning(
                title="Chưa chọn ứng dụng",
                content="Vui lòng nhấp chọn một dòng ứng dụng trong bảng.",
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self
            )
            return None

        row = selected_rows[0].row()
        name = self.table.item(row, 0).text()
        loc_text = self.table.item(row, 2).text()
        loc = "HKCU" if "HKCU" in loc_text else "HKLM"

        for a in self.apps:
            if a['name'] == name and a['location'] == loc:
                return a
        return None

    def disable_selected(self):
        animate_button_bounce(self.btn_disable)
        app = self._get_selected_app()
        if not app:
            return

        if app['status'] == 'Disabled':
            InfoBar.info(
                title="Thông báo",
                content=f"Ứng dụng '{app['name']}' đã ở trạng thái tắt từ trước.",
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self
            )
            return

        success, msg = self.sm.disable_startup_app(app['hkey'], app['key_path'], app['name'], app['command'])
        self._on_action_done(success, msg)

    def enable_selected(self):
        animate_button_bounce(self.btn_enable)
        app = self._get_selected_app()
        if not app:
            return

        if app['status'] == 'Enabled':
            InfoBar.info(
                title="Thông báo",
                content=f"Ứng dụng '{app['name']}' đang được kích hoạt sẵn.",
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self
            )
            return

        success, msg = self.sm.enable_startup_app(app['hkey'], app['key_path'], app['name'], app['command'])
        self._on_action_done(success, msg)

    def _on_action_done(self, success, msg):
        if success:
            InfoBar.success(
                title="Thành công",
                content=msg,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            TableFadeOutHelper.fade_out_table(self.table, duration=200, on_finished=self.refresh_list)
        else:
            InfoBar.error(
                title="Thất bại",
                content=msg,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self
            )
