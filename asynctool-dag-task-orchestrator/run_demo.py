#!/usr/bin/env python3
"""
高并发异步任务 DAG 编排与依赖容错隔离引擎 (AsyncTool-Style Orchestrator)
基于 WorkerWrapper 与线程池实现复杂依赖图解耦、异步扇入扇出与超时降级
"""
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Callable

class WorkResult:
    """包装单个任务的执行结果与状态"""
    def __init__(self, result: Any = None, status: str = "INIT", error: Optional[Exception] = None):
        self.result = result
        self.status = status  # INIT, SUCCESS, FAILED, TIMEOUT, DEFAULT
        self.error = error

    def __repr__(self):
        return f"<WorkResult status={self.status} result={self.result} error={self.error}>"

class WorkerWrapper:
    """任务编排包装器：持有任务上下文、前后依赖与回调契约"""
    def __init__(
        self,
        worker_id: str,
        action: Callable[[Any, Dict[str, "WorkerWrapper"]], Any],
        param: Any = None,
        default_value: Any = None,
        timeout_ms: int = 1000,
        callback: Optional[Callable[[bool, Any, WorkResult], None]] = None
    ):
        self.worker_id = worker_id
        self.action = action
        self.param = param
        self.default_value = default_value
        self.timeout_ms = timeout_ms
        self.callback = callback
        
        self.depends: List["WorkerWrapper"] = []
        self.next_wrappers: List["WorkerWrapper"] = []
        
        self.work_result = WorkResult()
        self.executed = False
        self.lock = threading.Lock()
        self.event = threading.Event()  # 触发后续任务就绪信号

    def add_depend(self, depend_wrapper: "WorkerWrapper"):
        self.depends.append(depend_wrapper)
        depend_wrapper.next_wrappers.append(self)

    def execute(self, all_wrappers: Dict[str, "WorkerWrapper"]):
        """等待所有前置依赖完成后执行自身业务逻辑"""
        # 1. 阻塞等待所有前置依赖完成
        for dep in self.depends:
            dep.event.wait()

        # 2. 检查依赖项是否出现致命失败需要熔断
        dep_failed = any(dep.work_result.status == "FAILED" for dep in self.depends)
        if dep_failed and self.default_value is not None:
            # 触发前置依赖降级
            self.work_result = WorkResult(result=self.default_value, status="DEFAULT")
            self.event.set()
            if self.callback:
                self.callback(True, self.param, self.work_result)
            return self.work_result

        # 3. 开始执行核心逻辑
        try:
            start_t = time.time()
            res = self.action(self.param, all_wrappers)
            cost = (time.time() - start_t) * 1000
            if cost > self.timeout_ms and self.default_value is not None:
                self.work_result = WorkResult(result=self.default_value, status="TIMEOUT")
            else:
                self.work_result = WorkResult(result=res, status="SUCCESS")
        except Exception as e:
            if self.default_value is not None:
                self.work_result = WorkResult(result=self.default_value, status="DEFAULT", error=e)
            else:
                self.work_result = WorkResult(result=None, status="FAILED", error=e)

        self.event.set()
        if self.callback:
            self.callback(self.work_result.status == "SUCCESS", self.param, self.work_result)
        return self.work_result

class AsyncDAGPool:
    """异步 DAG 编排引擎中枢"""
    def __init__(self, max_workers: int = 8):
        self.pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="AsyncDAGWorker-")

    def run_graph(self, wrappers: List[WorkerWrapper]) -> Dict[str, WorkResult]:
        all_wrappers = {w.worker_id: w for w in wrappers}
        futures = []
        for w in wrappers:
            futures.append(self.pool.submit(w.execute, all_wrappers))

        # 等待所有任务完成
        for f in as_completed(futures):
            f.result()

        return {w.worker_id: w.work_result for w in wrappers}

    def shutdown(self):
        self.pool.shutdown(wait=True)

def run_tests():
    print("=== 开始运行高并发异步任务 DAG 编排与依赖容错隔离引擎演练 ===")
    dag_pool = AsyncDAGPool(max_workers=6)

    # 模拟电商大促详情聚合场景：
    # Task A: 商品核心信息 (耗时 50ms)
    # Task B: 优惠券与红包计算 (依赖 A，耗时 80ms)
    # Task C: 会员 VIP 折扣与积分 (依赖 A，耗时 60ms)
    # Task D: 终局结算汇总与风控校验 (依赖 B 和 C 扇入，耗时 30ms)
    # Task E: 智能商品推荐瀑布流 (独立并行，耗时 100ms)

    def action_product(param, all_w):
        time.sleep(0.05)
        return {"id": param, "title": "4K Ultra-HD Monitor", "basePrice": 2000.0}

    def action_coupon(param, all_w):
        time.sleep(0.08)
        prod = all_w["Task-A"].work_result.result
        discount = 200.0 if prod["basePrice"] >= 1000.0 else 0.0
        return {"couponDiscount": discount}

    def action_vip(param, all_w):
        time.sleep(0.06)
        prod = all_w["Task-A"].work_result.result
        vip_rebate = prod["basePrice"] * 0.05  # 5% VIP 返现
        return {"vipRebate": vip_rebate}

    def action_summary(param, all_w):
        time.sleep(0.03)
        prod = all_w["Task-A"].work_result.result
        coupon = all_w["Task-B"].work_result.result
        vip = all_w["Task-C"].work_result.result
        final_price = prod["basePrice"] - coupon["couponDiscount"] - vip["vipRebate"]
        return {"orderId": "ORD-20261022-8888", "finalPrice": final_price}

    def action_recommend(param, all_w):
        time.sleep(0.1)
        return ["DisplayPort Cable", "Screen Cleaner Kit", "Ergonomic Monitor Arm"]

    # 组装 WorkerWrapper
    w_a = WorkerWrapper("Task-A", action_product, param=9901, default_value={"basePrice": 0.0})
    w_b = WorkerWrapper("Task-B", action_coupon, default_value={"couponDiscount": 0.0})
    w_c = WorkerWrapper("Task-C", action_vip, default_value={"vipRebate": 0.0})
    w_d = WorkerWrapper("Task-D", action_summary, default_value={"finalPrice": 0.0})
    w_e = WorkerWrapper("Task-E", action_recommend, default_value=[])

    # 声明 DAG 依赖图
    # B 依赖 A，C 依赖 A
    w_b.add_depend(w_a)
    w_c.add_depend(w_a)
    # D 依赖 B 与 C（双重扇入汇聚）
    w_d.add_depend(w_b)
    w_d.add_depend(w_c)
    # E 完全独立无依赖

    start_t = time.time()
    results = dag_pool.run_graph([w_a, w_b, w_c, w_d, w_e])
    total_cost = (time.time() - start_t) * 1000

    print(f"\n[DAG 执行完毕] 总耗时: {total_cost:.2f} ms (传统串行预计耗时: 320ms+)")
    for task_id, res in results.items():
        print(f"  [{task_id}] 状态: {res.status} | 产出: {res.result}")

    # 验证正确性
    assert results["Task-A"].status == "SUCCESS"
    assert results["Task-D"].status == "SUCCESS"
    assert results["Task-D"].result["finalPrice"] == 1700.0  # 2000 - 200 - 100 = 1700
    assert len(results["Task-E"].result) == 3

    dag_pool.shutdown()
    print("\n[OK] DAG 编排引擎与汇聚扇入用例 100% 验证通过！")

if __name__ == "__main__":
    run_tests()
