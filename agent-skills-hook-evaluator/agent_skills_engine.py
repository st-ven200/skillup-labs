#!/usr/bin/env python3
"""
Agent Skills 渐进式加载架构与 Forced Eval Hook 拦截实战引擎
(AgentSkillsEngine & Pre-flight Interceptor)

复现腾讯云开发 (CloudBase) 与 Claude Code 架构核心：
1. 渐进式加载三阶段 (Discovery -> Activation -> Execution)
2. 端环境隔离与语义防污染 (Web vs MP vs Node.js)
3. 决策惰性消除器：Forced Eval Hook 中间件
4. 真实上下文 Token 预算与激活率基准实测
"""

import re
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

@dataclass
class SkillMetadata:
    name: str
    description: str
    environment: str  # 'web', 'miniprogram', 'nodejs', 'universal'
    tags: List[str]
    full_instruction: str = ""
    bound_scripts: List[str] = field(default_factory=list)

@dataclass
class EvaluationDecision:
    skill_name: str
    decision: str  # 'ACTIVATE', 'SKIP'
    reason: str
    confidence: float

class AgentSkillsRegistry:
    """管理并维护系统所有注册的 Agent Skills"""

    def __init__(self):
        self.skills: Dict[str, SkillMetadata] = {}

    def register(self, skill: SkillMetadata):
        self.skills[skill.name] = skill

    def get_discovery_payload(self) -> List[Dict[str, str]]:
        """Phase 1: Discovery - 仅暴露名称、描述与适配环境，消耗极小上下文"""
        return [
            {
                "name": s.name,
                "description": s.description,
                "environment": s.environment
            }
            for s in self.skills.values()
        ]

    def load_full_instruction(self, skill_name: str) -> Optional[str]:
        """Phase 2: Activation - 按需完全加载操作规程指令"""
        skill = self.skills.get(skill_name)
        return skill.full_instruction if skill else None


class ForcedEvalHookMiddleware:
    """Forced Eval Hook 拦截中间件：消除大模型决策惰性，提升技能激活率"""

    def __init__(self, registry: AgentSkillsRegistry):
        self.registry = registry

    def intercept_and_evaluate(self, user_prompt: str, current_env: str) -> Tuple[str, List[EvaluationDecision]]:
        """
        拦截用户请求，在进入核心代码生成前，强制要求生成结构化评估判定报告
        """
        discovery_list = self.registry.get_discovery_payload()
        evaluations: List[EvaluationDecision] = []

        user_prompt_lower = user_prompt.lower()

        # 模拟中间件注入的评估器（在真实环境中由 Pre-flight Prompt 强制模型输出）
        for item in discovery_list:
            s_name = item["name"]
            s_env = item["environment"]
            s_desc = item["description"].lower()

            # 1. 环境边界隔离检查（防止环境语义污染）
            if s_env != "universal" and s_env != current_env:
                evaluations.append(EvaluationDecision(
                    skill_name=s_name,
                    decision="SKIP",
                    reason=f"环境不匹配 (当前: {current_env}, 技能要求: {s_env})",
                    confidence=1.0
                ))
                continue

            # 2. 意图关键词与语义匹配
            keywords = [w for w in s_desc.replace(",", " ").replace("、", " ").split() if len(w) > 2]
            matched_keywords = [k for k in keywords if k in user_prompt_lower]

            if matched_keywords or any(tag in user_prompt_lower for tag in ["auth", "login", "登录", "数据库", "nosql"]):
                evaluations.append(EvaluationDecision(
                    skill_name=s_name,
                    decision="ACTIVATE",
                    reason=f"命中意图特征: {matched_keywords[:3]}，强制注入安全约束",
                    confidence=0.92
                ))
            else:
                evaluations.append(EvaluationDecision(
                    skill_name=s_name,
                    decision="SKIP",
                    reason="未匹配到相关业务场景",
                    confidence=0.85
                ))

        # 构建强制注入的前置评估文本 (Forced Evaluation Block)
        eval_report_lines = [
            "<!-- FORCED_EVALUATION_REPORT -->",
            f"🎯 当前运行环境边界: [{current_env.upper()}]",
            "🔍 Agent Skills 预检评估报告:"
        ]
        for e in evaluations:
            icon = "✅" if e.decision == "ACTIVATE" else "⏸️"
            eval_report_lines.append(f"  {icon} [{e.decision}] {e.skill_name}: {e.reason}")
        eval_report_lines.append("<!-- END_EVALUATION_REPORT -->\n")

        hooked_prompt = "\n".join(eval_report_lines) + user_prompt
        return hooked_prompt, evaluations


