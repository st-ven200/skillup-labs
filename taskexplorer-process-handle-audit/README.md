# Lab 23: TaskExplorer 内核级进程句柄审计与死锁占用排障实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **实战定位**：解密 Windows TaskExplorer 与 Linux 内核进程/句柄底层透视原理，实战排查文件被锁死不可删、未释放 (deleted) 文件虚占磁盘空间以及网络端口隐形占用难题。

---

## 🎯 实验目标

1. **内核句柄与文件描述符映射**：掌握操作系统内核对象管理器（Object Manager）与句柄表（Handle Table）的数据结构，通过 `/proc/[pid]/fd` 穿透探测进程持有的所有句柄。
2. **定位“(deleted) 软链接未释放”引发的磁盘满载危机**：当文件已被 unlink 删除但持有其句柄的进程尚未退出时，如何实时捞取句柄与计算虚占磁盘容量。
3. **网络套接字（Socket）进程级溯源**：在不依赖外部 `netstat` 或 `lsof` 二进制的前提下，直接解析内核网络套接字表实现端口与进程的瞬时反查。
4. **并发句柄争用与自愈释放**：模拟进程锁死文件的排障场景，通过优雅释放与句柄解耦实现无损热修复。

---

## 🛠️ 环境准备与一键实训

无需在本地复杂搭建 C++ 驱动编译环境，点击下方直达云端开箱实操终端：

👉 [**Skillup 边学边练在线实验平台 (https://www.skillup.host/)**](https://www.skillup.host/)

### 本地运行依赖
- Linux / POSIX 系统，Python 3.8+ 标准库（无需 pip 外部依赖）

```bash
chmod +x handle_audit_core.py
python3 handle_audit_core.py
```

---

## 💻 核心脚本结构

```
labs/taskexplorer-process-handle-audit/
├── README.md               # 实验指导书与底层原理剖析
└── handle_audit_core.py    # 真实内核句柄探针与排障自愈脚本
```

---

## 🧪 验证与真实控制台输出

```text
=================================================================
🚀 [TaskExplorer Audit Engine] 启动内核级进程与系统句柄审计
=================================================================

📋 [Step 1] 当前诊断进程透视 (PID: 2520457 | python3):
   - 父进程 PPID: 2513405
   - 进程状态: R
   - 活跃线程数: 1
   - 句柄清单样例:
     [FD  0] PIPE       -> pipe:[30144594]
     [FD  1] PIPE       -> pipe:[30144595]
     [FD  3] FILE       -> /home/box/Downloads/Antigravity IDE/icudtl.dat

🌐 [Step 2] 系统活跃 TCP 监听套接字审计:
   - 监听端口: 50052  | 绑定 IP: 0.0.0.0         | Inode: 3166
   - 监听端口: 8790   | 绑定 IP: 0.0.0.0         | Inode: 2772
   - 监听端口: 5900   | 绑定 IP: 127.0.0.1       | Inode: 292525

=================================================================
🔥 [实战场景演练] 制造文件被锁死不可删场景与内核句柄自愈
=================================================================
📁 1. 创建测试目标文件: taskexp_test_lock.dat (大小: 524288 字节)
🔒 2. 模拟后台线程已成功持有底层打开句柄
⚠️ 3. 执行 unlink 删除操作！文件在文件系统目录消失，但句柄未关闭...
🔍 4. TaskExplorer 底层句柄穿透探测结果:
   - 句柄总数: 60
   - 探测到未释放的 (deleted) 僵尸句柄:
     -> FD 9: /tmp/taskexp_test_lock.dat (deleted) (虚占内存/磁盘空间: 524288 字节)
🛠️ 5. 执行优雅句柄释放与自愈...
✅ 6. 自愈完成！当前剩余 (deleted) 僵尸句柄已完全释放。
```
