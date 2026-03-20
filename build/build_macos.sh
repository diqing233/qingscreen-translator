#!/usr/bin/env bash
# ScreenTranslator macOS 打包脚本
# 使用方法: 在项目根目录运行 bash build/build_macos.sh

set -euo pipefail

VERSION="${1:-0.1.0}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== ScreenTranslator macOS 打包 v$VERSION ==="

# 安装依赖
echo ""
echo "[1/4] 安装依赖..."
pip3 install pyinstaller>=6.0 --quiet
pip3 install -r requirements.txt --quiet

# 清理旧构建
echo "[2/4] 清理旧构建..."
rm -rf dist/ScreenTranslator dist/ScreenTranslator.app

# PyInstaller 打包
echo "[3/4] 运行 PyInstaller..."
pyinstaller build/screen_translator.spec --noconfirm

# 打包为 DMG（优先）或 ZIP
echo "[4/4] 创建发布包..."
APP_PATH="dist/ScreenTranslator.app"
OUTPUT_NAME="ScreenTranslator-macos-$VERSION"

if command -v hdiutil &> /dev/null && [ -d "$APP_PATH" ]; then
    DMG_PATH="dist/$OUTPUT_NAME.dmg"
    # 创建临时目录
    TMP_DIR=$(mktemp -d)
    cp -R "$APP_PATH" "$TMP_DIR/"
    # 创建 DMG
    hdiutil create -volname "ScreenTranslator" \
        -srcfolder "$TMP_DIR" \
        -ov -format UDZO \
        "$DMG_PATH"
    rm -rf "$TMP_DIR"
    echo ""
    echo "=== 打包完成！==="
    echo "DMG: $DMG_PATH"
else
    ZIP_PATH="dist/$OUTPUT_NAME.zip"
    zip -r "$ZIP_PATH" dist/ScreenTranslator* -x "*.DS_Store"
    echo ""
    echo "=== 打包完成！==="
    echo "ZIP: $ZIP_PATH"
fi