def build_sample_cloudbase_registry() -> AgentSkillsRegistry:
    """初始化模拟 CloudBase 技能矩阵"""
    reg = AgentSkillsRegistry()

    reg.register(SkillMetadata(
        name="cloudbase-guidelines",
        description="必读总纲：环境判定与全局安全准则，杜绝前端明文凭证与横向越权",
        environment="universal",
        tags=["guidelines", "security", "architecture"],
        full_instruction="【CloudBase 架构设计与安全总纲 SOP】\n1. 环境边界判定：启动前首先检查项目是否存在 app.json (微信小程序)、package.json (Node/Web) 或 tcb.json，依据环境隔离调用，严禁跨端语义污染。\n2. 拒绝脆弱传参：严禁在前端通过 userId/openid 参数传给后端进行数据过滤，必须利用云底座原生互信上下文获取当前经过认证的身份凭据。\n3. 行级权限沙箱：所有数据库集合必须绑定安全规则 (Security Rules)，例如 'auth.uid == doc._openid'，即使业务逻辑代码存在 Bug，底座依然能从物理隔离层面拦截越权。\n4. 敏感凭据零泄露：API Key、Secret 与第三方 Token 一律托管在云端环境变量或安全凭证管理中心，禁止在客户端代码中硬编码。"
    ))

    reg.register(SkillMetadata(
        name="auth-wechat",
        description="小程序原生身份认证，通过云底座免密获取 openid，禁止前端篡改",
        environment="miniprogram",
        tags=["auth", "wechat", "openid"],
        full_instruction="【微信小程序原生鉴权开发规范】\n1. 调用 wx.cloud.callFunction({ name: 'login' }) 直接由云函数获取 event.userInfo.openId。\n2. 严禁前端通过 Storage 缓存并在请求参数中传递明文身份标识。\n3. 会话自动续期与免密换票：基于微信底层原生通道，无需手动处理 Cookie 与 JWT 刷新。\n4. 异常处理：捕获 ERR_OPENID_NOT_FOUND 并提示用户重新授权或检查云环境绑定 ID。"
    ))

    reg.register(SkillMetadata(
        name="auth-web",
        description="Web 端 Cookie/Token 会话管理，适配第三方 OAuth 与短信验证码登录",
        environment="web",
        tags=["auth", "web", "oauth"],
        full_instruction="【Web 网页全栈端鉴权规范】\n1. 初始化：使用 @cloudbase/js-sdk 的 auth({ persistence: 'local' }) 实例。\n2. 登录流：提供短信验证码 signInWithSmsCode、微信扫码 signInWithWechat 以及账号密码认证方式。\n3. CSRF 防护与 HttpOnly 模式：生产环境推荐启用 Cookie 代理转发模式，避免客户端脚本直触 Token。\n4. 会话监听：挂载 auth.onLoginStateChanged(state => ...) 实时监听登录失效与重定向。"
    ))

    reg.register(SkillMetadata(
        name="no-sql-web-sdk",
        description="Web 端文档数据库操作，严格遵守防 SQL 注入与行权限安全规则",
        environment="web",
        tags=["db", "nosql", "security"],
        full_instruction="【Web 端文档数据库最佳实践】\n1. 构造查询：const db = app.database(); db.collection('orders').where({ status: 'PAID' }).get();\n2. 权限约束：客户端调用只允许访问当前登录态允许的行，严禁客户端拼接 command 覆盖底座 ACL。\n3. 投影与分页优化：强制使用 .field({ secret: false }) 剔除敏感字段，强制调用 .limit(20) 防止拖库 OOM。\n4. 事务与原子自增：对于库存扣减等高并发操作，必须使用 db.runTransaction 或 _.inc 原子指令。"
    ))

    return reg


def run_benchmark():
    print("="*65)
    print("🚀 [Agent Skills Engine] 启动渐进式加载与 Forced Eval 拦截实测")
    print("="*65)

    registry = build_sample_cloudbase_registry()
    hook = ForcedEvalHookMiddleware(registry)

    # 1. 模拟三阶段上下文体积对比 (Progressive Disclosure)
    discovery_payload = registry.get_discovery_payload()
    discovery_bytes = len(json.dumps(discovery_payload, ensure_ascii=False))

    all_instructions = [s.full_instruction for s in registry.skills.values()]
    monolithic_bytes = sum(len(i) for i in all_instructions)

    print(f"\n📊 [1. 上下文负荷优化实测 (Progressive Disclosure)]:")
    print(f"   - 单体式 (Monolithic) 全量装载开销: {monolithic_bytes} 字符")
    print(f"   - 渐进式 (Discovery) 仅装载元数据开销: {discovery_bytes} 字符")
    print(f"   - 上下文带宽节约比例: {(1 - discovery_bytes / monolithic_bytes) * 100:.1f}%\n")

    # 2. 模拟典型用户请求
    test_cases = [
        {
            "env": "miniprogram",
            "prompt": "帮我写一个微信小程序登录与用户中心页面，获取当前用户的 openid 并展示个人信息"
        },
        {
            "env": "web",
            "prompt": "在 React 网页端接入文档数据库，查询当前用户订单列表，记得把 userId 从前端带过来"
        }
    ]

    for idx, tc in enumerate(test_cases, 1):
        print(f"-----------------------------------------------------------------")
        print(f"🧪 [测试用例 {idx}] 环境: [{tc['env']}]")
        print(f"   用户原始请求: \"{tc['prompt']}\"")
        
        hooked_prompt, decisions = hook.intercept_and_evaluate(tc["prompt"], tc["env"])
        
        activated = [d for d in decisions if d.decision == "ACTIVATE"]
        skipped = [d for d in decisions if d.decision == "SKIP"]
        
        print(f"\n   ⚙️ Forced Hook 拦截分析:")
        print(f"   - 激活技能数: {len(activated)} 个 -> {[a.skill_name for a in activated]}")
        print(f"   - 屏蔽/跳过数: {len(skipped)} 个 (含跨端语义防污染拦截)")
        
        # 验证是否成功加载完整指令
        for act in activated:
            instruction = registry.load_full_instruction(act.skill_name)
            print(f"   📥 [按需注入] {act.skill_name} => \"{instruction[:40]}...\"")

    print("\n" + "="*65)
    print("🎉 [Agent Skills Engine] 渐进式调度与防装死拦截全链路演练完成！")
    print("="*65)

if __name__ == "__main__":
    run_benchmark()
