import threading
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem, QAbstractItemView
)
from qfluentwidgets import (
    TitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    PrimaryPushButton, PushButton, SearchLineEdit, TableWidget,
    FluentIcon as FI, InfoBar, InfoBarPosition, MessageBox
)

from core.app_manager import AppManager
from .animations import animate_button_bounce, TableFadeOutHelper


class UninstallerSignals(QObject):
    loaded = pyqtSignal(list)
    action_done = pyqtSignal(bool, str)


class UninstallerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("UninstallerTab")
        self.app_manager = AppManager()
        self.signals = UninstallerSignals()
        self.signals.loaded.connect(self._on_loaded)
        self.signals.action_done.connect(self._on_action_done)

        self.apps = []

        self._init_ui()
        self.refresh_apps()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 24, 36, 24)
        main_layout.setSpacing(16)

        # 1. Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.addWidget(TitleLabel("Quản Lý & Gỡ Ứng Dụng", self))
        self.sub_label = BodyLabel("Xem danh sách phần mềm đã cài đặt trên máy và gỡ các ứng dụng không cần thiết.", self)
        self.sub_label.setStyleSheet("color: #888888;")
        title_box.addWidget(self.sub_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_refresh = PushButton(FI.SYNC, "Làm Mới", self)
        self.btn_refresh.setFixedHeight(38)
        self.btn_refresh.clicked.connect(self.refresh_apps)

        self.btn_uninstall = PrimaryPushButton("🗑️ Gỡ Cài Đặt", self)
        self.btn_uninstall.setFixedHeight(38)
        self.btn_uninstall.setStyleSheet("background-color: #D83B01; border-color: #D83B01;")
        self.btn_uninstall.clicked.connect(self._confirm_and_uninstall)

        header_layout.addWidget(self.btn_refresh)
        header_layout.addWidget(self.btn_uninstall)
        main_layout.addLayout(header_layout)

        # 2. Search box
        self.search_box = SearchLineEdit(self)
        self.search_box.setPlaceholderText("Tìm kiếm ứng dụng theo tên hoặc nhà phát hành...")
        self.search_box.textChanged.connect(self._filter_table)
        main_layout.addWidget(self.search_box)

        # 3. Table
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Tên Ứng Dụng", "Nhà Phát Hành", "Phiên Bản", "Dung Lượng Ước Tính", "Ngày Cài Đặt"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        main_layout.addWidget(self.table)

    def refresh_apps(self):
        animate_button_bounce(self.btn_refresh)
        self.btn_refresh.setEnabled(False)
        self.sub_label.setText("Đang quét danh sách phần mềm đã cài đặt...")

        def _worker():
            apps = self.app_manager.get_installed_apps()
            self.signals.loaded.emit(apps)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_loaded(self, apps):
        self.btn_refresh.setEnabled(True)
        self.apps = apps
        self.sub_label.setText(f"Tìm thấy tổng cộng: {len(apps)} ứng dụng được cài đặt trên hệ thống.")
        self._filter_table()

    def _filter_table(self):
        query = self.search_box.text().strip().lower()
        filtered = [
            a for a in self.apps
            if query in a['name'].lower() or query in a['publisher'].lower()
        ]

        self.table.setRowCount(len(filtered))
        for row, a in enumerate(filtered):
            name_item = QTableWidgetItem(f"📦 {a['name']}")
            name_item.setData(Qt.ItemDataRole.UserRole, a['uninstall_string'])

            pub_item = QTableWidgetItem(a['publisher'])
            ver_item = QTableWidgetItem(a['version'])
            ver_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            size_item = QTableWidgetItem(a['size_str'])
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            date_item = QTableWidgetItem(a['install_date'])
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, pub_item)
            self.table.setItem(row, 2, ver_item)
            self.table.setItem(row, 3, size_item)
            self.table.setItem(row, 4, date_item)

    def _confirm_and_uninstall(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            InfoBar.warning(
                title="Chưa chọn ứng dụng",
                content="Vui lòng nhấp chọn một ứng dụng trong bảng để gỡ cài đặt.",
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self
            )
            return

        row = selected_rows[0].row()
        name = self.table.item(row, 0).text().replace("📦 ", "")
        uninstall_str = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        msg = (
            f"Bạn có chắc chắn muốn gỡ cài đặt ứng dụng:\n\n"
            f"👉 {name}\n\n"
            "Chương trình gỡ cài đặt chính thức của ứng dụng sẽ được khởi chạy."
        )

        w = MessageBox("Xác nhận gỡ ứng dụng", msg, self.window())
        if not w.exec():
            return

        animate_button_bounce(self.btn_uninstall)
        success, note = self.app_manager.uninstall_app(uninstall_str)
        self._on_action_done(success, note)

    def _on_action_done(self, success, note):
        if success:
            InfoBar.success(
                title="Đang gỡ cài đặt",
                content=note,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self
            )
            TableFadeOutHelper.fade_out_table(self.table, duration=220, on_finished=self.refresh_apps)
        else:
            InfoBar.error(
                title="Lỗi gỡ cài đặt",
                content=note,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self
            )
