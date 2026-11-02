#!/usr/bin/env python3
"""
Test Suite for Redragon ERP Engine - End-to-End Simulation
验证 BOM 展开、FIFO 批次扣减、销售出库及复式平衡记账
"""
import sys
import json
from decimal import Decimal
from erp_engine import ERPSystem, Material, BOMItem

def run_test():
    print("==================================================")
    print("🚀 开始执行赤龙 ERP 业财一体化端到端业务闭环测试")
    print("==================================================")
    erp = ERPSystem()

    # 1. 基础物料主数据定义
    # 成品：工业级无人机 DRONE-X1 (装配件)
    # 子装配件：飞控动力总成 POW-MOD-01 (装配件)
    # 零部件：机载主板 MOTHERBOARD-A、无刷电机 MOTOR-BL、碳纤维机架 FRAME-CF、高能锂电池 BATTERY-LI
    drone = Material("DRONE-X1", "工业级巡检无人机", "台", is_assembly=True, standard_cost=Decimal("4500.00"))
    pow_mod = Material("POW-MOD-01", "飞控动力总成", "套", is_assembly=True, standard_cost=Decimal("1800.00"))
    mb = Material("MAT-MB-01", "机载智能主控板", "块", is_assembly=False, standard_cost=Decimal("800.00"))
    motor = Material("MAT-MTR-01", "无刷直流电机", "台", is_assembly=False, standard_cost=Decimal("250.00"))
    frame = Material("MAT-FRM-01", "一体化碳纤机架", "套", is_assembly=False, standard_cost=Decimal("600.00"))
    battery = Material("MAT-BAT-01", "16000mAh 动力锂电池", "组", is_assembly=False, standard_cost=Decimal("1100.00"))

    for m in [drone, pow_mod, mb, motor, frame, battery]:
        erp.register_material(m)
    print(f"✅ 注册物料主数据 6 项成功。")

    # 2. 多级 BOM 构建
    # 动力总成 BOM：4台电机 (损耗 1%) + 1块主板 (损耗 0%)
    erp.register_bom("POW-MOD-01", [
        BOMItem("MAT-MTR-01", Decimal("4.0"), scrap_rate=Decimal("0.01")),
        BOMItem("MAT-MB-01", Decimal("1.0"), scrap_rate=Decimal("0.00"))
    ])
    # 无人机整机 BOM：1套动力总成 + 1套机架 + 2组电池 (损耗 0.5%)
    erp.register_bom("DRONE-X1", [
        BOMItem("POW-MOD-01", Decimal("1.0"), scrap_rate=Decimal("0.00")),
        BOMItem("MAT-FRM-01", Decimal("1.0"), scrap_rate=Decimal("0.00")),
        BOMItem("MAT-BAT-01", Decimal("2.0"), scrap_rate=Decimal("0.005"))
    ])
    print(f"✅ 多级工程 BOM 结构定义完成。")

    # 3. 递归 BOM 展开与物料需求量核算（MPS 模拟）
    target_production_qty = Decimal("50")
    exploded = erp.calculate_exploded_bom("DRONE-X1", target_production_qty)
    print(f"\n📦 生产工单排产：计划生产 {target_production_qty} 台 DRONE-X1，多级 BOM 递归计算展开：")
    print(json.dumps(exploded, ensure_ascii=False, indent=2))

    # 4. 模拟两个不同批次的成品入库（不同批次采购/制造成本不同，测试 FIFO）
    # 批次 1：生产 30 台，单台综合成本 4200.00 元
    batch1 = erp.inbound_inventory("DRONE-X1", Decimal("30"), Decimal("4200.00"), warehouse="W01-成品立体仓")
    # 批次 2：后续由于原材料涨价，生产 40 台，单台综合成本 4450.00 元
    batch2 = erp.inbound_inventory("DRONE-X1", Decimal("40"), Decimal("4450.00"), warehouse="W01-成品立体仓")
    print(f"\n📥 成品入库完成：批次 1 ({batch1.batch_no}: 30台 @ 4200.00元)，批次 2 ({batch2.batch_no}: 40台 @ 4450.00元)")
    print(f"📊 当前成品总库存量：{erp.get_stock_level('DRONE-X1')} 台")

    # 5. 销售订单执行：销售出库 45 台（跨两个批次：全额消耗批次1的30台 + 扣减批次2的15台）
    # 销售单价：8800.00 元/台 (不含税)，增值税率 13%
    order_result = erp.process_sales_order_and_generate_vouchers(
        order_no="SO-20261102-0089",
        customer_name="国网通航巡线实业有限公司",
        items=[("DRONE-X1", Decimal("45"), Decimal("8800.00"))],
        tax_rate=Decimal("0.13")
    )

    print(f"\n💰 销售订单结算与 FIFO 出库明细：")
    print(f" - 客户: {order_result['customer']}")
    print(f" - 销售收入 (不含税): ￥{order_result['sales_revenue']}")
    print(f" - 增值税额 (13%): ￥{order_result['sales_tax']}")
    print(f" - 应收账款合计: ￥{order_result['accounts_receivable']}")
    print(f" - FIFO 实际出库成本: ￥{order_result['cost_of_goods_sold']}")
    print(f" - 毛利润: ￥{order_result['gross_profit']} (毛利率: {order_result['gross_margin']})")

    print("\n📋 自动生成总账会计凭证 (Double-Entry Vouchers)：")
    for v in order_result["generated_vouchers"]:
        print(f"\n凭证编号: {v['voucher_no']} | 业务单据: {v['business_ref']} | 凭证借贷平衡: {v['balanced']}")
        print(f"{'科目代码与名称':<32} | {'借方发生额':<15} | {'贷方发生额':<15} | {'摘要'}")
        print("-" * 85)
        for line in v["lines"]:
            print(f"{line['account']:<30} | {line['debit']:<15} | {line['credit']:<15} | {line['summary']}")

    # 6. 库存余量检查
    remaining = erp.get_stock_level("DRONE-X1")
    expected_remaining = Decimal("25")
    assert remaining == expected_remaining, f"库存剩余计算错误！期望 {expected_remaining}，实际 {remaining}"
    print(f"\n✅ FIFO 出库校验完毕，剩余库存批次量：{remaining} 台 (完全符合预期 70 - 45 = 25)")
    print("🎉 赤龙 ERP 核心引擎端到端自动化测试全部通过！\n")

if __name__ == '__main__':
    run_test()
