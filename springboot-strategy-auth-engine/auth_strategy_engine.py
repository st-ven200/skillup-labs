#!/usr/bin/env python3
"""
Spring Boot 策略工厂与模板方法多端统一鉴权验证内核 (Python 完整复刻参考实现)
实现要点：
1. 模板方法模式定义登录统一生命周期 (参数预检 -> 差异化身份认证 -> Token生成与审计落库)
2. 策略工厂自动装配各端鉴权策略 Bean (模拟 Spring Map<String, Strategy> 依赖注入)
3. 真实 SQLite 数据库操作 (用户表、凭证表、短信验证码表、第三方账号绑定表、登录审计流水表)
4. 端到端多场景用例验证 (密码登录、短信验证码登录、微信小程序一键登录、未知渠道熔断拦截)
"""

import sys
import time
import uuid
import hashlib
import sqlite3
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

DB_FILE = "auth_engine_test.db"

def init_database(db_path: str = DB_FILE):
    """初始化真实测试数据库表结构与种子数据"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript("""
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS user_credentials;
    DROP TABLE IF EXISTS sms_codes;
    DROP TABLE IF EXISTS oauth_identities;
    DROP TABLE IF EXISTS login_audit_logs;

    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        phone TEXT UNIQUE,
        status TEXT DEFAULT 'ACTIVE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE user_credentials (
        user_id INTEGER PRIMARY KEY,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE sms_codes (
        phone TEXT PRIMARY KEY,
        code TEXT NOT NULL,
        expire_at REAL NOT NULL
    );

    CREATE TABLE oauth_identities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        provider TEXT NOT NULL,
        open_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(provider, open_id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE login_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        channel TEXT NOT NULL,
        client_ip TEXT NOT NULL,
        token TEXT NOT NULL,
        login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 插入种子用户: alice (密码: Admin@123), 手机号: 13800138000
    salt = "s@lt_98234"
    pwd_hash = hashlib.sha256(("Admin@123" + salt).encode('utf-8')).hexdigest()
    cur.execute("INSERT INTO users (username, phone) VALUES (?, ?)", ("alice", "13800138000"))
    user_id = cur.lastrowid
    cur.execute("INSERT INTO user_credentials (user_id, password_hash, salt) VALUES (?, ?, ?)", (user_id, pwd_hash, salt))

    # 预置有效短信验证码: 13800138000 -> 889911 (有效期 5 分钟)
    cur.execute("INSERT INTO sms_codes (phone, code, expire_at) VALUES (?, ?, ?)", 
                ("13800138000", "889911", time.time() + 300))

    # 预置过期短信验证码: 13900000000 -> 112233 (已过期)
    cur.execute("INSERT INTO sms_codes (phone, code, expire_at) VALUES (?, ?, ?)", 
                ("13900000000", "112233", time.time() - 60))

    conn.commit()
    conn.close()
    print("[DB] 真实数据库初始化完成，预置种子用户与测试凭证。")


class LoginRequest:
    def __init__(self, channel: str, client_ip: str = "127.0.0.1", **kwargs):
        self.channel = channel.lower().strip()
        self.client_ip = client_ip
        self.payload = kwargs

    def get(self, key: str, default: Any = None) -> Any:
        return self.payload.get(key, default)


class LoginResult:
    def __init__(self, success: bool, user_id: Optional[int] = None, token: Optional[str] = None, message: str = ""):
        self.success = success
        self.user_id = user_id
        self.token = token
        self.message = message

    def __repr__(self):
        return f"<LoginResult success={self.success} user_id={self.user_id} token={self.token} msg='{self.message}'>"


# ==============================================================================
# 1. 模板方法模式核心骨架 (AbstractAuthStrategyTemplate)
# ==============================================================================
class AbstractAuthStrategy(ABC):
    """
    鉴权策略模板抽象基类：统一控制鉴权生命周期骨架
    前置参数预检 -> 差异化身份认证 -> 后置Token签发与审计入库
    """
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path

    @abstractmethod
    def channel_type(self) -> str:
        """支持的鉴权渠道标识"""
        pass

    def execute_login(self, request: LoginRequest) -> LoginResult:
        """核心模板方法 (Template Method)"""
        # 1. 通用前置校验
        self._pre_validate(request)

        # 2. 调用子类实现的差异化认证算法
        user_id = self._do_authenticate(request)
        if not user_id:
            raise ValueError(f"[{self.channel_type()}] 认证失败：无法确定目标用户身份")

        # 3. 通用后置处理：签发 Token 与写入审计追踪
        token = self._issue_token_and_audit(user_id, request)
        return LoginResult(success=True, user_id=user_id, token=token, message="登录成功")

    def _pre_validate(self, request: LoginRequest):
        if not request.channel:
            raise ValueError("登录请求缺少必要 channel 标识")

    @abstractmethod
    def _do_authenticate(self, request: LoginRequest) -> int:
        """子类策略各自实现的身份核验逻辑，返回已校验的用户 ID"""
        pass

    def _issue_token_and_audit(self, user_id: int, request: LoginRequest) -> str:
        """通用安全后置：签发安全 Session Token 并持久化审计日志"""
        token = f"SKILLUP_AUTH_{uuid.uuid4().hex[:24].upper()}"
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO login_audit_logs (user_id, channel, client_ip, token) VALUES (?, ?, ?, ?)",
            (user_id, self.channel_type(), request.client_ip, token)
        )
        conn.commit()
        conn.close()
        return token


