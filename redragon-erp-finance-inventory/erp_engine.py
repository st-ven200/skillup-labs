#!/usr/bin/env python3
"""
Redragon ERP Core Engine - Manufacturing, Inventory & Automatic Accounting Integration
赤龙 ERP 核心业务引擎：多级 BOM 递归计算、FIFO 动态库存扣减与复式自动记账凭证
"""
import sys
import json
import uuid
import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple

def round_money(val: Decimal) -> Decimal:
    return val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class Material:
    def __init__(self, sku: str, name: str, unit: str, is_assembly: bool = False, standard_cost: Decimal = Decimal('0.00')):
        self.sku = sku
        self.name = name
        self.unit = unit
        self.is_assembly = is_assembly
        self.standard_cost = standard_cost

class BOMItem:
    def __init__(self, component_sku: str, quantity: Decimal, scrap_rate: Decimal = Decimal('0.00')):
        self.component_sku = component_sku
        self.quantity = quantity
        self.scrap_rate = scrap_rate  # 损耗率，例如 0.02 表示 2%

class InventoryBatch:
    def __init__(self, batch_no: str, sku: str, quantity: Decimal, unit_cost: Decimal, warehouse: str):
        self.batch_no = batch_no
        self.sku = sku
        self.quantity = quantity
        self.unit_cost = unit_cost
        self.warehouse = warehouse
        self.created_at = datetime.datetime.now().isoformat()

class JournalEntryLine:
    def __init__(self, account_code: str, account_name: str, debit: Decimal = Decimal('0.00'), credit: Decimal = Decimal('0.00'), summary: str = ""):
        self.account_code = account_code
        self.account_name = account_name
        self.debit = round_money(debit)
        self.credit = round_money(credit)
        self.summary = summary

class JournalVoucher:
    def __init__(self, voucher_no: str, voucher_date: str, business_ref: str, lines: List[JournalEntryLine]):
        self.voucher_no = voucher_no
        self.voucher_date = voucher_date
        self.business_ref = business_ref
        self.lines = lines
        self.total_debit = sum(l.debit for l in lines)
        self.total_credit = sum(l.credit for l in lines)

    def validate_balance(self) -> bool:
        if self.total_debit != self.total_credit:
            raise ValueError(f"复式记账失衡！借方合计 {self.total_debit} != 贷方合计 {self.total_credit} (凭证: {self.voucher_no})")
        return True

    def to_dict(self):
        return {
            "voucher_no": self.voucher_no,
            "voucher_date": self.voucher_date,
            "business_ref": self.business_ref,
            "total_amount": str(self.total_debit),
            "balanced": self.total_debit == self.total_credit,
            "lines": [
                {
                    "account": f"{l.account_code} {l.account_name}",
                    "debit": str(l.debit) if l.debit > 0 else "-",
                    "credit": str(l.credit) if l.credit > 0 else "-",
                    "summary": l.summary
                }
                for l in self.lines
            ]
        }

