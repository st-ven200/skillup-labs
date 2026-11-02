#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
echo "======================================================================"
echo "🧪 [Lab 40 Runner] 执行 OpenResty + Lua + Redis 动态 IP 熔断仿真压测..."
echo "======================================================================"
python3 openresty_waf_sim.py
echo "✅ [Lab 40 Runner] 演练测试执行成功，数据闭环与性能断言正常！"
