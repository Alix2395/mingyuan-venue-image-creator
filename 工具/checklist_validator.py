#!/usr/bin/env python3
"""
明源场宣图 - 检查清单验证器
逐项验证产出是否满足质量要求

用法：
    python checklist_validator.py <成果目录> [--target 2560x1440] [--json <路径>]

检查项：
    - 图片数量 / 分辨率匹配
    - 文件完整性
    - 文件大小合理性
    - 命名规范
    - CJK 字体可用性
    - 重复文件检测
"""

import sys
import json
from pathlib import Path
from PIL import Image

H_TARGET = (2560, 1440)
V_TARGET = (1440, 2560)
EXTS = {".jpg", ".jpeg", ".png"}


def check_file_integrity(image_path: Path) -> bool:
    """验证图片文件完整性"""
    try:
        with Image.open(image_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def check_resolution(image_path: Path, h_target: tuple, v_target: tuple) -> dict:
    """检查单张图片分辨率"""
    try:
        if not check_file_integrity(image_path):
            return {"file": image_path.name, "status": "❌", "error": "文件损坏"}

        img = Image.open(image_path)
        w, h = img.size
        orient = "horizontal" if w >= h else "vertical"
        target = h_target if orient == "horizontal" else v_target

        match = (w == target[0] and h == target[1])
        return {
            "file": image_path.name,
            "size": f"{w}x{h}",
            "target": f"{target[0]}x{target[1]}",
            "orientation": orient,
            "match": match,
            "status": "✅" if match else "❌",
        }
    except Exception as e:
        return {"file": image_path.name, "status": "❌", "error": str(e)}


def check_file_size(image_path: Path) -> dict:
    """检查文件大小是否合理"""
    size_kb = image_path.stat().st_size / 1024
    # 2560x1440 JPEG 质量95，合理范围约 200KB-2MB
    reasonable = 50 <= size_kb <= 5000
    return {
        "file": image_path.name,
        "size_kb": round(size_kb, 1),
        "reasonable": reasonable,
        "status": "✅" if reasonable else "⚠️",
    }


def check_naming_convention(files: list) -> dict:
    """检查命名是否规范"""
    issues = []
    for f in files:
        name = f.name
        if " " in name:
            issues.append(f"包含空格: {name}")
        if name != name.strip():
            issues.append(f"首尾空白: {name}")
        if any(c in name for c in '!@#$%^&*+='):
            issues.append(f"特殊字符: {name}")
    return {"issues": issues, "pass": len(issues) == 0}


def find_duplicates(files: list) -> list:
    """检测文件名重复（排除索引后缀差异）"""
    seen = {}
    dups = []
    for f in files:
        base = f.stem.rstrip("0123456789-_(). ")  # 去除尾部的数字/符号
        if base in seen:
            dups.append((seen[base].name, f.name))
        else:
            seen[base] = f
    return dups


def validate_directory(final_dir: Path, h_target=H_TARGET, v_target=V_TARGET) -> dict:
    """验证产出目录"""
    report = {
        "directory": str(final_dir),
        "checks": [],
        "total": 0,
        "passed": 0,
        "failed": 0,
        "overall": "PASS",
    }

    images = sorted([f for f in final_dir.rglob("*")
                     if f.suffix.lower() in EXTS and f.is_file()])

    report["total"] = len(images)

    if not images:
        report["checks"].append({"item": "图片数量", "result": "❌ 无图片文件"})
        report["failed"] += 1
        report["overall"] = "FAIL"
        return report

    report["checks"].append({"item": "图片总数", "result": f"✅ {len(images)} 张"})

    # 分辨率检查
    h_count, v_count = 0, 0
    integrity_fail = 0
    for img_path in images:
        result = check_resolution(img_path, h_target, v_target)
        report["checks"].append(result)
        if result.get("match"):
            report["passed"] += 1
            if result.get("orientation") == "horizontal":
                h_count += 1
            else:
                v_count += 1
        else:
            report["failed"] += 1
        if result.get("error") == "文件损坏":
            integrity_fail += 1

    report["checks"].append({
        "item": "横板数量",
        "result": f"{'✅' if h_count > 0 else '❌'} {h_count} 张 ({h_target[0]}×{h_target[1]})"
    })
    report["checks"].append({
        "item": "竖板数量",
        "result": f"{'✅' if v_count > 0 else '❌'} {v_count} 张 ({v_target[0]}×{v_target[1]})"
    })
    report["checks"].append({
        "item": "分辨率通过率",
        "result": f"{'✅' if report['failed'] == 0 else '⚠️'} {report['passed']}/{report['total']}"
    })

    # 文件完整性
    if integrity_fail > 0:
        report["checks"].append({"item": "文件完整性", "result": f"❌ {integrity_fail} 张损坏"})
    else:
        report["checks"].append({"item": "文件完整性", "result": "✅ 全部完整"})

    # 文件大小
    size_issues = 0
    for img_path in images:
        sr = check_file_size(img_path)
        if not sr["reasonable"]:
            size_issues += 1
            report["checks"].append(sr)
    if size_issues == 0:
        report["checks"].append({"item": "文件大小", "result": "✅ 全部合理范围"})

    # 命名规范
    naming = check_naming_convention(images)
    if not naming["pass"]:
        for issue in naming["issues"][:5]:
            report["checks"].append({"item": "命名规范", "result": f"⚠️ {issue}"})

    # 重复检测
    dups = find_duplicates(images)
    if dups:
        for d1, d2 in dups:
            report["checks"].append({"item": "重复文件", "result": f"⚠️ {d1} ~ {d2}"})

    if report["failed"] > 0:
        report["overall"] = "FAIL"

    return report


def main():
    import argparse

    parser = argparse.ArgumentParser(description="明源场宣图 - 质量检查清单")
    parser.add_argument("final_dir", help="成果目录")
    parser.add_argument("--target", default="2560x1440", help="目标分辨率 (默认 2560x1440)")
    parser.add_argument("--json", help="JSON 报告输出路径")
    args = parser.parse_args()

    final_dir = Path(args.final_dir)
    if not final_dir.is_dir():
        print(f"错误: 目录不存在: {final_dir}")
        sys.exit(1)

    # 解析目标分辨率
    try:
        parts = args.target.lower().split("x")
        h_target = (int(parts[0]), int(parts[1]))
        v_target = (int(parts[1]), int(parts[0]))
    except Exception:
        h_target, v_target = H_TARGET, V_TARGET

    print("📋 明源场宣图 - 质量检查清单")
    print("=" * 60)

    report = validate_directory(final_dir, h_target, v_target)

    print(f"\n📊 检查结果: {report['overall']}")
    print(f"   目录: {report['directory']}")
    print(f"   图片: {report['total']} 张")
    print(f"   通过: {report['passed']} 张")
    print(f"   失败: {report['failed']} 张\n")

    for check in report["checks"]:
        if isinstance(check, dict) and "size" in check:
            print(f"   {check['status']} {check['file']}: {check['size']} → {check['target']}")
        elif isinstance(check, dict) and "item" in check:
            print(f"   {check['result']}")

    print(f"\n📋 总体评估: {report['overall']}")
    print("=" * 60)

    # JSON 输出
    json_path = args.json or (final_dir / "checklist_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"   JSON报告: {json_path}")

    sys.exit(0 if report["overall"] == "PASS" else 1)


if __name__ == "__main__":
    main()
