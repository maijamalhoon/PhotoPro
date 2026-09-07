# -*- mode: python ; coding: utf-8 -*-
# PhotoPro PyInstaller Specification File
# Builds standalone Windows Desktop distribution

import sys
import os

block_cipher = None
app_root = os.path.abspath(SPECPATH)

datas = [
    (os.path.join(app_root, 'u2netp.onnx'), '.'),
    (os.path.join(app_root, 'THIRD_PARTY_LICENSES.md'), '.'),
]

binaries = []
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtPrintSupport',
    'onnxruntime',
    'cv2',
    'PIL',
    'PIL.Image',
    'PIL.ImageOps',
    'sqlite3',
    'numpy',
]

a = Analysis(
    ['run_desktop.py'],
    pathex=[app_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PhotoPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # False = No black CMD window in production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PhotoPro',
)
