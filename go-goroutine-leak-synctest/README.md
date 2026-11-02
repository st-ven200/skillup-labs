# Lab 34: Go 1.25 synctest 虚拟时间气泡与 Goroutine 泄露检测实战

[![Skillup Cloud Terminal](https://img.shields.io/badge/%E5%9C%A8%E7%BA%BF%E5%AE%9E%E6%93%8D%E7%BB%88%E7%AB%AF-Skillup.host-blue?style=for-the-badge&logo=terminal)](https://www.skillup.host/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-%E5%BC%80%E6%BA%90%E4%BB%A3%E7%A0%81%E5%BA%93-181717?style=for-the-badge&logo=github)](https://github.com/st-ven200/skillup-labs/tree/main/labs/go-goroutine-leak-synctest)

## 📌 实验目标
本实验深入 Go 官方在 Go 1.25 正式生产可用的并发测试重磅特性 **`testing/synctest`**，全面对比传统通过脆弱的 `time.Sleep` 猜谜、`runtime.NumGoroutine()` 统计与第三方 `uber-go/goleak` 库的排查缺陷，实战演练：
1. **虚拟时间气泡（Virtual Time Bubble）**：在模拟时间环境中瞬移推进 10 小时长任务（0.001 秒完成真实唤醒），彻底消除 Flaky Test（偶发脆弱测试）；
2. **Durably Blocked 协程持久阻塞判定**：无缓冲 Channel 未读取导致的工作协程挂起，在气泡退出时直接触发确定性 Deadlock 判定，实现 0 配置的 Goroutine 泄露自动捕获；
3. **安全并发汇聚模型（Safe Gather Pattern）**：结合缓冲 Channel、`sync.WaitGroup` 以及 `context.Context` 广播生命周期，构建无泄漏并发回收闭环。

---

## 🛠️ 环境要求
- Go 1.25+ 运行环境（本实验支持 Go 1.25、Go 1.26 及 Go 1.27 标准库 `testing/synctest`）
- 支持 Linux、macOS、Windows

---

## 🚀 逐步演练与执行验证

### 第一步：进入实验目录
```bash
cd labs/go-goroutine-leak-synctest
```

### 第二步：运行全量单元测试与泄露捕获验证
```bash
go test -v ./...
```

### 第三步：验证现场控制台输出
```text
=== RUN   TestVirtualTimeAcceleration
    gather_test.go:33: ✅ 虚拟时间演进: 10小时 | 宿主机物理墙上耗时仅: 10h0m0s
--- PASS: TestVirtualTimeAcceleration (0.00s)
=== RUN   TestFixedGatherCleanExit
    gather_test.go:58: ✅ SafeGather 协程均已安全回收，气泡内无泄漏
--- PASS: TestFixedGatherCleanExit (0.00s)
=== RUN   TestLeakyGatherCaughtBySynctest
    gather_test.go:75: 🎯 成功捕获 synctest 气泡死锁异常: deadlock: main bubble goroutine has exited but blocked goroutines remain
--- PASS: TestLeakyGatherCaughtBySynctest (0.00s)
PASS
ok  	practice/synctest-leak	0.002s
```

---

## ⚠️ 小白排坑要点 (Pitfalls & Best Practices)

1. **气泡隔离契约（Bubble Isolation Contract）**：
   - 气泡内部创建的 Channel、Timer、Ticker 严禁在气泡外部进行操作（如从外层协程向内部通道发送数据），否则 Go runtime 会直接 panic 抛出 `operating on bubbled object from outside`；
   - 外部包级全局变量如 `var wg sync.WaitGroup` 无法绑定至气泡，建议统一使用局部指针或由函数参数传递。
2. **非持久阻塞操作（Non-durably Blocking）边界**：
   - `synctest` 仅对气泡内部创建的 Channel、`sync.Cond.Wait`、`sync.WaitGroup.Wait` 和 `time.Sleep` 判定为 Durably Blocked；
   - **网络 Socket I/O、磁盘文件读写、系统调用（Syscall）以及 `sync.Mutex` 互斥锁争用**不会被自动快进时间，如果测试涉及网络连接，必须使用内存管道（如 `net.Pipe()`）进行隔离模拟。
3. **线上生产环境配合 `goroutineleak` 分析器**：
   - `testing/synctest` 专注于**开发与 CI 测试阶段**的单元测试防御；
   - 对于已上线生产集群，可结合 Go 1.26+ 引入的 `goroutineleak` pprof 分析端点，按照堆栈聚合展示运行超过阈值且处于无活动挂起态的协程拓扑。

---

## 🔗 配套开源与在线实操
- 📖 **配套技术深度拆解文章**：[边学边练技术中台专栏](https://www.skillup.host/)
- 💻 **云端免安装在线演练终端**：[https://www.skillup.host/](https://www.skillup.host/)
- 📦 **GitHub 开源实验代码库**：[st-ven200/skillup-labs](https://github.com/st-ven200/skillup-labs/tree/main/labs/go-goroutine-leak-synctest)
