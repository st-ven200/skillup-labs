# Lab 25: OpenViking 层次化智能体记忆文件系统与跨 Agent 共享总线实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **实战场景**：在多 Agent 协同系统（如 OpenClaw / Multi-Agent Teams）中，每个 Agent 若每次对话全量加载扁平历史，会导致 Token 爆炸并引发失忆与幻觉。本实战实现字节跳动 OpenViking 同款层次化文件系统记忆引擎（L0 目录索引、L1 摘要大纲、L2 全文载荷）以及 P0/P1/P2 生命周期 TTL 淘汰策略，真实验证 Token 消耗直降 95.9% 并保证跨 Agent 知识一致性。

---

## 🎯 实验目标

1. **掌握 Memory as a File System 哲学**：通过类文件系统树状结构解耦 Inode 元数据、概要与大文本。
2. **三层按需加载状态机**：
   - **L0**：开机常驻 `.abstract.json`，仅耗费 ~100-500 Tokens；
   - **L1**：相关性命中的 Summary Outlines，按需载入；
   - **L2**：具体工程大载荷，确认需要时流式读取。
3. **P0 / P1 / P2 记忆保质期管理**：
   - **P0**：永生核心（身份设定、用户习惯）；
   - **P1**：活跃迭代（90 天 TTL，自动压缩归档）；
   - **P2**：临时排障（30 天 TTL，超时安全清除）。
4. **跨 Agent 原子共享总线**：多智能体并发协作写日志与即时查询，0 模拟 fake print。

---

## 💻 快速运行与验证

### 本地快速验证

```bash
chmod +x hierarchical_memory_bus.py
python3 hierarchical_memory_bus.py
```

### 预期运行产物与断言

```text
[Benchmark] Initializing OpenViking Memory Bus in: /tmp/openviking_test_...

================== TOKEN OPTIMIZATION METRICS ==================
L0 (Directory Index Only) :    541 tokens
L1 (Index + Summaries)    :   1527 tokens
L2 (Full Naive Context)   :  13236 tokens
Token Reduction (L2 -> L0): 95.91% drop!

[Benchmark] Testing TTL Eviction...
Purged 1 expired P2 records after 31 simulated days.
Verified P0 record safely retained indefinitely.

✅ All OpenViking memory bus assertions passed cleanly with 0 mock prints!
```

---

## ⚠️ 小白避坑与排错实录 (Pitfalls)

1. **Token 估算陷阱**：中文单字约等于 1.3~1.5 Tokens，若仅用 `len(str)` 按英文单词计算会导致大模型上下文窗口截断溢出。
2. **多线程/多进程写入竞争**：多 Agent 同时写共享日志时若不加文件锁或线程锁，容易造成 `.abstract` JSON 损坏。本实战通过原子锁与 append-only jsonl 结合，保障一致性。
3. **P0 误清理隐患**：永久记忆必须使用负数 TTL（如 `-1`）显式标记，禁止用 0 或 None 默认值，避免与过期条件碰撞。

---

## 🚀 云端免安装在线演练

无需本地配置 Python 环境，直接在浏览器中秒开云端终端验证：
👉 [Skillup 边学边练在线实验平台 (https://www.skillup.host/)](https://www.skillup.host/)
