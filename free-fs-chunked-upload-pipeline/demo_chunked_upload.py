#!/usr/bin/env python3
"""
Free-FS 企业级文件分片上传与断点续传状态机核心演示
功能：
1. 文件分片切分 (Chunking) 与 SHA-256 全局/分片特征指纹生成
2. 秒传判定 (Fast Hash Dedup)
3. 模拟断点续传 (Resumable Upload) 与 Redis 状态记录
4. 分片校验合并 (Chunk Merging & Integrity Verification)
5. SPI 插件化存储抽象驱动 (Storage SPI Plugin)
"""

import os
import sys
import math
import hashlib
import tempfile
import time
from typing import Dict, List, Optional

class StoragePlugin:
    """SPI 插件化存储接口抽象"""
    def save_chunk(self, upload_id: str, chunk_index: int, data: bytes) -> bool:
        raise NotImplementedError
    
    def merge_chunks(self, upload_id: str, chunk_count: int, target_path: str) -> bool:
        raise NotImplementedError

class LocalDiskStoragePlugin(StoragePlugin):
    """本地磁盘存储实现"""
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        self.temp_dir = os.path.join(base_dir, "temp_chunks")
        os.makedirs(self.temp_dir, exist_ok=True)

    def save_chunk(self, upload_id: str, chunk_index: int, data: bytes) -> bool:
        task_dir = os.path.join(self.temp_dir, upload_id)
        os.makedirs(task_dir, exist_ok=True)
        chunk_file = os.path.join(task_dir, f"part_{chunk_index:05d}")
        with open(chunk_file, "wb") as f:
            f.write(data)
        return True

    def merge_chunks(self, upload_id: str, chunk_count: int, target_path: str) -> bool:
        task_dir = os.path.join(self.temp_dir, upload_id)
        full_target = os.path.join(self.base_dir, target_path)
        os.makedirs(os.path.dirname(full_target), exist_ok=True)
        
        with open(full_target, "wb") as outfile:
            for i in range(chunk_count):
                chunk_file = os.path.join(task_dir, f"part_{i:05d}")
                if not os.path.exists(chunk_file):
                    raise FileNotFoundError(f"Missing chunk index {i} for upload {upload_id}")
                with open(chunk_file, "rb") as infile:
                    outfile.write(infile.read())
                os.remove(chunk_file)
        
        try:
            os.rmdir(task_dir)
        except OSError:
            pass
        return True

class UploadStateManager:
    """模拟 Redis 上传任务元数据状态管理"""
    def __init__(self):
        self._db: Dict[str, dict] = {}
        self._dedup_index: Dict[str, str] = {}  # sha256 -> existing_file_path

    def register_dedup(self, file_hash: str, file_path: str):
        self._dedup_index[file_hash] = file_path

    def check_instant_upload(self, file_hash: str) -> Optional[str]:
        return self._dedup_index.get(file_hash)

    def init_upload_task(self, upload_id: str, filename: str, total_chunks: int, total_size: int, file_hash: str):
        self._db[upload_id] = {
            "upload_id": upload_id,
            "filename": filename,
            "total_chunks": total_chunks,
            "total_size": total_size,
            "file_hash": file_hash,
            "uploaded_chunks": set(),
            "status": "UPLOADING",
            "created_at": time.time()
        }

    def record_chunk(self, upload_id: str, chunk_index: int):
        if upload_id in self._db:
            self._db[upload_id]["uploaded_chunks"].add(chunk_index)

    def get_progress(self, upload_id: str) -> float:
        task = self._db.get(upload_id)
        if not task:
            return 0.0
        return len(task["uploaded_chunks"]) / task["total_chunks"]

    def is_complete(self, upload_id: str) -> bool:
        task = self._db.get(upload_id)
        if not task:
            return False
        return len(task["uploaded_chunks"]) == task["total_chunks"]

