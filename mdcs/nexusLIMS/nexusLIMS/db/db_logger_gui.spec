# -*- mode: python ; coding: utf-8 -*-
# Run this file with Pyinstaller v3.5, on Python 3.4.4 (32-bit) via:
# C:\Python34-32\Scripts\pyinstaller.exe db_logger_gui.spec

block_cipher = None
options = [ ]

a = Analysis(['db_logger_gui.py'],
             pathex=['Z:\\tmp\\db', 'M:\\db'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

import os
on_vm = False
if os.path.isfile('M:\\db\\logo_bare.png'):
    on_vm = True

exe = EXE(pyz,
          a.scripts,
          options,
          a.binaries + [
              ('logo_bare.png',
              'M:\\db\\logo_bare.png' if on_vm else 'Z:\\tmp\\db\\logo_bare.png',
              'DATA'),
              ('logo_bare_xp.ico',
              'M:\\db\\logo_bare_xp.ico' if on_vm else 'Z:\\tmp\\db\\logo_bare_xp.ico',
              'DATA'),
              ('copy.png',
              'M:\\db\\copy.png' if on_vm else 'Z:\\tmp\\db\\copy.png',
              'DATA'),
              ('window-close.png',
              'M:\\db\\window-close.png' if on_vm else 'Z:\\tmp\\db\\window-close.png',
              'DATA'),
              ('file.png',
              'M:\\db\\file.png' if on_vm else 'Z:\\tmp\\db\\file.png',
              'DATA'),
              ('logo_text_250x100.png',
              'M:\\db\\logo_text_250x100.png' if on_vm else 'Z:\\tmp\\db\\logo_text_250x100.png',
              'DATA')
              ],
          a.zipfiles,
          a.datas,
          [],
          name='db_logger_gui',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True, 
          icon='logo_bare_xp.ico')
