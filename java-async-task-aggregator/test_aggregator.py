#!/usr/bin/env python3
"""
Test Suite for Java Concurrency Task Aggregator (LatchUtils / TaskAggregator)
验证有序结果收集、多异常压制聚合与超时快速诊断
"""
import time
import random
from async_aggregator import TaskAggregatorEngine, AggregatorExecutionException, AggregatorTimeoutException

def simulate_rpc_call(service_name: str, delay: float, should_fail: bool = False):
    def _call():
        time.sleep(delay)
        if should_fail:
            raise ConnectionError(f"下游服务 [{service_name}] 响应异常: Read timed out after {delay}s")
        return f"Result-From-{service_name} (latency={int(delay*1000)}ms)"
    return _call

def run_tests():
    print("==================================================")
    print("🚀 开始执行 TaskAggregator 异步任务聚合器并发场景测试")
    print("==================================================")
    engine = TaskAggregatorEngine(max_workers=8)

    # ----------------------------------------------------
    # 测试场景 1：全成功场景，验证多线程无序完成下的【严格保序回填】
    # ----------------------------------------------------
    print("\n--- [Scenario 1] 正常多并发调用：验证有序结果槽位 ---")
    # 故意让后面的任务比前面的任务先执行完，观察最终列表顺序是否与入参完全一致
    tasks_scenario1 = [
        simulate_rpc_call("UserService", delay=0.15),      # Index 0, 较慢
        simulate_rpc_call("OrderService", delay=0.05),     # Index 1, 极快完成
        simulate_rpc_call("InventoryService", delay=0.10), # Index 2, 中速完成
        simulate_rpc_call("CouponService", delay=0.02),    # Index 3, 最先完成
    ]

    t0 = time.time()
    results = engine.await_all(tasks_scenario1, timeout_seconds=1.0, trace_id="TRACE-ORD-SUCCESS-001")
    cost = time.time() - t0

    print(f"✅ 并发执行耗时: {cost:.3f}s (理论耗时约最慢任务 0.15s)")
    for idx, r in enumerate(results):
        print(f"   Slot [{idx}]: {r}")
    assert results[0].startswith("Result-From-UserService")
    assert results[1].startswith("Result-From-OrderService")
    assert results[2].startswith("Result-From-InventoryService")
    assert results[3].startswith("Result-From-CouponService")
    print("🎉 场景 1 校验通过：结果顺序严格保序！")

    # ----------------------------------------------------
    # 测试场景 2：部分子任务异常，验证【异常压制树 (addSuppressed) 全量收集】
    # ----------------------------------------------------
    print("\n--- [Scenario 2] 部分任务崩溃：验证异常压制树收集，杜绝吞异常 ---")
    tasks_scenario2 = [
        simulate_rpc_call("PaymentGateway", delay=0.05, should_fail=False),
        simulate_rpc_call("FraudDetectService", delay=0.08, should_fail=True),
        simulate_rpc_call("CreditCheckService", delay=0.06, should_fail=True),
    ]

    try:
        engine.await_all(tasks_scenario2, timeout_seconds=1.0, trace_id="TRACE-PAY-FAIL-002")
        assert False, "必须抛出 AggregatorExecutionException"
    except AggregatorExecutionException as ex:
        print("✅ 成功捕获聚合异常，且异常未被丢失：")
        print(ex.format_suppressed_tree())
        assert len(ex.suppressed_exceptions) == 2, "必须精确收集 2 个子异常"
        print("🎉 场景 2 校验通过：全量异常形成压制树，零吞没！")

    # ----------------------------------------------------
    # 测试场景 3：下游卡死引发超时，验证【带详细上下文的超时快速熔断】
    # ----------------------------------------------------
    print("\n--- [Scenario 3] 下游超时卡死：验证超时精准快速诊断 ---")
    tasks_scenario3 = [
        simulate_rpc_call("FastService", delay=0.05, should_fail=False),
        simulate_rpc_call("HangingService1", delay=2.00, should_fail=False), # 远超设定的 200ms
        simulate_rpc_call("HangingService2", delay=2.50, should_fail=False),
    ]

    try:
        t_start = time.time()
        engine.await_all(tasks_scenario3, timeout_seconds=0.20, trace_id="TRACE-TIMEOUT-003")
        assert False, "必须抛出 AggregatorTimeoutException"
    except AggregatorTimeoutException as ex:
        t_elapsed = time.time() - t_start
        print(f"✅ 成功于 {t_elapsed:.3f}s 精准熔断抛出超时异常：")
        print(f"   Context: {str(ex)}")
        assert ex.uncompleted_tasks == 2, f"期望 2 个未完成任务，实际 {ex.uncompleted_tasks}"
        print("🎉 场景 3 校验通过：超时极速断开并输出清晰诊断上下文！")

    engine.shutdown()
    print("\n==================================================")
    print("🏆 TaskAggregator 所有核心高并发场景测试全部通过！")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
