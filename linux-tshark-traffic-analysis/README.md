# Lab 01: Linux TShark 生产网络抓包与 TCP 重传排障实战

[![Run in Skillup](https://img.shields.io/badge/Run_in_Browser-Skillup_Terminal-blue?logo=linux)](https://www.skillup.host/)
[![Difficulty: Intermediate](https://img.shields.io/badge/Difficulty-Intermediate-yellow)](#)

> **实操场景**：微服务架构下跨节点调用偶尔出现 504 Gateway Timeout 或响应延迟突增，排查定位是否由于底层网络 TCP 重传、滑动窗口耗尽（Zero Window）或 TLS 握手异常所致。

---

## 🎯 练习目标

1. 掌握无需 GUI 界面的终端抓包利器 `tshark` 的核心命令行参数与输出字段提取；
2. 学会编写自动化统计脚本，快速计算指定时间窗口内的 **TCP 重传率**；
3. 定位 HTTP/HTTPS 通信中的高耗时（Time-To-First-Byte, TTFB）会话；
4. 运行 `analyze_pcap.sh` 脚本对网络流进行全景自动体检。

---

## 💻 云端免安装练习入口

> 如果你的本地系统缺少 Wireshark/TShark 依赖或受限无法抓包：  
> 👉 **点击一键直达【[Skillup 云端 Linux 实训终端](https://www.skillup.host/)】**，已内置测试网络栈与 tshark 工具链，开箱即练。

---

## 🛠️ 动手练习步骤

### 步骤 1：捕获测试网络数据流
模拟对 Web 服务的 100 次并发请求，并使用 tshark 捕获 200 个数据包：
```bash
# 监听本地回环或默认网卡 (eth0/lo)，捕获至 test_traffic.pcapng
tshark -i lo -f "tcp port 80 or tcp port 443" -c 200 -w test_traffic.pcapng
```

### 步骤 2：过滤 TCP 重传异常包
使用 Wireshark 显示过滤语法（Display Filter）提取重传数据包：
```bash
tshark -r test_traffic.pcapng -Y "tcp.analysis.retransmission" \
  -T fields -e frame.number -e ip.src -e ip.dst -e tcp.seq -e tcp.analysis.retransmission
```

### 步骤 3：统计高频请求与 HTTP 响应状态码分布
```bash
tshark -r test_traffic.pcapng -q -z http,stat
```

### 步骤 4：运行自动化诊断分析脚本
```bash
chmod +x analyze_pcap.sh
./analyze_pcap.sh test_traffic.pcapng
```

---

## ⚠️ 常见小白踩坑记录 (Pitfalls)

1. **`tshark: Permission denied`**：
   - *原因*：非 root 用户没有网络抓包能力；
   - *解决*：执行 `sudo usermod -aG wireshark $USER` 或切换至 root 执行。
2. **`BPF filter` 与 `Display filter` 混淆**：
   - `-f` 使用的是 Berkeley Packet Filter 语法（抓包前过滤，如 `port 80`）；
   - `-Y` 使用的是 Wireshark 协议分析树语法（抓包后显示过滤，如 `http.response.code >= 400`）。
