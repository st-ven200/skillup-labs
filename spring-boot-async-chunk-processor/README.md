# Lab 39 ｜ Spring Boot 泛型切片与自愈异步聚合引擎实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![Language: Java & Python](https://img.shields.io/badge/Language-Java_%26_Python-blue.svg)](https://www.skillup.host/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **实训靶场说明**：本项目为技术文章《百万级数据批处理如何兼顾吞吐与内存？Spring Boot 泛型切片与自愈异步聚合引擎设计》的官方配套开源演练库。

---

## 🎯 场景目标

在大规模批处理（如大批量订单核销、百万级资产对账、批量短信/通知推送、第三方接口同步）场景中，单线程顺序循环执行往往导致请求严重超时，而盲目加载所有数据并开启无界异步线程池又极易引发频繁 FullGC 甚至 `OutOfMemoryError: Java heap space` 内存雪崩。

本演练的目标是构建一套**生产级泛型切片与自愈异步聚合引擎**：
1. **内存零泄漏切片**：规避 `subList` 浅视图强引用底层大数组导致的 GC 逃逸，实现动态防御式分块；
2. **Spring 异步切面自愈**：攻克 `@Async` 内部自调用代理失效暗坑，提供基于 `ApplicationContext` 的自感应注入与解耦调用；
3. **双模聚合与动态背压**：
   - **模式 A (Future 聚合)**：基于 `CompletableFuture.allOf()` 实现非阻塞流式合并，支持单个分片异常隔离与弹性重试；
   - **模式 B (Latch 门禁)**：基于 `CountDownLatch` 与带界阻塞队列实现多线程并发保序处理，结合 `CallerRunsPolicy` 拒绝策略防止任务积压引发内存溢出；
4. **端到端断言闭环**：通过自包含的压测仿真引擎对 10,000 条记录进行分批高并发处理，验证数据完整性与零丢失。

---

## 🏗️ 核心架构与数据流转

```
[原始百万级数据源 (List<T>)]
             │
             ▼
   [防御式切片 splitList]  ──> 防越界解算 & 独立块视图隔离
             │
      ┌──────┴────────────────────────┐
      ▼                               ▼
[模式 A: 结果聚合流]              [模式 B: 消费门禁流]
CompletableFuture 派发           CountDownLatch(N) 门闩派发
      │                               │
      ▼                               ▼
[独立核心线程池 (ThreadPoolTaskExecutor)]
 ├── CorePoolSize: 8
 ├── MaxPoolSize: 16
 ├── QueueCapacity: 50
 └── RejectedHandler: CallerRunsPolicy (动态背压防御)
      │
      ▼
[分片执行 Function<List<T>, ChunkResult<R>>]
 ├── 单分片业务计算
 ├── 异常压制与局部失败捕获
 └── 耗时指标统计
      │
      ▼
[结果合并器 Aggregator]
 ├── 校验总记录数 == sum(chunks)
 ├── 错误上下文拼接
 └── 零数据丢失断言
```

---

## 💻 快速运行与实操演练

无需在本地配置庞大的 Spring 生态依赖，直接运行内置的压测与断言验证脚本：

```bash
# 赋予执行权限并运行
chmod +x run_lab.sh
./run_lab.sh
```

### 预期控制台输出

```text
======================================================================
🚀 [Lab 39] Spring Boot 泛型切片与自愈异步聚合引擎压测演练
======================================================================
[Config] 总记录数: 10,000 | 分片批次大小 (ChunkSize): 500 | 预期切片数: 20
[Config] 线程池配置: 核心线程=4, 最大线程=8, 工作队列容量=10, 拒绝策略=CallerRuns
----------------------------------------------------------------------
[Dispatcher] 正在切分数据流并派发并发异步任务...
  -> [Chunk-01] 范围: [0 -> 500], 大小: 500
  -> [Chunk-02] 范围: [500 -> 1000], 大小: 500
  ...
  -> [Chunk-20] 范围: [9500 -> 10000], 大小: 500
[Dispatcher] 20 个异步任务全部提交至线程池，开始等待并发屏障聚合...
  [Worker-1] 完成分片 Chunk-01 运算，耗时: 15ms，校验和: 124750
  ...
  [Worker-4] 完成分片 Chunk-20 运算，耗时: 18ms，校验和: 4874750
----------------------------------------------------------------------
[Aggregator] 并发任务全部结束，开始执行业务一致性核验:
  - 成功处理分片数: 20 / 20 (100.0%)
  - 累计处理记录数: 10,000 条
  - 实际总校验和: 49,995,000 | 理论数学总和: 49,995,000
  - 一致性状态: ✅ 完全匹配 (Zero Loss)
  - 总耗时: 42ms (比单线程串行提升约 380% 吞吐量)
======================================================================
🎉 [Lab 39] 核心断言校验全部通过！
======================================================================
```

---

## 🔍 踩坑与排错实录 (Troubleshooting)

### 坑 1：类内自调用导致 `@Async` 代理失效变串行
- **现象**：在 `ListProcessor` 类内部直接调用 `this.processChunkAsync(...)`，发现所有切片依然在同一个主线程中顺序执行，耗时毫秒未减。
- **原因**：Spring AOP 代理依托于外部调用。类内部方法间直接通过 `this` 调用属于原生 JVM 对象指针跳转，不会触发 CGLIB / JDK 动态代理切面逻辑。
- **解法**：通过持有 `ApplicationContext` 在运行时获取代理 Bean：`applicationContext.getBean(this.getClass()).processChunkAsync(...)`，或者在类上注入自身 `@Autowired private ListProcessor self;`。

### 坑 2：`subList` 浅视图引发的老年代内存驻留
- **现象**：分批处理完后，老年代内存占用居高不下，即使调用了 `System.gc()` 仍无法释放大数组。
- **原因**：`ArrayList.subList()` 返回的是内部类 `SubList`，其内部保存了对原始 `parent` 数组的强引用。如果分片任务长期驻留线程池或结果集被持有，整个原始大数组都无法被垃圾回收。
- **解法**：在切片时进行防御式浅拷贝：`new ArrayList<>(list.subList(from, to))`，切断对原始超大集合的隐式强引用。

---

## 🌐 在线云端实训终端

不想在本地配置任何环境？点击下方链接即可在浏览器中一键秒开 Skillup 交互式云端终端进行调试演练：

👉 **[点击启动 Skillup 在线实操终端](https://www.skillup.host/)**
