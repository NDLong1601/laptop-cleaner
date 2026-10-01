import winreg
import os
import subprocess
from core.cleaner import format_size


class AppManager:
    """
    Scans installed Windows applications from Registry and manages their uninstallation.
    """

    UNINSTALL_KEYS = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    ]

    def __init__(self):
        pass

    def get_installed_apps(self):
        """
        Retrieves a deduplicated list of all user-installed applications.
        Returns list of dicts:
        [{
           'name': ..., 'version': ..., 'publisher': ...,
           'size_str': ..., 'size_bytes': ..., 'install_date': ...,
           'uninstall_string': ..., 'quiet_uninstall_string': ...
        }]
        """
        apps = {}

        for root_key, subkey in self.UNINSTALL_KEYS:
            try:
                reg_key = winreg.OpenKey(root_key, subkey, 0, winreg.KEY_READ)
            except WindowsError:
                continue

            num_subkeys = winreg.QueryInfoKey(reg_key)[0]

            for i in range(num_subkeys):
                try:
                    app_key_name = winreg.EnumKey(reg_key, i)
                    app_key = winreg.OpenKey(reg_key, app_key_name, 0, winreg.KEY_READ)

                    def get_val(val_name):
                        try:
                            val, _ = winreg.QueryValueEx(app_key, val_name)
                            return val
                        except WindowsError:
                            return None

                    display_name = get_val("DisplayName")
                    uninstall_string = get_val("UninstallString")
                    system_component = get_val("SystemComponent")
                    parent_key = get_val("ParentKeyName")

                    # Filter out system components, updates, or entries without a name/uninstall string
                    if not display_name or not uninstall_string or system_component == 1 or parent_key:
                        winreg.CloseKey(app_key)
                        continue

                    # Filter out KB windows updates or patches
                    if display_name.startswith("KB") and display_name[2:].isdigit():
                        winreg.CloseKey(app_key)
                        continue

                    publisher = get_val("Publisher") or "Không rõ"
                    display_version = get_val("DisplayVersion") or "N/A"
                    install_date = get_val("InstallDate") or "N/A"
                    estimated_size_kb = get_val("EstimatedSize") or 0

                    # Convert estimated size from KB to bytes
                    size_bytes = int(estimated_size_kb) * 1024 if estimated_size_kb else 0
                    size_str = format_size(size_bytes) if size_bytes > 0 else "Không rõ"

                    # Normalize install date format YYYYMMDD -> YYYY-MM-DD
                    if len(str(install_date)) == 8 and str(install_date).isdigit():
                        d_str = str(install_date)
                        install_date = f"{d_str[:4]}-{d_str[4:6]}-{d_str[6:]}"

                    quiet_uninstall = get_val("QuietUninstallString")

                    # Deduplicate by DisplayName
                    if display_name not in apps or (size_bytes > apps[display_name]["size_bytes"]):
                        apps[display_name] = {
                            "name": display_name,
                            "version": str(display_version),
                            "publisher": str(publisher),
                            "size_bytes": size_bytes,
                            "size_str": size_str,
                            "install_date": str(install_date),
                            "uninstall_string": str(uninstall_string),
                            "quiet_uninstall_string": str(quiet_uninstall) if quiet_uninstall else None
                        }

                    winreg.CloseKey(app_key)
                except WindowsError:
                    continue

            winreg.CloseKey(reg_key)

        app_list = list(apps.values())
        # Sort alphabetically by name
        app_list.sort(key=lambda x: x["name"].lower())
        return app_list

    def uninstall_app(self, uninstall_string):
        """
        Launches the native uninstaller command.
        """
        if not uninstall_string:
            return False, "Không tìm thấy lệnh gỡ cài đặt cho ứng dụng này."

        try:
            # Handle MsiExec command or normal executable string
            # If it's a quoted command or has arguments, subprocess handles string with shell=True
            subprocess.Popen(uninstall_string, shell=True)
            return True, "Đã khởi chạy trình gỡ cài đặt. Vui lòng làm theo hướng dẫn trên màn hình."
        except Exception as e:
            return False, f"Không thể khởi chạy trình gỡ cài đặt: {e}"
