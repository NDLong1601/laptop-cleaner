import psutil
import subprocess
import re


class BatteryPowerManager:
    """
    Monitors laptop battery metrics and controls Windows Power Plans (Balanced, High Performance, Power Saver).
    """

    # Well-known Windows default power scheme GUIDs
    SCHEME_BALANCED = "381b4222-f694-41f0-9685-ff5bb260df2e"
    SCHEME_HIGH_PERF = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    SCHEME_POWER_SAVER = "a1841308-3541-4fab-bc81-f71556f20b4a"

    def __init__(self):
        pass

    @staticmethod
    def get_battery_info():
        """
        Returns a dict of battery status:
        {
           'has_battery': True/False,
           'percent': 100,
           'power_plugged': True/False,
           'secsleft': -1 or seconds,
           'status_text': 'Đang cắm sạc (100%)'
        }
        """
        try:
            batt = psutil.sensors_battery()
            if batt is None:
                return {
                    "has_battery": False,
                    "percent": 100,
                    "power_plugged": True,
                    "secsleft": -1,
                    "status_text": "Không phát hiện pin (Máy tính để bàn hoặc không hỗ trợ)"
                }

            plugged = batt.power_plugged
            pct = int(batt.percent)
            secs = batt.secsleft

            if plugged:
                if pct >= 99:
                    status = f"Đã sạc đầy 100% (Đang cắm nguồn AC)"
                else:
                    status = f"Đang cắm sạc ({pct}%)"
            else:
                if secs > 0:
                    hrs = secs // 3600
                    mins = (secs % 3600) // 60
                    status = f"Đang dùng pin ({pct}% - Còn khoảng {hrs}h {mins}m)"
                else:
                    status = f"Đang dùng pin ({pct}%)"

            return {
                "has_battery": True,
                "percent": pct,
                "power_plugged": plugged,
                "secsleft": secs,
                "status_text": status
            }
        except Exception:
            return {
                "has_battery": False,
                "percent": 100,
                "power_plugged": True,
                "secsleft": -1,
                "status_text": "Không thể đọc dữ liệu pin"
            }

    KNOWN_SCHEMES = {
        "381b4222-f694-41f0-9685-ff5bb260df2e": "Cân Bằng (Balanced - Khuyến nghị)",
        "a1841308-3541-4fab-bc81-f71556f20b4a": "Tiết Kiệm Pin (Power Saver / Eco)",
        "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c": "Hiệu Năng Cao (High Performance)",
        "e9a42b02-d5df-448d-aa00-03f14749eb61": "Hiệu Năng Tối Đa (Ultimate Performance)"
    }

    @classmethod
    def get_power_plans(cls):
        """
        Queries all available power plans on this Windows system.
        Returns list of {'guid': ..., 'name': ..., 'is_active': True/False}.
        """
        plans = []
        try:
            res = subprocess.check_output("powercfg /list", shell=True, text=True, errors="ignore")
            pattern = re.compile(r"Power Scheme GUID:\s+([a-f0-9\-]+)\s+\((.*?)\)(\s+\*)?", re.IGNORECASE)

            for line in res.splitlines():
                m = pattern.search(line)
                if m:
                    guid = m.group(1).strip().lower()
                    raw_name = m.group(2).strip()
                    is_active = bool(m.group(3))

                    # Use clean name if it's a known Windows scheme
                    if guid in cls.KNOWN_SCHEMES:
                        display_name = cls.KNOWN_SCHEMES[guid]
                    elif "acer" in raw_name.lower():
                        display_name = "Acer Chế Độ Riêng (Acer Optimized)"
                    else:
                        # Clean up any potential garbage characters
                        clean_chars = "".join(c for c in raw_name if c.isalnum() or c in " -_()/")
                        display_name = clean_chars.strip() or f"Chế độ ({guid[:8]})"

                    plans.append({
                        "guid": guid,
                        "name": display_name,
                        "is_active": is_active
                    })
        except Exception:
            pass

        return plans

    @staticmethod
    def set_active_plan(guid):
        """Activates the given power scheme GUID."""
        try:
            subprocess.run(f"powercfg /setactive {guid}", shell=True, check=True)
            return True, "Đã chuyển đổi chế độ nguồn thành công!"
        except Exception as e:
            return False, f"Không thể kích hoạt chế độ: {e}"
