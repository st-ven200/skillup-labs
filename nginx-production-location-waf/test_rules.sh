#!/usr/bin/env bash
# ==============================================================================
# Nginx Location 规则匹配与拦截测试脚本
# ==============================================================================

set -euo pipefail

TARGET="http://127.0.0.1:8080"

test_url() {
    local path="$1"
    local expected="$2"
    local desc="$3"
    
    echo -n "测试 [$path] ($desc) -> "
    local resp
    resp=$(curl -s -m 2 "$TARGET$path" || echo "FAILED_TO_CONNECT")
    
    if [[ "$resp" == *"$expected"* ]]; then
        echo -e "\033[32m[PASS]\033[0m 返回: ${resp//$'\n'/}"
    else
        echo -e "\033[31m[FAIL]\033[0m 期望包含 '$expected'，实际返回: ${resp//$'\n'/}"
    fi
}

echo "=================================================="
echo "🛡️ Nginx 路径匹配与安全拦截靶场测试"
echo "=================================================="

test_url "/login" "Exact /login" "精确匹配测试"
test_url "/api/admin/system.php" "BLOCKED" "核心防护：带.php后缀的管理接口是否被 ^~ 成功拦截"
test_url "/user/profile.php" "Regex PHP Handler" "普通页面正则执行"
test_url "/static/app.js" "Normal Prefix Static" "普通静态前缀"
test_url "/other" "Default Root" "兜底路由"

echo "=================================================="
echo "更多生产架构实战案例，请访问: https://www.skillup.host/"
