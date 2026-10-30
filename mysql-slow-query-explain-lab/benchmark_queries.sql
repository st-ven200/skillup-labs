-- =============================================================================
-- MySQL 8.0 性能对比测试 SQL 清单
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 【慢查询场景 1】未合理利用复合索引，触发全表扫描与文件排序
-- -----------------------------------------------------------------------------
EXPLAIN FORMAT=TREE
SELECT id, order_no, total_amount, created_at 
FROM tb_orders 
WHERE tenant_id = 1001 AND order_status IN (2, 3) 
ORDER BY created_at DESC 
LIMIT 20;

-- -----------------------------------------------------------------------------
-- 【索引优化方案】
-- 遵循最左前缀与排序优先：等值匹配 (tenant_id) -> 消除排序 (created_at) -> 范围过滤 (order_status)
-- -----------------------------------------------------------------------------
-- ALTER TABLE tb_orders ADD INDEX idx_tenant_created_status (tenant_id, created_at, order_status);

-- -----------------------------------------------------------------------------
-- 【优化后场景 2】命中复合索引，触发索引下推 (Using index condition)，消除 filesort
-- -----------------------------------------------------------------------------
EXPLAIN FORMAT=TREE
SELECT id, order_no, total_amount, created_at 
FROM tb_orders 
WHERE tenant_id = 1001 AND order_status IN (2, 3) 
ORDER BY created_at DESC 
LIMIT 20;
