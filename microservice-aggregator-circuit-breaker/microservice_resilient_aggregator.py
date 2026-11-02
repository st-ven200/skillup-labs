#!/usr/bin/env python3
"""
企业级微服务弹性聚合器与自适应断路器 (Resilient Service Aggregator & Circuit Breaker)
实现企业微服务编排模式、分支扇出与自适应熔断降级闭环
严格遵从 PROJECT_RULES.md §21 实战真实性与端到端闭环规范
"""
import time
import threading
import concurrent.futures
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class CircuitState(Enum):
    CLOSED = "CLOSED"        # 正常状态：流量全通，统计失败率
    OPEN = "OPEN"            # 熔断开启：直接快速失败，触发降级
    HALF_OPEN = "HALF_OPEN"  # 半开探测：允许少量金丝雀流量探测下游健康度


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 3       # 连续失败或窗口失败阈值
    recovery_timeout: float = 0.5    # 熔断冷却时间（秒）
    half_open_success_threshold: int = 2  # 半开状态下连续成功几次才关闭熔断


class CircuitBreaker:
    """
    工业级自适应状态机断路器
    """
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self._lock = threading.Lock()

    def execute(self, action: Callable[[], Any], fallback: Callable[[], Any]) -> Any:
        with self._lock:
            now = time.time()
            # 状态转移：若处于 OPEN 状态且超过冷却时间，尝试转入 HALF_OPEN
            if self.state == CircuitState.OPEN:
                if now - self.last_failure_time >= self.config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    # 依然在冷却期，直接触发降级
                    return fallback()

        # 执行下游调用
        try:
            result = action()
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            return fallback()

    def _on_success(self):
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.half_open_success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0

    def _on_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN):
                if self.failure_count >= self.config.failure_threshold or self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.OPEN


