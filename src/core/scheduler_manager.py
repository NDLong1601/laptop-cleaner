import os
import json
import winreg
import psutil


CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

DEFAULT_CONFIG = {
    "auto_clean_on_startup": False,
    "low_disk_alert": True,
    "low_disk_threshold_pct": 15,
    "schedule_frequency": "weekly",
    "clean_temp": True,
    "clean_logs": True,
    "clean_browser": False,
    "clean_recycle_bin": False
}


class SchedulerManager:
    """
    Manages automated cleaning schedules, low disk alerts, and startup integration.
    """

    RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "LaptopCleanerAutoOptimizer"

    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    # Merge with default keys
                    merged = DEFAULT_CONFIG.copy()
                    merged.update(cfg)
                    return merged
            except Exception:
                pass
        return DEFAULT_CONFIG.copy()

    def save_config(self, new_config):
        self.config.update(new_config)
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True, "Cài đặt đã được lưu thành công!"
        except Exception as e:
            return False, f"Lỗi khi lưu cài đặt: {e}"

    def check_low_disk_warning(self):
        """
        Checks if drive C: has free space less than the configured percentage.
        Returns (is_low, free_gb, percent_free).
        """
        try:
            du = psutil.disk_usage("C:")
            free_pct = 100.0 - du.percent
            threshold = self.config.get("low_disk_threshold_pct", 15)
            is_low = free_pct <= threshold
            free_gb = du.free / (1024 ** 3)
            return is_low, free_gb, free_pct
        except Exception:
            return False, 0, 100

    def sync_startup_registration(self, enable=True):
        """
        Registers or unregisters the app in HKCU Run to execute background auto-optimization.
        """
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.RUN_KEY_PATH, 0, winreg.KEY_ALL_ACCESS)
            if enable:
                script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
                cmd = f'"{os.sys.executable}" "{script_path}"'
                winreg.SetValueEx(key, self.APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, self.APP_NAME)
                except WindowsError:
                    pass
            winreg.CloseKey(key)
            return True, "Đã cập nhật trạng thái khởi động cùng Windows!"
        except Exception as e:
            return False, f"Không thể cập nhật cấu hình khởi động: {e}"
