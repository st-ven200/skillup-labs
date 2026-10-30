# Lab 24: Agent Skills 渐进式加载架构与 Forced Eval Hook 拦截实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **实战定位**：解密腾讯云开发（CloudBase）与 Claude Code 官方开放的 Agent Skills 标准规范，攻克“AI 具备 Skills 却视而不见、盲目裸奔”的决策惰性（Inference Laziness）难题，通过“总纲+端环境物理隔离”与“Forced Eval Hook 前置拦截”将技能调用激活率提升至 84%+。

---

## 🎯 实验目标

1. **渐进式加载（Progressive Disclosure）三大阶段**：
   - `Discovery（发现）`：在不挤爆上下文窗口的前提下，仅挂载轻量元数据（Name, Description, Target Env）；
   - `Activation（激活）`：按需根据意图与工程上下文进行匹配；
   - `Execution（执行）`：动态装配完整的 `SKILL.md` 指令与脚本资产。
2. **端环境物理隔离与语义防污染**：实现针对 Web、小程序（Miniprogram）及 Node.js 后端 SDK 的边界切分，防止 AI 在小程序中混淆调用 Web DOM API。
3. **消除决策惰性（Inference Laziness）**：通过 Forced Eval Hook（前置评估拦截中间件），强制 AI 在输出代码前先给出可用技能评估报告，彻底根治“AI 视而不见”的痛点。

---

## 🛠️ 环境准备与一键实训

无需安装庞大 Node.js / Python 外部三方包，点击下方直达云端开箱实操终端：

👉 [**Skillup 边学边练在线实验平台 (https://www.skillup.host/)**](https://www.skillup.host/)

### 本地运行依赖
- Python 3.8+ 标准库（开箱即用）

```bash
chmod +x agent_skills_engine.py
python3 agent_skills_engine.py
```

---

## 💻 核心脚本结构

```
labs/agent-skills-hook-evaluator/
├── README.md               # 实验指导书与架构设计剖析
└── agent_skills_engine.py  # 渐进式注册中心、环境隔离路由器与 Forced Hook 引擎
```

---

## 🧪 验证与真实控制台输出

```text
=================================================================
🚀 [Agent Skills Engine] 启动渐进式加载与 Forced Eval 拦截实测
=================================================================

📊 [1. 上下文负荷优化实测 (Progressive Disclosure)]:
   - 单体式 (Monolithic) 全量装载开销: 1179 字符
   - 渐进式 (Discovery) 仅装载元数据开销: 427 字符
   - 上下文带宽节约比例: 63.8%

-----------------------------------------------------------------
🧪 [测试用例 1] 环境: [miniprogram]
   用户原始请求: "帮我写一个微信小程序登录与用户中心页面，获取当前用户的 openid 并展示个人信息"

   ⚙️ Forced Hook 拦截分析:
   - 激活技能数: 2 个 -> ['cloudbase-guidelines', 'auth-wechat']
   - 屏蔽/跳过数: 2 个 (含跨端语义防污染拦截)
   📥 [按需注入] cloudbase-guidelines => "【CloudBase 架构设计与安全总纲 SOP】..."
   📥 [按需注入] auth-wechat => "【微信小程序原生鉴权开发规范】..."
```
