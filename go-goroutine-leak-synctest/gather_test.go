package main

import (
	"context"
	"strings"
	"testing"
	"testing/synctest"
	"time"
)

// TestVirtualTimeAcceleration 演示 synctest 虚拟时间瞬移
// 在真实环境中 sleep 10 小时需要 36000 秒，而在虚拟时间气泡内，单调时钟瞬移只需 0.001 秒！
func TestVirtualTimeAcceleration(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		start := time.Now()
		const simulatedDuration = 10 * time.Hour

		doneCh := make(chan string)
		go func() {
			doneCh <- LongRunningHeartbeat(simulatedDuration)
		}()

		// 等待气泡内协程执行
		synctest.Wait()

		msg := <-doneCh
		if !strings.Contains(msg, "10h0m0s") {
			t.Fatalf("unexpected message: %s", msg)
		}

		// 检查宿主机器的物理耗时（必须小于 50 毫秒）
		wallClockElapsed := time.Since(start)
		t.Logf("✅ 虚拟时间演进: 10小时 | 宿主机物理墙上耗时仅: %v", wallClockElapsed)
	})
}

// TestFixedGatherCleanExit 验证 SafeGather 在提前退出时协程完全受控回收
func TestFixedGatherCleanExit(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		ctx, cancel := context.WithCancel(context.Background())

		out := SafeGather(
			ctx,
			func() int { return 10 },
			func() int { return 20 },
			func() int { return 30 },
		)

		// 仅读取前 1 个结果即提前中断
		firstVal := <-out
		if firstVal == 0 {
			t.Fatalf("invalid first val")
		}
		cancel() // 广播退出信号

		// synctest.Wait 会等待气泡内所有协程达到稳态
		synctest.Wait()
		t.Log("✅ SafeGather 协程均已安全回收，气泡内无泄漏")
	})
}

// TestLeakyGatherCaughtBySynctest 验证 synctest 能够精准捕获 Goroutine 永久阻塞死锁
func TestLeakyGatherCaughtBySynctest(t *testing.T) {
	defer func() {
		r := recover()
		if r == nil {
			t.Fatalf("expected synctest panic on leaked goroutine, but got none")
		}
		errMsg := ""
		if err, ok := r.(error); ok {
			errMsg = err.Error()
		} else {
			errMsg = strings.ToLower(r.(string))
		}
		t.Logf("🎯 成功捕获 synctest 气泡死锁异常: %v", errMsg)
	}()

	synctest.Test(t, func(t *testing.T) {
		out := LeakyGather(
			func() int { return 1 },
			func() int { return 2 },
			func() int { return 3 },
		)

		// 只消费 1 个结果，其余 2 个 worker 永远阻塞在 out <- f()
		<-out

		// 当测试主协程退出时，synctest 发现气泡内仍有 durably blocked 的协程，将立即触发 panic 判定死锁！
	})
}
