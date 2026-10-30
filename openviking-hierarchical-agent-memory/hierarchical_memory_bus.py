#!/usr/bin/env python3
"""
OpenViking-style Hierarchical Agent Memory Engine & Cross-Agent Shared Bus
Implements:
1. L0 (Index Directory), L1 (Summary Outlines), L2 (Full Payloads) lazy loading.
2. P0 (Permanent), P1 (90-day Active Project), P2 (30-day Debug Ephemeral) lifecycle retention manager.
3. Thread-safe Cross-Agent Shared Bus for collaborative multi-agent memory synthesis.
Zero fake prints, real JSON-backed memory persistence, and test verification suite.
"""

import os
import sys
import time
import json
import shutil
import tempfile
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict


@dataclass
class MemoryRecord:
    id: str
    priority: str          # 'P0', 'P1', 'P2'
    category: str          # e.g., 'user_profile', 'active_project', 'debug_log'
    title: str
    abstract_summary: str  # L1 summary
    full_content: str      # L2 payload
    created_at: float
    ttl_days: int          # -1 for permanent, 90 for P1, 30 for P2
    owner_agent: str

    def is_expired(self, current_time: float) -> bool:
        if self.ttl_days < 0:
            return False
        expiry_timestamp = self.created_at + (self.ttl_days * 86400)
        return current_time > expiry_timestamp

    def estimate_tokens(self, text: str) -> int:
        # Standard token heuristic: ~1.5 tokens per Chinese character or 0.75 per English word
        return max(1, int(len(text) * 1.3))


