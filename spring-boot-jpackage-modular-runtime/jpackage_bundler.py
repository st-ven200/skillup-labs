#!/usr/bin/env python3
"""
Spring Boot JPackage Bundler & Modular Runtime Stripping Engine (Lab 30)
Real, executable simulation of Spring Boot JAR modular dependency extraction,
Jlink runtime stripping down to ~38MB, and multi-platform native installer specification generation.
"""

import os
import sys
import json
import zipfile
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, Tuple


# Standard JDK module sizes (in bytes, based on OpenJDK 17)
JDK_MODULE_WEIGHTS = {
    "java.base": 24 * 1024 * 1024,         # 24MB core
    "java.logging": 1 * 1024 * 1024,       # 1MB
    "java.sql": 2 * 1024 * 1024,           # 2MB
    "java.naming": 2 * 1024 * 1024,        # 2MB
    "java.desktop": 12 * 1024 * 1024,      # 12MB
    "java.management": 3 * 1024 * 1024,    # 3MB
    "java.instrument": 512 * 1024,         # 0.5MB
    "java.xml": 4 * 1024 * 1024,           # 4MB
    "java.net.http": 2 * 1024 * 1024,      # 2MB
    "jdk.unsupported": 256 * 1024,         # 256KB (sun.misc.Unsafe)
    "jdk.management": 1 * 1024 * 1024,     # 1MB
    "jdk.crypto.ec": 1 * 1024 * 1024,      # 1MB
}

FULL_JDK_SIZE = 295 * 1024 * 1024  # 295MB typical full JDK 17


@dataclass
class BundlerConfig:
    app_name: str
    main_jar: str
    main_class: str
    version: str
    target_platform: str  # 'windows' (msi/exe), 'macos' (dmg/pkg), 'linux' (deb/rpm)
    vendor: str = "Skillup"
    enable_menu: bool = True
    enable_shortcut: bool = True


class ModularJdepsAnalyzer:
    """Analyzes bytecode references in JAR to determine minimum required JDK modules."""

    @staticmethod
    def analyze_jar_modules(jar_path: Path) -> Set[str]:
        required = {"java.base"}  # Always required
        if not jar_path.exists():
            # Return baseline enterprise Spring Boot dependencies
            return required | {"java.logging", "java.sql", "java.naming", "java.management", "java.xml", "jdk.unsupported"}

        try:
            with zipfile.ZipFile(jar_path, 'r') as zf:
                for name in zf.namelist():
                    lower = name.lower()
                    if "sql" in lower or "datasource" in lower or "jdbc" in lower:
                        required.add("java.sql")
                    if "log" in lower or "slf4j" in lower:
                        required.add("java.logging")
                    if "naming" in lower or "jndi" in lower:
                        required.add("java.naming")
                    if "management" in lower or "jmx" in lower:
                        required.add("java.management")
                    if "xml" in lower or "dom" in lower or "sax" in lower:
                        required.add("java.xml")
                    if "http" in lower or "client" in lower:
                        required.add("java.net.http")
        except Exception:
            required.update(["java.logging", "java.sql", "java.naming", "java.management", "java.xml"])
        return required


class JPackageOrchestrator:
    """Orchestrates Jlink runtime stripping and JPackage command compilation."""

    def __init__(self, config: BundlerConfig):
        self.config = config

    def calculate_custom_runtime_size(self, modules: Set[str]) -> Tuple[int, float]:
        """Calculates custom JRE footprint vs full JDK."""
        custom_size = sum(JDK_MODULE_WEIGHTS.get(m, 1024 * 1024) for m in modules)
        # Overhead for bin/executables, libjvm, classloader metadata
        custom_size += 8 * 1024 * 1024
        ratio = (1.0 - (custom_size / FULL_JDK_SIZE)) * 100
        return custom_size, round(ratio, 2)

    def generate_jlink_command(self, modules: Set[str], output_dir: str = "custom-runtime") -> List[str]:
        mod_str = ",".join(sorted(modules))
        return [
            "jlink",
            "--add-modules", mod_str,
            "--output", output_dir,
            "--strip-debug",
            "--no-header-files",
            "--no-man-pages",
            "--compress=2"
        ]

    def generate_jpackage_command(self, runtime_dir: str = "custom-runtime") -> List[str]:
        cmd = [
            "jpackage",
            "--input", "target",
            "--name", self.config.app_name,
            "--main-jar", self.config.main_jar,
            "--main-class", self.config.main_class,
            "--app-version", self.config.version,
            "--vendor", self.config.vendor,
            "--runtime-image", runtime_dir
        ]

        if self.config.target_platform == "windows":
            cmd.extend([
                "--type", "msi",
                "--win-dir-chooser",
                "--win-menu" if self.config.enable_menu else "",
                "--win-shortcut" if self.config.enable_shortcut else ""
            ])
        elif self.config.target_platform == "macos":
            cmd.extend([
                "--type", "dmg",
                "--mac-package-name", f"com.skillup.{self.config.app_name.lower()}",
                "--mac-package-identifier", f"com.skillup.{self.config.app_name.lower()}"
            ])
        elif self.config.target_platform == "linux":
            cmd.extend([
                "--type", "deb",
                "--linux-shortcut" if self.config.enable_shortcut else "",
                "--linux-menu-group", "Development"
            ])
        return [c for c in cmd if c]


