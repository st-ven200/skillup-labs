# Lab 31: 微信公众号 HTML AST 语法树清洗与全量 Markdown 资产归档实战

[![Skillup Terminal](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![Status](https://img.shields.io/badge/Test-Passing-success)](https://github.com/st-ven200/skillup-labs)

## 🎯 实验目标
针对微信公众平台封闭生态、动态防反爬、`data-src` 懒加载防盗链以及富文本结构塌陷的难题，实现一套基于 **HTML AST 抽象语法树** 的清洗、媒体资源本地持久化映射与 Markdown 标准序列化管道：
1. **完整 AST 建模**：将微信原生深层嵌套的 DOM 元素解析为类型化语法树（Element / Text / Image Node）；
2. **防盗链与懒加载抽取**：捕获 `data-src` 真实图像地址，基于内容哈希落盘为本地静态资产，重写为相对路径；
3. **噪音过滤与代码块保真**：通过 AST 规则剪枝彻底消除微信二维码、广告容器与赞赏干扰，还原纯净代码块与排版。

## 🛠️ 环境要求
- Python 3.9+
- Linux / macOS / Windows

## 🚀 极速运行与验证
```bash
python3 wechat_ast_pipeline.py
```

### 验证输出实录
```text
=================================================================
🚀 Running Lab 31: Wechat Article AST Pipeline Tests
=================================================================
✅ HTML 解析为 AST 成功，捕获顶级节点数: 1
✅ 图片懒加载清洗成功: https://mmbiz.qpic.cn/mmbiz_png/abc12345/640?wx_fmt=png -> ./assets/img_36de2e22cd56.png
✅ 本地媒体持久化落盘验证通过: /tmp/lab31_wechat_assets/img_36de2e22cd56.png
📄 最终清洗生成的 Markdown 预览:
--------------------------------------------------
## 微信公众号深度归档实战

随着数字化知识沉淀的普及，**全量离线化**成为了刚需。

下面是架构数据流向图：

![核心架构图](./assets/img_36de2e22cd56.png)

```
const engine = new ASTPipeline();
engine.start();
```
--------------------------------------------------
✅ All assertions passed! Wechat AST Archiver pipeline verified.
=================================================================
```

## ⚠️ 小白排坑要点 (Pitfalls)
1. **微信图片 1px 占位图陷阱**：微信网页端默认将 `<img src="...">` 填入 `data:image/svg+xml` 或 1px Base64，真实图片地址存储在 `data-src` 中；若直接提取 `src` 将导致批量裂图。
2. **AST 递归终止条件缺失**：在剪枝广告容器（如 `qr_code_pc`）时，若仅将节点置空而未在父级重构子节点列表，可能留下大量无意义的空换行。

---

> 💻 **云端免安装在线实操**：一键在浏览器中秒开预装环境运行验证本实验 👉 [Skillup 边学边练在线实验平台 (https://www.skillup.host/)](https://www.skillup.host/)。
