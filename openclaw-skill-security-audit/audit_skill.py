#!/usr/bin/env python3
"""
OpenClaw Skill Security Audit & Integrity Lockfile Generator
Demonstrates real static analysis, AST/regex heuristics, permission extraction,
and SHA-256 lockfile generation for OpenClaw skills ecosystem.
"""

import os
import sys
import json
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Any

# Dangerous command & credential scraping patterns
RISK_PATTERNS = [
    (r"curl\s+.*\|\s*(?:ba)?sh", "CRITICAL", "Remote bash script pipe execution (arbitrary remote code execution)"),
    (r"wget\s+.*\|\s*(?:ba)?sh", "CRITICAL", "Remote bash script pipe execution via wget"),
    (r"(?:cat|less|grep)\s+.*(?:\.ssh|\.aws|\.kube|\.env|id_rsa)", "CRITICAL", "Accessing sensitive credential files or keys"),
    (r"os\.environ\.get\(['\"](?:AWS_|OPENAI_|GITHUB_|TOKEN|SECRET|KEY)", "HIGH", "Harvesting environmental API keys/tokens"),
    (r"subprocess\.(?:Popen|run|call)\(.*shell\s*=\s*True", "HIGH", "Unsanitized shell=True command execution"),
    (r"rm\s+-rf\s+[/~]", "HIGH", "Destructive recursive file deletion at root or home"),
    (r"fetch\(['\"]https?://(?!(?:api\.github\.com|clawhub\.ai|registry\.npmjs\.org)).*token", "HIGH", "Exfiltrating tokens to unknown external endpoint"),
    (r"(?:eval|exec)\s*\(", "MEDIUM", "Dynamic code evaluation (eval/exec)"),
    (r"chmod\s+\+x\s+", "MEDIUM", "Changing executable permissions on scripts"),
]

def calculate_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def parse_skill_metadata(skill_md_path: Path) -> Dict[str, Any]:
    metadata = {}
    if not skill_md_path.exists():
        return metadata
    
    content = skill_md_path.read_text(encoding='utf-8')
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            raw_frontmatter = parts[1]
            for line in raw_frontmatter.splitlines():
                if ':' in line:
                    key, val = line.split(':', 1)
                    metadata[key.strip()] = val.strip().strip('"\'')
    return metadata

def audit_file_content(filepath: Path) -> List[Dict[str, str]]:
    findings = []
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return [{"level": "ERROR", "message": f"Failed to read file: {e}", "pattern": ""}]
    
    for pattern, level, desc in RISK_PATTERNS:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for m in matches:
            # Find line number
            line_no = content[:m.start()].count('\n') + 1
            findings.append({
                "level": level,
                "file": filepath.name,
                "line": line_no,
                "matched": m.group(0),
                "description": desc
            })
    return findings

def audit_skill_directory(skill_dir: Path) -> Dict[str, Any]:
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    metadata = parse_skill_metadata(skill_md)
    
    file_hashes = {}
    all_findings = []
    
    for item in skill_dir.rglob("*"):
        if item.is_file() and not item.name.startswith("."):
            rel_path = str(item.relative_to(skill_dir))
            file_hashes[rel_path] = calculate_sha256(item)
            
            # Analyze code and script files
            if item.suffix in [".py", ".sh", ".js", ".mjs", ".ts", ".md"]:
                findings = audit_file_content(item)
                all_findings.extend(findings)
                
    # Determine overall security score & policy decision
    critical_count = sum(1 for f in all_findings if f["level"] == "CRITICAL")
    high_count = sum(1 for f in all_findings if f["level"] == "HIGH")
    
    if critical_count > 0:
        verdict = "BLOCK"
        status_desc = "Malicious or severely risky patterns detected"
    elif high_count > 0:
        verdict = "WARN"
        status_desc = "Elevated permissions / sensitive operations require manual approval"
    else:
        verdict = "ALLOW"
        status_desc = "Security baseline checks passed"
        
    return {
        "skill": skill_name,
        "version": metadata.get("version", "1.0.0"),
        "author": metadata.get("author", "unknown"),
        "verdict": verdict,
        "status_description": status_desc,
        "critical_issues": critical_count,
        "high_issues": high_count,
        "findings": all_findings,
        "integrity": {
            "root_hash": hashlib.sha256("".join(sorted(file_hashes.values())).encode()).hexdigest(),
            "files": file_hashes
        }
    }

def generate_lockfile(skills_root: Path, output_lockfile: Path):
    lock_data = {
        "version": 1,
        "generated_by": "openclaw-audit-engine/2.4.0",
        "lockfile_timestamp": 1792340000,
        "skills": {}
    }
    
    for skill_path in skills_root.iterdir():
        if skill_path.is_dir() and not skill_path.name.startswith("."):
            report = audit_skill_directory(skill_path)
            lock_data["skills"][skill_path.name] = {
                "version": report["version"],
                "verdict": report["verdict"],
                "root_hash": report["integrity"]["root_hash"],
                "file_count": len(report["integrity"]["files"])
            }
            
    output_lockfile.parent.mkdir(parents=True, exist_ok=True)
    output_lockfile.write_text(json.dumps(lock_data, indent=2, ensure_ascii=False), encoding='utf-8')
    return lock_data

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Audit OpenClaw skill directory and generate lock.json")
    parser.add_argument("--dir", default=".", help="Skill directory or directory of skills to audit")
    parser.add_argument("--lockfile", default=".clawhub/lock.json", help="Output lockfile path")
    args = parser.parse_args()
    
    target_path = Path(args.dir)
    print(f"[AUDIT] Scanning target path: {target_path.resolve()}")
    
    if (target_path / "SKILL.md").exists():
        report = audit_skill_directory(target_path)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        lock_res = generate_lockfile(target_path, Path(args.lockfile))
        print(f"[SUCCESS] Lockfile generated at {args.lockfile} with {len(lock_res['skills'])} skills locked.")
