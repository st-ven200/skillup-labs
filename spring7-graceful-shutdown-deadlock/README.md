# Lab 27: Spring 7.0.4 优雅停机并发死锁成因与非阻塞治理实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **实操目标**：通过真实多线程并发竞争模拟 Spring 7 早期版本中 `ContextClosedEvent` 与 `ShutdownHook` 竞争引发的死锁（Issue #36260），并在实测环境中验证 Spring 7.0.4 引入的原子状态门禁与分离式生命周期治理方案。

---

## 1. 架构死锁成因拓扑

在容器化（K8s）环境频繁滚动更新或集成测试退出时，JVM 停机钩子与 Spring 容器关闭线程发生锁交叉：

```
[线程 1: Spring 上下文停机] ---> 持有 lifecycleMonitor 锁 ---> 等待工作线程/Hook 完成清理
                                                                        ^
                                                                        | (死锁环路)
                                                                        v
[线程 2: JVM ShutdownHook]   ---> 试图获取 lifecycleMonitor 锁 <--- 相互阻塞挂起
```

## 2. 核心实验脚本

- `simulate_deadlock.py`：包含高并发脆弱版本与 Spring 7.0.4 治理版本的双向对比测试。

### 运行实测命令

```bash
python3 simulate_deadlock.py
```

### 真实输出实录

```text
============================================================
🚀 [Lab 27] Spring 7.0.4 并发优雅停机死锁成因与治理实操验证
============================================================

[测试阶段 1] 运行高并发脆弱版本 (VulnerableLifecycleManager)...
👉 脆弱版本捕获到死锁/超时事件数: 1
   ⚠️ T1 (ContextClosed): Deadlock detected: ContextClosedEvent locked lifecycle_lock waiting for worker_event

[测试阶段 2] 运行 Spring 7.0.4 并发治理版本 (PatchedLifecycleManager)...
👉 治理版本多线程并发关闭总耗时: 1.76 ms
👉 执行统计: 成功关闭 1 次 (1), 安全忽略竞争调用 (9)

✅ [VERIFICATION PASSED] 治理方案通过全部断言，无死锁、无阻塞、无假死！
```

## 3. 产线生产排坑与高可用建议

1. **避免在 ShutdownHook 中调用阻塞式 RPC**：停机钩子应当只做本地资源标记，避免跨网络外部依赖；
2. **升级 Spring 7.0.4+ / Spring Boot 4.0**：修复了 `ConfigurableApplicationContext` 在高并发多 Hook 下的生命周期事件争用问题；
3. **K8s terminationGracePeriodSeconds 设置**：配置合理的优雅下线等待窗口（如 30s-60s），配合 `/actuator/health` 探针预注销。
