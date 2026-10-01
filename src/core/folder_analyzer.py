import os
import shutil
import glob
from core.cleaner import format_size


# Safety classification levels
LEVEL_SAFE = "SAFE"        # 🟢 An toàn: Cache, temp, logs, dumps
LEVEL_CAUTION = "CAUTION"  # 🟡 Cân nhắc: Packages, toolchain caches, leftovers
LEVEL_DANGER = "DANGER"    # 🔴 Nguy hiểm: Cấu hình, profiles, credentials, sessions


class FolderAnalyzer:
    """
    Analyzes any given directory (default: AppData) and classifies subdirectories / files
    into safety categories based on heuristics and known patterns.
    """

    SAFE_KEYWORDS = [
        "cache", "gpucache", "code cache", "shadercache", "d3dscache",
        "crashdumps", "minidump", "logs", "log", "temp", "tmp",
        "webcache", "fontcache", "telemetry", "reportarchive"
    ]

    CAUTION_KEYWORDS = [
        "npm-cache", "pip", "nuget", "yarn", "gradle", "cargo",
        "huggingface", "torch", "package cache", "downloaded installations",
        "updater", "downloads"
    ]

    DANGER_KEYWORDS = [
        "protect", "credentials", "vault", "crypto", "security",
        "windows", "system", "user data", "profiles", "profile",
        "preferences", "config", "settings", "sessions", "session storage",
        "databases", "identity", "accounts"
    ]

    def __init__(self):
        pass

    @staticmethod
    def get_appdata_paths():
        """Return the default paths for Windows AppData directories."""
        user_profile = os.environ.get("USERPROFILE", "")
        return {
            "Local": os.environ.get("LOCALAPPDATA", os.path.join(user_profile, "AppData", "Local")),
            "Roaming": os.environ.get("APPDATA", os.path.join(user_profile, "AppData", "Roaming")),
            "LocalLow": os.path.join(user_profile, "AppData", "LocalLow")
        }

    @staticmethod
    def get_dir_size(path):
        """Calculates total size of a path in bytes."""
        total_size = 0
        if os.path.isfile(path):
            try:
                total_size = os.path.getsize(path)
            except (OSError, FileNotFoundError):
                pass
        elif os.path.isdir(path):
            try:
                for entry in os.scandir(path):
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total_size += entry.stat().st_size
                        elif entry.is_dir(follow_symlinks=False):
                            total_size += FolderAnalyzer.get_dir_size(entry.path)
                    except (OSError, FileNotFoundError):
                        pass
            except (OSError, PermissionError):
                pass
        return total_size

    def classify_target(self, name, relative_path=""):
        """
        Classifies an item based on name and relative path patterns.
        Returns (level, reason, impact_description).
        """
        name_lower = name.lower()
        rel_lower = relative_path.lower()
        combined = f"{rel_lower}/{name_lower}"

        # 1. Critical danger check first
        for kw in self.DANGER_KEYWORDS:
            if kw in combined:
                return (
                    LEVEL_DANGER,
                    "Chứa cấu hình, thiết lập hoặc thông tin tài khoản quan trọng",
                    "⚠️ NGUY HIỂM: Xóa mục này có thể làm mất thông tin đăng nhập, thiết lập cá nhân của phần mềm hoặc khiến ứng dụng bị lỗi khởi động."
                )

        # 2. Safe check (caches, temps, logs)
        for kw in self.SAFE_KEYWORDS:
            if kw in combined:
                return (
                    LEVEL_SAFE,
                    "Bộ nhớ đệm (Cache) / Tệp tạm / Logs lỗi",
                    "✅ AN TOÀN: Xóa không ảnh hưởng đến dữ liệu cá nhân hay môi trường máy. Phần mềm sẽ tự tạo lại khi cần thiết."
                )

        # 3. Caution check
        for kw in self.CAUTION_KEYWORDS:
            if kw in combined:
                return (
                    LEVEL_CAUTION,
                    "Gói cài đặt / Dữ liệu tải về / Thư viện build",
                    "⚡ CÂN NHẮC: Thường chiếm dung lượng lớn. Xóa xong máy vẫn hoạt động bình thường, nhưng các công cụ (npm/pip/nuget) sẽ phải tải lại khi biên dịch/chạy dự án."
                )

        # Default fallback: If it's a general app folder, mark as Danger or Caution
        return (
            LEVEL_DANGER,
            "Dữ liệu phần mềm tổng hợp",
            "⚠️ NGUY HIỂM: Thư mục gốc chứa toàn bộ dữ liệu làm việc của ứng dụng. Chỉ nên xóa nếu bạn đã gỡ cài đặt phần mềm này."
        )

    def scan_path(self, target_path, progress_callback=None, scan_depth=2):
        """
        Scans a target directory up to a given depth and evaluates items.
        Returns a list of structured analysis dictionaries.
        """
        if not os.path.exists(target_path):
            return []

        results = []
        try:
            # We scan the immediate children (and their prominent sub-caches)
            entries = [e for e in os.scandir(target_path)]
            total = len(entries)

            for idx, entry in enumerate(entries):
                if progress_callback and total > 0:
                    pct = int((idx / total) * 100)
                    progress_callback(f"Đang phân tích {entry.name}...", pct)

                try:
                    is_dir = entry.is_dir(follow_symlinks=False)
                    size = self.get_dir_size(entry.path)
                    if size < 1024 * 10:  # Skip empty or negligible files (< 10 KB)
                        continue

                    # Deep dive 1 level if it's a directory to find caches inside
                    found_sub_caches = False
                    if is_dir and scan_depth > 1:
                        try:
                            for sub in os.scandir(entry.path):
                                if sub.is_dir(follow_symlinks=False):
                                    sub_level, sub_reason, sub_impact = self.classify_target(sub.name, entry.name)
                                    if sub_level in [LEVEL_SAFE, LEVEL_CAUTION]:
                                        sub_size = self.get_dir_size(sub.path)
                                        if sub_size >= 1024 * 50:  # >= 50 KB
                                            results.append({
                                                "name": f"{entry.name} ➔ {sub.name}",
                                                "path": sub.path,
                                                "size": sub_size,
                                                "level": sub_level,
                                                "reason": sub_reason,
                                                "impact": sub_impact,
                                                "is_dir": True
                                            })
                                            found_sub_caches = True
                        except (PermissionError, OSError):
                            pass

                    # Also evaluate the top entry itself
                    level, reason, impact = self.classify_target(entry.name, "")
                    results.append({
                        "name": entry.name,
                        "path": entry.path,
                        "size": size,
                        "level": level,
                        "reason": reason,
                        "impact": impact,
                        "is_dir": is_dir
                    })

                except (PermissionError, OSError):
                    continue

        except (PermissionError, OSError):
            pass

        # Sort results: Largest size first
        results.sort(key=lambda x: x["size"], reverse=True)

        if progress_callback:
            progress_callback("Hoàn tất phân tích!", 100)

        return results

    def delete_items(self, item_paths, progress_callback=None):
        """
        Deletes the list of paths selected by the user.
        Returns (freed_bytes, failed_paths).
        """
        freed = 0
        failed = []
        total = len(item_paths)

        for i, path in enumerate(item_paths):
            if progress_callback and total > 0:
                pct = int((i / total) * 100)
                progress_callback(f"Đang xóa {os.path.basename(path)}...", pct)

            if not os.path.exists(path):
                continue

            size = self.get_dir_size(path)
            try:
                if os.path.isfile(path) or os.path.islink(path):
                    os.remove(path)
                    freed += size
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                    freed += size
            except Exception as e:
                failed.append((path, str(e)))

        if progress_callback:
            progress_callback("Dọn dẹp hoàn tất!", 100)

        return freed, failed
