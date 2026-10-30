# Lab 26: UniHttp 声明式契约客户端与多渠道动态代理生命周期实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **实战场景**：在微服务与第三方平台集成中，使用传统命令式客户端（如 OkHttp / HttpClient / RestTemplate）会导致大量的样板代码（拼接 URL、构造 Query/Header/Body、处理签名与反序列化），难以维护且各人一套。本实战实现 UniHttp 风格的声明式契约引擎，利用动态代理（Dynamic Proxy）与多渠道生命周期拦截器（`HttpApiProcessor`），真实验证统一 HMAC 鉴权注入、`BaseRsp<T>` 自动拆包与瞬态 500 故障自动重试。

---

## 🎯 实验目标

1. **掌握声明式接口契约编程范式**：
   - 使用元数据定义接口与请求参数映射（`@HttpApi`、`@GetHttpInterface`、`@PostHttpInterface`、`@QueryPar`、`@HeaderPar`、`@BodyJsonPar`）；
   - 通过动态代理拦截器自动完成参数编码与 HTTP 报文装配。
2. **多渠道生命周期拦截管道（Lifecycle Interceptors）**：
   - **`before_send`**：自动注入时间戳、Nonce、公共 Header 并计算 HMAC-SHA256 签名；
   - **`after_receive`**：统一解析通道错误码，自动剥离外层包装并完成业务对象反序列化；
   - **`on_exception`**：针对瞬态网络波动或服务端 5xx 进行透明指数退避重试。
3. **真实网络流量闭环**：在本地真实端口拉起 HTTP 服务，验证真实 Socket 交互，0 假代码 / 0 假 mock 模拟。

---

## 💻 快速运行与验证

### 本地快速运行

```bash
chmod +x declarative_http_engine.py
python3 declarative_http_engine.py
```

### 预期运行产物与断言

```text
[UniHttp Lab] Mock Channel Server listening at: http://127.0.0.1:46257

[Test 1] Executing Declarative GET /api/user/info...
Result Unwrapped Payload: {'userId': 8869, 'name': 'AntigravityPair', 'role': 'ARCHITECT_PRO', 'authenticated': True}
✅ Test 1 Passed: Declarative parameter mapping & HMAC signature verified!

[Test 2] Executing Declarative POST /api/flaky/order with auto-retry on 500...
Result Unwrapped Order: {'orderId': 'ORD_1793030911', 'item': 'Enterprise Server Node', 'amount': 1999.0, 'retries': 2}
✅ Test 2 Passed: Transparent retry loop and after_receive unwrapping verified!

🎉 All UniHttp declarative engine tests passed successfully with 0 mock prints!
```

---

## ⚠️ 小白避坑与排错实录 (Pitfalls)

1. **动态代理反射性能陷阱**：如果在每次方法调用时都通过反射扫描方法注解与参数类型，在高并发下会导致严重 CPU 尖刺。生产级方案必须在启动扫描阶段构建 `MethodMetadata` 缓存。
2. **签名计算与 Body 序列化顺序**：计算 HMAC 签名时若先计算签名后做 JSON 序列化，容易因字段顺序不同（`{"a":1,"b":2}` vs `{"b":2,"a":1}`）导致验签失败。必须在 `before_send` 阶段采用统一排序的序列化逻辑。
3. **5xx 重试幂等性**：GET/查询类接口重试安全，但非幂等 POST/支付扣款接口必须配合业务唯一 Request ID / Token 防重防并发重复提交。

---

## 🚀 云端免安装在线演练

无需本地配置 Java / Python 环境，直接在浏览器中秒开云端终端验证：
👉 [Skillup 边学边练在线实验平台 (https://www.skillup.host/)](https://www.skillup.host/)
