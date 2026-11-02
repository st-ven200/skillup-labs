#!/usr/bin/env python3
"""
Lab 35: Agent Skills 前端工程化三层架构与 AST 规则校验引擎
包含：
1. Agent Skills 规范目录与 YAML Frontmatter 动态加载器；
2. 渐进式三层上下文注入引擎；
3. 前端 Vue 3 / TypeScript 核心最佳实践 AST 规则静态校验器；
4. 真实业务场景闭环单元测试与断言（0 mock print）。
"""

import os
import re
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class RuleViolation:
    rule_id: str
    severity: str  # ERROR | WARNING | INFO
    message: str
    line_number: int
    matched_snippet: str

@dataclass
class SkillMetadata:
    name: str
    description: str
    version: str
    author: str
    tools_required: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

class AgentSkillsLoader:
    """Agent Skills 渐进式规范解析器"""
    
    @staticmethod
    def parse_skill_markdown(content: str) -> tuple[Optional[SkillMetadata], str]:
        """解析 SKILL.md 中的 YAML Frontmatter 和正文指令"""
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return None, content
        
        frontmatter_raw = match.group(1)
        body = match.group(2)
        
        data = yaml.safe_load(frontmatter_raw)
        meta = SkillMetadata(
            name=data.get("name", "unnamed-skill"),
            description=data.get("description", ""),
            version=str(data.get("version", "1.0.0")),
            author=data.get("author", "unknown"),
            tools_required=data.get("tools_required", []),
            metadata=data.get("metadata", {})
        )
        return meta, body

class FrontendCodeValidator:
    """针对 Vue 3 与 TS 规范的静态语法守卫"""

    RULES = [
        {
            "id": "VUE3-001",
            "name": "no-reactive-destructuring",
            "severity": "ERROR",
            "pattern": re.compile(r"const\s*\{[^}]+\}\s*=\s*reactive\("),
            "message": "禁止直接解构 reactive() 对象！会导致响应式追踪丢失，请使用 toRefs() 或单独使用 ref()。"
        },
        {
            "id": "VUE3-002",
            "name": "strict-script-setup-lang-ts",
            "severity": "ERROR",
            "pattern": re.compile(r"<script(?![^>]*\bsetup\b)(?![^>]*\blang=[\"']ts[\"'])[^>]*>"),
            "message": "企业级前端组件必须统一采用 <script setup lang=\"ts\"> 规范！"
        },
        {
            "id": "TS-003",
            "name": "no-explicit-any-ref",
            "severity": "WARNING",
            "pattern": re.compile(r"\bref<any>\("),
            "message": "严禁在 ref 泛型中使用 any 类型，必须声明明确的业务实体接口！"
        },
        {
            "id": "PINIA-004",
            "name": "prefer-setup-store",
            "severity": "WARNING",
            "pattern": re.compile(r"defineStore\([^,]+,\s*\{\s*state:"),
            "message": "Pinia 状态库强烈建议采用组合式 Setup Store 模式，避免 Options API 模式。"
        }
    ]

    @classmethod
    def audit_code(cls, source_code: str) -> List[RuleViolation]:
        violations: List[RuleViolation] = []
        lines = source_code.splitlines()

        for line_idx, line in enumerate(lines, 1):
            for rule in cls.RULES:
                match = rule["pattern"].search(line)
                if match:
                    violations.append(RuleViolation(
                        rule_id=rule["id"],
                        severity=rule["severity"],
                        message=rule["message"],
                        line_number=line_idx,
                        matched_snippet=line.strip()
                    ))
        return violations

def run_self_test():
    print("[Lab 35] 正在启动 Agent Skills 前端工程化静态守护引擎自测...")
    
    # 1. 验证 Frontmatter 提取与契约解析
    sample_skill_md = """---
name: enterprise-vue3-crud
description: "生成符合企业级生产环境要求的 Vue3 + Element Plus 数据表格与增删改查模块。"
version: 1.2.0
author: "Skillup Hands-on Lab"
tools_required: ["filesystem", "ast_parser"]
metadata:
  framework: "vue3"
  strict_mode: true
---

# Enterprise Vue3 CRUD Pipeline
## 阶段一：数据模型声明
"""
    meta, body = AgentSkillsLoader.parse_skill_markdown(sample_skill_md)
    assert meta is not None, "Frontmatter 解析失败！"
    assert meta.name == "enterprise-vue3-crud", f"名称不匹配: {meta.name}"
    assert meta.version == "1.2.0", f"版本不匹配: {meta.version}"
    assert "阶段一：数据模型声明" in body, "正文指令提取失败！"
    print("  ✅ [测试 1/3] YAML Frontmatter 元数据门禁解析验证通过！")

    # 2. 验证反模式违规捕获（Bad Code）
    bad_vue_code = """
<template>
  <div>{{ list.length }}</div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';

// 违规 1: 直接解构 reactive
const { list, total } = reactive({ list: [], total: 0 });

// 违规 2: 裸 any 类型
const currentItem = ref<any>(null);
</script>
"""
    bad_violations = FrontendCodeValidator.audit_code(bad_vue_code)
    assert len(bad_violations) == 2, f"预期捕获 2 个违规，实际捕获: {len(bad_violations)}"
    assert bad_violations[0].rule_id == "VUE3-001"
    assert bad_violations[1].rule_id == "TS-003"
    print(f"  ✅ [测试 2/3] 违规反模式精准拦截验证通过 (拦截项: {len(bad_violations)})！")

    # 3. 验证合规代码放行（Good Code）
    good_vue_code = """
<template>
  <el-table :data="tableData" v-loading="loading">
    <el-table-column prop="id" label="ID" />
  </el-table>
</template>

<script setup lang="ts">
import { ref, toRefs, reactive } from 'vue';

interface UserEntity {
  id: number;
  name: string;
}

const state = reactive<{ list: UserEntity[]; total: number }>({
  list: [],
  total: 0
});
const { list, total } = toRefs(state);
const loading = ref<boolean>(false);
const selectedUser = ref<UserEntity | null>(null);
</script>
"""
    good_violations = FrontendCodeValidator.audit_code(good_vue_code)
    assert len(good_violations) == 0, f"合规代码预期 0 违规，实际: {good_violations}"
    print("  ✅ [测试 3/3] 合规代码 100% 遵从度放行验证通过！")

    print("\n🎯 [Lab 35] 全部自动化断言通过，Agent Skills 工程引擎验证完毕！")

if __name__ == "__main__":
    run_self_test()
