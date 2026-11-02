# Lab 35: Agent Skills 前端工程化三层架构与 AST 规则校验引擎

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![Status: Verified](https://img.shields.io/badge/Status-Verified_Passed-success.svg)](https://www.skillup.host/)

> 本实操是技术文章《从提示词黑盒到标准化技能包：深入拆解 Agent Skills 规范架构与前端工程化落地实践》的配套实训。

---

## 🎯 实验目标
1. 掌握 Agent Skills 的标准化目录结构与 YAML Frontmatter 元数据门禁提取；
2. 理解三层渐进式披露机制（Metadata -> Core Workflow -> On-demand Rules）；
3. 运行静态规则扫描引擎，拦截 Vue3 响应式解构失效、裸 any 泛型与错误模板语法；
4. 完成全自动化断言测试，实现 100% 规则遵从度落地。

---

## 💻 快速开始

```bash
# 执行自动化断言与规则审计
python labs/agent-skills-frontend-engineering/skills_engine.py
```

---

## 🛠️ 排错与避坑实录

- **常见踩坑 1**：直接解构 `const { list } = reactive(...)` 会瞬间断开 Vue 3 的 Proxy 依赖收集链路，模板无法响应式刷新。引擎通过规则 `VUE3-001` 强制拦截。
- **常见踩坑 2**：在 AI 生成代码中滥用 `ref<any>` 导致重构灾难。引擎通过规则 `TS-003` 警告并提示注入强类型接口。

👉 **免安装一键运行**：[Skillup 在线实操终端](https://www.skillup.host/)
