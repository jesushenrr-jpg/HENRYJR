# corretor.spec
# -*- mode: python ; coding: utf-8 -*-
import os, sys, site

block_cipher = None

# Inclui os dados Tcl/Tk que o PyInstaller às vezes não detecta automaticamente
_TCL = os.path.join(sys.prefix, 'tcl', 'tcl8.6')
_TK  = os.path.join(sys.prefix, 'tcl', 'tk8.6')

# Coleta requests e dependências do user site-packages
from PyInstaller.utils.hooks import collect_all, collect_submodules
import certifi as _certifi_mod

_req_d, _req_b, _req_h   = collect_all('requests')
_url_d, _url_b, _url_h   = collect_all('urllib3')
_cer_d, _cer_b, _cer_h   = collect_all('certifi')
_chr_d, _chr_b, _chr_h   = collect_all('charset_normalizer')
_idn_d, _idn_b, _idn_h   = collect_all('idna')

# Garante que cacert.pem seja sempre incluído (collect_all pode falhar em user site-packages)
_cacert_pem = _certifi_mod.where()   # caminho absoluto do cacert.pem instalado
_cer_d += [(_cacert_pem, 'certifi')]  # destino: _internal/certifi/cacert.pem

# Adiciona user site-packages ao path para PyInstaller encontrar os pacotes
_user_site = site.getusersitepackages()

a = Analysis(
    ['corretor.py'],
    pathex=[_user_site],
    binaries=[] + _req_b + _url_b + _cer_b + _chr_b + _idn_b,
    datas=[
        (_TCL, '_tcl_data'),
        (_TK,  '_tk_data'),
    ] + _req_d + _url_d + _cer_d + _chr_d + _idn_d,
    hiddenimports=[
        'PIL._tkinter_finder',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_agg',
    ] + _req_h + _url_h + _cer_h + _chr_h + _idn_h,
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