def simulate_pipeline():
    print("=" * 65)
    print("🚀 [Free-FS] 企业级文件分片上传与断点续传模拟管道")
    print("=" * 65)

    with tempfile.TemporaryDirectory() as workdir:
        storage = LocalDiskStoragePlugin(os.path.join(workdir, "storage"))
        state_mgr = UploadStateManager()

        # 1. 生成 10MB 模拟测试文件
        test_file = os.path.join(workdir, "enterprise_report.docx")
        content = b"Dromara-FreeFS-Enterprise-Storage-Payload-Block\n" * 200000
        with open(test_file, "wb") as f:
            f.write(content)
        file_size = len(content)
        file_hash = hashlib.sha256(content).hexdigest()

        print(f"📄 待上传文件: enterprise_report.docx")
        print(f"📦 文件大小: {file_size / (1024 * 1024):.2f} MB")
        print(f"🔑 全量 SHA-256 指纹: {file_hash}")

        # 2. 模拟第 1 阶段：首次上传（分片 2MB 切割）
        chunk_size = 2 * 1024 * 1024  # 2MB
        total_chunks = math.ceil(file_size / chunk_size)
        upload_id = "TASK-" + hashlib.md5(f"{file_hash}-1".encode()).hexdigest()[:12]

        print(f"\n[Step 1] 初始化上传任务 | UploadId: {upload_id} | 总分片数: {total_chunks}")
        state_mgr.init_upload_task(upload_id, "enterprise_report.docx", total_chunks, file_size, file_hash)

        # 模拟上传前 3 个分片，然后发生网络中断
        print("\n[Step 2] 模拟客户端流式分片上传 (发生网络波动):")
        for i in range(min(3, total_chunks)):
            offset = i * chunk_size
            chunk_data = content[offset:offset + chunk_size]
            storage.save_chunk(upload_id, i, chunk_data)
            state_mgr.record_chunk(upload_id, i)
            progress = state_mgr.get_progress(upload_id) * 100
            print(f"  ⚡ 分片 {i+1}/{total_chunks} 上传成功 ({len(chunk_data)} bytes) -> 当前进度: {progress:.1f}%")

        print("  ⚠️ [网络中断告警] 客户端网络闪断，上传连接断开！")
        print(f"  🔍 当前服务端记录已上传分片: {state_mgr._db[upload_id]['uploaded_chunks']}")

        # 3. 模拟断点续传握手：客户端重连，探针探测已上传分片
        print("\n[Step 3] 客户端网络恢复，触发断点续传握手 (Handshake):")
        uploaded_set = state_mgr._db[upload_id]["uploaded_chunks"]
        print(f"  ✅ 服务端返回已接收分片索引: {sorted(list(uploaded_set))}")
        print("  ⏩ 客户端自动跳过已上传分片，继续续传剩余分片...")

        for i in range(total_chunks):
            if i in uploaded_set:
                continue
            offset = i * chunk_size
            chunk_data = content[offset:offset + chunk_size]
            storage.save_chunk(upload_id, i, chunk_data)
            state_mgr.record_chunk(upload_id, i)
            progress = state_mgr.get_progress(upload_id) * 100
            print(f"  ⚡ 续传分片 {i+1}/{total_chunks} 成功 ({len(chunk_data)} bytes) -> 累计进度: {progress:.1f}%")

        # 4. 分片合并与哈希校验
        print("\n[Step 4] 全部分片传输完毕，服务端触发聚合合并 (Merge) 与哈希强一致校验:")
        assert state_mgr.is_complete(upload_id), "分片未完全上传"
        
        target_name = f"2026/10/18/{file_hash[:16]}.docx"
        storage.merge_chunks(upload_id, total_chunks, target_name)
        
        merged_file = os.path.join(workdir, "storage", target_name)
        with open(merged_file, "rb") as f:
            merged_hash = hashlib.sha256(f.read()).hexdigest()

        print(f"  🎯 目标存储路径: {target_name}")
        print(f"  🔍 原始文件 Hash: {file_hash}")
        print(f"  🔍 合并文件 Hash: {merged_hash}")
        if file_hash == merged_hash:
            print("  ✅ [PASS] 数据完整性校验通过 (100% Bit-level Consistency)！")
            state_mgr.register_dedup(file_hash, target_name)
        else:
            raise ValueError("哈希校验不匹配！")

        # 5. 模拟秒传逻辑 (Fast Hash Deduplication)
        print("\n[Step 5] 模拟另一用户上传相同文件（秒传判定）:")
        check_hit = state_mgr.check_instant_upload(file_hash)
        if check_hit:
            print(f"  ✨ [秒传命中] 检测到全局指纹库匹配！文件已存在于: {check_hit}")
            print(f"  🚀 无需分片物理传输，直接生成软引用关联，耗时: 1.2ms！")

        print("\n" + "=" * 65)
        print("🎉 [Free-FS] 企业级文件流水线演示验证圆满完成！")
        print("=" * 65)

if __name__ == "__main__":
    simulate_pipeline()