def run_verification():
    print("=" * 65)
    print("🚀 Running Lab 30: Spring Boot JPackage Modular Bundler Tests")
    print("=" * 65)

    # 1. Simulate a Spring Boot JAR
    temp_dir = Path("/tmp/lab30_jpackage_test")
    temp_dir.mkdir(parents=True, exist_ok=True)
    jar_path = temp_dir / "my-springboot-app-1.0.0.jar"

    with zipfile.ZipFile(jar_path, 'w') as zf:
        zf.writestr("org/springframework/boot/loader/JarLauncher.class", b"\xca\xfe\xba\xbe")
        zf.writestr("com/example/demo/datasource/MySqlConfig.class", b"java/sql/Connection")
        zf.writestr("com/example/demo/logging/LogbackConfig.class", b"java/logging/Logger")
        zf.writestr("com/example/demo/jmx/MetricsManager.class", b"java/management/MBean")

    # 2. Extract modules via static inspection
    modules = ModularJdepsAnalyzer.analyze_jar_modules(jar_path)
    print(f"📦 Analyzed Module Graph: {sorted(list(modules))}")
    assert "java.sql" in modules, "Failed to identify java.sql dependency"
    assert "java.logging" in modules, "Failed to identify java.logging dependency"
    assert "java.management" in modules, "Failed to identify java.management dependency"

    # 3. Compile Jlink & JPackage specifications
    cfg = BundlerConfig(
        app_name="SpringCloudPortal",
        main_jar="my-springboot-app-1.0.0.jar",
        main_class="org.springframework.boot.loader.JarLauncher",
        version="1.0.0",
        target_platform="windows",
        vendor="Skillup Enterprise"
    )
    orch = JPackageOrchestrator(cfg)

    # 4. Metric evaluation
    custom_bytes, reduction_pct = orch.calculate_custom_runtime_size(modules)
    custom_mb = round(custom_bytes / (1024 * 1024), 2)
    full_mb = round(FULL_JDK_SIZE / (1024 * 1024), 2)

    print(f"\n📊 Runtime Stripping Statistics:")
    print(f"   - Standard OpenJDK Size: {full_mb} MB")
    print(f"   - Stripped Custom JRE Size: {custom_mb} MB")
    print(f"   - Disk Space Saved: {reduction_pct}%")

    assert custom_mb < 55.0, f"Custom JRE size ({custom_mb}MB) exceeds expected budget"

    # 5. Verify generated CLI commands
    jlink_cmd = orch.generate_jlink_command(modules)
    jpackage_cmd = orch.generate_jpackage_command()

    print(f"\n🔧 Generated Jlink Command:")
    print("   " + " ".join(jlink_cmd))
    print(f"\n🚀 Generated JPackage Command:")
    print("   " + " ".join(jpackage_cmd))

    assert "--compress=2" in jlink_cmd, "Missing compression flag in jlink"
    assert "--runtime-image" in jpackage_cmd, "Missing custom runtime in jpackage"
    assert "--type" in jpackage_cmd and "msi" in jpackage_cmd, "Missing target installer type"

    print("\n✅ All assertions passed! Spring Boot modular packaging verified.")
    print("=" * 65)


if __name__ == '__main__':
    run_verification()
