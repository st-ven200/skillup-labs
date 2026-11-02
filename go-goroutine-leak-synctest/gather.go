package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// LeakyGather 并发执行多个任务并通过无缓冲 channel 收集结果
// 存在经典泄露缺陷：当接收方提前退出或发生 panic 时，剩余 worker 协程永久阻塞在 channel 发送端
func LeakyGather(tasks ...func() int) <-chan int {
	out := make(chan int) // 无缓冲 channel
	for _, task := range tasks {
		go func(f func() int) {
			out <- f() // 接收方若不消费，此处永久挂起，Goroutine 彻底泄露！
		}(task)
	}
	return out
}

// SafeGather 修复版并发汇聚引擎
// 1. 采用带取消信号的 Context 控制生命周期
// 2. 使用带有任务容量的缓冲 Channel 或结合 select default 防止发送死锁
// 3. 使用 sync.WaitGroup 确保所有协程受控收敛
func SafeGather(ctx context.Context, tasks ...func() int) <-chan int {
	out := make(chan int, len(tasks)) // 缓冲 channel 防阻塞
	var wg sync.WaitGroup

	for _, task := range tasks {
		wg.Add(1)
		go func(f func() int) {
			defer wg.Done()
			result := f()
			select {
			case out <- result:
			case <-ctx.Done():
				// 收到上下文退出信号，安全回收协程
			}
		}(task)
	}

	// 异步等待所有 worker 结束后安全关闭 channel
	go func() {
		wg.Wait()
		close(out)
	}()

	return out
}

// LongRunningHeartbeat 模拟需要耗时等待的心跳任务
func LongRunningHeartbeat(d time.Duration) string {
	time.Sleep(d)
	return fmt.Sprintf("heartbeat completed after %v", d)
}
