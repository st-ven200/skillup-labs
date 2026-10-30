#!/usr/bin/env python3
"""
Lab 27: Spring 7.0.4 优雅停机并发死锁复盘与非阻塞治理实战
实操目标：
1. 真实模拟 Spring 7 早期版本中 ContextClosedEvent 与 ShutdownHook 竞争引发的死锁（Issue #36260）；
2. 真实演示 Spring 7.0.4 引入的原子状态门禁与分离式生命周期非阻塞释放，实现 0 死锁优雅停机；
3. 纯真实并发锁（threading.Lock, threading.Event, concurrent.futures），绝无 Mock 假打印。
"""

import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor

class VulnerableLifecycleManager:
    """
    模拟 Spring 7.0.3 早期版本：单一大锁 lifecycleMonitor + 闭环事件同步分发导致的死锁模型
    """
    def __init__(self):
        self.lifecycle_lock = threading.Lock()
        self.worker_event = threading.Event()
        self.is_closed = False

    def trigger_context_closed_event(self):
        """主线程或定时容器执行上下文关闭"""
        with self.lifecycle_lock:
            # 持有生命周期锁，开始通知监听器
            # 监听器中等待外部工作线程完成清理
            success = self.worker_event.wait(timeout=1.5)
            if not success:
                # 发生死锁超时
                raise TimeoutError("Deadlock detected: ContextClosedEvent locked lifecycle_lock waiting for worker_event")
            self.is_closed = True

    def shutdown_hook_cleanup(self):
        """JVM ShutdownHook 线程并发执行停机"""
        # 外部线程试图在退出前获取生命周期锁
        acquired = self.lifecycle_lock.acquire(timeout=1.5)
        if not acquired:
            raise TimeoutError("Deadlock detected: ShutdownHook blocked waiting for lifecycle_lock")
        try:
            self.worker_event.set()
        finally:
            self.lifecycle_lock.release()


class PatchedLifecycleManager:
    """
    模拟 Spring 7.0.4 修复方案：
    1. 原子状态门禁 (Atomic State Guard)
    2. 分离式生命周期锁与阶段性非阻塞排干 (Phase-based Non-blocking Draining)
    """
    def __init__(self):
        self._state_lock = threading.Lock()
        self._closing = False
        self._closed = False
        self.worker_event = threading.Event()

    def try_begin_close(self) -> bool:
        """原子检查并设置 closing 状态，避免多 Hook 重复竞争"""
        with self._state_lock:
            if self._closing or self._closed:
                return False
            self._closing = True
            return True

    def close(self, caller_name: str) -> dict:
        start_time = time.time()
        if not self.try_begin_close():
            return {
                "caller": caller_name,
                "status": "SKIPPED_ALREADY_CLOSING",
                "cost_ms": round((time.time() - start_time) * 1000, 2)
            }

        # 触发阶段性通知（不持有全局锁）
        self.worker_event.set()
        with self._state_lock:
            self._closed = True

        return {
            "caller": caller_name,
            "status": "SUCCESS_CLOSED",
            "cost_ms": round((time.time() - start_time) * 1000, 2)
        }


def run_benchmark():
    print("=" * 60)
    print("🚀 [Lab 27] Spring 7.0.4 并发优雅停机死锁成因与治理实操验证")
    print("=" * 60)

    # 1. 验证早期模型死锁行为
    print("\n[测试阶段 1] 运行高并发脆弱版本 (VulnerableLifecycleManager)...")
    vuln = VulnerableLifecycleManager()
    deadlock_caught = []

    def t1_action():
        try:
            vuln.trigger_context_closed_event()
        except TimeoutError as e:
            deadlock_caught.append(f"T1 (ContextClosed): {e}")

    def t2_action():
        # 微小延迟制造竞态窗口
        time.sleep(0.05)
        try:
            vuln.shutdown_hook_cleanup()
        except TimeoutError as e:
            deadlock_caught.append(f"T2 (ShutdownHook): {e}")

    t1 = threading.Thread(target=t1_action)
    t2 = threading.Thread(target=t2_action)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print(f"👉 脆弱版本捕获到死锁/超时事件数: {len(deadlock_caught)}")
    for err in deadlock_caught:
        print(f"   ⚠️ {err}")
    assert len(deadlock_caught) > 0, "脆弱版本应当触发死锁竞态异常！"

    # 2. 验证 Spring 7.0.4 治理版本
    print("\n[测试阶段 2] 运行 Spring 7.0.4 并发治理版本 (PatchedLifecycleManager)...")
    patched = PatchedLifecycleManager()
    results = []

    def concurrent_closer(worker_id):
        res = patched.close(f"Worker-{worker_id}")
        results.append(res)

    # 模拟 10 个并发 ShutdownHook / 外部停机信号同时触发
    threads = [threading.Thread(target=concurrent_closer, args=(i,)) for i in range(10)]
    t0 = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    total_cost = round((time.time() - t0) * 1000, 2)

    print(f"👉 治理版本多线程并发关闭总耗时: {total_cost} ms")
    success_count = sum(1 for r in results if r["status"] == "SUCCESS_CLOSED")
    skipped_count = sum(1 for r in results if r["status"] == "SKIPPED_ALREADY_CLOSING")
    print(f"👉 执行统计: 成功关闭 1 次 ({success_count}), 安全忽略竞争调用 ({skipped_count})")

    assert success_count == 1, "必须有且仅有一次成功关闭"
    assert skipped_count == 9, "其余 9 个并发请求必须被原子门禁拦截避免锁争用"
    print("\n✅ [VERIFICATION PASSED] 治理方案通过全部断言，无死锁、无阻塞、无假死！")


if __name__ == "__main__":
    run_benchmark()
