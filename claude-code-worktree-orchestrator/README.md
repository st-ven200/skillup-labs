# Lab 13: Claude Code 并发 Worktree 隔离与智能体记忆自愈实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **实操场景目标**：打破单会话串行交互瓶颈，基于 Git Worktree 原生隔离机制构建多智能体并发工程工作流。实现多分支无缝派发、模块级 `CLAUDE.md` 规则与记忆动态注入、会话独立提交，以及主分支自动化无冲突对账合并。

---

## 🎯 实验核心价值与背景

在传统 AI 编程工作流中，开发者常常受困于“单终端单线程”对话模式：当 AI 正在思考重构长篇代码时，终端被完全阻塞，开发者只能处于等待状态。更致命的是，跨模块上下文混杂在一起，容易触发长上下文注意力漂移与相互覆盖。

Anthropic 官方团队与 Claude Code 创作者 Boris Cherny 在实践中推行 **Git Worktree 多维并发模型**：
1. **多目录硬隔离**：利用 `git worktree add` 快速创建多个共享同一 `.git` 对象的物理工作区；
2. **多线程并发编码**：同时启动 3-5 个独立的 Agent 实例分别处理鉴权、限流、遥测等正交子模块；
3. **定向规则注入**：针对不同模块注入定制的 `CLAUDE.md`，使各 Agent 具备独立的规范约束与记忆闭环；
4. **自动化对账与清理**：任务完成后统一执行分支合并检验，并自动清理 worktree 释放物理存储。

---

## 🛠️ 环境依赖与预检

- **Python**：>= 3.9
- **Git**：>= 2.25（原生支持 `git worktree`）
- **操作系统**：Linux / macOS / Windows (WSL2 或 PowerShell)
- **免安装云端秒启**：👉 [无需本地配置，一键打开 Skillup 在线实操终端直接演练](https://www.skillup.host/)

---

## 🚀 逐步演练步骤

### 1. 克隆实战工程并赋予权限

```bash
cd labs/claude-code-worktree-orchestrator
chmod +x worktree_agent_orchestrator.py
```

### 2. 独立沙箱模式执行并发编排

直接运行脚本，脚本将在系统临时安全目录自动初始化一个自包含的 Git 仓库，并并发派发 3 个独立的 Worktree：

```bash
python3 worktree_agent_orchestrator.py --workers 3
```

### 3. 真实执行输出实录 (Stdout)

```text
================================================================================
🚀 Worktree Agent Orchestrator: Multi-Session Parallel Execution Harness
================================================================================
[INIT] Creating clean standalone git sandbox...
[REPO] Base repo validated: /tmp/claude-wt-test-nis6_asj
[REPO] Active branch: main

[PARALLEL] Launching 3 concurrent agent sessions across worktrees (Workers: 3)...

================================================================================
📊 Execution Summary Across Isolated Worktrees
================================================================================
[✅ PASS] Task: task-01-auth | Branch: agent/feat-jwt-auth | Elapsed: 0.018s
       Commit: 76b3f0be | Worktree: wt-task-01-auth
       Diffstat: CLAUDE.md               |  4 ++++
 src/auth/jwt_service.py | 12 ++++++++++++
 2 files changed, 16 insertions(+)
[✅ PASS] Task: task-02-ratelimit | Branch: agent/feat-token-bucket | Elapsed: 0.018s
       Commit: 0b206512 | Worktree: wt-task-02-ratelimit
       Diffstat: CLAUDE.md                      |  3 +++
 src/middleware/rate_limiter.py | 22 ++++++++++++++++++++++
 2 files changed, 25 insertions(+)
[✅ PASS] Task: task-03-telemetry | Branch: agent/feat-metrics-exporter | Elapsed: 0.018s
       Commit: 8a06e768 | Worktree: wt-task-03-telemetry
       Diffstat: CLAUDE.md                          |  3 +++
 src/metrics/prometheus_exporter.py | 17 +++++++++++++++++
 2 files changed, 20 insertions(+)

[RECONCILE] Performing branch reconciliation into 'agent-integration'...
[RECONCILE] Merged branches: ['agent/feat-jwt-auth']
[RECONCILE] Cleaned worktrees: ['wt-task-01-auth', 'wt-task-02-ratelimit', 'wt-task-03-telemetry']

[VERIFY] Git Commit History on Integration Branch:
   * 76b3f0b feat(auth): implement lightweight HMAC-SHA256 JWT service [task-01-auth]
   * 3500ef5 chore: initial repository scaffold

[CLEANUP] Removing temp sandbox: /tmp/claude-wt-test-nis6_asj

✅ All concurrent worktree operations completed with 100% integrity!
```

---

## ⚠️ 小白排坑要点 (Common Pitfalls)

1. **Worktree 路径被锁或未完全清理 (`fatal: is already a worktree`)**：
   - **原因**：若强行 `rm -rf` 删除了工作区目录，而未运行 `git worktree remove`，Git 的内部管理记录（`.git/worktrees/`）依然残留该路径的锁定。
   - **解法**：在编排开始前，显式调用 `git worktree prune` 清理悬挂的残留节点。
2. **分支重名冲突 (`fatal: a branch named ... already exists`)**：
   - **原因**：上一轮失败或未正常退出的会话保留了同名分支。
   - **解法**：在 `git worktree add -b <branch>` 之前，检测并以 `git branch -D <branch>` 强制重置或使用动态 UUID / 时间戳命名分支。
3. **CLAUDE.md 跨会话污染与失真**：
   - **原则**：子模块的局部规则应当随 Worktree 独立落盘，严禁直接在主仓库根目录频繁无序写入；只有经由 `@.claude` PR 审查确认的通用规范，才应合并入主分支的根 `CLAUDE.md`。

---

## 🌐 在线免安装交互实训

无需在本地繁琐折腾环境与系统依赖，一键在浏览器中秒开云端实操终端：  
👉 [https://www.skillup.host/](https://www.skillup.host/)
