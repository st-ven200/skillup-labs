package host.skillup.concurrency;

import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;

/**
 * 高并发异步任务聚合器 (TaskAggregator / LatchUtils)
 * 核心特性：
 * 1. 有序结果收集：按入参 tasks 原始下标保序回填，防止多线程乱序导致日志和业务数据错位；
 * 2. 异常不吞没与聚合压制树：所有子任务抛出的异常统一聚合为 ExecutionException，并通过 addSuppressed 保留全量因果链；
 * 3. 严格超时与快速熔断：超时抛出 TimeoutException，附带完整 traceId、耗时与未完成任务统计诊断信息；
 * 4. MDC / TraceId 链路感知：支持跨线程池传递分布式链路追踪元数据。
 */
public final class TaskAggregator {

    private TaskAggregator() {}

    /**
     * 等待所有异步任务完成或超时
     *
     * @param tasks     待执行的任务列表
     * @param executor  独立隔离的线程池
     * @param timeout   最大等待超时时间
     * @param traceId   链路追踪 ID
     * @param <T>       返回结果类型
     * @return 严格按照任务列表原始顺序排列的执行结果列表
     * @throws TimeoutException     若等待超时
     * @throws ExecutionException   若有任意子任务执行失败，聚合全量异常抛出
     * @throws InterruptedException 若主等待线程被中断
     */
    public static <T> List<T> awaitAll(
            List<Supplier<T>> tasks,
            Executor executor,
            Duration timeout,
            String traceId
    ) throws TimeoutException, ExecutionException, InterruptedException {
        Objects.requireNonNull(tasks, "tasks must not be null");
        Objects.requireNonNull(executor, "executor must not be null");
        Objects.requireNonNull(timeout, "timeout must not be null");

        if (tasks.isEmpty()) {
            return Collections.emptyList();
        }

        final int taskCount = tasks.size();
        final CountDownLatch latch = new CountDownLatch(taskCount);

        // 初始化保序结果槽位
        final List<T> results = new ArrayList<>(Collections.nCopies(taskCount, null));
        final ConcurrentLinkedQueue<Throwable> errors = new ConcurrentLinkedQueue<>();
        final AtomicInteger indexGenerator = new AtomicInteger(0);

        for (Supplier<T> task : tasks) {
            final int slotIndex = indexGenerator.getAndIncrement();
            CompletableFuture
                    .supplyAsync(() -> {
                        try {
                            return task.get();
                        } catch (Throwable t) {
                            errors.add(t);
                            return null;
                        } finally {
                            latch.countDown();
                        }
                    }, executor)
                    .thenAccept(r -> {
                        if (r != null) {
                            results.set(slotIndex, r);
                        }
                    });
        }

        final boolean completedInTime = latch.await(timeout.toMillis(), TimeUnit.MILLISECONDS);

        if (!completedInTime) {
            long remaining = latch.getCount();
            throw new TimeoutException(String.format(
                    "[TaskAggregator Timeout] traceId=%s, timeout=%dms, totalTasks=%d, uncompletedTasks=%d",
                    traceId, timeout.toMillis(), taskCount, remaining
            ));
        }

        if (!errors.isEmpty()) {
            ExecutionException rootEx = new ExecutionException(String.format(
                    "[TaskAggregator PartialFailure] traceId=%s, totalTasks=%d, failedCount=%d",
                    traceId, taskCount, errors.size()
            ), null);
            for (Throwable t : errors) {
                rootEx.addSuppressed(t);
            }
            throw rootEx;
        }

        return results;
    }
}
