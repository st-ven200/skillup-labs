#!/usr/bin/env python3
"""
demo_qoder_skills_runner.py
仿真阿里桌面端智能体 QoderWork 的核心架构引擎：
1. 三级渐进式披露机制（Progressive Disclosure：元数据索引 -> 指南加载 -> 确定性脚本）
2. 任务复杂度自适应模型双轨路由（标准档 Standard vs 旗舰档 Flagship）
3. 本地受限沙盒目录隔离与最小权限安全守卫（Path Guard & Human-in-the-loop 阻断）
"""

import os
import sys
import json
import re
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

# ==========================================
# 1. 结构体与领域模型
# ==========================================

@dataclass
class SkillMetadata:
    """第一级：常驻系统提示词中的元数据卡片"""
    name: str
    description: str
    tags: List[str]
    tier: int = 1
    token_cost: int = 45  # 模拟仅占用数十 Token

@dataclass
class SkillDefinition:
    """第二级：任务命中后动态加载的执行指南"""
    meta: SkillMetadata
    instructions: str
    allowed_tools: List[str]
    risk_level: str  # 'low', 'medium', 'high'
    token_cost: int = 1200

@dataclass
class TaskPlan:
    task_id: str
    user_prompt: str
    model_tier: str  # 'standard' 或 'flagship'
    selected_skills: List[str]
    execution_steps: List[Dict[str, Any]]
    total_tokens_budget: int

# ==========================================
# 2. 技能仓库与渐进式加载器
# ==========================================

class QoderSkillsEngine:
    def __init__(self, sandbox_root: Path):
        self.sandbox_root = sandbox_root
        self.sandbox_root.mkdir(parents=True, exist_ok=True)
        self.skills_catalog: Dict[str, SkillDefinition] = {}
        self._init_mock_skill_store()

    def _init_mock_skill_store(self):
        """初始化官方预置与市场技能"""
        # Skill 1: 发票结构化识别与财报汇总
        self.skills_catalog["invoice-ledger"] = SkillDefinition(
            meta=SkillMetadata(
                name="invoice-ledger",
                description="自动扫描提取 PDF/图像发票中的金额、税号与项目明细，汇总并生成 Excel 台账",
                tags=["finance", "excel", "ocr", "office"]
            ),
            instructions=(
                "1. 扫描输入目录中的发票文件；\n"
                "2. 提取发票代码、金额与开票日期；\n"
                "3. 校验金额汇总，调用 Python pandas 生成报销汇总表。"
            ),
            allowed_tools=["read_file", "write_file", "run_script"],
            risk_level="low"
        )

        # Skill 2: 小红书/微信图文卡片排版生成
        self.skills_catalog["social-card-designer"] = SkillDefinition(
            meta=SkillMetadata(
                name="social-card-designer",
                description="将长文要点转换为符合小红书视觉比例的高转化图文卡片与排版文案",
                tags=["design", "marketing", "image", "content"]
            ),
            instructions=(
                "1. 提取长文本核心金句与 3 个二级要点；\n"
                "2. 匹配视觉色板与排版栅格；\n"
                "3. 调用本地渲染引擎导出高保真图片卡片。"
            ),
            allowed_tools=["render_card", "write_file"],
            risk_level="low"
        )

        # Skill 3: 桌面应用与自动化系统运维
        self.skills_catalog["desktop-automation"] = SkillDefinition(
            meta=SkillMetadata(
                name="desktop-automation",
                description="调用本地命令行与应用自动化接口，执行环境自检与批量软件状态管理",
                tags=["system", "cli", "ops", "windows"]
            ),
            instructions=(
                "1. 校验目标进程与服务状态；\n"
                "2. 执行受控 Shell 命令；\n"
                "3. 遇到涉及系统敏感路径时必须阻断并请求用户二次授权。"
            ),
            allowed_tools=["run_command", "inspect_system"],
            risk_level="high"
        )

    def get_tier1_catalog(self) -> List[Dict[str, str]]:
        """获取一级元数据：仅暴露简明描述，Token 极省"""
        return [
            {"name": s.meta.name, "desc": s.meta.description, "tags": ",".join(s.meta.tags)}
            for s in self.skills_catalog.values()
        ]

    def resolve_skill(self, name: str) -> Optional[SkillDefinition]:
        """二级渐进式按需加载正文"""
        return self.skills_catalog.get(name)

# ==========================================
# 3. 双轨模型路由器 (Dual-Tier Model Router)
# ==========================================

class ModelRouter:
    @staticmethod
    def evaluate_task(prompt: str) -> Tuple[str, str]:
        """
        评估用户自然语言意图复杂性：
        - 基础文件整理、报销提取、常规格式化 -> 'standard' (快速、低 Token 成本)
        - 多阶段规划、多智能体协同、视频分镜脚本重构 -> 'flagship' (深度推理、复杂工具调用)
        """
        complex_keywords = ["视频", "二创", "分镜", "漫剧", "跨应用协同", "架构重构", "多Agent", "多阶段"]
        is_complex = any(kw in prompt for kw in complex_keywords) or len(prompt) > 80
        
        if is_complex:
            return "flagship", "检测到复合创作/多阶段推理链路，路由至【旗舰档 Flagship】模型以保障任务规划深度"
        else:
            return "standard", "识别为标准桌面办公/格式化任务，路由至【标准档 Standard】模型以提升吞吐并节省配额"

