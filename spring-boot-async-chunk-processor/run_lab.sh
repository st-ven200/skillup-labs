#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
echo "======================================================================"
echo "🧪 [Lab 39 Runner] 执行 Spring Boot 异步切片与聚合引擎仿真压测..."
echo "======================================================================"
python3 chunk_processor_sim.py
echo "✅ [Lab 39 Runner] 演练测试执行成功，数据闭环与性能断言正常！"