class MicroserviceAggregator:
    """
    微服务聚合器 (Aggregator Pattern)：
    并发编排多个微服务分支（User, Order, Recommendation, Inventory），
    并对下游依赖加装独立断路器，确保单点不可用不引发雪崩故障。
    """
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {
            "user_svc": CircuitBreaker("user_svc", CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.3)),
            "order_svc": CircuitBreaker("order_svc", CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.3)),
            "recom_svc": CircuitBreaker("recom_svc", CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.3)),
            "points_svc": CircuitBreaker("points_svc", CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.3))
        }

    # 下游微服务模拟实现
    def _call_user_service(self, user_id: str) -> Dict[str, Any]:
        return {"user_id": user_id, "name": "Alice", "level": "VIP"}

    def _call_order_service(self, user_id: str) -> Dict[str, Any]:
        return {"user_id": user_id, "order_count": 12, "last_order_amount": 358.0}

    def _call_recom_service(self, user_id: str, inject_failure: bool = False) -> Dict[str, Any]:
        if inject_failure:
            raise ConnectionError("Recom service timeout (HTTP 504 Gateway Timeout)")
        return {"user_id": user_id, "items": ["Product_A", "Product_B", "Product_C"]}

    def _call_points_service(self, user_id: str) -> Dict[str, Any]:
        return {"user_id": user_id, "points": 1240}

    def aggregate_user_dashboard(self, user_id: str, fail_recom: bool = False) -> Dict[str, Any]:
        """
        并发扇出调用下游 4 个微服务并实施聚合
        """
        results: Dict[str, Any] = {}

        def fetch_user():
            return self.breakers["user_svc"].execute(
                lambda: self._call_user_service(user_id),
                fallback=lambda: {"user_id": user_id, "fallback": True, "name": "Guest"}
            )

        def fetch_order():
            return self.breakers["order_svc"].execute(
                lambda: self._call_order_service(user_id),
                fallback=lambda: {"user_id": user_id, "fallback": True, "order_count": 0}
            )

        def fetch_recom():
            return self.breakers["recom_svc"].execute(
                lambda: self._call_recom_service(user_id, inject_failure=fail_recom),
                fallback=lambda: {"user_id": user_id, "fallback": True, "items": ["Hot_Item_Default"]}
            )

        def fetch_points():
            return self.breakers["points_svc"].execute(
                lambda: self._call_points_service(user_id),
                fallback=lambda: {"user_id": user_id, "fallback": True, "points": 0}
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_user = executor.submit(fetch_user)
            future_order = executor.submit(fetch_order)
            future_recom = executor.submit(fetch_recom)
            future_points = executor.submit(fetch_points)

            results["user"] = future_user.result()
            results["order"] = future_order.result()
            results["recommendation"] = future_recom.result()
            results["points"] = future_points.result()

        return results


def run_microservice_patterns_test():
    print("=" * 70)
    print(">>> 启动微服务核心模式验证：弹性聚合器与自适应断路器测试")
    print("=" * 70)

    aggregator = MicroserviceAggregator()
    recom_breaker = aggregator.breakers["recom_svc"]

    # 1. 正常聚合测试
    print("\n[STEP 1] 验证正常全链路并发扇出聚合...")
    dash1 = aggregator.aggregate_user_dashboard("UID_1001", fail_recom=False)
    assert dash1["user"]["name"] == "Alice"
    assert dash1["order"]["order_count"] == 12
    assert dash1["recommendation"]["items"] == ["Product_A", "Product_B", "Product_C"]
    assert recom_breaker.state == CircuitState.CLOSED
    print("  -> 正常全链路聚合响应成功，断路器处于 CLOSED 状态！")

    # 2. 模拟下游依赖故障触发断路器熔断
    print("\n[STEP 2] 模拟下游推荐服务超时故障，触发熔断与优雅降级...")
    # 连续调用 2 次失败
    dash_fail1 = aggregator.aggregate_user_dashboard("UID_1001", fail_recom=True)
    assert dash_fail1["recommendation"]["fallback"] is True
    assert dash_fail1["recommendation"]["items"] == ["Hot_Item_Default"]

    dash_fail2 = aggregator.aggregate_user_dashboard("UID_1001", fail_recom=True)
    assert dash_fail2["recommendation"]["fallback"] is True

    # 此时失败次数达到阈值 2，断路器必须进入 OPEN 状态
    assert recom_breaker.state == CircuitState.OPEN, f"断路器状态应为 OPEN，实际为 {recom_breaker.state}"
    print(f"  -> 推荐服务连续失败达到阈值，断路器成功跃迁至 OPEN 状态！")

    # 3. 验证熔断期间的快速失败（不真正发起下游调用）
    print("\n[STEP 3] 验证 OPEN 状态下的极速短路与降级保护...")
    t_start = time.perf_counter()
    dash_fast_fail = aggregator.aggregate_user_dashboard("UID_1001", fail_recom=False)
    duration_ms = (time.perf_counter() - t_start) * 1000.0
    assert dash_fast_fail["recommendation"]["fallback"] is True
    print(f"  -> 熔断阻断快速返回耗时: {duration_ms:.2f} ms，下游得到绝对隔离保护！")

    # 4. 验证自适应冷却恢复 (HALF_OPEN -> CLOSED)
    print("\n[STEP 4] 验证冷却窗口后的金丝雀流量探测与自愈恢复...")
    time.sleep(0.35)  # 超过 recovery_timeout (0.3s)

    # 第一次金丝雀请求成功
    dash_recover1 = aggregator.aggregate_user_dashboard("UID_1001", fail_recom=False)
    assert dash_recover1["recommendation"]["items"] == ["Product_A", "Product_B", "Product_C"]
    assert recom_breaker.state == CircuitState.HALF_OPEN

    # 第二次金丝雀请求成功 -> 恢复 CLOSED
    dash_recover2 = aggregator.aggregate_user_dashboard("UID_1001", fail_recom=False)
    assert dash_recover2["recommendation"]["items"] == ["Product_A", "Product_B", "Product_C"]
    assert recom_breaker.state == CircuitState.CLOSED
    print("  -> 自愈探测完成，断路器自动恢复至 CLOSED 正常状态！")

    print("\n" + "=" * 70)
    print(">>> 结论：微服务聚合编排与断路器自适应状态机 100% 验证通过！")
    print("=" * 70)


if __name__ == "__main__":
    run_microservice_patterns_test()