class ERPSystem:
    def __init__(self):
        self.materials: Dict[str, Material] = {}
        self.bom_registry: Dict[str, List[BOMItem]] = {}
        # Inventory: sku -> List[InventoryBatch] (FIFO order)
        self.inventory: Dict[str, List[InventoryBatch]] = {}
        self.vouchers: List[JournalVoucher] = []

    def register_material(self, material: Material):
        self.materials[material.sku] = material
        if material.sku not in self.inventory:
            self.inventory[material.sku] = []

    def register_bom(self, parent_sku: str, components: List[BOMItem]):
        if parent_sku not in self.materials or not self.materials[parent_sku].is_assembly:
            raise ValueError(f"父物料 {parent_sku} 不存在或未标记为装配件")
        self.bom_registry[parent_sku] = components

    def calculate_exploded_bom(self, parent_sku: str, target_qty: Decimal, level: int = 1) -> List[Dict]:
        """递归展开多级 BOM 清单，计算考虑损耗率后的底层总物料需求量"""
        if parent_sku not in self.bom_registry:
            return []
        
        exploded_items = []
        for item in self.bom_registry[parent_sku]:
            component = self.materials.get(item.component_sku)
            # 考虑废品损耗率
            effective_qty = target_qty * item.quantity * (Decimal('1.00') + item.scrap_rate)
            effective_qty = round_money(effective_qty)
            
            sub_items = []
            if component and component.is_assembly and item.component_sku in self.bom_registry:
                sub_items = self.calculate_exploded_bom(item.component_sku, effective_qty, level + 1)
            
            exploded_items.append({
                "level": level,
                "sku": item.component_sku,
                "name": component.name if component else "未知物料",
                "unit": component.unit if component else "件",
                "base_quantity": str(item.quantity),
                "scrap_rate": f"{float(item.scrap_rate * 100):.1f}%",
                "required_total": str(effective_qty),
                "is_assembly": component.is_assembly if component else False,
                "sub_components": sub_items
            })
        return exploded_items

    def inbound_inventory(self, sku: str, qty: Decimal, unit_cost: Decimal, warehouse: str = "W01-总仓") -> InventoryBatch:
        """采购或生产入库"""
        batch_no = f"BAT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        batch = InventoryBatch(batch_no, sku, qty, unit_cost, warehouse)
        self.inventory[sku].append(batch)
        return batch

    def get_stock_level(self, sku: str) -> Decimal:
        """获取当前有效可用库存"""
        return sum(b.quantity for b in self.inventory.get(sku, []))

    def deduct_inventory_fifo(self, sku: str, required_qty: Decimal) -> Tuple[Decimal, List[Dict]]:
        """FIFO 先进先出出库算法，返回 (总出库实际成本, 出库批次明细)"""
        available = self.get_stock_level(sku)
        if available < required_qty:
            raise ValueError(f"物料 {sku} ({self.materials[sku].name}) 库存不足！当前库存 {available}，需要 {required_qty}")

        total_cost = Decimal('0.00')
        deducted_batches = []
        remaining_needed = required_qty

        batches = self.inventory[sku]
        i = 0
        while i < len(batches) and remaining_needed > 0:
            batch = batches[i]
            if batch.quantity <= remaining_needed:
                # 整个批次扣尽
                used_qty = batch.quantity
                cost = used_qty * batch.unit_cost
                total_cost += cost
                remaining_needed -= used_qty
                deducted_batches.append({
                    "batch_no": batch.batch_no,
                    "used_quantity": str(used_qty),
                    "unit_cost": str(batch.unit_cost),
                    "subtotal_cost": str(round_money(cost))
                })
                batches.pop(i)
            else:
                # 批次部分扣减
                used_qty = remaining_needed
                cost = used_qty * batch.unit_cost
                total_cost += cost
                batch.quantity -= used_qty
                deducted_batches.append({
                    "batch_no": batch.batch_no,
                    "used_quantity": str(used_qty),
                    "unit_cost": str(batch.unit_cost),
                    "subtotal_cost": str(round_money(cost))
                })
                remaining_needed = Decimal('0.00')
                break

        return round_money(total_cost), deducted_batches

    def process_sales_order_and_generate_vouchers(
        self,
        order_no: str,
        customer_name: str,
        items: List[Tuple[str, Decimal, Decimal]], # (sku, qty, selling_price_without_tax)
        tax_rate: Decimal = Decimal('0.13')
    ) -> Dict:
        """
        销售出库与业财一体化自动凭证生成：
        1. 校验并扣减成品库存（FIFO 先进先出计价）
        2. 自动生成收入确认凭证（借：应收账款，贷：主营业务收入、应交税费-应交增值税(销项税额)）
        3. 自动生成结转销售成本凭证（借：主营业务成本，贷：库存商品）
        """
        total_revenue = Decimal('0.00')
        total_tax = Decimal('0.00')
        total_ar = Decimal('0.00')
        total_cogs = Decimal('0.00')
        outbound_details = []

        for sku, qty, price in items:
            mat = self.materials[sku]
            cost, batch_details = self.deduct_inventory_fifo(sku, qty)
            total_cogs += cost
            
            line_rev = round_money(qty * price)
            line_tax = round_money(line_rev * tax_rate)
            total_revenue += line_rev
            total_tax += line_tax
            
            outbound_details.append({
                "sku": sku,
                "name": mat.name,
                "quantity": str(qty),
                "selling_price": str(price),
                "revenue": str(line_rev),
                "tax": str(line_tax),
                "fifo_cogs": str(cost),
                "batches": batch_details
            })

        total_ar = total_revenue + total_tax
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")

        # 凭证 1：收入确认
        v1_no = f"V-REV-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        v1_lines = [
            JournalEntryLine("1122", "应收账款", debit=total_ar, summary=f"确认客户 {customer_name} 订单 {order_no} 应收货款"),
            JournalEntryLine("6001", "主营业务收入", credit=total_revenue, summary=f"销售出库商品销售收入"),
            JournalEntryLine("2221.0102", "应交税费-应交增值税(销项税额)", credit=total_tax, summary=f"销售税额(税率{float(tax_rate*100):.0f}%)")
        ]
        voucher1 = JournalVoucher(v1_no, today_str, order_no, v1_lines)
        voucher1.validate_balance()
        self.vouchers.append(voucher1)

        # 凭证 2：成本结转
        v2_no = f"V-COST-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        v2_lines = [
            JournalEntryLine("6401", "主营业务成本", debit=total_cogs, summary=f"结转销售订单 {order_no} 销售成本"),
            JournalEntryLine("1405", "库存商品", credit=total_cogs, summary=f"商品出库减少存货")
        ]
        voucher2 = JournalVoucher(v2_no, today_str, order_no, v2_lines)
        voucher2.validate_balance()
        self.vouchers.append(voucher2)

        gross_profit = total_revenue - total_cogs
        gross_margin = (gross_profit / total_revenue * Decimal('100')).quantize(Decimal('0.1')) if total_revenue > 0 else Decimal('0.0')

        return {
            "order_no": order_no,
            "customer": customer_name,
            "sales_revenue": str(total_revenue),
            "sales_tax": str(total_tax),
            "accounts_receivable": str(total_ar),
            "cost_of_goods_sold": str(total_cogs),
            "gross_profit": str(gross_profit),
            "gross_margin": f"{gross_margin}%",
            "outbound_items": outbound_details,
            "generated_vouchers": [voucher1.to_dict(), voucher2.to_dict()]
        }

if __name__ == '__main__':
    erp = ERPSystem()
    print("赤龙 ERP 核心引擎模块初始化成功。")
