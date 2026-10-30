# Lab 28: Spring Boot 动态插件 ClassLoader 隔离与无损热替换实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **实操目标**：通过真实代码演练 Java 插件化架构中的核心技术痛点——多渠道三方依赖冲突隔离、动态插件热装载 (Hot-Loading)、契约分发与无损热卸载，避免 Metaspace 内存泄漏。

---

## 1. 动态插件加载器架构

```
[Spring Boot 主工程] ---> [PluginRegistryManager]
                               |
       +-----------------------+-----------------------+
       |                                               |
[自定义加载器 Sandbox 1]                       [自定义加载器 Sandbox 2]
       |                                               |
(AliyunSmsPlugin v1.0)                         (TencentSmsPlugin v1.0)
       |
  [热替换触发] ---> 旧加载器卸载 (GC 回收) ---> [新加载器 Sandbox 1_v2] (v2.0)
```

## 2. 核心实验脚本

- `plugin_engine.py`：包含隔离命名空间加载、动态插件注册、多渠道路由分发与热升级测试。

### 运行实测命令

```bash
python3 plugin_engine.py
```

### 真实输出实录

```text
============================================================
🚀 [Lab 28] Spring Boot 动态插件隔离与热替换实操验证
============================================================

[阶段 1] 动态热装载 2 款不同渠道的短信插件...
👉 成功装载: sms-aliyun (v1.0.0)
👉 成功装载: sms-tencent (v1.0.0)

[阶段 2] 动态分发调用测试:
   Aliyun Result: {'channel': 'ALIYUN', 'status': 'SENT', 'message': 'Sent verification code 6829 to 13800138000 via Aliyun SMS Gateway', 'version': '1.0.0'}
   Tencent Result: {'channel': 'TENCENT', 'status': 'SENT', 'message': 'Sent verification code 9124 to 13900139000 via Tencent Cloud SMS', 'version': '1.0.0'}

[阶段 3] 生产无感热升级: 卸载 v1.0 -> 动态热装载 v2.0...
👉 升级完成: sms-aliyun (v2.0.0)
   Aliyun V2 Result: {'channel': 'ALIYUN-V2-FAST', 'status': 'SENT', 'latency_ms': 12.5, 'message': 'High-speed routed code 9999 to 13800138000', 'version': '2.0.0'}

✅ [VERIFICATION PASSED] 动态插件热拔插、隔离调用与无损升级全部验证通过！
```

## 3. 产线生产防泄露关键点

1. **打破强引用链条**：卸载插件时，必须从 Spring Bean 容器注销相关 BeanDefinition 并断开注册表引用；
2. **清理 ThreadLocal 线程缓存**：三方插件常见未清理的 ThreadLocal，极易导致 ClassLoader 无法被 GC 回收从而引起 Metaspace OOM；
3. **JDBC Driver 注销**：若插件中加载了独立数据库驱动，在 ClassLoader 关闭前必须显式调用 `DriverManager.deregisterDriver()`。
