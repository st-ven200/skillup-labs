# Lab 14: 企业级双核流程引擎：状态机长事务与 DAG 拓扑编排实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **实操场景目标**：打破传统单一模型编排的局限，构建“状态机（FSM）治理宏观长周期事务 + 有向无环图（DAG）驱动微观并发任务”的双核业务流程引擎。实现基于 Kahn 算法的动态拓扑入度调度、持久化 SQLite 事件账本流，以及下游任务故障时的自动化逆序 Saga 补偿回滚。

---

## 🎯 实验核心价值与背景

在现代企业分布式系统中，复杂的业务流程（如电商履约结算、大数据 ETL、AI 智能体工作流、审批流）面临两个对立的诉求：
1. **长周期与状态交互**：需要状态机明确定义“当前在什么状态，能因什么事件跃迁”，保证幂等与状态审计；
2. **高并发与拓扑并行**：内部包含多项并行的 RPC 检查或数据处理（如查库存、扣余额、验券、风控评分），需要通过 DAG 拓扑分析实现极致的并发编排。

本实验实现了企业级双核流程引擎：
- **宏观状态机（FSM）**：管理 `INIT -> RUNNING -> COMPLETED / COMPENSATING -> COMPENSATED` 全局状态；
- **微观 DAG 调度器**：采用 Kahn 算法计算任务入度，入度为 0 的节点立即下发至线程池并发执行；
- **Saga 逆序补偿机制**：当下游节点发生网络超时（如物流 504），自动逆序调用已成功节点的补偿逻辑（退款、解锁库存、恢复优惠券）；
- **持久化审计日志**：每一笔事件均事务性落盘至 SQLite 事件表中。

---

## 🛠️ 环境依赖与预检

