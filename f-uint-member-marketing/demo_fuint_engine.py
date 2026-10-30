#!/usr/bin/env python3
"""
F-Uint 实体门店会员营销与收银结算原子状态机核心实战
演示会员双轨记账、卡券核销防重放、乐观锁防超扣与等级自动晋升引擎
"""
import time
import uuid
import threading
from typing import Dict, Any, Optional

class MemberAccount:
    def __init__(self, member_id: str, name: str, phone: str):
        self.member_id = member_id
        self.name = name
        self.phone = phone
        self.balance_cents = 0       # 储值卡余额 (分)
        self.points = 0              # 积分
        self.total_spent_cents = 0   # 累计消费额 (分)
        self.tier = "NORMAL"         # NORMAL -> SILVER -> GOLD -> DIAMOND
        self.version = 0             # 乐观锁版本号
        self._lock = threading.Lock()

class Coupon:
    def __init__(self, coupon_id: str, coupon_type: str, min_spent_cents: int, discount_cents: int):
        self.coupon_id = coupon_id
        self.coupon_type = coupon_type      # CASH_OFF (满减), TIMES_CARD (次卡)
        self.min_spent_cents = min_spent_cents
        self.discount_cents = discount_cents
        self.is_used = False
        self.used_time: Optional[float] = None

class FuintSettlementEngine:
    TIER_THRESHOLDS = [
        ("DIAMOND", 500000, 1.5, 0.85),  # 累消 >= 5000元: 积分1.5倍加速，8.5折
        ("GOLD",    200000, 1.2, 0.90),  # 累消 >= 2000元: 积分1.2倍加速，9.0折
        ("SILVER",   50000, 1.0, 0.95),  # 累消 >= 500元: 积分1.0倍加速，9.5折
        ("NORMAL",       0, 1.0, 1.00),  # 普通会员
    ]

    def __init__(self):
        self.members: Dict[str, MemberAccount] = {}
        self.coupons: Dict[str, Coupon] = {}
        self.ledger_logs = []

    def register_member(self, member_id: str, name: str, phone: str) -> MemberAccount:
        acc = MemberAccount(member_id, name, phone)
        self.members[member_id] = acc
        return acc

    def issue_coupon(self, coupon_id: str, c_type: str, min_spent_cents: int, discount_cents: int) -> Coupon:
        c = Coupon(coupon_id, c_type, min_spent_cents, discount_cents)
        self.coupons[coupon_id] = c
        return c

    def recharge(self, member_id: str, amount_cents: int, bonus_cents: int = 0) -> Dict[str, Any]:
        member = self.members.get(member_id)
        if not member:
            raise ValueError(f"会员 {member_id} 不存在")
        with member._lock:
            total_add = amount_cents + bonus_cents
            member.balance_cents += total_add
            member.version += 1
            log_entry = {
                "tx_id": str(uuid.uuid4())[:8],
                "type": "RECHARGE",
                "member_id": member_id,
                "amount_cents": amount_cents,
                "bonus_cents": bonus_cents,
                "new_balance": member.balance_cents,
                "timestamp": time.time()
            }
            self.ledger_logs.append(log_entry)
            return log_entry

    def checkout(self, member_id: str, raw_order_cents: int, coupon_id: Optional[str] = None, use_points: int = 0) -> Dict[str, Any]:
        member = self.members.get(member_id)
        if not member:
            raise ValueError(f"会员 {member_id} 不存在")

        with member._lock:
            # 1. 计算会员等级基础折扣
            _, _, point_accel, discount_rate = self._get_tier_policy(member.tier)
            payable_cents = int(raw_order_cents * discount_rate)

            # 2. 卡券核销防重放
            coupon_discount_cents = 0
            if coupon_id:
                coupon = self.coupons.get(coupon_id)
                if not coupon:
                    raise ValueError(f"优惠券 {coupon_id} 不存在")
                if coupon.is_used:
                    raise ValueError(f"优惠券 {coupon_id} 已被核销，禁止双花！")
                if payable_cents < coupon.min_spent_cents:
                    raise ValueError(f"订单金额未达优惠券门槛 {coupon.min_spent_cents/100:.2f} 元")
                coupon_discount_cents = coupon.discount_cents
                payable_cents = max(0, payable_cents - coupon_discount_cents)
                coupon.is_used = True
                coupon.used_time = time.time()

            # 3. 积分抵扣 (100积分 = 1元 = 100分)
            points_discount_cents = 0
            if use_points > 0:
                if member.points < use_points:
                    raise ValueError(f"会员积分不足: 现有 {member.points}, 拟抵扣 {use_points}")
                points_discount_cents = use_points  # 1积分 = 1分钱
                if points_discount_cents > payable_cents:
                    points_discount_cents = payable_cents
                actual_points_used = points_discount_cents
                member.points -= actual_points_used
                payable_cents -= points_discount_cents

            # 4. 储值卡扣款
            if member.balance_cents < payable_cents:
                raise ValueError(f"储值余额不足: 现有 {member.balance_cents/100:.2f} 元, 应付 {payable_cents/100:.2f} 元")
            
            member.balance_cents -= payable_cents
            member.total_spent_cents += raw_order_cents
            member.version += 1

            # 5. 积分返赠 (按实付金额 * 加速比率)
            earned_points = int((payable_cents / 100) * point_accel)
            member.points += earned_points

            # 6. 检查自动升阶
            old_tier = member.tier
            new_tier = self._eval_tier(member.total_spent_cents)
            member.tier = new_tier

            receipt = {
                "order_id": f"ORD-{uuid.uuid4().hex[:8].upper()}",
                "member_id": member_id,
                "raw_order_yuan": raw_order_cents / 100,
                "tier_applied": old_tier,
                "tier_discount_rate": discount_rate,
                "coupon_discount_yuan": coupon_discount_cents / 100,
                "points_deducted": points_discount_cents,
                "actual_balance_paid_yuan": payable_cents / 100,
                "points_earned": earned_points,
                "remaining_balance_yuan": member.balance_cents / 100,
                "current_points": member.points,
                "tier_upgraded": old_tier != new_tier,
                "new_tier": new_tier
            }
            self.ledger_logs.append(receipt)
            return receipt

    def _get_tier_policy(self, tier: str):
        for name, thresh, accel, rate in self.TIER_THRESHOLDS:
            if name == tier:
                return name, thresh, accel, rate
        return "NORMAL", 0, 1.0, 1.0

    def _eval_tier(self, total_spent_cents: int) -> str:
        for name, thresh, _, _ in self.TIER_THRESHOLDS:
            if total_spent_cents >= thresh:
                return name
        return "NORMAL"

