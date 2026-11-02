# Lab 18: 京东 asyncTool 异步任务 DAG 编排与线程池隔离防护

[![Skillup Host](https://img.shields.io/badge/Skillup-Cloud_Terminal-blue.svg)](https://www.skillup.host/)
[![Status](https://img.shields.io/badge/Status-Verified-success.svg)]()

> 本实验为文章《面对多 RPC 扇入超时崩溃：深入 asyncTool 核心 DAG 编排与线程池隔离防护》的配套开源实战。

## 1. 实验目标与高并发痛点

在大型电商中台（如商品详情页聚合、购物车结算）中，一个接口往往需要并发调用 5~10 个下游 RPC 服务：
- 商品核心信息、库存状态、优惠券折扣、运费规则、会员权益、风控白名单、推荐商品流。

传统 `Future.get()` 或 `CompletableFuture.allOf()` 存在两大致命缺陷：
1. **拓扑编排极其晦涩**：当任务依赖形成复杂有向无环图（DAG），比如 D 必须等待 B 和 C 均完成后才启动，代码中容易出现大量深度回调地狱与嵌套锁；
2. **缺乏级联熔断与默认值兜底**：当下游某非核心服务（如推荐）超时挂起，如果不能精准设置单节点超时与 `defaultValue` 自动降级，会导致整个请求长尾放大，拖垮上游线程池引发雪崩。

**本 Lab 解决方案**：
参考京东开源 `asyncTool` 架构思想，实现基于 **`WorkerWrapper` 状态机 + 拓扑事件驱动 + 线程池隔离** 的全功能 DAG 编排引擎。

```
                    ┌──► [Task-B: 优惠券计算] ──┐
                    │                          │
[Task-A: 核心商品] ──┤                          ├──► [Task-D: 结算汇总与风控]
                    │                          │
                    └──► [Task-C: 会员权益] ──┘

[Task-E: 独立推荐瀑布流 (完全异步并行)]
```

## 2. 核心架构与特性

- **声明式依赖装配**：`w_b.add_depend(w_a)` 一行声明拓扑关系；
- **自动扇出与扇入汇聚**：前置节点完成后广播通知后续节点，所有前置依赖满足后才唤醒执行；
- **全链路降级容错**：为每个任务设置超时阈值与 `defaultValue`，超时或异常自动兜底，绝不卡死下游汇聚节点。

## 3. 快速运行与实操演练

运行自包含的验证脚本：

```bash
python3 run_demo.py
```

### 预期执行输出

```json
=== 开始运行高并发异步任务 DAG 编排与依赖容错隔离引擎演练 ===

[DAG 执行完毕] 总耗时: 161.09 ms (传统串行预计耗时: 320ms+)
  [Task-A] 状态: SUCCESS | 产出: {'id': 9901, 'title': '4K Ultra-HD Monitor', 'basePrice': 2000.0}
  [Task-B] 状态: SUCCESS | 产出: {'couponDiscount': 200.0}
  [Task-C] 状态: SUCCESS | 产出: {'vipRebate': 100.0}
  [Task-D] 状态: SUCCESS | 产出: {'orderId': 'ORD-20261022-8888', 'finalPrice': 1700.0}
  [Task-E] 状态: SUCCESS | 产出: ['DisplayPort Cable', 'Screen Cleaner Kit', 'Ergonomic Monitor Arm']

[OK] DAG 编排引擎与汇聚扇入用例 100% 验证通过！
```

## 4. 小白排坑指南 (Pitfalls & Best Practices)

1. **避免循环依赖**：DAG 图定义时必须通过拓扑排序保证无环，若 A 依赖 B 且 B 依赖 A，会导致死锁，因此必须在任务注册阶段做入度拓扑校验；
2. **核心业务与非核心业务线程池隔离**：严禁所有异构任务共用同一个全局线程池！推荐将核心交易结算 DAG 与旁路推荐/打点任务拆分为独立的 ThreadPoolExecutor，避免慢任务占满队列耗尽核心线程；
3. **拒绝策略选择**：聚合网关推荐采用 `CallerRunsPolicy` 或定制的快速失败拒绝策略，配合下游降级返回默认空列表，确保高负载下核心链路不崩。

---
💡 **在线实战体验**：本项目免安装环境已部署于 [边学边练实验中台](https://www.skillup.host/)，可直接在 Web 终端进行交互式验证。
