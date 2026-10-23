# Skillup Hands-on Labs ｜ 边学边练高质量实战练习库

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/st-ven200/skillup-labs/pulls)

> **让技术的每一次落地，都有真实可运行的实操闭环。**  
> 本子项目是【[边学边练 (www.skillup.host)](https://www.skillup.host/)】全网深度落地技术文章的官方配套练习库。每一个练习均附带**排查思路、环境准备、可运行脚本、报错排坑实录**以及**一键云端免安装运行终端**。

---

## 🚀 为什么要有这个练习库？

在阅读技术文章或看源码时，开发者最大的痛点通常是：
1. **纸上谈兵**：看完觉得“懂了”，自己动手时连第一步命令都报错；
2. **环境折磨**：为了验证一个几行的知识点，本地折腾环境、处理系统依赖耗费半天；
3. **踩坑无据**：教程给的都是完美答案，遇到版本变动或参数异常无从下手。

**Skillup Labs 的设计原则：**
- **开箱即用**：所有脚本和演练代码均经过去敏感化、自包含设计；
- **云端秒启**：不想在本地折腾繁琐依赖？点击章节对应的【Skillup 云端实操终端】链接，直接在浏览器中秒开预装环境开始练习；
- **带坑解析**：每个练习不仅展示“如何做对”，更记录“小白常踩的坑与排错输出”。

---

## 📚 练习索引目录 (Labs Index)

| 编号 | 练习主题 | 技术栈 | 难度 | 对应落地文章与实训入口 |
|:---:|---|---|:---:|---|
| **Lab 01** | [Linux TShark 生产网络抓包与 TCP 重传排障实战](./linux-tshark-traffic-analysis/) | `Linux` `TShark` `Shell` | ⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 02** | [Nginx Location 匹配优先级陷阱与 WAF 安全过滤](./nginx-production-location-waf/) | `Nginx` `WAF` `HTTP` | ⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 03** | [现代 Python Ruff 极速规范检查与 CI 自动化流水线](./python-ruff-linter-automation/) | `Python` `Ruff` `CI/CD` | ⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 04** | [MySQL 8.0 慢查询分析与索引下推 (ICP) 调优实战](./mysql-slow-query-explain-lab/) | `MySQL 8` `SQL` `DBA` | ⭐️⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 05** | [桌面端智能体 QoderWork 沙盒隔离与渐进式 Skills 编排实战](./qoderwork-desktop-agent-sandbox/) | `AI Agent` `Python` `Sandbox` | ⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 06** | [Block 开源 AI 研发智能体 Goose 自主循环与 MCP 扩展实战](./goose-autonomous-agent-loop/) | `AI Agent` `Rust` `MCP` | ⭐️⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 07** | [OpenObserve 轻量级云原生全栈可观测性与万级 QPS 日志流实战](./openobserve-lightweight-observability/) | `Rust` `Parquet` `SQL` | ⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 08** | [BettaFish 多智能体协同流水线与实时舆情研判实战](./bettafish-multi-agent-analysis/) | `AI Agent` `Multi-Agent` `Python` | ⭐️⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 09** | [Free-FS 企业级文件分片上传与断点续传状态机实战](./free-fs-chunked-upload-pipeline/) | `Spring Boot` `Storage` `Python` | ⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 10** | [OpenClaw 多智能体 Squad 敏捷协同与 agentToAgent 路由引擎实战](./openclaw-squad-agent-orchestrator/) | `AI Agent` `Multi-Agent` `Feishu` | ⭐️⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 11** | [OpenClaw Skills 供应链安全静态审计与依赖锁定](./openclaw-skill-security-audit/) | `Python` `AI Agent` `Security` | ⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 12** | [OpenClaw Manager 跨渠道网关适配与守护进程 IPC 桥接](./openclaw-manager-gateway-bridge/) | `Tauri` `Rust` `Python` `IM` | ⭐️⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 13** | [Claude Code 并发 Worktree 隔离与智能体记忆自愈实战](./claude-code-worktree-orchestrator/) | `Git` `Claude Code` `Python` `CLI` | ⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 14** | [企业级双核流程引擎：状态机长事务与 DAG 拓扑编排实战](./workflow-dual-engine-core/) | `Workflow` `DAG` `StateMachine` `Python` | ⭐️⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 15** | [RabbitMQ 原生事务缺陷对比与异步 Confirm / 本地消息表高可用实战](./rabbitmq-transaction-publisher-confirm/) | `RabbitMQ` `Outbox` `Python` `MessageQueue` | ⭐️⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 16** | [企业级微服务聚合编排与自适应断路器实战](./microservice-aggregator-circuit-breaker/) | `Microservice` `CircuitBreaker` `Python` `Architecture` | ⭐️⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 17** | [Spring Boot 枚举断言模式与零侵入异常切面收敛](./spring-boot-enum-assert-pattern/) | `Spring Boot` `Java` `CleanCode` `Python` | ⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 18** | [京东 asyncTool 异步任务 DAG 编排与线程池隔离防护](./asynctool-dag-task-orchestrator/) | `asyncTool` `DAG` `Concurrency` `Python` | ⭐️⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 19** | [Spring Boot 泛型策略工厂与多端统一鉴权架构实战](./springboot-strategy-auth-engine/) | `Spring Boot` `DesignPattern` `Python` `Auth` | ⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |
| **Lab 20** | [sg-exam 行级多租户隔离与动态组卷内核实战](./multi-tenant-exam-engine/) | `MultiTenant` `SaaS` `Python` `Algorithms` | ⭐️⭐️⭐️⭐️ | [配套文章](https://www.skillup.host/) ｜ [👉 在线实操终端](https://www.skillup.host/) |

---

## 🛡️ 隐私保护与安全红线 (Security & Privacy)

本仓库所有公开示例严格遵循**无私有凭证原则**：
1. **脱敏占位**：所有示例中出现的 IP 均为标准回环地址（`127.0.0.1`）或保留私网段（`192.168.1.0/24`），域名一律使用 `example.com` 或官方门户；
2. **禁止凭据提交**：严禁硬编码任何真实 API Key、生产数据库账号、私有 Token 或网络抓包敏感载荷；
3. **安全审计**：配置有严格的 `.gitignore` 规则，防止私有文件误入版本控制。

---

## 🤝 贡献与互动

- 如果你在演练过程中发现了更好的排错解法或新特性演进，欢迎提交 Pull Request！
- 发现任何 Bug 或环境问题，欢迎在 [Issues](https://github.com/st-ven200/skillup-labs/issues) 中交流。