# ==========================================
# 4. 本地沙盒与安全执行守卫 (Sandbox & Guardrail)
# ==========================================

class LocalSandboxGuard:
    def __init__(self, sandbox_dir: Path):
        self.sandbox_dir = sandbox_dir.resolve()

    def validate_path(self, target_path_str: str) -> bool:
        """检查目标路径是否被限制在安全沙盒以内，防止目录逃逸（Directory Traversal）"""
        target = Path(target_path_str).resolve()
        try:
            target.relative_to(self.sandbox_dir)
            return True
        except ValueError:
            return False

    def execute_script(self, script_name: str, args: Dict[str, Any], risk: str) -> Dict[str, Any]:
        """模拟第三级确定性脚本的安全执行"""
        if risk == "high":
            # 模拟 Human-in-the-loop 机制
            print(f"  [SECURITY-GATE] 触发高危操作审计门禁: 操作包含 '{script_name}'，风险等级: {risk.upper()}")
            print(f"  [HUMAN-IN-THE-LOOP] 已向用户桌面弹出授权通知 -> 自动化模拟: 用户已在弹窗点击【允许本次】")

        output_file = self.sandbox_dir / f"output_{int(time.time())}.json"
        result_payload = {
            "status": "success",
            "script": script_name,
            "args": args,
            "sandbox_path": str(output_file),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, ensure_ascii=False, indent=2)

        return result_payload

# ==========================================
# 5. 主演示流程
# ==========================================

def run_simulation():
    print("=" * 70)
    print("🚀 QoderWork 桌面智能体架构仿真探针 (QoderWork Desktop Agent Engine)")
    print("=" * 70)

    sandbox_path = Path("./scratch/qoder_sandbox_workspace")
    engine = QoderSkillsEngine(sandbox_path)
    router = ModelRouter()
    guard = LocalSandboxGuard(sandbox_path)

    # 1. 模拟第一级：常驻技能目录构建
    tier1_items = engine.get_tier1_catalog()
    t1_tokens = sum(item.meta.token_cost for item in engine.skills_catalog.values())
    full_tokens = sum(item.token_cost for item in engine.skills_catalog.values())
    
    print("\n[Phase 1] 三级渐进式披露机制（一级常驻元数据）:")
    print(f"  已注册 Skills 数量: {len(tier1_items)} 个")
    print(f"  常驻 System Prompt 仅占用 Token: {t1_tokens} tokens (相比全量加载 {full_tokens} tokens 压缩率: {(1 - t1_tokens/full_tokens)*100:.1f}%)")
    for s in tier1_items:
        print(f"    - [{s['name']}]: {s['desc'][:40]}... (标签: {s['tags']})")

    # 2. 模拟双任务输入与双轨模型路由
    test_cases = [
        "把下载文件夹里的 3 张电子发票识别出来，整理金额和报销单，并导出 Excel",
        "把刚才公众号的技术文章解析提取关键论点，用漫剧 Skills 自动编写 30 秒带货视频分镜脚本"
    ]

    for idx, prompt in enumerate(test_cases, 1):
        print("\n" + "-" * 70)
        print(f"📝 [Task {idx}] 用户指令: \"{prompt}\"")
        
        # 模型双轨路由决策
        model_tier, reason = router.evaluate_task(prompt)
        print(f"  ⚡ 模型路由决策: 【{model_tier.upper()}】档 | 原因: {reason}")

        # 技能命中与二级加载
        matched_skills = []
        if "发票" in prompt or "Excel" in prompt:
            matched_skills.append("invoice-ledger")
        if "文章" in prompt or "视频" in prompt or "分镜" in prompt:
            matched_skills.append("social-card-designer")
            matched_skills.append("desktop-automation")

        print(f"  🎯 意图命中技能: {matched_skills}")
        for sk_name in matched_skills:
            skill = engine.resolve_skill(sk_name)
            if skill:
                print(f"  📖 [二级披露] 动态注入 SKILL.md: '{skill.meta.name}' (风险级别: {skill.risk_level})")
                print(f"     允许工具: {skill.allowed_tools}")

        # 3. 第三级执行与安全沙盒校验
        print("  ⚙️  [三级披露] 调度确定性脚本并在本地沙盒中闭环执行:")
        
        # 安全逃逸测试（校验路径围栏）
        unsafe_path = "/etc/hosts"
        is_safe = guard.validate_path(unsafe_path)
        print(f"     [Guard Check] 访问 '{unsafe_path}' -> 沙盒校验: {'合规放行' if is_safe else '⚠️ 越权阻断 (Permission Denied)'}")

        safe_target = str(sandbox_path / "invoices_202610.xlsx")
        is_safe_2 = guard.validate_path(safe_target)
        print(f"     [Guard Check] 访问 '{safe_target}' -> 沙盒校验: {'合规放行' if is_safe_2 else '越权阻断'}")

        # 执行动作
        script_to_run = "process_invoices.py" if idx == 1 else "generate_storyboard.py"
        exec_res = guard.execute_script(script_to_run, {"target": safe_target}, risk="high" if idx == 2 else "low")
        print(f"     [Execution] 脚本输出已落盘: {exec_res['sandbox_path']} (状态: {exec_res['status']})")

    print("\n" + "=" * 70)
    print("✅ QoderWork 架构核心链路仿真演示完成: 渐进式披露、双轨路由与沙盒围栏全部通过验证！")
    print("=" * 70)

if __name__ == "__main__":
    run_simulation()
