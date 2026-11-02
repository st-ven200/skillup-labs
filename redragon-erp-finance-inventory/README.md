# Lab 37: 赤龙 ERP 核心业务与财务一体化仿真引擎实战

[![Skillup Platform](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **实训场景目标**：深入拆解现代开源企业级 ERP（以赤龙 ERP Redragon-ERP 为蓝本）的内核架构，实现**多级物料清单（BOM）递归展开算法**、**FIFO（先进先出）动态批次库存计价扣减**以及**复式记账法（Double-Entry Bookkeeping）总账凭证自动平衡生成**。

---

## 🎯 业务与技术核心难点

1. **多级 BOM 递归爆炸（BOM Explosion）与损耗率计算**：
   - 工业制造中，顶层成品（如工业无人机）通常由动力子系统、机架、电池等组成，而子系统又由芯片主板、无刷电机组成。
   - 生产排产时必须自动递归穿透到底层原材料，并准确叠加不同工序的废品损耗率（Scrap Rate），避免生产缺料停工。
2. **存货动态计价与批次追踪（FIFO Engine）**：
   - 制造企业原料与成品在不同时间段的入库成本均不同（如原材料价格波动）。
   - 必须按批次严格先进先出扣减，实时计算真实的销售出库成本（COGS），为财务核算提供精准支撑。
3. **业财一体化（Business-Finance Integration）凭证自动生成**：
   - 业务单据（销售发货单、领料单、采购入库单）确认时，核心引擎必须自动触发财务记账凭证（Journal Voucher）。
   - 严格遵循借贷记账法（借方合计 == 贷方合计），自动分离应收账款、主营业务收入、增值税销项税额及存货结转成本。

---

## 📁 目录结构

```
labs/redragon-erp-finance-inventory/
├── README.md               # 本实验说明文档与排坑实录
├── erp_engine.py           # 赤龙 ERP 核心业务与财务一体化建模引擎
└── test_erp_flow.py        # 端到端业务闭环测试（BOM展开 -> FIFO出库 -> 自动凭证生成）
```

---

## 💻 快速开始

### 方式一：云端免安装秒级实操（推荐）
点击一键进入 [Skillup 边学边练在线实操平台 (https://www.skillup.host/)](https://www.skillup.host/)，在云端终端中选择 `Lab 37: 赤龙 ERP 业财一体化` 即可免装环境直接运行。

### 方式二：本地运行验证

```bash
# 1. 进入实验目录
cd /workspace/article/labs/redragon-erp-finance-inventory

# 2. 赋予可执行权限并运行端到端测试
python3 test_erp_flow.py
```

---

## 🔍 控制台真实执行结果实录

```text
==================================================
🚀 开始执行赤龙 ERP 业财一体化端到端业务闭环测试
==================================================
✅ 注册物料主数据 6 项成功。
✅ 多级工程 BOM 结构定义完成。

📦 生产工单排产：计划生产 50 台 DRONE-X1，多级 BOM 递归计算展开：
[
  {
    "level": 1,
    "sku": "POW-MOD-01",
    "name": "飞控动力总成",
    "unit": "套",
    "base_quantity": "1.0",
    "scrap_rate": "0.0%",
    "required_total": "50.00",
    "is_assembly": true,
    "sub_components": [
      {
        "level": 2,
        "sku": "MAT-MTR-01",
        "name": "无刷直流电机",
        "unit": "台",
        "base_quantity": "4.0",
        "scrap_rate": "1.0%",
        "required_total": "202.00",
        "is_assembly": false,
        "sub_components": []
      },
      {
        "level": 2,
        "sku": "MAT-MB-01",
        "name": "机载智能主控板",
        "unit": "块",
        "base_quantity": "1.0",
        "scrap_rate": "0.0%",
        "required_total": "50.00",
        "is_assembly": false,
        "sub_components": []
      }
    ]
  },
  {
    "level": 1,
    "sku": "MAT-FRM-01",
    "name": "一体化碳纤机架",
    "unit": "套",
    "base_quantity": "1.0",
    "scrap_rate": "0.0%",
    "required_total": "50.00",
    "is_assembly": false,
    "sub_components": []
  },
  {
    "level": 1,
    "sku": "MAT-BAT-01",
    "name": "16000mAh 动力锂电池",
    "unit": "组",
    "base_quantity": "2.0",
    "scrap_rate": "0.5%",
    "required_total": "100.50",
    "is_assembly": false,
    "sub_components": []
  }
]

📥 成品入库完成：批次 1 (30台 @ 4200.00元)，批次 2 (40台 @ 4450.00元)
📊 当前成品总库存量：70 台

💰 销售订单结算与 FIFO 出库明细：
 - 客户: 国网通航巡线实业有限公司
 - 销售收入 (不含税): ￥396000.00
 - 增值税额 (13%): ￥51480.00
 - 应收账款合计: ￥447480.00
 - FIFO 实际出库成本: ￥192750.00
 - 毛利润: ￥203250.00 (毛利率: 51.3%)

📋 自动生成总账会计凭证 (Double-Entry Vouchers)：

凭证编号: V-REV-20261102-4794 | 业务单据: SO-20261102-0089 | 凭证借贷平衡: True
科目代码与名称                          | 借方发生额           | 贷方发生额           | 摘要
-------------------------------------------------------------------------------------
1122 应收账款                      | 447480.00       | -               | 确认客户 国网通航巡线实业有限公司 订单 SO-20261102-0089 应收货款
6001 主营业务收入                    | -               | 396000.00       | 销售出库商品销售收入
2221.0102 应交税费-应交增值税(销项税额)     | -               | 51480.00        | 销售税额(税率13%)

凭证编号: V-COST-20261102-A0AE | 业务单据: SO-20261102-0089 | 凭证借贷平衡: True
科目代码与名称                          | 借方发生额           | 贷方发生额           | 摘要
-------------------------------------------------------------------------------------
6401 主营业务成本                    | 192750.00       | -               | 结转销售订单 SO-20261102-0089 销售成本
1405 库存商品                      | -               | 192750.00       | 商品出库减少存货

✅ FIFO 出库校验完毕，剩余库存批次量：25 台 (完全符合预期 70 - 45 = 25)
🎉 赤龙 ERP 核心引擎端到端自动化测试全部通过！
```

---

## ⚠️ 小白排坑与架构要点 (Pitfalls)

1. **浮点数精度截断陷阱**：
   - 在财务与物料损耗核算中，**严禁使用标准 float/double 类型**进行金额与数量相乘，否则极易出现 `0.1 + 0.2 = 0.30000000000000004` 导致总账凭证借贷无法配平。必须统一采用高精度定点数（如 Python `decimal.Decimal` 或 Java `BigDecimal`），并在每一步计算中明确指定舍入规则（`ROUND_HALF_UP`）。
2. **多级 BOM 递归死循环防御**：
   - 如果业务配置中出现物料 A 依赖物料 B，而物料 B 又循环依赖物料 A，会导致递归展开出现栈溢出（StackOverflow）。实际系统中需加入有向无环图（DAG）环路检测，防范非法拓扑结构。
3. **FIFO 并发出库的行锁与超卖问题**：
   - 生产环境中多个发货员并发扣减同一 SKU 时，必须在数据库事务层结合 `SELECT ... FOR UPDATE` 悲观锁或乐观版本号机制，确保批次扣减的原子性，杜绝超卖。
