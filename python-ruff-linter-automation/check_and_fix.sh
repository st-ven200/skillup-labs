#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo "⚡ Ruff 极速代码扫描与自修复演练"
echo "=================================================="

if ! command -v ruff &>/dev/null; then
    echo "⚠️ 本地未检测到 ruff 命令，可执行: pip install ruff"
    echo "💡 或直接使用已预装好全套工具链的云端环境: https://www.skillup.host/"
    exit 0
fi

echo "🔍 1. 运行静态规则扫描:"
ruff check bad_code.py || true

echo ""
echo "🛠️ 2. 执行安全规则自修复 (Fixing):"
ruff check bad_code.py --fix || true

echo ""
echo "🎨 3. 执行格式美化 (Formatting):"
ruff format bad_code.py

echo "=================================================="
echo "✅ 修复完成！查看更多 Python 现代工程实战: https://www.skillup.host/"
