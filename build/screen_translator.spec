# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# spec 文件在 build/ 子目录，需要用项目根目录的绝对路径
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))

a = Analysis(
    [os.path.join(_ROOT, 'src', 'main.py')],
    pathex=[_ROOT, os.path.join(_ROOT, 'src')],
    binaries=[],
    datas=[
        (os.path.join(_ROOT, 'assets', 'fonts'), os.path.join('assets', 'fonts')),
    ],
    hiddenimports=[
        # src 内部模块
        'core.controller',
        'core.settings',
        'core.history',
        'core.box_manager',
        'core.overlay_layout',
        'ui.theme',
        'ui.translation_box',
        'ui.result_bar',
        'ui.selection_overlay',
        'ui.settings_window',
        'ui.history_window',
        'ui.tray',
        'ui.onboarding',
        'ocr.engine',
        'ocr.ocr_worker',
        'translation.router',
        'translation.google_trans',
        'translation.baidu_trans',
        'translation.deepl_trans',
        'translation.ai_trans',
        'translation.sogou_trans',
        'translation.youdao_trans',
        'translation.bing_trans',
        'translation.dictionary',
        'translation.dict_db',
        'translation.dict_downloader',
        # 第三方
        'rapidocr_onnxruntime',
        'onnxruntime',
        'onnxruntime.capi',
        'PyQt5.sip',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtNetwork',
        'pynput.keyboard',
        'pynput.mouse',
        'pynput._util',
        'deep_translator',
        'deepl',
        'openai',
        'anthropic',
        'mss',
        'mss.windows',
        'mss.darwin',
        'nltk',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['paddleocr', 'paddlepaddle', 'easyocr', 'cv2'],
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
    name='ScreenTranslator',
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
    icon=os.path.join(_ROOT, 'build', 'icon.ico') if sys.platform == 'win32' else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ScreenTranslator',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='ScreenTranslator.app',
        icon=os.path.join(_ROOT, 'build', 'icon.icns'),
        bundle_identifier='com.screentranslator.app',
        info_plist={
            'CFBundleDisplayName': 'ScreenTranslator',
            'CFBundleVersion': '0.1.0',
            'CFBundleShortVersionString': '0.1.0',
            'NSHighResolutionCapable': True,
            'LSUIElement': True,
            'NSAppleEventsUsageDescription': 'ScreenTranslator 需要访问屏幕内容进行 OCR 识别',
            'NSScreenRecordingUsageDescription': 'ScreenTranslator 需要录制屏幕以进行 OCR 识别',
        },
    )
