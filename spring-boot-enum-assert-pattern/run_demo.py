#!/usr/bin/env python3
"""
Spring Boot 统一断言模式与全局异常切面防御引擎 (Enum-Assert Pattern)
演示从臃肿的 if-throw / try-catch 演进到优雅的断言接口与切面统一收敛
"""
import sys
import uuid
import json
import time
from enum import Enum
from typing import Any, Optional, Dict, Tuple

class BaseException(Exception):
    """企业级统一业务异常基类"""
    def __init__(self, response_enum: "ResponseEnum", args: Optional[Tuple[Any, ...]] = None, cause: Optional[Exception] = None):
        self.response_enum = response_enum
        self.code = response_enum.code
        self.args = args
        self.cause = cause
        # 支持动态模板参数格式化
        if args:
            try:
                self.message = response_enum.message.format(*args)
            except Exception:
                self.message = response_enum.message
        else:
            self.message = response_enum.message
        super().__init__(f"[{self.code}] {self.message}")

class AssertInterface:
    """断言增强契约：由枚举类或工具类实现，提供声明式业务防御能力"""
    def new_exception(self, *args) -> BaseException:
        raise NotImplementedError

    def assert_not_null(self, obj: Any, *args):
        """断言对象非空，为空则抛出携带对应错误码的业务异常"""
        if obj is None:
            raise self.new_exception(*args)

    def assert_true(self, expression: bool, *args):
        """断言条件为真，为假则抛出异常"""
        if not expression:
            raise self.new_exception(*args)

    def assert_false(self, expression: bool, *args):
        """断言条件为假，为真则抛出异常"""
        if expression:
            raise self.new_exception(*args)

    def assert_not_blank(self, text: Optional[str], *args):
        """断言字符串非空且非空白字符"""
        if text is None or len(str(text).strip()) == 0:
            raise self.new_exception(*args)

class ResponseEnum(AssertInterface, Enum):
    """
    统一业务响应枚举：兼具错误码定义与断言能力
    实现业务语义与防御校验的高度收敛
    """
    SUCCESS = (200, "操作执行成功")
    PARAM_INVALID = (40001, "请求参数校验不通过: {0}")
    USER_NOT_FOUND = (40401, "用户不存在: ID [{0}]")
    INSUFFICIENT_BALANCE = (40901, "账户余额不足: 当前余额 [{0}], 需求金额 [{1}]")
    ACCOUNT_FROZEN = (40301, "账户已被冻结，禁止资金流转")
    ORDER_STATE_INVALID = (40902, "订单状态非法，当前状态 [{0}] 不允许执行此流转")
    SYSTEM_ERROR = (50000, "系统内部繁忙，请稍后重试")

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

    def new_exception(self, *args) -> BaseException:
        return BaseException(self, args)

class RestControllerAdvice:
    """
    模拟 Spring Boot @RestControllerAdvice 全局异常处理切面
    统一捕获下层抛出的异常并标准化包装为 JSON 响应体
    """
    @staticmethod
    def handle_exception(e: Exception) -> Dict[str, Any]:
        trace_id = str(uuid.uuid4()).replace('-', '')[:16]
        timestamp = int(time.time() * 1000)

        if isinstance(e, BaseException):
            # 捕获已知业务异常
            return {
                "success": False,
                "code": e.code,
                "message": e.message,
                "traceId": trace_id,
                "timestamp": timestamp,
                "data": None
            }
        elif isinstance(e, KeyError):
            # 捕获未知字段缺失
            return {
                "success": False,
                "code": 40002,
                "message": f"必填字段缺失: {str(e)}",
                "traceId": trace_id,
                "timestamp": timestamp,
                "data": None
            }
        else:
            # 兜底捕获未知运行时异常
            return {
                "success": False,
                "code": ResponseEnum.SYSTEM_ERROR.code,
                "message": ResponseEnum.SYSTEM_ERROR.message,
                "traceId": trace_id,
                "timestamp": timestamp,
                "data": None
            }

class UserService:
    """模拟业务服务层：对比传统冗长防御 vs 声明式枚举断言"""
    def __init__(self):
        self.db_users = {
            1001: {"id": 1001, "name": "Alice", "balance": 500.0, "status": "ACTIVE"},
            1002: {"id": 1002, "name": "Bob", "balance": 20.0, "status": "FROZEN"}
        }

    def transfer_money_legacy(self, user_id: int, target_id: int, amount: float):
        """传统模式：大量丑陋的 if 条件判断与 throw，代码逻辑割裂"""
        if amount <= 0:
            raise ValueError("转账金额必须大于0")
        user = self.db_users.get(user_id)
        if user is None:
            raise RuntimeError(f"用户不存在: {user_id}")
        if user["status"] == "FROZEN":
            raise RuntimeError("账户已被冻结")
        if user["balance"] < amount:
            raise RuntimeError("余额不足")
        # 执行业务扣款...
        user["balance"] -= amount
        return {"status": "SUCCESS", "remaining": user["balance"]}

    def transfer_money_with_assert(self, user_id: int, target_id: int, amount: float):
        """
        优雅断言模式：采用枚举断言接口，一行代码完成校验与错误码绑定
        核心业务逻辑清晰一目了然
        """
        ResponseEnum.PARAM_INVALID.assert_true(amount > 0, "转账金额必须大于0")
        
        user = self.db_users.get(user_id)
        ResponseEnum.USER_NOT_FOUND.assert_not_null(user, user_id)
        ResponseEnum.ACCOUNT_FROZEN.assert_false(user["status"] == "FROZEN")
        ResponseEnum.INSUFFICIENT_BALANCE.assert_true(user["balance"] >= amount, user["balance"], amount)

        # 核心业务扣款
        user["balance"] -= amount
        return {"userId": user_id, "transferred": amount, "balance": user["balance"]}

def run_tests():
    print("=== 开始运行 Spring Boot 枚举断言与全局切面防御引擎真实演练 ===")
    service = UserService()

    test_cases = [
        ("场景1: 正常转账", lambda: service.transfer_money_with_assert(1001, 2001, 100.0)),
        ("场景2: 用户不存在校验", lambda: service.transfer_money_with_assert(9999, 2001, 100.0)),
        ("场景3: 冻结账户校验", lambda: service.transfer_money_with_assert(1002, 2001, 10.0)),
        ("场景4: 余额不足校验", lambda: service.transfer_money_with_assert(1001, 2001, 800.0)),
        ("场景5: 非法参数校验", lambda: service.transfer_money_with_assert(1001, 2001, -50.0)),
    ]

    for title, action in test_cases:
        print(f"\n--- {title} ---")
        try:
            res = action()
            response_json = {
                "success": True,
                "code": 200,
                "message": "success",
                "data": res
            }
        except Exception as e:
            # 经过 RestControllerAdvice 切面收敛
            response_json = RestControllerAdvice.handle_exception(e)

        print(json.dumps(response_json, ensure_ascii=False, indent=2))
        if "场景1" in title:
            assert response_json["success"] is True
            assert response_json["code"] == 200
        elif "场景2" in title:
            assert response_json["code"] == 40401
            assert "9999" in response_json["message"]
        elif "场景3" in title:
            assert response_json["code"] == 40301
        elif "场景4" in title:
            assert response_json["code"] == 40901
        elif "场景5" in title:
            assert response_json["code"] == 40001

    print("\n[OK] 所有断言防御与切面收敛用例 100% 验证通过！")

if __name__ == "__main__":
    run_tests()
