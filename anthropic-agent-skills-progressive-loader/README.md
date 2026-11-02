# Lab 29: Anthropic Agent Skills 渐进式加载架构与 Schema 验证实战

[![Skillup Terminal](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![Status](https://img.shields.io/badge/Test-Passing-success)](https://github.com/st-ven200/skillup-labs)

## 🎯 实验目标
本实验基于 Anthropic 官方发布的《The Complete Guide to Building Skills for Claude》（32 页完整规范），实现一套可运行的 **三层渐进式披露（Progressive Disclosure）引擎** 与 **Frontmatter Schema 校验门禁**：
1. **Level 1 元数据驻留层**：将数十个技能压缩至仅占系统提示词约 100 Tokens 的常驻索引区，实现极低开销；
2. **多语言触发词路由与评分**：支持中文、英文及短语强匹配，自动提取意图关键词并计算相关度评分；
3. **Level 2 / Level 3 按需水合机制**：仅在任务意图命中时才将工作流指令与外部工具载入内存，彻底杜绝上下文膨胀与幻觉污染。

## 🛠️ 环境要求
- Python 3.9+
- Linux / macOS / Windows

## 🚀 极速运行与验证
```bash
python3 progressive_skill_loader.py
```

### 验证输出实录
```text
=================================================================
🚀 Running Lab 29: Anthropic Progressive Skills Architecture Tests
=================================================================
✅ Registered skills: ['sentry-code-review', 'linear-sprint-planner']
📊 Level 1 Baseline Overhead: 49 tokens across 2 skills

🔍 Query: '帮我看看这个线上堆栈，sentry报错提示空指针异常'
🎯 Matched Skills: [('sentry-code-review', 1.0), ('linear-sprint-planner', 0.05)]
⚡ Hydrated Skill: sentry-code-review | Status: Level 2
📈 Level 2 Expanded Overhead: 57 tokens (Only loaded on demand)
🛡️ Lazy Load Ratio: 1/2 skills activated

✅ All assertions passed! Progressive disclosure architecture verified.
=================================================================
```

## ⚠️ 小白排坑要点 (Pitfalls)
1. **Description 缺少明确触发时机**：根据 Anthropic 规范，仅写“分析代码”会导致大模型无法决断何时激活；必须在 description 中显式补充“当用户提到……”或“When user asks to...”。
2. **多语言分词陷阱**：中文语句无自然空格，若使用简单正则 `\w+` 切分会导致长句被当作单一大 Token 丢失命中，必须使用 N-gram（二元滑动窗口）加触发短语强命中。

---

> 💻 **云端免安装在线实操**：一键在浏览器中秒开预装环境运行验证本实验 👉 [Skillup 边学边练在线实验平台 (https://www.skillup.host/)](https://www.skillup.host/)。
