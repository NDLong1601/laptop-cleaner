import threading
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem
)
from qfluentwidgets import (
    TitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    PrimaryPushButton, PushButton, SearchLineEdit, TableWidget,
    FluentIcon as FI, InfoBar, InfoBarPosition, MessageBox
)

from core.process_manager import ProcessManager
from .animations import animate_button_bounce, TableFadeOutHelper


class ProcessSignals(QObject):
    processes_loaded = pyqtSignal(list)
    process_killed = pyqtSignal(bool, str)


class ProcessesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("ProcessesTab")
        self.pm = ProcessManager()
        self.signals = ProcessSignals()
        self.signals.processes_loaded.connect(self._on_processes_loaded)
        self.signals.process_killed.connect(self._on_process_killed)

        self.all_processes = []

        self._init_ui()
        self.refresh_list()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 24, 36, 24)
        main_layout.setSpacing(16)

        # 1. Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.addWidget(TitleLabel("Quản Lý Tiến Trình", self))
        self.sub_label = BodyLabel("Xem các tiến trình đang chạy ngầm và giải phóng tài nguyên.", self)
        self.sub_label.setStyleSheet("color: #888888;")
        title_box.addWidget(self.sub_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_refresh = PushButton(FI.SYNC, "Làm Mới", self)
        self.btn_refresh.setFixedHeight(38)
        self.btn_refresh.clicked.connect(self.refresh_list)

        self.btn_kill = PushButton("🛑 Kết Thúc Tiến Trình", self)
        self.btn_kill.setFixedHeight(38)
        self.btn_kill.clicked.connect(self.kill_selected)

        header_layout.addWidget(self.btn_refresh)
        header_layout.addWidget(self.btn_kill)
        main_layout.addLayout(header_layout)

        # 2. Search Bar
        self.search_box = SearchLineEdit(self)
        self.search_box.setPlaceholderText("Tìm kiếm theo tên tiến trình hoặc PID...")
        self.search_box.textChanged.connect(self._filter_table)
        main_layout.addWidget(self.search_box)

        # 3. Table
        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Tên Tiến Trình", "PID", "RAM Sử Dụng", "Mức Tiêu Thụ"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(TableWidget.SelectionMode.SingleSelection)
        main_layout.addWidget(self.table)

    def refresh_list(self):
        animate_button_bounce(self.btn_refresh)
        self.btn_refresh.setEnabled(False)
        self.sub_label.setText("Đang tải danh sách tiến trình...")

        def _worker():
            procs = self.pm.get_processes()
            self.signals.processes_loaded.emit(procs)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_processes_loaded(self, procs):
        self.btn_refresh.setEnabled(True)
        self.all_processes = procs
        self.sub_label.setText(f"Tổng cộng: {len(procs)} tiến trình đang hoạt động")
        self._filter_table()

    def _filter_table(self):
        query = self.search_box.text().strip().lower()
        filtered = [
            p for p in self.all_processes
            if query in p.get('name', '').lower() or query in str(p.get('pid', ''))
        ]

        self.table.setRowCount(len(filtered))
        for row, p in enumerate(filtered):
            name_item = QTableWidgetItem(str(p.get('name', 'N/A')))
            pid_item = QTableWidgetItem(str(p.get('pid', '')))
            pid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            mem_mb = p.get('memory_mb', 0)
            mem_item = QTableWidgetItem(f"{mem_mb:.1f} MB")
            mem_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            if mem_mb >= 500:
                tag = "🔴 Rất cao"
            elif mem_mb >= 150:
                tag = "🟡 Trung bình"
            else:
                tag = "🟢 Thấp"

            tag_item = QTableWidgetItem(tag)
            tag_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, pid_item)
            self.table.setItem(row, 2, mem_item)
            self.table.setItem(row, 3, tag_item)

    def kill_selected(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            InfoBar.warning(
                title="Chưa chọn tiến trình",
                content="Vui lòng nhấp chọn một tiến trình trong bảng để kết thúc.",
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self
            )
            return

        row = selected_rows[0].row()
        name = self.table.item(row, 0).text()
        pid = int(self.table.item(row, 1).text())

        # Confirmation Dialog
        w = MessageBox(
            "Xác nhận dừng tiến trình",
            f"Bạn có chắc chắn muốn đóng tiến trình '{name}' (PID: {pid}) không?",
            self.window()
        )
        if not w.exec():
            return

        animate_button_bounce(self.btn_kill)

        def _worker():
            success, msg = self.pm.kill_process(pid)
            self.signals.process_killed.emit(success, f"'{name}' (PID: {pid}) - {msg}")

        threading.Thread(target=_worker, daemon=True).start()

    def _on_process_killed(self, success, msg):
        if success:
            InfoBar.success(
                title="Đã dừng tiến trình",
                content=msg,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            TableFadeOutHelper.fade_out_table(self.table, duration=200, on_finished=self.refresh_list)
        else:
            InfoBar.error(
                title="Không thể dừng tiến trình",
                content=msg,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self
            )
