#!/usr/bin/env python3
"""
初始化当前 C# 工业视觉项目的 AGENTS.md 准则文件。
支持自动探测工程技术栈（Avalonia / WPF / OpenCvSharp / Halcon / 相机驱动 SDK 等）并生成定制化行为准则。
"""

import argparse
import os
import re
import sys
from pathlib import Path


def detect_project_features(target_dir: Path) -> dict:
    """探测目标目录中的 C# 与视觉技术栈特征"""
    features = {
        "is_csharp": False,
        "frameworks": set(),
        "ui": "未知/无 UI",
        "vision_libs": set(),
        "hardware_sdks": set(),
        "build_cmd": "dotnet build -c Debug --nologo",
    }

    # 递归搜索 .csproj, .sln
    csproj_files = list(target_dir.glob("**/*.csproj"))
    sln_files = list(target_dir.glob("*.sln")) + list(target_dir.glob("*/*.sln"))

    if csproj_files or sln_files:
        features["is_csharp"] = True

    for csproj in csproj_files[:15]:  # 最多分析前15个项目文件
        try:
            content = csproj.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # 探测 TargetFramework
        tf_match = re.search(r"<TargetFramework.*?>([^<]+)</TargetFramework.*?>", content)
        if tf_match:
            features["frameworks"].add(tf_match.group(1))

        # 探测 UI 框架
        if "Avalonia" in content:
            features["ui"] = "Avalonia"
        elif "<UseWPF>true</UseWPF>" in content or "PresentationCore" in content:
            features["ui"] = "WPF"
        elif "<UseWindowsForms>true</UseWindowsForms>" in content:
            features["ui"] = "WinForms"

        # 探测视觉算法库
        if "OpenCvSharp" in content:
            features["vision_libs"].add("OpenCvSharp")
        if "halcondotnet" in content.lower() or "halcon" in content.lower():
            features["vision_libs"].add("Halcon")
        if "Emgu.CV" in content:
            features["vision_libs"].add("Emgu.CV")

        # 探测硬件 SDK
        if "MvCameraControl" in content or "MVS" in content:
            features["hardware_sdks"].add("Hikvision (海康 MVS)")
        if "Pylon" in content or "Basler" in content:
            features["hardware_sdks"].add("Basler (Pylon)")
        if "GxIAPICSharp" in content or "Daheng" in content:
            features["hardware_sdks"].add("Daheng (大恒 Galaxy)")
        if "Spinnaker" in content or "FLIR" in content:
            features["hardware_sdks"].add("FLIR (Spinnaker)")

    return features


def generate_agents_md(target_dir: Path, force: bool = False) -> tuple[bool, str]:
    target_dir = target_dir.resolve()
    target_file = target_dir / "AGENTS.md"

    if target_file.exists() and not force:
        return (
            False,
            f"目标路径已存在 AGENTS.md: {target_file}\n如需覆盖，请添加 --force 参数。",
        )

    # 定位模板
    script_dir = Path(__file__).resolve().parent
    template_file = script_dir.parent / "templates" / "AGENTS.md.template"

    if template_file.exists():
        template_content = template_file.read_text(encoding="utf-8")
    else:
        return False, f"未找到模板文件: {template_file}"

    # 技术栈探测
    features = detect_project_features(target_dir)

    summary_lines = []
    if features["is_csharp"]:
        summary_lines.append(f"- **目标平台**: {', '.join(sorted(features['frameworks'])) or '.NET'}")
        summary_lines.append(f"- **UI 架构**: {features['ui']}")
        if features["vision_libs"]:
            summary_lines.append(f"- **视觉算法**: {', '.join(sorted(features['vision_libs']))}")
        if features["hardware_sdks"]:
            summary_lines.append(f"- **硬件驱动**: {', '.join(sorted(features['hardware_sdks']))}")

    feature_header = ""
    if summary_lines:
        feature_header = "\n> **当前项目环境探测**:\n" + "\n".join(summary_lines) + "\n"

    # 在文档第一段后插入探测到的特征（如果有）
    insertion_marker = "优先级：**用户当前明确要求 > 本文档 > 通用系统提示词**。一切以**当前源码、工程配置、运行日志与真实环境反馈**为事实基准。"
    if insertion_marker in template_content and feature_header:
        final_content = template_content.replace(
            insertion_marker,
            f"{insertion_marker}\n{feature_header}",
            1,
        )
    else:
        final_content = template_content

    # 写入文件
    target_file.write_text(final_content, encoding="utf-8")
    return True, f"成功在项目本地生成 AGENTS.md 准则文件！\n文件路径: {target_file}\n大小: {len(final_content)} 字符"


def main():
    parser = argparse.ArgumentParser(
        description="为 C# 工业视觉项目生成规范完备的 AGENTS.md 行为准则文件"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="目标项目根目录（默认为当前工作目录）",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="如果 AGENTS.md 已存在，强制覆盖",
    )

    args = parser.parse_args()
    target_path = Path(args.target)

    if not target_path.exists():
        print(f"错误: 目标路径不存在: {target_path}", file=sys.stderr)
        sys.exit(1)

    success, msg = generate_agents_md(target_path, force=args.force)
    print(msg)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
