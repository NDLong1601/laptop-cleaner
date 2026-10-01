import os
import hashlib
from collections import defaultdict
from core.cleaner import format_size


class DuplicateFinder:
    """
    High-performance duplicate file finder with 2-pass hashing:
    1. Size grouping
    2. Quick 4KB header hash
    3. Full MD5 hash for exact matching
    """

    def __init__(self):
        pass

    @staticmethod
    def _quick_hash(filepath):
        """Read only the first 4KB of a file for initial comparison."""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read(4096)).hexdigest()
        except (OSError, PermissionError):
            return None

    @staticmethod
    def _full_hash(filepath, block_size=65536):
        """Compute full MD5 hash of a file."""
        hasher = hashlib.md5()
        try:
            with open(filepath, 'rb') as f:
                for block in iter(lambda: f.read(block_size), b''):
                    hasher.update(block)
            return hasher.hexdigest()
        except (OSError, PermissionError):
            return None

    def find_duplicates(self, target_dir, min_size_bytes=1024*1024, progress_callback=None):
        """
        Scans target_dir and returns groups of duplicate files.
        Returns:
        [
            {
                "hash": "...",
                "size": 1542000,
                "size_str": "1.47 MB",
                "files": [path1, path2, ...]
            },
            ...
        ]
        """
        if not os.path.exists(target_dir):
            return []

        # 1. Collect all files and group by size
        if progress_callback:
            progress_callback("Đang lập danh mục tệp tin...", 10)

        size_map = defaultdict(list)
        file_count = 0

        for root, _, files in os.walk(target_dir):
            for filename in files:
                filepath = os.path.join(root, filename)
                try:
                    # Ignore junctions, symlinks
                    if not os.path.islink(filepath):
                        s = os.path.getsize(filepath)
                        if s >= min_size_bytes:
                            size_map[s].append(filepath)
                            file_count += 1
                except (OSError, PermissionError):
                    continue

        # Filter out sizes with only 1 file
        candidate_sizes = {s: paths for s, paths in size_map.items() if len(paths) > 1}
        if not candidate_sizes:
            if progress_callback:
                progress_callback("Không phát hiện tệp trùng lặp nào.", 100)
            return []

        # 2. Pass 1: Quick Header Hash
        total_candidates = sum(len(paths) for paths in candidate_sizes.values())
        processed = 0

        quick_hash_map = defaultdict(list)
        for s, paths in candidate_sizes.items():
            for p in paths:
                processed += 1
                if progress_callback and total_candidates > 0:
                    pct = 10 + int((processed / total_candidates) * 45)
                    progress_callback(f"Kiểm tra nhanh: {os.path.basename(p)}...", pct)

                q_hash = self._quick_hash(p)
                if q_hash:
                    quick_hash_map[(s, q_hash)].append(p)

        # Filter candidates from pass 1
        full_hash_candidates = {k: paths for k, paths in quick_hash_map.items() if len(paths) > 1}

        # 3. Pass 2: Full MD5 Hash
        final_hash_map = defaultdict(list)
        total_final = sum(len(paths) for paths in full_hash_candidates.values())
        processed = 0

        for (s, _), paths in full_hash_candidates.items():
            for p in paths:
                processed += 1
                if progress_callback and total_final > 0:
                    pct = 55 + int((processed / total_final) * 40)
                    progress_callback(f"Băm chính xác: {os.path.basename(p)}...", pct)

                f_hash = self._full_hash(p)
                if f_hash:
                    final_hash_map[(s, f_hash)].append(p)

        # Format results
        duplicate_groups = []
        for (s, f_hash), paths in final_hash_map.items():
            if len(paths) > 1:
                duplicate_groups.append({
                    "hash": f_hash,
                    "size": s,
                    "size_str": format_size(s),
                    "wasted_size": s * (len(paths) - 1),
                    "files": paths
                })

        # Sort groups by wasted size descending
        duplicate_groups.sort(key=lambda x: x["wasted_size"], reverse=True)

        if progress_callback:
            progress_callback(f"Hoàn tất! Tìm thấy {len(duplicate_groups)} nhóm tệp trùng lặp.", 100)

        return duplicate_groups

    @staticmethod
    def delete_files(filepaths):
        """Deletes selected duplicate files."""
        freed = 0
        failed = []
        for fp in filepaths:
            try:
                if os.path.exists(fp):
                    s = os.path.getsize(fp)
                    os.remove(fp)
                    freed += s
            except Exception as e:
                failed.append((fp, str(e)))
        return freed, failed
