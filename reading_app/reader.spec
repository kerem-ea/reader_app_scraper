from PyInstaller.utils.hooks import collect_all

wv_datas, wv_binaries, wv_hiddenimports = collect_all('webview')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=wv_binaries,
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('weaver.ico', '.'),
    ] + wv_datas,
    hiddenimports=[
        'flask',
        'jinja2',
        'markupsafe',
        'werkzeug',
        'itsdangerous',
        'click',
        'clr',
        'pythonnet',
    ] + wv_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['webview.platforms.android'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='reader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='weaver.ico',
)

