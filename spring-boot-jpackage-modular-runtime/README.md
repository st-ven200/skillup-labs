# Lab 30: Spring Boot 结合 JPackage 原生打包与模块瘦身实战

[![Skillup Terminal](https://img.shields.io/badge/Online_Terminal-Skillup.host-brightgreen?logo=linux)](https://www.skillup.host/)
[![Status](https://img.shields.io/badge/Test-Passing-success)](https://github.com/st-ven200/skillup-labs)

## 🎯 实验目标
本实验提供完整的自动化脚本，演示如何将一个标准企业级 Spring Boot 可执行 Fat Jar 经过 **Jdeps 字节码静态依赖扫描**、**Jlink 定制化 JRE 模块级裁剪**（从 295MB 裁剪至 38MB），并通过 **JPackage 生成跨平台自包含原生安装包**（Windows MSI、macOS DMG、Linux DEB）：
1. **真实依赖图谱提取**：扫描目标应用所需的 Java 核心模块（`java.base`, `java.sql`, `java.logging`, `java.management` 等），剔除 Swing、CORBA 等冗余模块；
2. **多级瘦身与调试信息剔除**：使用 `--strip-debug`、`--no-header-files` 与 `--compress=2` 实现高达 87.12% 的体积缩减；
3. **跨平台原生启动器生成**：生成直接绑死特定优化 JRE 的平台原生启动器，用户端彻底免安装 JRE。

## 🛠️ 环境要求
- JDK 17+ (JDK 自带 jdeps, jlink, jpackage 工具)
- Python 3.9+
- 各平台原生打包工具（Windows 需 WiX 3.11+，Linux 需 fakeroot / rpm-build，macOS 需 xcode-select）

## 🚀 极速运行与验证
```bash
python3 jpackage_bundler.py
```

### 验证输出实录
```text
=================================================================
🚀 Running Lab 30: Spring Boot JPackage Modular Bundler Tests
=================================================================
📦 Analyzed Module Graph: ['java.base', 'java.logging', 'java.management', 'java.sql']

📊 Runtime Stripping Statistics:
   - Standard OpenJDK Size: 295.0 MB
   - Stripped Custom JRE Size: 38.0 MB
   - Disk Space Saved: 87.12%

🔧 Generated Jlink Command:
   jlink --add-modules java.base,java.logging,java.management,java.sql --output custom-runtime --strip-debug --no-header-files --no-man-pages --compress=2

🚀 Generated JPackage Command:
   jpackage --input target --name SpringCloudPortal --main-jar my-springboot-app-1.0.0.jar --main-class org.springframework.boot.loader.JarLauncher --app-version 1.0.0 --vendor Skillup Enterprise --runtime-image custom-runtime --type msi --win-dir-chooser --win-menu --win-shortcut

✅ All assertions passed! Spring Boot modular packaging verified.
=================================================================
```

## ⚠️ 小白排坑要点 (Pitfalls)
1. **Spring Boot JarLauncher 引导类陷阱**：在指定 `--main-class` 时，Spring Boot 的 Fat Jar 必须指定 `org.springframework.boot.loader.JarLauncher`，而非你的业务 `@SpringBootApplication` 主类，否则类加载器无法正确定位 `BOOT-INF/lib` 下的嵌套依赖。
2. **动态反射导致的 NoClassDefFoundError**：Spring 体系大量使用反射和动态代理（如 CGLIB / ByteBuddy），纯靠 `jdeps` 静态分析可能会漏掉 `jdk.unsupported`（包含 `sun.misc.Unsafe`）或 `java.instrument`。在 Jlink 参数中建议显式补充兜底关键模块。

---

> 💻 **云端免安装在线实操**：一键在浏览器中秒开预装环境运行验证本实验 👉 [Skillup 边学边练在线实验平台 (https://www.skillup.host/)](https://www.skillup.host/)。
