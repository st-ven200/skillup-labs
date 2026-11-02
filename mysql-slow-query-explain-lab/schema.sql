-- =============================================================================
-- MySQL 8.0 慢查询靶场测试表结构 (完全脱敏示例)
-- =============================================================================

CREATE TABLE IF NOT EXISTS `tb_orders` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '订单主键ID',
  `order_no` varchar(64) NOT NULL COMMENT '订单流水号',
  `tenant_id` int unsigned NOT NULL DEFAULT '0' COMMENT '租户ID',
  `user_id` bigint unsigned NOT NULL COMMENT '用户ID',
  `total_amount` decimal(10,2) NOT NULL DEFAULT '0.00' COMMENT '订单总金额',
  `order_status` tinyint unsigned NOT NULL DEFAULT '1' COMMENT '状态: 1-待付 2-已付 3-已发货 4-已取消',
  `pay_type` tinyint unsigned NOT NULL DEFAULT '1' COMMENT '支付渠道',
  `remark` varchar(255) DEFAULT '' COMMENT '订单备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_order_no` (`order_no`),
  KEY `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='核心订单业务表';
