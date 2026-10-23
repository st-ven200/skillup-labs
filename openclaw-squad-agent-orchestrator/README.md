# Lab 10: OpenClaw 多智能体 Squad 敏捷协同与 agentToAgent 路由引擎实战

[![Skillup Interactive Lab](https://img.shields.io/badge/Skillup-Cloud%20Terminal-blue?style=for-the-badge&logo=linux)](https://www.skillup.host/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-st--ven200%2Fskillup--labs-green?style=for-the-badge&logo=github)](https://github.com/st-ven200/skillup-labs/tree/main/openclaw-squad-agent-orchestrator)

本实验是文章《让 16 个 AI 员工在飞书群自我协同：基于 OpenClaw 的多 Agent 敏捷 Squad 拓扑与一人公司实操》配套的自包含动手练习。演示在多 Agent 协同网络中，如何通过 SOUL.md 人设建模、agentToAgent 消息总线路由与 maxRecursion 熔断机制实现全自主的端到端敏捷研发流转。

---

## 🎯 实验目标

1. 掌握基于 SOUL.md 人设规范的角色建模与持续性记忆管理；
2. 理解敏捷 Squad 团队模型（产品增长队、技术平台队、营销增长队）向多智能体拓扑的映射；
3. 演练 agentToAgent 跨智能体自主递归通信链路与上下文传递；
4. 掌握规避多 Agent 对话死循环的安全熔断（maxRecursion）机制；
5. 了解飞书（Lark）多机器人 Webhook 与事件订阅桥接设计。

---

## 💻 快速开始

### 方式 A：云端免安装在线演练（推荐）
无需在本地配置任何复杂依赖，直接在浏览器中秒开云端实验终端：
👉 [边学边练在线实验平台 (https://www.skillup.host/)](https://www.skillup.host/)

### 方式 B：本地环境运行

```bash
# 执行自包含的多 Agent 敏捷协同总线演练
python3 demo_squad_agents.py
```

---

## 🛠️ 关键排坑指南 (Pitfalls)

1. **Agent 间消息死循环（Infinite Ping-Pong）**：当多个 Agent 相互征求意见或反复确认时，极易陷入无休止的对话风暴，导致 Token 快速耗尽。必须在调度总线中严格限制 `maxRecursion`（默认建议设为 3 ~ 4 跳），并在检测到收敛信号时强制打断。
2. **SOUL.md 人设过泛导致角色越界**：如果给 Agent 的人设定义了过于宽泛的职责（如“协助全公司所有事务”），Agent 在收到任务时会越过专业负责人抢答。SOUL.md 必须明确限定“你不是谁”以及核心交付指标。
3. **飞书多机器人限频与鉴权防抖**：当同时接入 16 个独立的飞书机器人时，瞬时高并发事件容易触发飞书开放平台的 API 限频（429）。建议在 Webhook 分发网关层配置异步队列（如 Redis Stream）做缓冲削峰。
