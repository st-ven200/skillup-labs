# Lab 38: 高并发异步任务聚合器设计与压测治理实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **实训场景目标**：解决 Java 高并发业务中“散弹式异步并发聚合”的核心痛点（手写 `CountDownLatch` 极易死等泄露、`CompletableFuture.allOf` 异常被隐式吞没且无序、超时缺乏上下文诊断等）。实现一套生产级的高并发异步任务聚合器（`TaskAggregator` / `LatchUtils`）。

---

## 🎯 业务与技术核心痛点

1. **多线程并发下的保序槽位回填（Ordered Slots）**：
   - 聚合层并发调用“用户信息”、“订单详情”、“优惠券”、“风控校验”等多个微服务，由于网络延迟与处理耗时不同，各线程完成的时间差异极大。
   - 如果直接使用线程不安全的 `ArrayList.add`，不仅会发生并发写入丢失，更会导致结果集顺序错乱，上层业务取值发生致命错位。
2. **异常零吞没与压制树收集（Suppressed Exception Tree）**：
   - 传统的 `CompletableFuture.anyOf` 或普通 `latch.await` 往往只能抛出最先发生的单个异常，甚至在某些链式调用中把下游真实的异常原因吞掉，只抛出 `CompletionException: null`。
   - 生产级聚合器必须全量捕获所有子任务抛出的异常，统一汇聚到根 `ExecutionException`，并通过 `addSuppressed()` 保留完整的调用链堆栈。
3. **带排查上下文的快速超时熔断（Diagnostic Timeout）**：
   - 线上流量洪峰时下游服务可能突发卡死，如果等待超时，绝不能只抛出冷冰冰的 `TimeoutException: null`。
   - 必须在异常信息中清晰打印：`traceId`、设定超时阈值、已完成任务数、未完成滞后任务数，让值班人员夜间告警一眼看清堵塞点。

---

## 📁 目录结构

```
labs/java-async-task-aggregator/
├── README.md               # 本实验说明文档与排坑实录
├── TaskAggregator.java     # 生产级 Java 原生任务聚合器源码
├── async_aggregator.py     # 原生并发仿真引擎（双轨实现）
└── test_aggregator.py      # 核心场景测试套件（保序回填、异常压制树、超时熔断）
```

---

## 💻 快速开始

### 方式一：云端免安装秒级实操（推荐）
点击一键进入 [Skillup 边学边练在线实操平台 (https://www.skillup.host/)](https://www.skillup.host/)，在云端终端中选择 `Lab 38: 高并发异步任务聚合器` 即可免装环境直接运行。

### 方式二：本地运行验证

```bash
# 1. 进入实验目录
cd /workspace/article/labs/java-async-task-aggregator

# 2. 运行高并发场景测试
python3 test_aggregator.py
```

---

## 🔍 控制台真实执行结果实录

```text
==================================================
🚀 开始执行 TaskAggregator 异步任务聚合器并发场景测试
==================================================

--- [Scenario 1] 正常多并发调用：验证有序结果槽位 ---
✅ 并发执行耗时: 0.150s (理论耗时约最慢任务 0.15s)
   Slot [0]: Result-From-UserService (latency=150ms)
   Slot [1]: Result-From-OrderService (latency=50ms)
   Slot [2]: Result-From-InventoryService (latency=100ms)
   Slot [3]: Result-From-CouponService (latency=20ms)
🎉 场景 1 校验通过：结果顺序严格保序！

--- [Scenario 2] 部分任务崩溃：验证异常压制树收集，杜绝吞异常 ---
✅ 成功捕获聚合异常，且异常未被丢失：
❌ [TaskAggregator PartialFailure] traceId=TRACE-PAY-FAIL-002, totalTasks=3, failedCount=2:
   ├── [Suppressed #1] ConnectionError: 下游服务 [CreditCheckService] 响应异常: Read timed out after 0.06s
   ├── [Suppressed #2] ConnectionError: 下游服务 [FraudDetectService] 响应异常: Read timed out after 0.08s
🎉 场景 2 校验通过：全量异常形成压制树，零吞没！

--- [Scenario 3] 下游超时卡死：验证超时精准快速诊断 ---
✅ 成功于 0.200s 精准熔断抛出超时异常：
   Context: [TaskAggregator Timeout] traceId=TRACE-TIMEOUT-003, timeout=200ms, totalTasks=3, uncompletedTasks=2
🎉 场景 3 校验通过：超时极速断开并输出清晰诊断上下文！

==================================================
🏆 TaskAggregator 所有核心高并发场景测试全部通过！
==================================================
```

---

## ⚠️ 小白排坑与高并发架构要点 (Pitfalls)

1. **严禁在子线程执行 join() 阻塞等待**：
   - 在向线程池分发任务时，很多初学者在 `CompletableFuture` 后立即调用 `.join()` 或 `.get()`，这会直接把主线程或工作线程锁死，不仅失去了并发优势，还会导致局部异常提前抛出而无法等齐其他任务。
2. **线程池隔离与上下文（MDC/TraceId）丢失**：
   - 异步提交到通用线程池时，主线程的 `MDC`（Mapped Diagnostic Context）默认不会自动透传到子线程，导致日志中 `traceId` 丢失。生产环境中必须使用装饰器（如 `MdcTaskDecorator`）或在提交前手动捕获并塞入子线程上下文。
3. **超时后未完成任务的幽灵执行与连接泄漏**：
   - 当 `latch.await` 超时抛出异常后，提交到线程池中的慢任务可能仍在后台持续占用 HTTP 连接或数据库连接。应根据业务需要决定是否持有 `Future` 引用并在超时时触发 `future.cancel(true)` 发出中断信号。
