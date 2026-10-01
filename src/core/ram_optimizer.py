import ctypes
import psutil

class RAMOptimizer:
    def __init__(self):
        # Constants for SetProcessWorkingSetSize
        self.PROCESS_SET_QUOTA = 0x0100
        
    def get_memory_info(self):
        """Get current memory usage."""
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "percent": mem.percent,
            "used": mem.used
        }

    def optimize(self):
        """Flush working set of all processes to free up RAM."""
        before = self.get_memory_info()
        freed = 0
        
        try:
            # Requires admin for many processes, but we try what we can
            kernel32 = ctypes.windll.kernel32
            
            # Simple approach: iterate psutil and use EmptyWorkingSet API if available, 
            # or SetProcessWorkingSetSize(-1, -1)
            for proc in psutil.process_iter(['pid']):
                try:
                    pid = proc.info['pid']
                    if pid == 0:
                        continue
                    
                    handle = kernel32.OpenProcess(self.PROCESS_SET_QUOTA, False, pid)
                    if handle:
                        # -1, -1 flushes the working set
                        kernel32.SetProcessWorkingSetSize(handle, -1, -1)
                        kernel32.CloseHandle(handle)
                except:
                    pass
                    
            after = self.get_memory_info()
            freed = before["used"] - after["used"]
            if freed < 0:
                freed = 0
            return True, freed, after
        except Exception as e:
            return False, 0, before
