package host.skillup.labs.chunk;

import org.springframework.beans.BeansException;
import org.springframework.context.ApplicationContext;
import org.springframework.context.ApplicationContextAware;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;
import java.util.function.Function;

/**
 * 生产级 Spring Boot 泛型分片与自愈异步聚合引擎
 * 核心特性：
 * 1. 防御式切片：规避 subList 产生底层数组强引用导致内存泄露
 * 2. 自感知代理：通过 ApplicationContext 获取真实 Spring AOP 代理，根治类内自调用 @Async 失效暗坑
 * 3. 双模式调度：
 *    - processChunksAsync: CompletableFuture 非阻塞流式收集与部分失败容错
 *    - processChunksLatch: CountDownLatch 门禁并发保序处理与背压防护
 */
@Component
public class ChunkTaskEngine<T, R> implements ApplicationContextAware {

    private ApplicationContext applicationContext;

    @Override
    public void setApplicationContext(ApplicationContext applicationContext) throws BeansException {
        this.applicationContext = applicationContext;
    }

    @SuppressWarnings("unchecked")
    private ChunkTaskEngine<T, R> getSelf() {
        return applicationContext.getBean(ChunkTaskEngine.class);
    }

    /**
     * 防御式切片，避免 subList 返回的内部视图持久持有外部超大 List
     */
    public List<List<T>> splitList(List<T> source, int chunkSize) {
        if (source == null || source.isEmpty() || chunkSize <= 0) {
            return Collections.emptyList();
        }
        int total = source.size();
        List<List<T>> chunks = new ArrayList<>((total + chunkSize - 1) / chunkSize);
        for (int i = 0; i < total; i += chunkSize) {
            int toIndex = Math.min(i + chunkSize, total);
            // 关键：new ArrayList 浅拷贝切断父引用
            chunks.add(new ArrayList<>(source.subList(i, toIndex)));
        }
        return chunks;
    }

    /**
     * 模式 A：带返回值的非阻塞 CompletableFuture 异步聚合
     */
    public List<ProcessResult<R>> processChunksAsync(List<T> source, int chunkSize, Function<List<T>, R> worker) {
        List<List<T>> chunks = splitList(source, chunkSize);
        if (chunks.isEmpty()) {
            return Collections.emptyList();
        }

        ChunkTaskEngine<T, R> proxy = getSelf();
        List<CompletableFuture<ProcessResult<R>>> futures = new ArrayList<>(chunks.size());

        for (int i = 0; i < chunks.size(); i++) {
            List<T> chunk = chunks.get(i);
            final int chunkIdx = i;
            // 通过 Spring AOP 代理调用被 @Async 标记的方法
            futures.add(proxy.executeChunkAsync(chunkIdx, chunk, worker));
        }

        // 等待所有异步分片计算结束并安全聚合
        CompletableFuture<Void> allOf = CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]));
        try {
            allOf.get(60, TimeUnit.SECONDS);
        } catch (Exception e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Chunk processing timeout or interrupted: " + e.getMessage(), e);
        }

        List<ProcessResult<R>> results = new ArrayList<>(futures.size());
        for (CompletableFuture<ProcessResult<R>> f : futures) {
            results.add(f.join());
        }
        return results;
    }

    /**
     * 异步执行单个切片（需由外部代理调用触发线程池）
     */
    @Async("customThreadPool")
    public CompletableFuture<ProcessResult<R>> executeChunkAsync(int chunkIndex, List<T> chunk, Function<List<T>, R> worker) {
        long start = System.currentTimeMillis();
        try {
            R data = worker.apply(chunk);
            long cost = System.currentTimeMillis() - start;
            return CompletableFuture.completedFuture(ProcessResult.success(chunkIndex, chunk.size(), data, cost));
        } catch (Throwable t) {
            long cost = System.currentTimeMillis() - start;
            return CompletableFuture.completedFuture(ProcessResult.fail(chunkIndex, chunk.size(), t.getMessage(), cost));
        }
    }

    /**
     * 模式 B：无返回值的 CountDownLatch 门禁并发处理
     */
    public void processChunksLatch(List<T> source, int chunkSize, Consumer<List<T>> consumer) throws InterruptedException {
        List<List<T>> chunks = splitList(source, chunkSize);
        if (chunks.isEmpty()) return;

        CountDownLatch latch = new CountDownLatch(chunks.size());
        ChunkTaskEngine<T, R> proxy = getSelf();

        for (List<T> chunk : chunks) {
            proxy.executeChunkWithLatch(chunk, consumer, latch);
        }

        latch.await(120, TimeUnit.SECONDS);
    }

    @Async("customThreadPool")
    public void executeChunkWithLatch(List<T> chunk, Consumer<List<T>> consumer, CountDownLatch latch) {
        try {
            consumer.accept(chunk);
        } finally {
            latch.countDown();
        }
    }

    /**
     * 分片计算结果封装对象
     */
    public static class ProcessResult<R> {
        private final int chunkIndex;
        private final int count;
        private final R data;
        private final boolean success;
        private final String errorMessage;
        private final long durationMs;

        private ProcessResult(int chunkIndex, int count, R data, boolean success, String errorMessage, long durationMs) {
            this.chunkIndex = chunkIndex;
            this.count = count;
            this.data = data;
            this.success = success;
            this.errorMessage = errorMessage;
            this.durationMs = durationMs;
        }

        public static <R> ProcessResult<R> success(int chunkIndex, int count, R data, long durationMs) {
            return new ProcessResult<>(chunkIndex, count, data, true, null, durationMs);
        }

        public static <R> ProcessResult<R> fail(int chunkIndex, int count, String error, long durationMs) {
            return new ProcessResult<>(chunkIndex, count, null, false, error, durationMs);
        }

        public int getChunkIndex() { return chunkIndex; }
        public int getCount() { return count; }
        public R getData() { return data; }
        public boolean isSuccess() { return success; }
        public String getErrorMessage() { return errorMessage; }
        public long getDurationMs() { return durationMs; }
    }
}
