import ctypes
import sys
import os


def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except:
        return False


def run_as_admin():
    """
    Re-launch the current script with administrative privileges via UAC.
    Uses the ABSOLUTE path of the script to avoid working-directory issues
    when the elevated process starts in a different folder.
    Returns True if already admin, False if elevation failed/cancelled.
    Calls sys.exit() on the non-admin process after spawning the elevated one.
    """
    if is_admin():
        return True

    try:
        # Always use the absolute path of the script being run
        script_abs = os.path.abspath(sys.argv[0])
        # The working directory for the elevated process should be the script's folder
        script_dir = os.path.dirname(script_abs)

        # Build args string: the absolute script path plus any extra argv arguments
        extra_args = " ".join(f'"{a}"' for a in sys.argv[1:])
        params = f'"{script_abs}" {extra_args}'.strip()

        hinstance = ctypes.windll.shell32.ShellExecuteW(
            None,           # hwnd
            "runas",        # lpOperation — triggers UAC
            sys.executable, # lpFile — python.exe
            params,         # lpParameters — absolute path to script + args
            script_dir,     # lpDirectory — working directory for the new process
            1               # nShowCmd — SW_NORMAL
        )

        if hinstance <= 32:
            # ShellExecute returned an error code (user cancelled UAC, etc.)
            return False

        # Successfully spawned elevated process — close the current non-admin one
        sys.exit(0)
    except Exception as e:
        print(f"[admin] Failed to elevate privileges: {e}")
        return False
