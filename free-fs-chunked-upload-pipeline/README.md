# Lab 09: Free-FS 企业级文件分片上传与断点续传状态机实战

[![Skillup Interactive Lab](https://img.shields.io/badge/Skillup-Cloud%20Terminal-blue?style=for-the-badge&logo=linux)](https://www.skillup.host/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-st--ven200%2Fskillup--labs-green?style=for-the-badge&logo=github)](https://github.com/st-ven200/skillup-labs/tree/main/free-fs-chunked-upload-pipeline)

本实验是文章《从分片续传到 SPI 插件化扩展：Free-FS 企业级文件系统核心架构与万能预览技术拆解》配套的自包含动手练习。演示企业级分布式文件存储系统中的大文件分片、断点续传握手、SHA-256 全量一致性校验与秒传机制。

---

## 🎯 实验目标

1. 理解大文件切片（Chunking）机制与特征指纹生成；
2. 掌握服务端上传任务状态机（Redis State Tracking）与已上传分片位图设计；
3. 模拟弱网环境下连接中断后的断点续传（Resumable Upload）握手探测；
4. 验证合并后文件的哈希完整性校验（100% Bit-level Consistency）；
5. 掌握全量指纹库实现的快速秒传（Fast Hash Dedup）逻辑。

---

## 💻 快速开始

### 方式 A：云端免安装在线演练（推荐）
无需在本地配置 Python 或 Docker 运行时，直接访问在线实验终端：
👉 [边学边练在线实验平台 (https://www.skillup.host/)](https://www.skillup.host/)

### 方式 B：本地环境运行

```bash
# 1. 运行自包含 Python 分片模拟脚本
python3 demo_chunked_upload.py

# 2. 可选：拉起本地 Redis 与 MinIO S3 容器环境进行全链路对接
docker compose up -d
```

---

## 🛠️ 关键排坑指南 (Pitfalls)

1. **分片并发合并时的 I/O 阻塞**：TB 级大文件如果采用同步全量流合并，会瞬间占满磁盘写入带宽。生产环境应采用类似 Free-FS 的异步队列合并或直接调用底层存储（如 MinIO Multipart Upload）的服务器端合并。
2. **秒传与哈希碰撞安全**：仅使用 MD5 进行秒传存在人为构造哈希碰撞的伪造风险。推荐采用 SHA-256 全量指纹与文件大小组合索引。
3. **分片生命周期过期清理**：用户中途放弃上传的分片如果不清理会大量占用存储空间。Redis 元数据与临时分片目录必须配置 24 小时绝对过期策略（TTL 清理任务）。
