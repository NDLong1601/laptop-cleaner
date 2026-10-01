import os
import glob
import winreg
import ctypes
from core.cleaner import format_size


class PrivacyCleaner:
    """
    Cleans privacy traces:
    - Recent items & Quick Access history
    - JumpLists
    - Run dialog (Win+R) history
    - Explorer typed paths
    - Thumbnail caches
    - Clipboard history
    """

    def __init__(self):
        pass

    @staticmethod
    def clear_clipboard():
        """Clears Windows system clipboard."""
        try:
            user32 = ctypes.windll.user32
            if user32.OpenClipboard(None):
                user32.EmptyClipboard()
                user32.CloseClipboard()
                return True
        except Exception:
            pass
        return False

    def scan_privacy_items(self):
        """
        Scans all privacy items and returns categories with item counts and descriptions.
        """
        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")

        categories = {
            "recent_files": {
                "id": "recent_files",
                "title": "📋 Tệp Tin Mở Gần Đây (Recent Items)",
                "desc": "Danh sách shortcut các tài liệu, ảnh, tệp tin vừa mở trên File Explorer",
                "paths": [],
                "count": 0,
                "size": 0
            },
            "jumplists": {
                "id": "jumplists",
                "title": "📑 Lịch Sử JumpLists Trên Taskbar",
                "desc": "Danh sách các tệp ghim hoặc vừa mở khi chuột phải vào icon trên Taskbar",
                "paths": [],
                "count": 0,
                "size": 0
            },
            "run_mru": {
                "id": "run_mru",
                "title": "📜 Lịch Sử Hộp Thoại Run (Win + R)",
                "desc": "Các câu lệnh hoặc đường dẫn người dùng đã gõ trong hộp thoại Run",
                "registry_keys": [r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"],
                "count": 0,
                "size": 0
            },
            "typed_paths": {
                "id": "typed_paths",
                "title": "🌐 Đường Dẫn Đã Gõ Trong File Explorer",
                "desc": "Lịch sử thanh địa chỉ của Windows Explorer (TypedPaths)",
                "registry_keys": [r"Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths"],
                "count": 0,
                "size": 0
            },
            "thumbnail_cache": {
                "id": "thumbnail_cache",
                "title": "🖼️ Bộ Nhớ Đệm Hình Thu Nhỏ (Thumbnail Cache)",
                "desc": "Các file thumbcache_*.db lưu ảnh thu nhỏ của tài liệu, video và ảnh",
                "paths": [],
                "count": 0,
                "size": 0
            },
            "clipboard": {
                "id": "clipboard",
                "title": "✂️ Bộ Nhớ Tạm Clipboard",
                "desc": "Nội dung văn bản, hình ảnh đang lưu trong bộ nhớ copy/paste",
                "count": 1,
                "size": 0
            }
        }

        # 1. Recent Files
        recent_dir = os.path.join(appdata, "Microsoft", "Windows", "Recent")
        if os.path.exists(recent_dir):
            for f in glob.glob(os.path.join(recent_dir, "*.lnk")):
                try:
                    s = os.path.getsize(f)
                    categories["recent_files"]["paths"].append(f)
                    categories["recent_files"]["size"] += s
                except (OSError, PermissionError):
                    pass
            categories["recent_files"]["count"] = len(categories["recent_files"]["paths"])

        # 2. JumpLists
        for jl_folder in ["AutomaticDestinations", "CustomDestinations"]:
            jl_path = os.path.join(recent_dir, jl_folder)
            if os.path.exists(jl_path):
                for f in glob.glob(os.path.join(jl_path, "*")):
                    try:
                        s = os.path.getsize(f)
                        categories["jumplists"]["paths"].append(f)
                        categories["jumplists"]["size"] += s
                    except (OSError, PermissionError):
                        pass
        categories["jumplists"]["count"] = len(categories["jumplists"]["paths"])

        # 3. Run MRU
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU", 0, winreg.KEY_READ) as k:
                count = winreg.QueryInfoKey(k)[1]
                categories["run_mru"]["count"] = max(0, count - 1)  # exclude 'MRUList' key
        except WindowsError:
            pass

        # 4. Typed Paths
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths", 0, winreg.KEY_READ) as k:
                categories["typed_paths"]["count"] = winreg.QueryInfoKey(k)[1]
        except WindowsError:
            pass

        # 5. Thumbnail Cache
        explorer_dir = os.path.join(localappdata, "Microsoft", "Windows", "Explorer")
        if os.path.exists(explorer_dir):
            for f in glob.glob(os.path.join(explorer_dir, "thumbcache_*.db")):
                try:
                    s = os.path.getsize(f)
                    categories["thumbnail_cache"]["paths"].append(f)
                    categories["thumbnail_cache"]["size"] += s
                except (OSError, PermissionError):
                    pass
        categories["thumbnail_cache"]["count"] = len(categories["thumbnail_cache"]["paths"])

        return categories

    def clean_privacy_categories(self, category_ids, progress_callback=None):
        """
        Cleans the selected privacy categories.
        Returns (cleaned_count, freed_bytes).
        """
        scanned = self.scan_privacy_items()
        cleaned_count = 0
        freed_bytes = 0
        total = len(category_ids)

        for i, cat_id in enumerate(category_ids):
            if cat_id not in scanned:
                continue

            cat = scanned[cat_id]
            if progress_callback and total > 0:
                pct = int((i / total) * 100)
                progress_callback(f"Đang dọn {cat['title']}...", pct)

            # Files deletion
            for fp in cat.get("paths", []):
                try:
                    if os.path.exists(fp):
                        s = os.path.getsize(fp)
                        os.remove(fp)
                        freed_bytes += s
                        cleaned_count += 1
                except Exception:
                    pass

            # Registry deletion
            for reg_path in cat.get("registry_keys", []):
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_ALL_ACCESS) as k:
                        values = []
                        num_vals = winreg.QueryInfoKey(k)[1]
                        for v_idx in range(num_vals):
                            try:
                                v_name = winreg.EnumValue(k, v_idx)[0]
                                values.append(v_name)
                            except WindowsError:
                                break
                        for v_name in values:
                            try:
                                winreg.DeleteValue(k, v_name)
                                cleaned_count += 1
                            except WindowsError:
                                pass
                except WindowsError:
                    pass

            # Clipboard
            if cat_id == "clipboard":
                if self.clear_clipboard():
                    cleaned_count += 1

        if progress_callback:
            progress_callback("Dọn dẹp dấu vết riêng tư hoàn tất!", 100)

        return cleaned_count, freed_bytes
