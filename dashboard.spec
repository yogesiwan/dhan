# -*- mode: python ; coding: utf-8 -*-
import sys

block_cipher = None

# Common data files for both platforms
datas = [
    ('background.png', '.'),
    ('bg_blurlow.png', '.'),
]

a = Analysis(
    ['dashboard.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='FinancialDashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    target_arch='arm',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FinancialDashboard'
)

# For Linux, create a .desktop file for the application
if sys.platform.startswith('linux'):
    import os
    desktop_file = '''[Desktop Entry]
Name=Financial Dashboard
Comment=A Financial Dashboard Application
Exec=/usr/local/bin/financial-dashboard/FinancialDashboard
Icon=/usr/local/bin/financial-dashboard/icon.png
Terminal=false
Type=Application
Categories=Finance;
'''
    
    with open('FinancialDashboard.desktop', 'w') as f:
        f.write(desktop_file) 