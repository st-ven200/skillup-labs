# Lab 36: StarGantt 开源甘特图拓扑排期与关键路径调度计算引擎

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![Status: Verified](https://img.shields.io/badge/Status-Verified_Passed-success.svg)](https://www.skillup.host/)

> 本实操是技术文章《告别臃肿商业排期工具：基于 Vue3 + Element Plus 的轻量级开源甘特图 StarGantt 架构剖析与二次开发实战》的配套实训。

---

## 🎯 实验目标
1. 掌握基于有向无环图 (DAG) 的项目排期与任务依赖拓扑建模；
2. 掌握关键路径法 (CPM, Critical Path Method) 的正向与反向计算算法；
3. 计算每个任务的最早/最晚时间与总时差 (Total Float)，精准标记关键链路；
4. 实现时间轴网格到屏幕像素的精准映射与循环依赖死锁防御。

---

## 💻 快速开始

```bash
# 执行自动化排期与关键路径断言计算
python labs/stargantt-vue3-element-plus/gantt_core.py
```

---

## 🛠️ 排错与避坑实录

- **常见踩坑 1**：在用户交互频繁的拖拽场景中，若产生反向连线（A 依赖 B 且 B 依赖 A），会导致无限递归拓扑计算。引擎通过 DFS 三色染色法严格识别环路并抛出死锁异常。
- **常见踩坑 2**：时间映射未进行整天对齐，导致跨时区渲染时甘特横道产生 1 像素偏差。引擎通过标准化天级偏移基准消除抖动。

👉 **免安装一键运行**：[Skillup 在线实操终端](https://www.skillup.host/)
