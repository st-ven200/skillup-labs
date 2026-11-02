#!/usr/bin/env python3
"""
Python High-Concurrency Task Aggregator Engine (Dual implementation of TaskAggregator / LatchUtils)
多线程异步任务聚合与超时异常压制树治理引擎
"""
import sys
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import List, Callable, Any, Optional, Dict

class AggregatorExecutionException(Exception):
    """聚合执行异常，携带所有失败子任务的异常树（Suppressed Exceptions）"""
    def __init__(self, message: str, suppressed_exceptions: List[Exception]):
        super().__init__(message)
        self.suppressed_exceptions = suppressed_exceptions

    def format_suppressed_tree(self) -> str:
        lines = [f"❌ {str(self)}:"]
        for idx, ex in enumerate(self.suppressed_exceptions, 1):
            lines.append(f"   ├── [Suppressed #{idx}] {type(ex).__name__}: {str(ex)}")
        return "\n".join(lines)

class AggregatorTimeoutException(Exception):
    """聚合超时异常，附带完整诊断上下文与滞后任务统计"""
    def __init__(self, trace_id: str, timeout_ms: int, total_tasks: int, uncompleted_tasks: int):
        self.trace_id = trace_id
        self.timeout_ms = timeout_ms
        self.total_tasks = total_tasks
        self.uncompleted_tasks = uncompleted_tasks
        super().__init__(
            f"[TaskAggregator Timeout] traceId={trace_id}, timeout={timeout_ms}ms, "
            f"totalTasks={total_tasks}, uncompletedTasks={uncompleted_tasks}"
        )

class TaskAggregatorEngine:
    def __init__(self, max_workers: int = 16):
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="AggregatorPool")

    def await_all(
        self,
        tasks: List[Callable[[], Any]],
        timeout_seconds: float,
        trace_id: Optional[str] = None
    ) -> List[Any]:
        """
        并发执行并等待所有任务完成：
        1. 严格保序（Preserve input order）；
        2. 全量收集异常（No swallowed exceptions via suppressed list）；
        3. 明确超时熔断（Timeout fast-fail）。
        """
        if not trace_id:
            trace_id = f"TR-{uuid.uuid4().hex[:8].upper()}"

        task_count = len(tasks)
        if task_count == 0:
            return []

        results = [None] * task_count
        errors: List[Exception] = []
        errors_lock = threading.Lock()
        
        # 线程同步屏障：模拟 CountDownLatch
        completed_count = 0
        barrier_event = threading.Event()
        counter_lock = threading.Lock()

        def worker(index: int, task_fn: Callable[[], Any]):
            nonlocal completed_count
            try:
                val = task_fn()
                results[index] = val
            except Exception as e:
                with errors_lock:
                    errors.append(e)
            finally:
                with counter_lock:
                    completed_count += 1
                    if completed_count == task_count:
                        barrier_event.set()

        for idx, task in enumerate(tasks):
            self.executor.submit(worker, idx, task)

        # 等待屏障触发或超时
        finished = barrier_event.wait(timeout=timeout_seconds)

        if not finished:
            uncompleted = task_count - completed_count
            raise AggregatorTimeoutException(
                trace_id=trace_id,
                timeout_ms=int(timeout_seconds * 1000),
                total_tasks=task_count,
                uncompleted_tasks=uncompleted
            )

        if errors:
            raise AggregatorExecutionException(
                f"[TaskAggregator PartialFailure] traceId={trace_id}, totalTasks={task_count}, failedCount={len(errors)}",
                suppressed_exceptions=errors
            )

        return results

    def shutdown(self):
        self.executor.shutdown(wait=False)