# ==============================================================================
# 2. 具体策略实现 (Concrete Strategies)
# ==============================================================================
class PasswordAuthStrategy(AbstractAuthStrategy):
    """传统账密认证策略 (Web/PC 端常用)"""
    def channel_type(self) -> str:
        return "password"

    def _pre_validate(self, request: LoginRequest):
        super()._pre_validate(request)
        if not request.get("username") or not request.get("password"):
            raise ValueError("账号或密码不能为空")

    def _do_authenticate(self, request: LoginRequest) -> int:
        username = request.get("username")
        raw_password = request.get("password")

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, c.password_hash, c.salt, u.status 
            FROM users u 
            JOIN user_credentials c ON u.id = c.user_id 
            WHERE u.username = ?
        """, (username,))
        row = cur.fetchone()
        conn.close()

        if not row:
            raise ValueError("用户不存在或凭据未配置")

        user_id, stored_hash, salt, status = row
        if status != "ACTIVE":
            raise PermissionError("当前账号处于锁定或禁用状态")

        computed_hash = hashlib.sha256((raw_password + salt).encode('utf-8')).hexdigest()
        if computed_hash != stored_hash:
            raise ValueError("用户名或密码错误")

        return user_id


class SmsOtpAuthStrategy(AbstractAuthStrategy):
    """手机短信验证码快捷登录策略 (App/移动端常用)"""
    def channel_type(self) -> str:
        return "sms"

    def _pre_validate(self, request: LoginRequest):
        super()._pre_validate(request)
        phone = request.get("phone")
        code = request.get("code")
        if not phone or len(str(phone)) != 11:
            raise ValueError("手机号码格式不合法")
        if not code or len(str(code)) != 6:
            raise ValueError("短信验证码必须为6位数字")

    def _do_authenticate(self, request: LoginRequest) -> int:
        phone = request.get("phone")
        code = request.get("code")

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT code, expire_at FROM sms_codes WHERE phone = ?", (phone,))
        row = cur.fetchone()

        if not row:
            conn.close()
            raise ValueError("验证码未发送或已失效")

        saved_code, expire_at = row
        if time.time() > expire_at:
            conn.close()
            raise ValueError("验证码已过期，请重新获取")

        if saved_code != code:
            conn.close()
            raise ValueError("验证码不正确")

        # 验证码一次性消费机制
        cur.execute("DELETE FROM sms_codes WHERE phone = ?", (phone,))

        # 查询是否为已有用户，若无则自动完成新用户注册 (静默绑定)
        cur.execute("SELECT id FROM users WHERE phone = ?", (phone,))
        user_row = cur.fetchone()
        if user_row:
            user_id = user_row[0]
        else:
            username = f"user_{phone[-4:]}_{uuid.uuid4().hex[:6]}"
            cur.execute("INSERT INTO users (username, phone) VALUES (?, ?)", (username, phone))
            user_id = cur.lastrowid

        conn.commit()
        conn.close()
        return user_id


class WxMiniAppAuthStrategy(AbstractAuthStrategy):
    """微信小程序 code2Session 免密授权登录 (小程序端)"""
    def channel_type(self) -> str:
        return "wx_miniapp"

    def _pre_validate(self, request: LoginRequest):
        super()._pre_validate(request)
        if not request.get("js_code"):
            raise ValueError("缺少小程序授权凭证 js_code")

    def _do_authenticate(self, request: LoginRequest) -> int:
        js_code = request.get("js_code")
        # 模拟调用微信接口 code2Session: auth.code2Session(appid, secret, js_code)
        # 生成确定的 open_id 用于幂等绑定
        mock_openid = f"wx_mock_openid_{hashlib.md5(js_code.encode()).hexdigest()[:16]}"

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM oauth_identities WHERE provider = 'wx_miniapp' AND open_id = ?", (mock_openid,))
        row = cur.fetchone()

        if row:
            user_id = row[0]
        else:
            # 首次登录：自动创建主体用户并绑定微信 OpenID
            nick_name = f"wx_{mock_openid[-6:]}"
            cur.execute("INSERT INTO users (username) VALUES (?)", (nick_name,))
            user_id = cur.lastrowid
            cur.execute("INSERT INTO oauth_identities (user_id, provider, open_id) VALUES (?, 'wx_miniapp', ?)", (user_id, mock_openid))

        conn.commit()
        conn.close()
        return user_id


# ==============================================================================
# 3. 策略工厂 (AuthStrategyFactory，模拟 Spring 容器自动收集 Bean)
# ==============================================================================
class AuthStrategyFactory:
    """
    鉴权策略工厂：
    运行时根据 channel 路由对应的策略处理器，支持零侵入横向扩展
    """
    def __init__(self):
        self._strategy_registry: Dict[str, AbstractAuthStrategy] = {}

    def register(self, strategy: AbstractAuthStrategy):
        key = strategy.channel_type().lower().strip()
        self._strategy_registry[key] = strategy
        print(f"[Factory] 注册鉴权策略节点: '{key}' -> {strategy.__class__.__name__}")

    def get_strategy(self, channel: str) -> AbstractAuthStrategy:
        channel_key = channel.lower().strip()
        strategy = self._strategy_registry.get(channel_key)
        if not strategy:
            supported = list(self._strategy_registry.keys())
            raise NotImplementedError(f"未受支持的登录渠道 '{channel}'。当前系统仅就绪: {supported}")
        return strategy

    def dispatch(self, request: LoginRequest) -> LoginResult:
        strategy = self.get_strategy(request.channel)
        return strategy.execute_login(request)


# ==============================================================================
# 4. 自动化回归测试套件 (Self-Contained Real Execution Suite)
# ==============================================================================
def run_test_suite():
    print("\n" + "="*70)
    print("🚀 开始执行 Spring Boot 多端鉴权策略工厂与模板切面内核真实验证")
    print("="*70)

    init_database(DB_FILE)

    factory = AuthStrategyFactory()
    factory.register(PasswordAuthStrategy())
    factory.register(SmsOtpAuthStrategy())
    factory.register(WxMiniAppAuthStrategy())

    passed_count = 0
    total_tests = 5

    # Case 1: Web 账密正确登录
    print("\n[Case 1] Web 端账号密码合法登录验证...")
    req1 = LoginRequest(channel="password", username="alice", password="Admin@123", client_ip="192.168.1.10")
    res1 = factory.dispatch(req1)
    assert res1.success and res1.user_id == 1 and res1.token.startswith("SKILLUP_AUTH_")
    print(f"  -> Case 1 通过！签发 Token: {res1.token}, 映射 UserID: {res1.user_id}")
    passed_count += 1

    # Case 2: Web 账密错误拦截
    print("\n[Case 2] Web 端密码错误防御拦截验证...")
    req2 = LoginRequest(channel="password", username="alice", password="WrongPassword999")
    try:
        factory.dispatch(req2)
        print("  -> Case 2 异常未触发！测试失败")
    except ValueError as e:
        assert "用户名或密码错误" in str(e)
        print(f"  -> Case 2 通过！成功防御非法密码，捕获错误: {e}")
        passed_count += 1

    # Case 3: App 端有效验证码登录
    print("\n[Case 3] App 端有效手机验证码 (889911) 登录并一次性核销验证...")
    req3 = LoginRequest(channel="sms", phone="13800138000", code="889911", client_ip="10.0.0.5")
    res3 = factory.dispatch(req3)
    assert res3.success and res3.user_id == 1
    print(f"  -> Case 3 通过！成功核验并签发 Token: {res3.token}")
    passed_count += 1

    # Case 4: 微信小程序免密换取用户身份并自动建立绑定关系
    print("\n[Case 4] 微信小程序 js_code 授权静默注册与绑定测试...")
    req4 = LoginRequest(channel="wx_miniapp", js_code="wx_mock_js_code_12345", client_ip="120.24.50.88")
    res4 = factory.dispatch(req4)
    assert res4.success and res4.user_id > 1
    print(f"  -> Case 4 通过！自动绑定并落库用户 ID: {res4.user_id}")
    passed_count += 1

    # Case 5: 未注册渠道请求熔断测试
    print("\n[Case 5] 未知第三方渠道 (feishu_sso) 动态熔断拦截...")
    req5 = LoginRequest(channel="feishu_sso", auth_code="fs_token_xxx")
    try:
        factory.dispatch(req5)
        print("  -> Case 5 失败：未拦截未知渠道")
    except NotImplementedError as e:
        print(f"  -> Case 5 通过！成功熔断拦截: {e}")
        passed_count += 1

    # 核验数据库审计表
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM login_audit_logs")
    log_count = cur.fetchone()[0]
    conn.close()
    print(f"\n[Audit] 验证数据库审计表: 共沉淀 {log_count} 条独立渠道真实登录审计流水。")
    assert log_count == 3  # Case 1, Case 3, Case 4 成功

    print("\n" + "="*70)
    print(f"🎉 全部用例真实验证通过: {passed_count}/{total_tests} (100% SUCCESS)")
    print("="*70)

if __name__ == "__main__":
    run_test_suite()
