# Laptop Cleaner & Optimizer — Build Spec
# PyInstaller 6.x one-file build với Windows 11 Fluent UI
#
# Cách build:
#   pyinstaller laptop_cleaner.spec
#
# Output: dist/LaptopCleaner.exe

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[str(Path('src').resolve())],
    binaries=[],
    datas=[
        ('src/config.json', '.'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtNetwork',
        # qfluentwidgets — critical to include all submodules
        'qfluentwidgets',
        'qfluentwidgets.components',
        'qfluentwidgets.components.widgets',
        'qfluentwidgets.components.navigation',
        'qfluentwidgets.components.settings',
        'qfluentwidgets.common',
        'qfluentwidgets.common.icon',
        'qfluentwidgets.window',
        'qfluentwidgets.window.fluent_window',
        # Windows API
        'win32api',
        'win32con',
        'win32process',
        'win32security',
        'win32event',
        'pywintypes',
        'winerror',
        # psutil
        'psutil',
        'psutil._pswindows',
        # Standard lib
        'winreg',
        'ctypes',
        'ctypes.wintypes',
        'threading',
        'hashlib',
        'shutil',
        'subprocess',
        'os',
        'sys',
        'time',
        'json',
        'platform',
        'getpass',
    ],
    excludes=[
        # Remove unused large libraries
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'IPython',
        'notebook',
        'pytest',
        'setuptools',
        'pkg_resources',
        'distutils',
        'email',
        'http',
        'urllib',
        'xml',
        'xmlrpc',
        'unittest',
        'doctest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LaptopCleaner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,           # Compress với UPX nếu có
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # Ẩn cửa sổ console (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Yêu cầu quyền Admin khi khởi chạy (UAC manifest)
    uac_admin=True,
    version='version_info.txt' if Path('version_info.txt').exists() else None,
    icon='assets/icon.ico' if Path('assets/icon.ico').exists() else None,
)
