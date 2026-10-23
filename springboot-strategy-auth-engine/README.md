# Lab 19: Spring Boot 泛型策略工厂与多端统一鉴权架构实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **实战目标**：彻底消灭多端登录时膨胀臃肿的 `if-else / switch-case` 坏味道。基于 **策略模式（Strategy Pattern）+ 工厂模式（Factory Pattern）+ 模板方法模式（Template Method Pattern）**，构建一套支持零侵入横向扩充新登录渠道（账密、短信验证码、微信小程序、第三方 SSO 等）的企业级高内聚鉴权框架内核。

---

## 🚀 场景痛点分析

在企业多端业务（PC Web、移动 App、微信小程序、企业内部协同办公端）快速演进过程中，鉴权逻辑极易退化为“面条代码”：
1. **Controller 频繁受污染**：每新增一个渠道（如新增钉钉免密），都要在 Controller 和 Service 增加判断分支，严重违反开闭原则（OCP）；
2. **鉴权生命周期混乱**：参数校验、前置黑名单过滤、密码解密、OpenID 换取、用户注册与 Token 签发交织在一起，各端重复编码；
3. **安全审计脱节**：不同渠道的登录成功事件无法统一收敛到公共切面，审计日志字段不一致。

---

## 🛠️ 实验环境准备

- **语言环境**: Python 3.8+ (本实验提供轻量级自包含的 Python 真实复刻实现，逻辑与 Java Spring Boot 1:1 对齐)
- **底层存储**: 内嵌 SQLite 3 (自动落盘表结构与登录流水，真实读写校验)
- **免安装云端快速体验**:
  👉 [点击在 Skillup 云端 Linux 实操终端秒开运行验证](https://www.skillup.host/)

---

## 💻 快速运行与验证命令

```bash
# 赋予可执行权限
chmod +x auth_strategy_engine.py

# 执行自动化回归验证套件
python3 auth_strategy_engine.py
```

### 真实控制台执行输出实录 (Stdout)

```text
======================================================================
🚀 开始执行 Spring Boot 多端鉴权策略工厂与模板切面内核真实验证
======================================================================
[DB] 真实数据库初始化完成，预置种子用户与测试凭证。
[Factory] 注册鉴权策略节点: 'password' -> PasswordAuthStrategy
[Factory] 注册鉴权策略节点: 'sms' -> SmsOtpAuthStrategy
[Factory] 注册鉴权策略节点: 'wx_miniapp' -> WxMiniAppAuthStrategy

[Case 1] Web 端账号密码合法登录验证...
  -> Case 1 通过！签发 Token: SKILLUP_AUTH_7D7A6FB66BFE407188441064, 映射 UserID: 1

[Case 2] Web 端密码错误防御拦截验证...
  -> Case 2 通过！成功防御非法密码，捕获错误: 用户名或密码错误

[Case 3] App 端有效手机验证码 (889911) 登录并一次性核销验证...
  -> Case 3 通过！成功核验并签发 Token: SKILLUP_AUTH_5D8E4068E2E84FA480D1C401

[Case 4] 微信小程序 js_code 授权静默注册与绑定测试...
  -> Case 4 通过！自动绑定并落库用户 ID: 2

[Case 5] 未知第三方渠道 (feishu_sso) 动态熔断拦截...
  -> Case 5 通过！成功熔断拦截: 未受支持的登录渠道 'feishu_sso'。当前系统仅就绪: ['password', 'sms', 'wx_miniapp']

[Audit] 验证数据库审计表: 共沉淀 3 条独立渠道真实登录审计流水。

======================================================================
🎉 全部用例真实验证通过: 5/5 (100% SUCCESS)
======================================================================
```

---

## ⚠️ 小白排坑要点 (Common Pitfalls)

1. **Spring 容器中 Bean 名称冲突踩坑**：
   - 在 Spring Boot 中利用 `@Autowired private Map<String, AuthStrategy> strategyMap;` 自动装配时，Map 的 Key 默认是 Bean 名称。若未显式指定 `@Component("sms")`，默认驼峰类名 `smsOtpAuthStrategy` 会导致请求中的 `channel="sms"` 发生路由匹配缺失而抛出空指针。
   - **防御手段**：在策略接口中定义 `String supportChannel()` 方法，工厂在 `InitializingBean` 或构造函数中遍历 Collection 构建确定的规范枚举或小写映射表。

2. **验证码一次性消费防重放**：
   - 短信验证码校验通过后，**必须在同一本地事务中立即从 Redis 或数据库删除该 Key**，杜绝并发重放攻击。

3. **第三方登录的首次登录数据竞争**：
   - 微信小程序高并发扫码授权时，同一 OpenID 若短时间内并发打入，可能因多次 `SELECT ... WHERE open_id = ?` 均返回空而触发多条重复插入冲突。
   - **防御手段**：对 `(provider, open_id)` 建立唯一复合索引，并捕获 Duplicate Key 异常转化为重试。

---

## 🌐 在线免安装体验

无需在本地繁琐折腾环境与系统依赖，一键在浏览器中秒开云端实操终端进行交互验证 👉 [Skillup 边学边练在线实验平台 (https://www.skillup.host/)](https://www.skillup.host/)。
