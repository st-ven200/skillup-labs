# Lab 11: OpenClaw Skills 供应链安全静态审计与依赖锁定 (openclaw-skill-security-audit)

[![Skillup Cloud Terminal](https://img.shields.io/badge/Skillup-Cloud%20Terminal-blue?logo=terminal)](https://www.skillup.host/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-skillup--labs-green?logo=github)](https://github.com/st-ven200/skillup-labs/tree/main/openclaw-skill-security-audit)

## 1. 实验场景与目标
随着 OpenClaw / ClawHub 社区生态扩张至 5,400+ 技能，第三方 Skills 带来的供应链投毒攻击与凭据窃取成为 AI 智能体落地的最大安全威胁。
本实操实验旨在构建一套**确定性的技能安全静态审计引擎与 Lockfile 校验器**：
1. 静态解析 `SKILL.md` 元数据与权限声明；
2. 扫描高危反模式（如 `curl | bash` 远程管道执行、`~/.ssh` 敏感私钥探测、未授权环境变量搜刮等）；
3. 计算全量文件 SHA-256 完整性摘要并生成 `.clawhub/lock.json`；
4. 做出 `ALLOW`、`WARN` 或 `BLOCK` 准入判定。

## 2. 环境依赖
- Python 3.8+
- 操作系统：Linux / macOS / Windows

## 3. 逐步演练与验证命令

### 步骤 1：审查安全基线技能（预期 ALLOW）
```bash
python3 audit_skill.py --dir fixtures/safe_weather_skill
```
**预期输出**：
- `verdict`: `"ALLOW"`
- `critical_issues`: 0
- 成功输出各文件独立 SHA-256 哈希值与整体 `root_hash`。

### 步骤 2：拦截高危投毒技能（预期 BLOCK）
```bash
python3 audit_skill.py --dir fixtures/malicious_crypto_skill
```
**预期输出**：
- `verdict`: `"BLOCK"`
- 精准定位第 6 行 `curl | bash`、第 9 行 `cat ~/.ssh/id_rsa` 等关键投毒代码。

### 步骤 3：批量生成依赖锁定账本 (.clawhub/lock.json)
```bash
python3 audit_skill.py --dir fixtures/ --lockfile .clawhub/lock.json
cat .clawhub/lock.json
```

## 4. 排坑要点 (Pitfalls)
1. **隐式执行反模式**：不要仅通过文件名过滤，必须递归检查所有 `.sh`、`.py`、`.js` 脚本内容。
2. **符号链接穿透风险**：生产环境中应防御 Symlink 穿透攻击，使用 `Path.resolve()` 确保所有待审计路径均在技能受控沙箱目录之内。
3. **版本漂移**：缺少 Lockfile 锁定时，远程仓库的 force-push 会使本地 Agent 静默加载被篡改的恶意版本，必须坚持哈希校验。

---

> 📂 **开源实操代码与云端演练**：
> - 💻 **GitHub 开源实操仓库**：本文配套的完整工程、可执行脚本与测试样例已开源归档至 [GitHub: skillup-labs/openclaw-skill-security-audit](https://github.com/st-ven200/skillup-labs/tree/main/openclaw-skill-security-audit)，欢迎 Star 关注。
> - 🚀 **在线免安装体验运行验证**：无需本地折腾复杂的运行时与系统依赖，一键在浏览器中秒开云端实操终端进行交互验证 👉 [Skillup 边学边练在线实验平台 (https://www.skillup.host/)](https://www.skillup.host/)。
