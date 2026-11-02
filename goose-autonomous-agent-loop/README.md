# Lab 06 ｜ Block 开源 AI 研发智能体 Goose 自主循环与 MCP 扩展实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

> **目标**：理解从“人机对话补全”向“自主工程执行体”演进的范式转移，通过仿真探针亲手验证 Block 开源项目 Goose 的微内核循环、Model Context Protocol (MCP) 标准工具接入、并行隔离子智能体（Subagents）上下文防污染与命令安全门禁。

---

## 🎯 实验目的与架构设计

在传统 AI 编程工作流中，开发者常常充当了疲惫的“中间件”：
1. 复制需求给 AI -> 复制生成的代码到 IDE；
2. 本地执行报错 -> 复制几十行错误日志回传给 AI；
3. 来回拉扯数次，全程必须人工盯盘。

Block 研发并捐赠给 Linux Foundation 的开源 Agent **Goose (github.com/block/goose)** 彻底颠覆了这种低效模式：
- **微内核自主循环（Reasoning Loop）**：接收高阶任务配方（Recipe），自主读取目录、执行命令、分析报错、修补文件直至验收；
- **MCP 标准化工具生态**：解耦工具与 Agent，通过统一标准协议动态挂载文件、Shell、GitHub 等工具集；
- **Subagents 隔离防污染**：全量单元测试或海量编译日志由临时子智能体吸收总结，仅向上回传核心结论，节省 90% 以上上下文窗口；
- **人机协同安全网闸（Human-in-the-Loop）**：识别危险命令，在关键步骤提示授权，平衡自主性与系统安全。

---

## 💻 快速运行

无需安装外部依赖，标准 Python 即可执行：

```bash
# 1. 运行 Goose 核心循环仿真探针
python3 demo_goose_agent_loop.py
```

### 预期控制台输出
```text
🪿 Goose 自主研发智能体启动: 配方 [AutoFix-TestSuite-Pipeline]
🎯 终极目标: 自动扫描工程失败单测，精确定位根因，修补代码并完成 PR 发起
...
[Step 0] MCP 握手完成，挂载工具集 (4 个):
  - [filesystem] read_file: 读取本地代码或配置文件内容 (权限: read_only)
  - [developer_shell] run_command: 在工程工作区内执行 Shell 命令与单测 (权限: system_command)
...
    [SUBAGENT-SPAWN] 启动隔离子智能体: 'pytest_noisy_analyzer' (独立瞬态上下文)
    [SUBAGENT-RETURN] 提炼完成！原始数据已丢弃，向主智能体回传轻量总结 (2 处失败)
  💡 主智能体吸收关键归因: tests/test_auth.py:84: AssertionError: expected 200, got 401
...
  ✏️  成功应用代码补丁: src/middleware/auth.py
  🚀 [PR-DISPATCH] 已向 GitHub 成功提交 Pull Request
```

---

## 🛠️ 排坑与避坑指南

1. **死循环与 Token 熔断（Loop Exhaustion）**：
   - 常见陷阱：当测试用例本身存在断言逻辑错误时，自主 Agent 可能陷入无限修复-运行测试的无止境循环。
   - 治理方案：在 Recipe 中显式设定 `max_steps` 上限，并实现梯度惩罚（同一报错连续尝试 3 轮未收敛即阻断并向开发者报警）。

2. **高危命令黑名单与执行边界**：
   - 常见陷阱：大模型在自主寻找清理临时文件命令时生成类似 `rm -rf /` 或强制覆盖主干分支。
   - 治理方案：在 MCP Shell 工具执行层严格注入命令正则拦截层与 Human-in-the-loop 交互确认机制。

---

## 🌐 在线免安装终端实操
不想在本地配置环境？点击以下链接直接在浏览器沙盒终端中运行：  
👉 [https://www.skillup.host/](https://www.skillup.host/)
