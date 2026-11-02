# Lab 15: RabbitMQ 原生事务缺陷对比与异步 Confirm / 本地消息表高可用实战

[![Skillup Cloud Terminal](https://img.shields.io/badge/Skillup-在线交互实操终端-blue?style=for-the-badge&logo=gnubash)](https://www.skillup.host/)

> 📂 **所属专栏与项目**：[Skillup Hands-on Labs (st-ven200/skillup-labs)](https://github.com/st-ven200/skillup-labs)  
> 🔗 **配套文章**：《吞吐量暴跌 200 倍的代价：RabbitMQ 原生事务缺陷与高并发异步 Confirm/本地消息表实战解构》  
> 🚀 **免安装在线验证**：无需本地折腾复杂的 RabbitMQ 与 Python 依赖，一键在浏览器中秒开云端实操终端进行交互验证 👉 [Skillup 边学边练在线实验平台 (https://www.skillup.host/)](https://www.skillup.host/)。

---

## 1. 实验场景与核心目标

在金融支付、电商交易等核心链路上，“消息绝对不能丢”是系统的生命线。很多工程师直觉选择 RabbitMQ 原生事务（`txSelect` / `txCommit` / `txRollback`），却在压测时遭遇吞吐量断崖式暴跌（超 200 倍跌幅）。

本实验通过自包含的端到端可执行引擎，深入验证以下核心能力：
1. **原子回滚验证**：基于本地消息表（Transactional Outbox Pattern）实现业务落库与消息暂存的强一致事务绑定，彻底杜绝孤儿消息。
2. **异步 Confirm 状态流转**：模拟轻量级非阻塞 Publisher Confirm 协议，验证成功 ACK 归档与失败 NACK/超时指数退避重试。
3. **消费端幂等过滤**：通过唯一 Message ID 约束防止重复投递导致的二次业务操作。
4. **吞吐量性能基准比对**：精确比对原生事务同步阻塞 RTT 与批量异步 Confirm 的微秒级性能差异。

---

## 2. 快速上手与运行验证

### 步骤 1：直接运行自包含对比引擎

无需前置部署 RabbitMQ 即可直接验证协议与本地消息表闭环逻辑：

```bash
python3 rabbitmq_outbox_confirm_engine.py
```

预期终端输出：
```text
======================================================================
>>> 启动 RabbitMQ 原生事务 vs Publisher Confirm 与本地消息表引擎验证
======================================================================

[STEP 1] 验证业务操作异常时的本地消息表原子回滚...
  -> 原子回滚校验通过：业务失败未残留孤儿消息！

[STEP 2] 验证 Publisher Confirm 状态流转与失败重试熔断...
  -> 重试与死信熔断状态机校验通过！

[STEP 3] 验证消费端基于唯一 Message ID 的幂等防重机制...
  -> 消费端幂等过滤校验通过！

[STEP 4] 运行吞吐量对照测试 (Message Count: 50)...
  - 原生事务 tx.commit (同步阻塞 50 条): 133.75 ms
  - 异步 Publisher Confirm (流水线 50 条): 5.30 ms
  - 性能加速比 (Throughput Speedup): 25.2x 倍提升！
```

### 步骤 2：启动真实 RabbitMQ 容器拓扑（可选扩展）

如需对接真实 Broker 进行实时队列投递，可一键拉起 Docker Compose：

```bash
docker compose up -d
# 访问 RabbitMQ Web 管理台：http://localhost:15672 (账号密码: guest / guest)
```

---

## 3. 生产踩坑排障实录 (Pitfalls)

1. **绝对不要在同个 Channel 混用 `txSelect()` 与 `confirmSelect()`**：
   - RabbitMQ 协议规范中，两者是互斥模式。若在同一个通道内先后调用，Broker 会直接抛出 `406 (PRECONDITION_FAILED)` 异常并强制关闭 Channel。
2. **异步 Confirm 的 ACK 丢失陷阱**：
   - 生产环境中 Publisher 发送消息后，若在收到 Broker 的 `basic.ack` 之前发生网络抖动或服务崩溃，本地消息表状态仍为 `PENDING`。后台调度器再次补偿重试会导致消息重复发送，因此**消费端必须实现基于业务唯一 ID 的幂等去重防线**。
3. **本地消息表定时扫描的慢查询与死锁防范**：
   - 在高并发系统中，Outbox 表数据增长极快。必须对 `status` 和 `created_at` 建立联合索引，并在抓取待发消息时使用 `SELECT ... FOR UPDATE SKIP LOCKED`（MySQL 8.0+ / PostgreSQL），避免分布式工作节点出现锁竞争争用。
