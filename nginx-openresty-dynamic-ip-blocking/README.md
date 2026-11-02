# Lab 40 ｜ OpenResty + Lua + Redis 毫秒级动态 IP 熔断与限流防护实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![Language: Lua & Python](https://img.shields.io/badge/Language-Lua_%26_Python-blue.svg)](https://www.skillup.host/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **实训靶场说明**：本项目为技术文章《阻击高频恶意爬虫与扫描探测：OpenResty + Lua + Redis 毫秒级动态 IP 熔断与限流防护实战》的官方配套开源演练库。

---

## 🎯 场景目标

面对恶意扫描器探测、高频脱机爬虫以及暴力碰撞攻击，传统的 Web 安全防护手段面临严峻挑战：
- **操作物理层 (iptables/nftables)**：虽然性能损耗低，但无法感知 HTTP 请求路径、Host 域名等应用层属性，且频繁调 Shell 增删规则容易造成规则锁死；
- **Nginx 原生 `deny`**：每次增删 IP 必须执行 `nginx -s reload`，高并发下频繁重载会导致 worker 进程抖动与连接中断；
- **后端应用层拦截 (Spring/Go)**：恶意流量已经穿透了接入网关层，占满了 Web 容器工作线程与数据库连接池。

本演练的目标是构建一套**生产级 OpenResty 接入层毫秒级动态熔断与黑名单防护系统**：
1. **接入层前置拦截**：在 Nginx 的 `access_by_lua` 阶段完成零拷贝阻断，恶意请求未达 upstream 即可直接返回 HTTP 403 / 429；
2. **多级缓存加速架构**：
   - **L1 本地内存**：利用 Nginx Worker 间的 `lua_shared_dict` 缓存高频黑名单，避免每个请求都访问 Redis 导致网卡与连接池打满；
   - **L2 Redis 集群**：分布式共享黑名单与访问滑动计数桶，多机集群同步生效；
3. **安全防伪造与连接池治理**：
   - 严格解析最左侧真实 IP，防御客户端恶意构造 `X-Forwarded-For: 127.0.0.1` 绕过拦截；
   - 基于 `get_reused_times()` 实现连接池认证免重入，配合 `set_keepalive()` 实现高并发连接安全回收；
4. **自动化 TTL 弹性自愈**：利用 Redis 的 Key 过期机制实现“封禁指定时间后自动解封”，告别手动清理运维负担。

---

## 🏗️ 核心架构与请求生命周期

```
[客户端请求 HTTP Request]
            │
            ▼
[Nginx / OpenResty: access_by_lua]
            │
            ├─ 1. 白名单检查 (Office IP / Search Engine Bot) ──> 放行 (200 OK)
            │
            ├─ 2. L1 本地字典检查 (lua_shared_dict)
            │      └── 命中黑名单 ──> 直接拦截 (403 Forbidden, 0ms Redis开销)
            │
            ├─ 3. L2 Redis 状态检查 (连接池复用)
            │      └── 命中分布式黑名单 ──> 同步写入 L1 并拦截 (403 Forbidden)
            │
            ├─ 4. 计数器滑动递增 (INCR limit:count:IP)
            │      ├── 首次请求: 设置 EXPIRE 窗口时间
            │      └── 超过阈值: 触发熔断 ──> SET limit:block:IP 1 EX expire_sec
            │
            ▼
    [安全放行 -> Upstream 后端服务]
```

---

## 💻 快速运行与实操演练

无需本地搭建复杂的 OpenResty 与 Redis 集群，直接执行内置的自动化逻辑仿真压测：

```bash
chmod +x run_lab.sh
./run_lab.sh
```

### 预期控制台输出

```text
======================================================================
🚀 [Lab 40] OpenResty + Lua + Redis 动态 IP 熔断与限流防护压测
======================================================================
[Config] 限流阈值: 1 秒内最多 3 次请求 | 熔断封禁时间: 5 秒
[Config] 白名单配置: ['127.0.0.1', '10.0.0.88']
----------------------------------------------------------------------
[Round 1] 测试白名单客户端请求 (IP: 10.0.0.88)
  -> 连续发起 5 次高频请求...
  -> 响应状态: 200, 200, 200, 200, 200 (白名单 100% 豁免放行)
----------------------------------------------------------------------
[Round 2] 测试恶意爬虫客户端高频探测 (IP: 198.51.100.23)
  -> 请求 #1: 计数器=1 | 结果: 200 (允许放行)
  -> 请求 #2: 计数器=2 | 结果: 200 (允许放行)
  -> 请求 #3: 计数器=3 | 结果: 200 (达到预警临界值)
  -> 请求 #4: 计数器=4 | 结果: 403 (触发阈值，进入熔断黑名单)
  -> 请求 #5: 黑名单拦截 | 结果: 403 (L1 本地缓存秒级阻断)
----------------------------------------------------------------------
[Round 3] 模拟时间窗口推进，验证自动解封机制
  -> 等待 TTL (5.0s) 到期...
  -> 再次发起请求 | 结果: 200 (黑名单已自动失效解封，服务恢复)
======================================================================
🎉 [Lab 40] 核心断言校验全部通过！
======================================================================
```

---

## 🔍 踩坑与排错实录 (Troubleshooting)

### 坑 1：未复用连接池导致高并发下 Redis 连接数打满
- **现象**：压测 QPS 达到 2000 时，OpenResty 频繁抛出 `connect() failed (111: Connection refused)`，Redis 客户端连接数暴涨至上限。
- **原因**：每次 HTTP 请求都执行 `red:connect()` 并在退出前调用 `red:close()`，导致短连接暴增、TCP TIME_WAIT 堆积。
- **解法**：在脚本退出前必须调用 `red:set_keepalive(pool_max_idle_time, pool_size)` 归还连接池；并在获取连接后通过 `red:get_reused_times()` 判断是否为复用连接，非 0 则跳过 `AUTH` 认证。

### 坑 2：`X-Forwarded-For` 伪造导致任意穿透
- **现象**：攻击者在请求 Header 中携带 `X-Forwarded-For: 127.0.0.1`，直接被误判为本地白名单绕过封禁。
- **原因**：脚本直接盲目读取 `ngx.req.get_headers()["X-Forwarded-For"]`。
- **解法**：必须在 Nginx 层面配置受信任的代理源 `set_real_ip_from <CDN网段>` 并结合 `real_ip_header X-Forwarded-For`，在 Lua 中统一提取经过 Nginx 验证的 `ngx.var.remote_addr`。

---

## 🌐 在线云端实训终端

不想在本地配置任何环境？点击下方链接即可在浏览器中一键秒开 Skillup 交互式云端终端进行调试演练：

👉 **[点击启动 Skillup 在线实操终端](https://www.skillup.host/)**
