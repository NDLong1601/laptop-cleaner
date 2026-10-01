import sys
import os

# Ensure src directory is in path regardless of where Python is launched from
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from ui.app import LaptopCleanerApp
from core.admin import is_admin, run_as_admin


def main():
    # Attempt to request Admin privileges.
    # run_as_admin() calls sys.exit() on the non-admin process, so code
    # below this block only runs when we ARE admin (or elevation was skipped).
    if not is_admin():
        elevated = run_as_admin()
        # If elevation failed (user cancelled UAC), run anyway in normal mode
        # elevated == False means we continue without admin rights

    # Set Windows AppUserModelID so taskbar groups and shows correct icon
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("NDLong.LaptopCleaner.App.1.0")
    except Exception:
        pass

    # Enable crisp High-DPI rendering on modern displays
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

    # Set application icon
    from PyQt6.QtGui import QIcon
    icon_path = os.path.normpath(os.path.join(src_dir, "..", "assets", "icon.png"))
    if not os.path.exists(icon_path):
        base_dir = getattr(sys, '_MEIPASS', src_dir)
        icon_path = os.path.join(base_dir, "assets", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = LaptopCleanerApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
