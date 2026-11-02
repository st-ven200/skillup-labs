# Lab 17: Spring Boot 枚举断言模式与零侵入异常切面收敛

[![Skillup Host](https://img.shields.io/badge/Skillup-Cloud_Terminal-blue.svg)](https://www.skillup.host/)
[![Status](https://img.shields.io/badge/Status-Verified-success.svg)]()

> 本实验为文章《把条件校验收敛到枚举接口：Spring Boot 统一断言模式与零污染异常切面工程化》的配套开源实战。

## 1. 实验目标与架构痛点

在企业级 Java/Spring Boot 工程中，业务层往往充斥着海量的条件防御代码：
```java
if (user == null) {
    throw new BusinessException(7001, "用户不存在");
}
if (user.isFrozen()) {
    throw new BusinessException(7002, "账户被冻结");
}
```
这种冗余模板代码带来三大痛点：
1. **代码噪音过高**：真正的核心业务逻辑被淹没在长篇累牍的 `if-throw` 样板中；
2. **错误码与错误信息分散**：各业务分支随手硬编码状态码，导致接口契约混乱；
3. **Controller / Service 臃肿捕获**：随意嵌套 `try-catch`，导致异常堆栈丢失或 swallow。

**本 Lab 解决方案**：
采用 **接口断言（Assert Interface）+ 业务枚举（ResponseEnum）+ 全局切面（RestControllerAdvice）** 架构模式，将防御逻辑收敛至枚举内部，实现**一行代码断言、自动绑定错误码、统一全局切面收敛**。

```
[客户端请求] 
     │
     ▼
[Controller]
     │
     ▼
[Service 业务层] ─── ResponseEnum.USER_NOT_FOUND.assertNotNull(user)
     │                                     │
     │ (断言失败抛出 BaseException)          ▼
     └──────────────────────────────► [@RestControllerAdvice]
                                           │
                                           ▼ (标准化封装)
                                     [ApiResponse<T>]
```

## 2. 实验核心环境与依赖

- 语言：Python 3.8+ / Java 8+ / Spring Boot 2.x/3.x
- 依赖：标准库（无需外部重型中间件依赖，开箱即测）

## 3. 快速运行与实操演练

运行自包含的验证脚本：

```bash
python3 run_demo.py
```

### 预期执行输出

```json
=== 开始运行 Spring Boot 枚举断言与全局切面防御引擎真实演练 ===

--- 场景1: 正常转账 ---
{
  "success": true,
  "code": 200,
  "message": "success",
  "data": {
    "userId": 1001,
    "transferred": 100.0,
    "balance": 400.0
  }
}

--- 场景2: 用户不存在校验 ---
{
  "success": false,
  "code": 40401,
  "message": "用户不存在: ID [9999]",
  "traceId": "e72fa08a3b82427b",
  "timestamp": 1792598772978,
  "data": null
}
```

## 4. 小白排坑指南 (Pitfalls & Best Practices)

1. **枚举单例开销**：Java 中的枚举是天然单例，避免了每次抛出异常时重复实例化无状态校验器；
2. **动态占位符参数**：消息文本建议支持 `{0}`, `{1}` 动态参数占位，断言触发时才进行格式化字符串拼接，避免在判定前发生无效的字符串性能开销；
3. **切面分层捕获**：全局切面中必须分级捕获：
   - 优先捕获子类 `BusinessException`（返回可读的业务友好提示与业务状态码）；
   - 其次捕获 `MethodArgumentNotValidException` 等参数校验框架异常；
   - 最后兜底捕获 `Exception.class`（返回统一的 500 降级文案并记录完整 Error 日志，严防内部敏感堆栈泄漏）。

---
💡 **在线实战体验**：本项目免安装环境已部署于 [边学边练实验中台](https://www.skillup.host/)，可直接在 Web 终端进行交互式验证。
