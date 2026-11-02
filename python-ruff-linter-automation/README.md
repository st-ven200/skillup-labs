# Lab 03: 现代 Python Ruff 极速规范检查与 CI 自动化流水线

[![Run in Skillup](https://img.shields.io/badge/Run_in_Browser-Skillup_Terminal-blue?logo=linux)](https://www.skillup.host/)
[![Difficulty: Beginner](https://img.shields.io/badge/Difficulty-Beginner-green)](#)

> **实操场景**：传统 Python 项目使用 Flake8 + Black + isort 检查极慢且规则容易冲突；本练习通过 Rust 编写的现代化工具 Ruff，实现毫秒级 100x 速度完成代码格式化、依赖自动整理与代码漏洞静态扫描。

---

## 🎯 练习目标

1. 掌握 `pyproject.toml` 中配置工业级 Ruff 严苛规则集（E、F、B、I、UP、SIM）；
2. 识别 Python 中常见隐蔽缺陷（可变默认参数、异常裸抛、未关闭文件句柄）；
3. 掌握 `ruff check --fix` 自动安全修复机制；
4. 运行 `check_and_fix.sh` 脚本进行对比演练。

---

## 💻 云端免安装练习入口

> 想要直接运行测试 Python 环境？  
> 👉 **点击直达【[Skillup 云端 Python 实操终端](https://www.skillup.host/)】**，开箱即练。

---

## 🛠️ 动手练习步骤

### 步骤 1：审查待修复的问题代码
打开 `bad_code.py`，观察代码中的坏味道（包括未使用的模块、危险的可变默认字典、无效的条件判断等）。

### 步骤 2：执行静态扫描
```bash
ruff check bad_code.py
```
观察 Ruff 毫秒级输出的错误报告清单（如 `B006 Mutable data structure as default argument`）。

### 步骤 3：执行自动修复
```bash
ruff check bad_code.py --fix
ruff format bad_code.py
```

### 步骤 4：运行一键自动化脚本
```bash
chmod +x check_and_fix.sh
./check_and_fix.sh
```
