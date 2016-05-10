# -*- mode: python -*-

# Settings for PyInstaller

a = Analysis(['./mavlink_decode.py'],
              hiddenimports = ['pymavlink.DFReader'])
resources=[]
import sys, os

kwargs = {}
exe_ext = ''
if os.name == 'nt':
  exe_ext = '.exe'

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='dataflash2sbpjson'+exe_ext,
          debug=False,
          strip=None,
          upx=True,
          console=False,
          **kwargs
          )
coll = COLLECT(exe,
               resources,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='dataflash2sbpjson')

if sys.platform.startswith('darwin'):
  app = BUNDLE(coll,
               name='dataflash2sbpjson.app')
