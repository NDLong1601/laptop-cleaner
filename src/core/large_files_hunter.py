import os
import time
from core.cleaner import format_size


class LargeFilesHunter:
    """
    Scans files on drives or folders exceeding a specified size threshold.
    """

    def __init__(self):
        pass

    def scan_large_files(self, target_dir, min_size_bytes=100*1024*1024, max_results=300, progress_callback=None):
        """
        Scans target_dir for files with size >= min_size_bytes.
        Returns sorted list of file metadata.
        """
        if not os.path.exists(target_dir):
            return []

        results = []
        files_scanned = 0

        for root, dirs, files in os.walk(target_dir):
            # Skip hidden Windows folders like System Volume Information, $Recycle.Bin
            dirs[:] = [d for d in dirs if not d.startswith('$') and d != 'System Volume Information']

            for filename in files:
                files_scanned += 1
                if progress_callback and files_scanned % 500 == 0:
                    progress_callback(f"Đã quét {files_scanned} tệp... Tìm thấy {len(results)} tệp lớn", 50)

                filepath = os.path.join(root, filename)
                try:
                    if not os.path.islink(filepath):
                        stat = os.stat(filepath)
                        s = stat.st_size
                        if s >= min_size_bytes:
                            # Format date modified
                            mtime_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime))
                            _, ext = os.path.splitext(filename)

                            results.append({
                                "name": filename,
                                "path": filepath,
                                "dir": root,
                                "size": s,
                                "size_str": format_size(s),
                                "ext": ext.lower() if ext else "Không rõ",
                                "mtime": mtime_str
                            })
                except (OSError, PermissionError):
                    continue

        # Sort largest first
        results.sort(key=lambda x: x["size"], reverse=True)

        if max_results and len(results) > max_results:
            results = results[:max_results]

        if progress_callback:
            progress_callback(f"Hoàn tất quét! Tìm thấy {len(results)} tệp tin lớn.", 100)

        return results

    @staticmethod
    def delete_file(filepath):
        """Deletes a file and returns (success, error_msg)."""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True, "Đã xóa thành công"
            return False, "Tệp không tồn tại"
        except Exception as e:
            return False, str(e)
