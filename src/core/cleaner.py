import os
import glob
import shutil
import tempfile
import ctypes
import ctypes.wintypes

def format_size(size_bytes):
    """Format bytes into readable string (B, KB, MB, GB)."""
    if size_bytes <= 0:
        return "0 MB"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

class Cleaner:
    def __init__(self):
        self.temp_dirs = [
            tempfile.gettempdir(),
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Temp'),
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'SoftwareDistribution', 'Download')
        ]
        
        local_app_data = os.environ.get('LOCALAPPDATA', '')
        if local_app_data:
            chrome_cache = os.path.join(local_app_data, 'Google', 'Chrome', 'User Data', 'Default', 'Cache')
            edge_cache = os.path.join(local_app_data, 'Microsoft', 'Edge', 'User Data', 'Default', 'Cache')
            self.browser_caches = [chrome_cache, edge_cache]

            ff_profiles_root = os.path.join(local_app_data, 'Mozilla', 'Firefox', 'Profiles')
            if os.path.isdir(ff_profiles_root):
                for ff_cache in glob.glob(os.path.join(ff_profiles_root, '*', 'cache2')):
                    self.browser_caches.append(ff_cache)
        else:
            self.browser_caches = []

    def get_size(self, path):
        """Get size of a directory or file in bytes."""
        total_size = 0
        if os.path.isfile(path):
            try:
                total_size = os.path.getsize(path)
            except (OSError, FileNotFoundError):
                pass
        elif os.path.isdir(path):
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        try:
                            total_size += os.path.getsize(fp)
                        except (OSError, FileNotFoundError):
                            pass
        return total_size

    def scan_categories(self, progress_callback=None):
        """
        Scans junk files grouped into structured categories.
        Returns a dict of categories:
        {
           'windows_temp': {'title': ..., 'desc': ..., 'items': [...], 'size': ...},
           ...
        }
        """
        categories = {
            'windows_temp': {
                'id': 'windows_temp',
                'title': 'Tệp tạm hệ thống & Windows Update',
                'desc': '%TEMP%, C:\\Windows\\Temp và gói tải về của Windows Update',
                'items': [],
                'size': 0
            },
            'browser_cache': {
                'id': 'browser_cache',
                'title': 'Bộ nhớ đệm trình duyệt Web',
                'desc': 'Cache bộ nhớ từ Google Chrome, Microsoft Edge, Mozilla Firefox',
                'items': [],
                'size': 0
            },
            'logs_dumps': {
                'id': 'logs_dumps',
                'title': 'Nhật ký lỗi & Memory Dumps',
                'desc': 'Các file log cũ và crash dump tốn dung lượng của ứng dụng',
                'items': [],
                'size': 0
            },
            'recycle_bin': {
                'id': 'recycle_bin',
                'title': 'Thùng rác Windows (Recycle Bin)',
                'desc': 'Tất cả các tệp tin hiện đang nằm trong thùng rác',
                'items': [],
                'size': 0
            }
        }

        # 1. Windows Temp
        if progress_callback:
            progress_callback("Đang quét file tạm hệ thống...", 15)
        for path in self.temp_dirs:
            if os.path.exists(path):
                s = self.get_size(path)
                if s > 0:
                    categories['windows_temp']['items'].append({'path': path, 'size': s, 'type': 'Directory'})
                    categories['windows_temp']['size'] += s

        # 2. Browser Caches
        if progress_callback:
            progress_callback("Đang quét bộ nhớ đệm trình duyệt...", 45)
        for path in self.browser_caches:
            if os.path.exists(path):
                s = self.get_size(path)
                if s > 0:
                    categories['browser_cache']['items'].append({'path': path, 'size': s, 'type': 'Browser Cache'})
                    categories['browser_cache']['size'] += s

        # 3. Logs & Dumps
        if progress_callback:
            progress_callback("Đang quét nhật ký & Crash dumps...", 70)
        log_dirs = [
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Logs'),
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Minidump'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'CrashDumps')
        ]
        for log_dir in log_dirs:
            if os.path.exists(log_dir):
                for dirpath, _, filenames in os.walk(log_dir):
                    for f in filenames:
                        if f.lower().endswith(('.log', '.dmp')):
                            fp = os.path.join(dirpath, f)
                            try:
                                s = os.path.getsize(fp)
                                categories['logs_dumps']['items'].append({'path': fp, 'size': s, 'type': 'Log/Dump'})
                                categories['logs_dumps']['size'] += s
                            except (OSError, FileNotFoundError):
                                pass

        # 4. Recycle Bin
        if progress_callback:
            progress_callback("Đang kiểm tra Thùng rác...", 90)
        try:
            class SHQUERYRBINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.wintypes.DWORD),
                    ("i64Size", ctypes.c_int64),
                    ("i64NumItems", ctypes.c_int64),
                ]
            rb_info = SHQUERYRBINFO()
            rb_info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
            res = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(rb_info))
            if res == 0 and rb_info.i64Size > 0:
                categories['recycle_bin']['items'].append({'path': 'Recycle Bin', 'size': rb_info.i64Size, 'type': 'Recycle Bin'})
                categories['recycle_bin']['size'] = rb_info.i64Size
        except Exception:
            pass

        if progress_callback:
            progress_callback("Hoàn tất quét!", 100)

        return categories

    def scan_junk(self, progress_callback=None):
        """Flat scan for backward compatibility."""
        cats = self.scan_categories(progress_callback)
        flat_items = []
        total_size = 0
        for cat in cats.values():
            flat_items.extend(cat['items'])
            total_size += cat['size']
        return flat_items, total_size

    def clean_item(self, path):
        """Cleans a specific path."""
        try:
            if path == "Recycle Bin":
                try:
                    SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
                    SHEmptyRecycleBin(None, None, 7)
                    return True
                except:
                    return False

            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                for filename in os.listdir(path):
                    file_path = os.path.join(path, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception:
                        pass
            return True
        except Exception:
            return False

    def clean_all(self, items, progress_callback=None):
        """Cleans all items in the list."""
        cleaned_size = 0
        total = len(items)
        for i, item in enumerate(items):
            if progress_callback and total > 0:
                progress = (i / total) * 100
                progress_callback(f"Đang xóa {os.path.basename(item['path'])}...", progress)

            if self.clean_item(item['path']):
                cleaned_size += item['size']

        if progress_callback:
            progress_callback("Dọn dẹp hoàn tất.", 100)

        return cleaned_size
