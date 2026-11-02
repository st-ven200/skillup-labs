# Lab 33: F-Uint 开源实体门店会员营销与分布式收银结算引擎实战

[![Skillup Cloud Terminal](https://img.shields.io/badge/%E5%9C%A8%E7%BA%BF%E5%AE%9E%E6%93%8D%E7%BB%88%E7%AB%AF-Skillup.host-blue?style=for-the-badge&logo=terminal)](https://www.skillup.host/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-%E5%BC%80%E6%BA%90%E4%BB%A3%E7%A0%81%E5%BA%93-181717?style=for-the-badge&logo=github)](https://github.com/st-ven200/skillup-labs/tree/main/labs/f-uint-member-marketing)

## 📌 实验目标
本实操练习基于开源实体门店收银与会员管理系统 **F-Uint** 的核心业务流，通过自包含的可执行 Python 脚本，完整复刻实体店收银场景中高并发与数据一致性要求最为苛刻的四大核心模块：
1. **双轨资金与积分账本（Double-entry Member Ledger）**：储值卡实充本金与活动赠金分账管理、消费积分按等级加速阶梯累加；
2. **卡券核销防重放与防双花（Anti-Double-Spend Coupon Lock）**：优惠券核销状态机控制与并发结算安全；
3. **复合抵扣与动态等级裁决（Tier & Point Engine）**：会员等级折扣、优惠券减免、积分抵扣复合结算，消费后驱动等级实时自动升阶。

---

## 🛠️ 环境要求
- Python 3.8+ 运行环境（无任何第三方外部依赖，纯原生标准库实现）
- 支持 Linux、macOS、Windows 各大操作系统

---

## 🚀 逐步演练与执行验证

### 第一步：进入实验目录并赋予执行权限
```bash
cd labs/f-uint-member-marketing
chmod +x demo_fuint_engine.py
```

### 第二步：运行结算引擎演练
```bash
python3 demo_fuint_engine.py
```

### 第三步：验证现场控制台输出
预期将输出清晰的开卡、发券、充值、首单结算小票、优惠券防重放拦截以及大额消费后自动升阶至 `GOLD` 等级审计流水：
```text
=================================================================
🚀 F-Uint 实体门店会员营销与收银结算引擎现场实操演示
=================================================================
✅ 会员开卡: 张三 (13800138000) | 初始等级: NORMAL | 余额: 0元
🎫 发放优惠券: CP-50-10 (满 50 元减 10 元)
💰 储值入账: 本金 500.0 元 + 赠送 50.0 元 -> 当前可用余额: 550.0 元

--- 🧾 首次收银结算小票 ---
单号: ORD-AD1ACA92 | 原价: 120.0 元
会员等级: NORMAL (折扣率: 1.0)
卡券优惠: -10.0 元 | 储值实扣: 110.0 元
消费返积分: +110 分 | 账户剩余余额: 440.0 元
会员等级状态: 当前等级 NORMAL (升阶: False)

🛡️ 优惠券防双花拦截触发成功: 优惠券 CP-50-10 已被核销，禁止双花！

--- 🧾 大额收银结算小票 ---
单号: ORD-9622876D | 原价: 4500.0 元
等级折扣: NORMAL (折扣率: 1.0)
积分抵扣: -0.50 元 | 储值实扣: 4499.5 元
消费返积分: +4499 分 | 账户升级状态: NORMAL -> GOLD (升阶通知触发: True)
=================================================================
```

---

## ⚠️ 小白排坑要点 (Pitfalls & Best Practices)

1. **浮点数金额精度陷阱**：生产环境严禁直接在数据库使用 `FLOAT` 或 `DOUBLE` 存储金额！必须全部以**最小货币单位“分”（INTEGER/BIGINT）**或 `DECIMAL(10,2)` 存储计算，避免 `0.1 + 0.2 = 0.30000000000000004` 导致的结算账目平账失败。
2. **储值本金与赠送金解耦退款**：在设计储值卡时，必须将“用户实充本金”与“营销赠送金”拆分为两个字段记账。当用户发起退卡或退款诉求时，按照比例优先扣除赠金，不可将赠送资金直接原路提现。
3. **收银端脱机应急容灾**：网络抖动是实体店收银的致命痛点。F-Uint 客户端在设计上支持断网弱网模式，先在 Electron 本地 SQLite 生成离线挂单，网络恢复后通过幂等流水号向云端补传重放。

---

## 🔗 配套开源与在线实操
- 📖 **配套技术深度拆解文章**：[边学边练技术中台专栏](https://www.skillup.host/)
- 💻 **云端免安装在线演练终端**：[https://www.skillup.host/](https://www.skillup.host/)
- 📦 **GitHub 开源实验代码库**：[st-ven200/skillup-labs](https://github.com/st-ven200/skillup-labs/tree/main/labs/f-uint-member-marketing)
