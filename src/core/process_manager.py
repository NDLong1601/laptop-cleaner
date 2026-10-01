import psutil
import time

class ProcessManager:
    def get_processes(self):
        """Get a list of all running processes with their info."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                # psutil cpu_percent requires a delay to be accurate, we will just use memory for sorting initially
                # or a 0 value, otherwise it blocks too much.
                pinfo = proc.info
                pinfo['memory_mb'] = pinfo['memory_info'].rss / (1024 * 1024) if pinfo['memory_info'] else 0
                processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Sort by memory usage
        processes = sorted(processes, key=lambda p: p.get('memory_mb', 0), reverse=True)
        return processes

    def kill_process(self, pid):
        """Kill a process by PID."""
        try:
            p = psutil.Process(pid)
            p.terminate()
            p.wait(timeout=3)
            return True, "Success"
        except psutil.AccessDenied:
            return False, "Access Denied. Try running as Administrator."
        except psutil.NoSuchProcess:
            return False, "Process no longer exists."
        except Exception as e:
            return False, str(e)
