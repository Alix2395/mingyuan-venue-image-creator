#!/usr/bin/env python3
"""
明源场宣图 - 检查清单验证器
逐项验证产出是否满足质量要求

用法：
    python checklist_validator.py <成果目录>
"""

import sys
import json
from pathlib import Path
from PIL import Image


H_TARGET = (2560, 1440)
V_TARGET = (1440, 2560)


def check_resolution(image_path: Path) -> dict:
    """检查单张图片分辨率"""
    try:
        img = Image.open(image_path)
        w, h = img.size
        orient = "horizontal" if w >= h else "vertical"
        target = H_TARGET if orient == "horizontal" else V_TARGET

        match = (w == target[0] and h == target[1])
        return {
            "file": str(image_path.name),
            "size": f"{w}x{h}",
            "target": f"{target[0]}x{target[1]}",
            "orientation": orient,
            "match": match,
            "status": "✅" if match else "❌",
        }
    except Exception as e:
        return {
            "file": str(image_path.name),
            "status": "❌",
            "error": str(e),
        }


def validate_directory(final_dir: Path) -> dict:
    """验证产出目录"""
    report = {
        "directory": str(final_dir),
        "checks": [],
        "total": 0,
        "passed": 0,
        "failed": 0,
        "overall": "PASS",
    }

    # 收集所有图片
    exts = {".jpg", ".jpeg", ".png"}
    images = sorted([f for f in final_dir.rglob("*")
                     if f.suffix.lower() in exts and f.is_file()])

    report["total"] = len(images)

    if not images:
        report["checks"].append({"item": "图片数量", "result": "❌ 无图片文件"})
        report["failed"] += 1
        report["overall"] = "FAIL"
        return report

    report["checks"].append({"item": "图片总数", "result": f"✅ {len(images)} 张"})

    # 检查分辨率
    h_count, v_count = 0, 0
    for img_path in images:
        result = check_resolution(img_path)
        report["checks"].append(result)
        if result.get("match"):
            report["passed"] += 1
            if result.get("orientation") == "horizontal":
                h_count += 1
            else:
                v_count += 1
        else:
            report["failed"] += 1

    report["checks"].append({
        "item": "横板数量",
        "result": f"{'✅' if h_count > 0 else '❌'} {h_count} 张 (2560×1440)"
    })
    report["checks"].append({
        "item": "竖板数量",
        "result": f"{'✅' if v_count > 0 else '❌'} {v_count} 张 (1440×2560)"
    })
    report["checks"].append({
        "item": "分辨率通过率",
        "result": f"{'✅' if report['failed'] == 0 else '⚠️'} {report['passed']}/{report['total']}"
    })

    if report["failed"] > 0:
        report["overall"] = "FAIL"

    return report


def main():
    if len(sys.argv) < 2:
        print("用法: python checklist_validator.py <成果目录>")
        sys.exit(1)

    final_dir = Path(sys.argv[1])

    if not final_dir.is_dir():
        print(f"错误: 目录不存在: {final_dir}")
        sys.exit(1)

    print("📋 明源场宣图 - 质量检查清单")
    print("=" * 60)

    report = validate_directory(final_dir)

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

    # 同时输出 JSON 报告
    json_path = final_dir / "checklist_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"   JSON报告: {json_path}")

    sys.exit(0 if report["overall"] == "PASS" else 1)


if __name__ == "__main__":
    main()
