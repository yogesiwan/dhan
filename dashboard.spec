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
    hiddenimports=['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets'],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FinancialDashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# For Linux, create a .desktop file for the application
if sys.platform.startswith('linux'):
    import os
    desktop_file = '''[Desktop Entry]
Name=Financial Dashboard
Comment=A Financial Dashboard Application
Exec={}/FinancialDashboard
Icon={}/icon.png
Terminal=false
Type=Application
Categories=Finance;
'''.format('${INSTALL_PATH}', '${INSTALL_PATH}')
    
    with open('FinancialDashboard.desktop', 'w') as f:
        f.write(desktop_file)
    
    # Add the .desktop file to datas
    a.datas += [('FinancialDashboard.desktop', 'FinancialDashboard.desktop', 'DATA')] 