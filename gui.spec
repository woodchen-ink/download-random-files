# FilesDownloader.spec
block_cipher = None

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FilesDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    name='FilesDownloader'
)

app = BUNDLE(
    coll,
    name='FilesDownloader.app',
    icon='icons/logo800.icns',  # 指定 .icns 图标文件
    bundle_identifier='com.example.FilesDownloader',
    info_plist={
        'CFBundleName': 'FilesDownloader',
        'CFBundleDisplayName': 'FilesDownloader',
        'CFBundleExecutable': 'FilesDownloader',
        'CFBundlePackageType': 'APPL',
        'CFBundleIdentifier': 'com.example.FilesDownloader',
        'NSHighResolutionCapable': True,
    }
)
