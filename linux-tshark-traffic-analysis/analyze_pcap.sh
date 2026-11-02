#!/usr/bin/env bash
# ==============================================================================
# Linux TShark 生产流量深度诊断体检脚本 (Traffic Analyzer)
# 用法: ./analyze_pcap.sh <pcap_file>
# ==============================================================================

set -euo pipefail

PCAP_FILE="${1:-}"

if [[ -z "$PCAP_FILE" || ! -f "$PCAP_FILE" ]]; then
    echo "⚠️ 错误: 请指定有效的抓包文件路径 (pcap/pcapng)"
    echo "用法: $0 <pcap_file>"
    exit 1
fi

if ! command -v tshark &>/dev/null; then
    echo "❌ 错误: 未检测到 tshark 命令，请先安装: apt-get install -y tshark 或在 Skillup 在线终端运行"
    exit 1
fi

echo "=================================================="
echo "📊 PCAP 全景网络流量自动化体检报告"
echo "文件: $PCAP_FILE"
echo "=================================================="

# 1. 统计总帧数
TOTAL_FRAMES=$(tshark -r "$PCAP_FILE" | wc -l)
echo "📦 总数据包数量: $TOTAL_FRAMES"

# 2. 统计 TCP 重传数与重传率
RETRANS_COUNT=$(tshark -r "$PCAP_FILE" -Y "tcp.analysis.retransmission" 2>/dev/null | wc -l || echo 0)
if [[ "$TOTAL_FRAMES" -gt 0 ]]; then
    RETRANS_RATE=$(awk "BEGIN {printf \"%.2f\", ($RETRANS_COUNT / $TOTAL_FRAMES) * 100}")
else
    RETRANS_RATE="0.00"
fi
echo "🔁 TCP 重传包数: $RETRANS_COUNT (重传率: ${RETRANS_RATE}%)"

# 3. 统计零窗口警报 (Zero Window)
ZEROWIN_COUNT=$(tshark -r "$PCAP_FILE" -Y "tcp.analysis.zero_window" 2>/dev/null | wc -l || echo 0)
echo "🛑 接收端零窗口警告: $ZEROWIN_COUNT"

# 4. 统计 HTTP 异常响应码 (>=400)
echo ""
echo "🔴 HTTP 异常状态码统计 (>= 400):"
tshark -r "$PCAP_FILE" -Y "http.response.code >= 400" -T fields -e http.response.code 2>/dev/null \
    | sort | uniq -c | sort -nr || echo "   (无 HTTP 异常响应)"

# 5. 会话延迟 Top 5
echo ""
echo "⏱️ 握手与响应延迟分析 (Round Trip Time Top 5):"
tshark -r "$PCAP_FILE" -Y "tcp.analysis.ack_rtt" -T fields -e ip.src -e ip.dst -e tcp.analysis.ack_rtt 2>/dev/null \
    | sort -k3 -nr | head -n 5 || echo "   (未识别到 TCP RTT 字段)"

echo "=================================================="
echo "✅ 诊断完成。如需一键在线重放排查，请访问 https://www.skillup.host/"
