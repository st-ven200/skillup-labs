# Lab 05 ｜ 桌面端智能体 QoderWork 沙盒隔离与渐进式 Skills 编排实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

> **目标**：掌握桌面端 AI 智能体（Desktop Agent）的核心架构设计，通过仿真探针亲手验证“三级渐进式披露（Progressive Disclosure）”机制、双轨模型分级路由（Standard vs Flagship）以及本地安全受限沙盒的路径守卫。

---

## 🎯 实验目的与架构设计

在传统开源 Agent（如 OpenClaw 或各类未隔离脚本）中，开发者常面临两大痛点：
1. **上下文爆炸与迟钝**：一次性将所有 Tools 与几十个 Skill 的全量说明塞入 System Prompt，导致每次请求消耗数千 Token 且首字延迟极高；
2. **越权执行风险**：AI Agent 直接持有宿主操作系统的 Root/管理员权限，缺乏路径审计与高危拦截。

阿里桌面端 Agent **QoderWork** 通过三级架构解决了这一矛盾：
- **一级披露**：常驻 System Prompt 的仅为 Skill 元数据卡片（Name + Description），Token 消耗降低 90% 以上；
- **二级披露**：意图命中特定任务后，按需动态将该 Skill 的 `SKILL.md` 操作指南加载到上下文；
- **三级披露**：由 Agent 调用 `scripts/` 中的确定性脚本与资产模板执行，杜绝大模型随机幻觉；
- **沙盒防护**：强制工作目录隔离，针对敏感系统路径与越权调用触发安全守卫与人工确认（Human-in-the-loop）。

---

## 💻 快速运行

无需安装外部重型依赖，使用 Python 标准库即可秒级执行：

```bash
# 1. 运行仿真探针
python3 demo_qoder_skills_runner.py
```

### 预期控制台输出关键段落
```text
[Phase 1] 三级渐进式披露机制（一级常驻元数据）:
  已注册 Skills 数量: 3 个
  常驻 System Prompt 仅占用 Token: 135 tokens (相比全量加载 3600 tokens 压缩率: 96.2%)
...
📝 [Task 1] 用户指令: "把下载文件夹里的 3 张电子发票识别出来，整理金额和报销单，并导出 Excel"
  ⚡ 模型路由决策: 【STANDARD】档 | 原因: 识别为标准桌面办公/格式化任务，路由至【标准档 Standard】模型以提升吞吐并节省配额
  🎯 意图命中技能: ['invoice-ledger']
...
     [Guard Check] 访问 '/etc/hosts' -> 沙盒校验: ⚠️ 越权阻断 (Permission Denied)
```

---

## 🛠️ 排坑与避坑指南

1. **目录逃逸风险（Directory Traversal）**：
   - 常见陷阱：大模型在自主生成参数时可能传入 `../../../../etc/passwd` 或 Windows 的 `C:\Windows\System32`。
   - 治理方案：在工具执行器入口处使用 `Path.resolve().relative_to(sandbox_dir)` 强制校验，发现逃逸立即抛出 `PermissionError` 并上报。

2. **模型分级路由防抖**：
   - 常见陷阱：过于敏感的关键词匹配会导致大量微小任务被错误路由到昂贵而缓慢的旗舰推理模型。
   - 治理方案：结合 Token 预算器与语义复杂度打分器，仅对“多阶段依赖/跨工具长链条/复杂代码生成”开启旗舰档。

---

## 🌐 在线免安装终端实操
不想在本地配置环境？点击以下链接直接在浏览器沙盒终端中运行：  
👉 [https://www.skillup.host/](https://www.skillup.host/)
