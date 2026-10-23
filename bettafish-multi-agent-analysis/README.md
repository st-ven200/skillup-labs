# Lab 08 ｜ BettaFish 多智能体协同流水线与实时舆情研判实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Multi-Agent Ready](https://img.shields.io/badge/Multi--Agent-Architecture-purple)](https://www.skillup.host/)

> **目标**：单一大语言模型在处理复杂舆情与行业热点时，极易陷入事实幻觉、情感偏见与信息茧房。本实训基于 GitHub 爆火的 24k Star 开源项目 **BettaFish (微舆)**，拆解并动手实现由 **QueryAgent（检索）**、**MediaAgent（多模态）**、**InsightAgent（知识图谱）** 以及核心 **ForumEngine（链式辩论仲裁引擎）** 组成的多智能体协同舆情研判闭环。

---

## 🎯 实验环境准备

| 组件 | 版本/环境要求 | 说明 |
|---|---|---|
| **Python** | `Python 3.9+` | 运行多 Agent 编排流水线与论坛辩论引擎 |
| **云端免安装环境** | [👉 点击一键秒开 Skillup 云端 Linux 实验终端](https://www.skillup.host/) | 无需配置繁重依赖，直接在浏览器中秒开终端运行演练 |

---

## 🚀 极速实操步骤

### 第一步：检视多 Agent 协作拓扑

BettaFish 采用分工明确的智能体拓扑与虚拟圆桌论坛辩论机制：
1. **QueryAgent**：全网抓取并过滤文本噪音；
2. **MediaAgent**：从海量截图中提取 OCR 证据与视频关键帧情绪比重；
3. **InsightAgent**：关联企业品牌历史危机数据库；
4. **ForumEngine**：交叉审讯与互相质疑，消除单一 Agent 的幻觉；
5. **ReportAgent**：聚合输出带置信度分数的决策级研报。

### 第二步：运行自包含协同脚本

```bash
python3 demo_bettafish_agent_forum.py --topic "某企业云存储数据同步异常舆情研判"
```

预期标准输出：
```text
======================================================================
🤖 BettaFish 24k Star 开源多智能体舆情分析系统仿真运行
   当前目标议题: 某企业云存储数据同步异常舆情研判
======================================================================

  🔍 [QueryAgent-Alpha] 正在全网检索话题: '某企业云存储数据同步异常舆情研判'...
  🖼️ [MediaAgent-Vision] 解析多模态图文特征、视频热评弹幕分布...
  🧠 [InsightAgent-Core] 检索知识图谱，匹配历史 12 起智驾能耗舆情样本...

🏛️ [ForumModerator-AI] 启动多 Agent 交叉质询与一致性评估会话:
   💬 [轮次 1] 主持人: 'QueryAgent 提交的文本热度与 MediaAgent 的多模态情绪分布是否存在矛盾？'
       -> QueryAgent: '社群文本关注点聚焦在“数据丢失”，情绪较为激烈。'
       -> MediaAgent: '控制台OCR实测截图表明为网络重试引起的展示延迟，未检测到底层块损毁证据。'
   💬 [轮次 2] 主持人: '结合历史知识库，当前舆情是技术认知偏差还是产品硬缺陷？'
       -> InsightAgent: '属于网关更新未做降级通告引发的用户误解。'
   🎯 会议达成共识！置信度评分: 94.0%

======================================================================
📊 BettaFish (微舆) 智能体舆情研判综合报告
======================================================================
【监测议题】: 某企业云存储数据同步异常舆情研判
【生成时间】: 2026-10-17 00:04:15
【综合置信度】: 94.0%
...
```

---

## ⚠️ 小白常踩的排坑实录 (Pitfalls)

1. **多 Agent 辩论发散导致的死循环 (Debate Loop Hang)**：
   - *现象*：两个智能体各执一词，互相反驳超过 10 轮以上，Token 消耗暴增且迟迟不生成结果。
   - *解法*：必须引入带有最大辩论轮次上限（如 `max_rounds=3`）与早停机制的 **Forum Moderator**（仲裁主持智能体），一旦置信度达到阈值（如 `confidence >= 0.85`）或达到轮次硬上限，强制进行加权投票决议。

2. **跨平台爬取频率限制 (Rate Limit 429)**：
   - *现象*：QueryAgent 爬虫在并发请求几分钟后出现频繁 403 / 429 封禁。
   - *解法*：在请求调度队列中引入指数退避（Exponential Backoff）重试机制与随机 Jitter 延迟。

---

## 🔗 配套文章与延伸

- 配套深度技术解析：《打破单模型幻觉与信息茧房：24k Star 开源 BettaFish 的多智能体辩论拓扑与实时舆情研判实战》
- 线上免安装实践入口：[Skillup 边学边练实验云终端 (https://www.skillup.host/)](https://www.skillup.host/)