def run_fuint_simulation():
    print("=" * 65)
    print("🚀 F-Uint 实体门店会员营销与收银结算引擎现场实操演示")
    print("=" * 65)

    engine = FuintSettlementEngine()

    # 1. 注册会员与发券
    m = engine.register_member("M1001", "张三", "13800138000")
    print(f"✅ 会员开卡: {m.name} ({m.phone}) | 初始等级: {m.tier} | 余额: {m.balance_cents}元")

    c1 = engine.issue_coupon("CP-50-10", "CASH_OFF", min_spent_cents=5000, discount_cents=1000)
    print(f"🎫 发放优惠券: {c1.coupon_id} (满 50 元减 10 元)")

    # 2. 会员充值 (充500送50)
    rc = engine.recharge("M1001", amount_cents=50000, bonus_cents=5000)
    print(f"💰 储值入账: 本金 {rc['amount_cents']/100} 元 + 赠送 {rc['bonus_cents']/100} 元 -> 当前可用余额: {rc['new_balance']/100} 元")

    # 3. 首次结算 (原价 120 元, 用券 10 元)
    r1 = engine.checkout("M1001", raw_order_cents=12000, coupon_id="CP-50-10")
    print("\n--- 🧾 首次收银结算小票 ---")
    print(f"单号: {r1['order_id']} | 原价: {r1['raw_order_yuan']} 元")
    print(f"会员等级: {r1['tier_applied']} (折扣率: {r1['tier_discount_rate']})")
    print(f"卡券优惠: -{r1['coupon_discount_yuan']} 元 | 储值实扣: {r1['actual_balance_paid_yuan']} 元")
    print(f"消费返积分: +{r1['points_earned']} 分 | 账户剩余余额: {r1['remaining_balance_yuan']} 元")
    print(f"会员等级状态: 当前等级 {r1['new_tier']} (升阶: {r1['tier_upgraded']})")

    # 4. 防双花测试 (再次尝试核销 CP-50-10)
    try:
        engine.checkout("M1001", raw_order_cents=8000, coupon_id="CP-50-10")
    except ValueError as e:
        print(f"\n🛡️ 优惠券防双花拦截触发成功: {e}")

    # 5. 大额消费与自动晋升测试 (原价 4500 元)
    engine.recharge("M1001", amount_cents=500000)
    r2 = engine.checkout("M1001", raw_order_cents=450000, use_points=50)
    print("\n--- 🧾 大额收银结算小票 ---")
    print(f"单号: {r2['order_id']} | 原价: {r2['raw_order_yuan']} 元")
    print(f"等级折扣: {r2['tier_applied']} (折扣率: {r2['tier_discount_rate']})")
    print(f"积分抵扣: -{r2['points_deducted']/100:.2f} 元 | 储值实扣: {r2['actual_balance_paid_yuan']} 元")
    print(f"消费返积分: +{r2['points_earned']} 分 | 账户升级状态: {r2['tier_applied']} -> {r2['new_tier']} (升阶通知触发: {r2['tier_upgraded']})")
    print("=" * 65)

if __name__ == "__main__":
    run_fuint_simulation()
