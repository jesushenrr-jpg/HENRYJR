# corretor.spec
# -*- mode: python ; coding: utf-8 -*-
import os, sys

block_cipher = None

# Inclui os dados Tcl/Tk que o PyInstaller às vezes não detecta automaticamente
_TCL = os.path.join(sys.prefix, 'tcl', 'tcl8.6')
_TK  = os.path.join(sys.prefix, 'tcl', 'tk8.6')

a = Analysis(
    ['corretor.py'],
    pathex=[],
    binaries=[],
    datas=[
        (_TCL, '_tcl_data'),
        (_TK,  '_tk_data'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_agg',
        'requests',
        'requests.adapters',
        'requests.auth',
        'requests.cookies',
        'requests.exceptions',
        'requests.models',
        'requests.sessions',
        'urllib3',
        'urllib3.util',
        'urllib3.util.retry',
        'certifi',
        'charset_normalizer',
        'idna',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['test', 'pytest', 'unittest'],
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
    name='CORRETOR-HENRYJR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CORRETOR-HENRYJR',
)