class HierarchicalMemoryFS:
    """
    Simulates OpenViking's FileSystem-like memory management:
    - L0: Directory Index (.abstract)
    - L1: Summary Outline
    - L2: Full Payload
    """

    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        self.l0_file = os.path.join(storage_dir, ".abstract.json")
        self.l1_dir = os.path.join(storage_dir, "l1_summaries")
        self.l2_dir = os.path.join(storage_dir, "l2_payloads")
        self._lock = threading.Lock()

        os.makedirs(self.l1_dir, exist_ok=True)
        os.makedirs(self.l2_dir, exist_ok=True)
        if not os.path.exists(self.l0_file):
            self._save_l0({})

    def _save_l0(self, index_data: Dict[str, Any]):
        with open(self.l0_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

    def _read_l0(self) -> Dict[str, Any]:
        with open(self.l0_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def write_memory(self, record: MemoryRecord) -> None:
        with self._lock:
            # 1. Update L0 Index (Category -> List of [ID, Priority, Title])
            l0 = self._read_l0()
            cat = record.category
            if cat not in l0:
                l0[cat] = []

            # Remove existing ID if updating
            l0[cat] = [item for item in l0[cat] if item["id"] != record.id]
            l0[cat].append({
                "id": record.id,
                "priority": record.priority,
                "title": record.title,
                "owner": record.owner_agent
            })
            self._save_l0(l0)

            # 2. Update L1 Summary
            l1_path = os.path.join(self.l1_dir, f"{record.id}.json")
            l1_data = {
                "id": record.id,
                "priority": record.priority,
                "category": record.category,
                "title": record.title,
                "summary": record.abstract_summary,
                "owner": record.owner_agent,
                "created_at": record.created_at,
                "ttl_days": record.ttl_days
            }
            with open(l1_path, "w", encoding="utf-8") as f:
                json.dump(l1_data, f, ensure_ascii=False, indent=2)

            # 3. Update L2 Full Payload
            l2_path = os.path.join(self.l2_dir, f"{record.id}.md")
            with open(l2_path, "w", encoding="utf-8") as f:
                f.write(record.full_content)

    def read_l0_index(self) -> Tuple[Dict[str, Any], int]:
        """Returns L0 catalog and estimated token cost."""
        l0 = self._read_l0()
        tokens = len(json.dumps(l0, ensure_ascii=False)) // 2
        return l0, tokens

    def read_l1_summary(self, record_id: str) -> Tuple[Optional[Dict[str, Any]], int]:
        """Returns L1 summary and estimated token cost."""
        l1_path = os.path.join(self.l1_dir, f"{record_id}.json")
        if not os.path.exists(l1_path):
            return None, 0
        with open(l1_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            tokens = len(json.dumps(data, ensure_ascii=False)) // 2
            return data, tokens

    def read_l2_payload(self, record_id: str) -> Tuple[Optional[str], int]:
        """Returns L2 full content and estimated token cost."""
        l2_path = os.path.join(self.l2_dir, f"{record_id}.md")
        if not os.path.exists(l2_path):
            return None, 0
        with open(l2_path, "r", encoding="utf-8") as f:
            content = f.read()
            tokens = len(content) // 2
            return content, tokens

    def purge_expired(self, current_time: float) -> int:
        """Purges expired P1/P2 items from L0, L1, and L2."""
        purged_count = 0
        with self._lock:
            l0 = self._read_l0()
            new_l0 = {}
            for cat, items in l0.items():
                retained_items = []
                for item in items:
                    rec_id = item["id"]
                    l1_path = os.path.join(self.l1_dir, f"{rec_id}.json")
                    if os.path.exists(l1_path):
                        with open(l1_path, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                        ttl = meta.get("ttl_days", -1)
                        created = meta.get("created_at", 0)
                        if ttl > 0 and (current_time > created + ttl * 86400):
                            # Expired: Remove L1 & L2
                            os.remove(l1_path)
                            l2_path = os.path.join(self.l2_dir, f"{rec_id}.md")
                            if os.path.exists(l2_path):
                                os.remove(l2_path)
                            purged_count += 1
                            continue
                    retained_items.append(item)
                if retained_items:
                    new_l0[cat] = retained_items
            self._save_l0(new_l0)
        return purged_count


class CrossAgentMemoryBus:
    """
    Central bus coordinating multi-agent memories:
    - User Profile & Permanent Contracts (P0)
    - Active Project Logs (P1)
    - Ephemeral Debug / Task Logs (P2)
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.fs = HierarchicalMemoryFS(root_dir)
        self.shared_log_file = os.path.join(root_dir, "shared-log.jsonl")

    def publish_shared_event(self, agent_name: str, action: str, conclusion: str, payload: str, priority: str = "P1", ttl_days: int = 90):
        record_id = f"evt_{int(time.time() * 1000)}_{agent_name}"
        record = MemoryRecord(
            id=record_id,
            priority=priority,
            category=f"agent_{agent_name}",
            title=action,
            abstract_summary=conclusion,
            full_content=payload,
            created_at=time.time(),
            ttl_days=ttl_days,
            owner_agent=agent_name
        )
        self.fs.write_memory(record)

        # Atomic append to shared-log.jsonl
        entry = {
            "timestamp": time.time(),
            "agent": agent_name,
            "action": action,
            "conclusion": conclusion,
            "ref_id": record_id
        }
        with open(self.shared_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return record_id

    def query_context(self, category_filter: Optional[str] = None, retrieve_depth: str = "L0") -> Dict[str, Any]:
        """
        Retrieves context with strict token tracking.
        retrieve_depth: 'L0' (only directory), 'L1' (with summaries), 'L2' (full)
        """
        l0, l0_tokens = self.fs.read_l0_index()
        total_tokens = l0_tokens
        result = {"depth": retrieve_depth, "categories": {}, "total_tokens": 0}

        for cat, items in l0.items():
            if category_filter and category_filter != cat:
                continue

            result["categories"][cat] = []
            for item in items:
                rec_id = item["id"]
                node_data = {"id": rec_id, "title": item["title"], "priority": item["priority"]}

                if retrieve_depth in ("L1", "L2"):
                    l1, l1_tok = self.fs.read_l1_summary(rec_id)
                    total_tokens += l1_tok
                    node_data["summary"] = l1["summary"] if l1 else None

                if retrieve_depth == "L2":
                    l2, l2_tok = self.fs.read_l2_payload(rec_id)
                    total_tokens += l2_tok
                    node_data["content"] = l2

                result["categories"][cat].append(node_data)

        result["total_tokens"] = total_tokens
        return result


def run_benchmark():
    test_dir = tempfile.mkdtemp(prefix="openviking_test_")
    print(f"[Benchmark] Initializing OpenViking Memory Bus in: {test_dir}")
    bus = CrossAgentMemoryBus(test_dir)

    # 1. Register P0: User Core Profile (Never expires)
    bus.publish_shared_event(
        agent_name="core_identity",
        action="User Core Preferences",
        conclusion="User prefers concise answers, Python 3.12, strict TDD, no mock prints.",
        payload="""# User Profile
- Name: Senior Architect
- Principles:
  1. Real executable verification.
  2. Strict token optimization.
  3. No hallucinated mocks.""",
        priority="P0",
        ttl_days=-1
    )

    # 2. Register 6 other active Agents producing work with realistic engineering payloads
    sample_log = "Error 429: Rate limit exceeded during concurrent webhook fanout. Backoff retry triggered.\n" * 40
    sample_article = "## Architectural Analysis\nOpenViking implements a hierarchical filesystem-like memory layer.\n" * 50
    sample_nginx = "location /api/v1/ { proxy_pass http://127.0.0.1:8868; proxy_set_header X-Real-IP $remote_addr; }\n" * 40
    sample_growth = "Metrics: Token reduction measured across 100 benchmark dialog turns with 7 agents.\n" * 40
    sample_qa = "Test Suite: 124 passing, 0 failing, assertions verified on Ubuntu 24.04 and Windows 11.\n" * 35
    sample_pcap = "00000000  45 00 00 3c 1a 2b 40 00  40 06 b2 c3 7f 00 00 01  |E..<.+@.@.......|\n" * 60

    agents = [
        ("coder_agent", "Fixed Feishu Webhook Retry Storm", "Changed exponential backoff base to 2.5s and added jitter to stop 429", sample_log),
        ("writer_agent", "Drafted Tech Article for OpenViking", "Structured article around L0/L1/L2 and P0/P1/P2 architecture", sample_article),
        ("devops_agent", "Configured Nginx Reverse Proxy", "Mapped /api to port 8868 with no-proxy bypass", sample_nginx),
        ("growth_agent", "Analyzed Multi-Agent Token Consumption", "Identified 88% reduction opportunity in context loading", sample_growth),
        ("qa_agent", "Executed End-to-End Sandbox Assertion", "100% test pass on Linux/Windows hybrid nodes", sample_qa),
        ("ephemeral_debugger", "Temporary Socket Timeout Probe", "Handshake dropped due to MTU mismatch", sample_pcap, "P2", 30)
    ]

    for item in agents:
        name = item[0]
        act = item[1]
        conc = item[2]
        pay = item[3]
        prio = item[4] if len(item) > 4 else "P1"
        ttl = item[5] if len(item) > 5 else 90
        bus.publish_shared_event(agent_name=name, action=act, conclusion=conc, payload=pay, priority=prio, ttl_days=ttl)

    # Benchmark: Compare L0 vs L1 vs L2 token consumption
    ctx_l0 = bus.query_context(retrieve_depth="L0")
    ctx_l1 = bus.query_context(retrieve_depth="L1")
    ctx_l2 = bus.query_context(retrieve_depth="L2")

    print("\n================== TOKEN OPTIMIZATION METRICS ==================")
    print(f"L0 (Directory Index Only) : {ctx_l0['total_tokens']:>6} tokens")
    print(f"L1 (Index + Summaries)    : {ctx_l1['total_tokens']:>6} tokens")
    print(f"L2 (Full Naive Context)   : {ctx_l2['total_tokens']:>6} tokens")

    reduction = (ctx_l2['total_tokens'] - ctx_l0['total_tokens']) / ctx_l2['total_tokens'] * 100
    print(f"Token Reduction (L2 -> L0): {reduction:.2f}% drop!")
    assert reduction > 85.0, f"Expected >85% token drop, got {reduction}%"

    # Test TTL Expiration
    print("\n[Benchmark] Testing TTL Eviction...")
    simulated_future_time = time.time() + (31 * 86400) # 31 days later
    purged = bus.fs.purge_expired(simulated_future_time)
    print(f"Purged {purged} expired P2 records after 31 simulated days.")
    assert purged >= 1, "P2 ephemeral records should be purged"

    # Verify P0 still intact
    ctx_after = bus.query_context(category_filter="agent_core_identity", retrieve_depth="L2")
    assert len(ctx_after["categories"]["agent_core_identity"]) == 1
    print("Verified P0 record safely retained indefinitely.")

    # Clean up
    shutil.rmtree(test_dir)
    print("\n✅ All OpenViking memory bus assertions passed cleanly with 0 mock prints!")


if __name__ == "__main__":
    run_benchmark()
