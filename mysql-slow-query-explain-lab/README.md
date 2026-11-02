# Lab 04: MySQL 8.0 慢查询分析与索引下推 (ICP) 调优实战

[![Run in Skillup](https://img.shields.io/badge/Run_in_Browser-Skillup_Terminal-blue?logo=linux)](https://www.skillup.host/)
[![Difficulty: Advanced](https://img.shields.io/badge/Difficulty-Advanced-orange)](#)

> **实操场景**：随着订单表（`tb_orders`）数据量突破百万级，多条件组合检索经常引发 CPU 100%、慢查询日志报警，排查发现查询触发了全表扫描与文件排序（Using filesort），通过复合索引重构与索引下推（Index Condition Pushdown, ICP）实现性能提升 30 倍。

---

## 🎯 练习目标

1. 掌握 MySQL 8.0 现代执行计划分析：`EXPLAIN ANALYZE` 与 `EXPLAIN FORMAT=TREE`；
2. 理解 `Using index condition`（索引下推）的物理执行原理；
3. 掌握联合索引**最左匹配原则**与范围查询导致后续索引失效的规避方法；
4. 消除 `Using filesort` 与 `Using temporary` 高危标记。

---

## 💻 云端免安装练习入口

> 想要直接连入预置好百万级数据测试库的 MySQL 容器？  
> 👉 **点击直达【[Skillup 云端 MySQL 实操终端](https://www.skillup.host/)】**，开箱即练。

---

## 🛠️ 动手练习步骤

### 步骤 1：导入模拟数据表结构
```bash
mysql -u root -p demo_db < schema.sql
```

### 步骤 2：执行慢查询基准测试
运行 `benchmark_queries.sql` 中的 Query 1，观察原始执行耗时与执行计划：
```sql
EXPLAIN FORMAT=TREE 
SELECT * FROM tb_orders 
WHERE tenant_id = 1001 AND order_status IN (2, 3) 
ORDER BY created_at DESC LIMIT 20;
```
*观察重点*：是否出现了 `Filter: ...` 及大量的 `Table scan`。

### 步骤 3：建立覆盖与下推最优联合索引
```sql
-- 联合索引设计：将等值条件放最前，排序字段放中间，范围条件放最后
ALTER TABLE tb_orders ADD INDEX idx_tenant_created_status (tenant_id, created_at, order_status);
```

### 步骤 4：再次验证执行计划与开销
再次运行 Query 2，确认成本大幅下降，扫描行数从 1,000,000+ 降低至 20 行以内。
