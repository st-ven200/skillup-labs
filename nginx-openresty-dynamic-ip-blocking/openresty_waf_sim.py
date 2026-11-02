#!/usr/bin/env python3
"""
Lab 40: OpenResty + Lua + Redis 动态 IP 熔断与限流防护压测仿真
功能：
1. 真实时序仿真 OpenResty 接入层 WAF 判定逻辑
2. 内存状态机模拟 Redis 键空间 (INCR, EXPIRE, GET, SET) 与 TTL 过期淘汰
3. L1 进程内存与 L2 共享存储多级缓存加速仿真
4. 验证高频攻击阻断与自动恢复闭环，断言全部通过
"""
import time
from typing import Dict, Optional, Tuple

class MockRedisStore:
    def __init__(self):
        # key -> (value, expire_timestamp)
        self.data: Dict[str, Tuple[str, Optional[float]]] = {}

    def _purge_expired(self, key: str):
        if key in self.data:
            val, exp = self.data[key]
            if exp is not None and time.time() > exp:
                del self.data[key]

    def get(self, key: str) -> Optional[str]:
        self._purge_expired(key)
        if key in self.data:
            return self.data[key][0]
        return None

    def set(self, key: str, value: str, ex: Optional[float] = None):
        exp = time.time() + ex if ex else None
        self.data[key] = (str(value), exp)

    def incr(self, key: str) -> int:
        self._purge_expired(key)
        if key in self.data:
            val, exp = self.data[key]
            new_val = int(val) + 1
            self.data[key] = (str(new_val), exp)
            return new_val
        else:
            self.data[key] = ("1", None)
            return 1

    def expire(self, key: str, seconds: float):
        if key in self.data:
            val, _ = self.data[key]
            self.data[key] = (val, time.time() + seconds)

class OpenRestyWafSimulator:
    def __init__(self, ip_max_count: int = 3, ip_time_out: float = 1.0, ip_block_time: float = 3.0):
        self.ip_max_count = ip_max_count
        self.ip_time_out = ip_time_out
        self.ip_block_time = ip_block_time
        self.redis = MockRedisStore()
        self.l1_cache: Dict[str, float] = {}  # ip -> l1_expire
        self.whitelist = {"127.0.0.1", "10.0.0.88"}

    def handle_request(self, client_ip: str) -> Tuple[int, str]:
        # 1. 白名单前置放行
        if client_ip in self.whitelist:
            return 200, "WHITELIST_ALLOWED"

        now = time.time()
        # 2. L1 本地缓存
        if client_ip in self.l1_cache:
            if now < self.l1_cache[client_ip]:
                return 403, "L1_CACHE_BLOCKED"
            else:
                del self.l1_cache[client_ip]

        block_key = f"limit:block:{client_ip}"
        count_key = f"limit:count:{client_ip}"

        # 3. L2 Redis 黑名单
        is_blocked = self.redis.get(block_key)
        if is_blocked == "1":
            self.l1_cache[client_ip] = now + min(self.ip_block_time, 2.0)
            return 403, "L2_REDIS_BLOCKED"

        # 4. 滑动计数
        count = self.redis.incr(count_key)
        if count == 1:
            self.redis.expire(count_key, self.ip_time_out)

        # 5. 超限熔断
        if count > self.ip_max_count:
            self.redis.set(block_key, "1", ex=self.ip_block_time)
            self.l1_cache[client_ip] = now + min(self.ip_block_time, 2.0)
            return 403, "RATE_LIMIT_TRIGGERED"

        return 200, f"ALLOWED_COUNT_{count}"

def main():
    print("=" * 70)
    print("🚀 [Lab 40] OpenResty + Lua + Redis 动态 IP 熔断与限流防护压测")
    print("=" * 70)

    waf = OpenRestyWafSimulator(ip_max_count=3, ip_time_out=1.0, ip_block_time=2.0)
    print(f"[Config] 限流阈值: 1 秒内最多 3 次请求 | 熔断封禁时间: 2.0 秒")
    print(f"[Config] 白名单配置: {list(waf.whitelist)}")
    print("-" * 70)

    # Round 1: 白名单测试
    print("[Round 1] 测试白名单客户端请求 (IP: 10.0.0.88)")
    whitelist_codes = []
    for i in range(5):
        code, msg = waf.handle_request("10.0.0.88")
        whitelist_codes.append(code)
    print(f"  -> 连续发起 5 次高频请求...")
    print(f"  -> 响应状态: {whitelist_codes} (白名单 100% 豁免放行)")
    assert all(c == 200 for c in whitelist_codes), "白名单请求被错误拦截！"

    print("-" * 70)
    # Round 2: 恶意爬虫请求拦截测试
    crawler_ip = "198.51.100.23"
    print(f"[Round 2] 测试恶意爬虫客户端高频探测 (IP: {crawler_ip})")
    responses = []
    for i in range(1, 6):
        code, msg = waf.handle_request(crawler_ip)
        responses.append((code, msg))
        print(f"  -> 请求 #{i}: 结果: {code} ({msg})")

    assert responses[0][0] == 200, "第 1 次请求应被放行"
    assert responses[1][0] == 200, "第 2 次请求应被放行"
    assert responses[2][0] == 200, "第 3 次请求应被放行"
    assert responses[3][0] == 403, "第 4 次请求应触发熔断 403"
    assert responses[4][0] == 403, "第 5 次请求应被黑名单拦截 403"

    print("-" * 70)
    # Round 3: 自动解封机制测试
    print("[Round 3] 模拟时间窗口推进，验证自动解封自愈机制")
    print("  -> 正在等待 TTL (2.1s) 到期...")
    time.sleep(2.2)

    code_after_exp, msg_after_exp = waf.handle_request(crawler_ip)
    print(f"  -> 解封后再次发起请求 | 结果: {code_after_exp} ({msg_after_exp})")
    assert code_after_exp == 200, "封禁到期后请求未正常恢复放行！"

    print("=" * 70)
    print("🎉 [Lab 40] 核心断言校验全部通过！")
    print("=" * 70)

if __name__ == "__main__":
    main()
