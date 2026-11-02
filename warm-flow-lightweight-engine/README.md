# Lab 32: Warm-Flow 7 张表国产轻量级工作流引擎与 SpEL 条件分支实战

[![Skillup Terminal](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![Status](https://img.shields.io/badge/Test-Passing-success)](https://github.com/st-ven200/skillup-labs)

## 🎯 实验目标
针对 Flowable / Activiti 等传统 BPMN 2.0 框架 28+ 张表结构过于臃肿、中国式审批适配成本高昂的痛点，本实验通过 SQLite 物理存储构建 **Warm-Flow 核心 7 表工作流模型**，实现完整的企业级审批流转闭环：
1. **7 张核心表物理建模**：解构设计期（Definition/Node/Skip）、运行时（Instance/Task/HisTask）与权限关联（User）；
2. **状态机驱动与 SpEL 条件分支**：实现类似 `#{amount > 1000}` 的动态业务规则评估，自动分流至指定审批节点；
3. **任务审批、直结与历史归档**：实现大额多级审核与小额直通归档双链路流转，全生命周期可追溯。

## 🛠️ 环境要求
- Python 3.9+
- Linux / macOS / Windows
- 无需外部数据库依赖（自带嵌入式 SQLite 引擎）

## 🚀 极速运行与验证
```bash
python3 warm_flow_engine.py
```

### 验证输出实录
```text
=================================================================
🚀 Running Lab 32: Warm-Flow 7 Tables Engine Tests
=================================================================
✅ 流程模型成功装配并部署入库 (flow_definition / flow_node / flow_skip)

--- 场景 A: 大额报销流程流转验证 (amount = 3500) ---
✅ 实例启动成功 ID: 1，首个活动任务为经理审批 [部门经理审批]
✅ SpEL 分支命中成功: #{amount > 1000} -> 流转至 [财务总监审批]
✅ 大额报销全流程正常归档闭环！

--- 场景 B: 小额报销直结验证 (amount = 600) ---
✅ 小额报销跳过财务直通 end 归档成功！
✅ 历史记录流转轨迹 (flow_his_task) 校验通过: 2 条审批快照

=================================================================
✅ All 7 tables assertions passed! Warm-Flow lightweight engine verified.
=================================================================
```

## ⚠️ 小白排坑要点 (Pitfalls)
1. **多跳分支条件互斥性检查**：在配置条件连线时，务必保证分支条件的完备性（如 `amount > 1000` 与 `amount <= 1000`），避免边界值命中空指针或无合法流转分支。
2. **历史记录不可变性**：在任务流转完成后，当前待办必须立即转移到 `flow_his_task`，禁止物理覆盖待办记录，否则会破坏审计追溯链。

---

> 💻 **云端免安装在线实操**：一键在浏览器中秒开预装环境运行验证本实验 👉 [Skillup 边学边练在线实验平台 (https://www.skillup.host/)](https://www.skillup.host/)。