- **Python**：>= 3.8（仅依赖标准库 `sqlite3`、`concurrent.futures`、`threading`）
- **操作系统**：Linux / macOS / Windows
- **免安装云端秒启**：👉 [无需本地配置，一键打开 Skillup 在线实操终端直接演练](https://www.skillup.host/)

---

## 🚀 逐步演练步骤

### 1. 进入实验目录并赋权

```bash
cd labs/workflow-dual-engine-core
chmod +x dual_workflow_engine.py
```

### 2. 执行双场景实战演练

```bash
python3 dual_workflow_engine.py
```

### 3. 真实控制台输出 (Console Stdout)

```text
================================================================================
🚀 Dual Workflow Engine: FSM + DAG Hybrid Architecture Harness
================================================================================

>>> Scenario A: Normal Execution (All Tasks Complete)

[ENGINE] Dispatching workflow instance: ORDER-INST-1792426234
[ENGINE] Mode: HAPPY PATH
[ENGINE] Final FSM State: COMPLETED | Execution Success: True

[JOURNAL] Persistent Event Store Audit Log:
   2026-10-19 16:10:34 | FSM_TRANSITION                                | {"from": "INIT", "to": "RUNNING"}
   2026-10-19 16:10:34 | NODE_START           [node_freeze_stock]      | {}
   2026-10-19 16:10:34 | NODE_START           [node_deduct_balance]    | {}
   2026-10-19 16:10:34 | NODE_START           [node_lock_coupon]       | {}
   2026-10-19 16:10:34 | NODE_SUCCESS         [node_deduct_balance]    | {"result": "Balance deducted: $199.00"}
   2026-10-19 16:10:34 | NODE_SUCCESS         [node_freeze_stock]      | {"result": "Inventory frozen: 2 units"}
   2026-10-19 16:10:34 | NODE_SUCCESS         [node_lock_coupon]       | {"result": "Coupon SAVE50 applied"}
   2026-10-19 16:10:34 | NODE_START           [node_create_shipment]   | {}
   2026-10-19 16:10:34 | NODE_SUCCESS         [node_create_shipment]   | {"result": "SF-987162534"}
   2026-10-19 16:10:34 | FSM_TRANSITION                                | {"from": "RUNNING", "to": "COMPLETED"}

--------------------------------------------------------------------------------
>>> Scenario B: Downstream Node Failure & Saga Backward Compensation

[ENGINE] Dispatching workflow instance: ORDER-INST-1792426234
[ENGINE] Mode: SIMULATED ERROR & SAGA COMPENSATION

[SAGA] Node 'node_create_shipment' failed: Logistics third-party API timeout (HTTP 504 Gateway Timeout)
[SAGA] Initiating reverse compensation rollback for completed tasks: ['node_lock_coupon', 'node_freeze_stock', 'node_deduct_balance']
       ↩️  Compensated node: node_lock_coupon (锁定优惠券)
       ↩️  Compensated node: node_freeze_stock (锁定库存)
       ↩️  Compensated node: node_deduct_balance (扣减用户余额)
[ENGINE] Final FSM State: COMPENSATED | Execution Success: False

[JOURNAL] Persistent Event Store Audit Log:
   2026-10-19 16:10:34 | FSM_TRANSITION                                | {"from": "INIT", "to": "RUNNING"}
   2026-10-19 16:10:34 | NODE_START           [node_freeze_stock]      | {}
   2026-10-19 16:10:34 | NODE_START           [node_deduct_balance]    | {}
   2026-10-19 16:10:34 | NODE_START           [node_lock_coupon]       | {}
   2026-10-19 16:10:34 | NODE_SUCCESS         [node_deduct_balance]    | {"result": "Balance deducted: $199.00"}
   2026-10-19 16:10:34 | NODE_SUCCESS         [node_freeze_stock]      | {"result": "Inventory frozen: 2 units"}
   2026-10-19 16:10:34 | NODE_SUCCESS         [node_lock_coupon]       | {"result": "Coupon SAVE50 applied"}
   2026-10-19 16:10:34 | NODE_START           [node_create_shipment]   | {}
   2026-10-19 16:10:34 | NODE_FAILURE         [node_create_shipment]   | {"error": "Logistics third-party API timeout (HTTP 504 Gateway Timeout)"}
   2026-10-19 16:10:34 | FSM_TRANSITION                                | {"from": "RUNNING", "to": "COMPENSATING", "failed_at": "node_create_shipment"}
   2026-10-19 16:10:34 | COMPENSATION_START   [node_lock_coupon]       | {}
   2026-10-19 16:10:34 | COMPENSATION_SUCCESS [node_lock_coupon]       | {}
   2026-10-19 16:10:34 | COMPENSATION_START   [node_freeze_stock]      | {}
   2026-10-19 16:10:34 | COMPENSATION_SUCCESS [node_freeze_stock]      | {}
   2026-10-19 16:10:34 | COMPENSATION_START   [node_deduct_balance]    | {}
   2026-10-19 16:10:34 | COMPENSATION_SUCCESS [node_deduct_balance]    | {}
   2026-10-19 16:10:34 | FSM_TRANSITION                                | {"from": "COMPENSATING", "to": "COMPENSATED"}

================================================================================
✅ All dual-core workflow test scenarios verified successfully!
```

---

## ⚠️ 小白排坑要点 (Common Pitfalls)

1. **DAG 循环依赖死锁 (`Cycle detected in Workflow DAG topology definition`)**：
   - **原因**：节点 A 依赖 B，节点 B 又间接依赖 A，导致没有节点的入度能够归零，调度线程永久阻塞。
   - **解法**：在调度执行前，必须显式调用基于 Kahn 算法的环路校验（`validate_dag`），发现环路立即抛出清晰异常。
2. **Saga 补偿逻辑非幂等引发数据资损**：
   - **原因**：网络抖动导致补偿重试，若扣减金额的退款逻辑没有幂等校验，可能重复退款。
   - **解法**：补偿动作中必须包含防重锁与流水单据状态核验。
3. **上下文变量多线程写入竞态 (Race Condition)**：
   - **原因**：并行执行的节点同时向 `WorkflowContext` 写入数据导致脏读脏写。
   - **解法**：使用线程锁（`threading.Lock`）保护上下文数据字典，或采用不可变局部变量传递。

---

## 🌐 在线免安装交互实训

无需在本地繁琐折腾环境与系统依赖，一键在浏览器中秒开云端实操终端：  
👉 [https://www.skillup.host/](https://www.skillup.host/)
