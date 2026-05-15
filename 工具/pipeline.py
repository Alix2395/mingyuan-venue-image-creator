#!/usr/bin/env python3
"""
明源场宣图 - 一键全链路处理管线
用法：
    python pipeline.py <输入zip文件> <配置.json> [--output-dir 成果/]

流程：
    [阶段0] 解包zip + 素材审计
    [阶段1] 格式规范化 → 2K标准
    [阶段2] 轻度图片优化
    [阶段3] 素材叠加 → 先各1张样板确认
    [阶段4] 打包zip交付
"""

import sys
import os
import json
import zipfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


SCRIPTS_DIR = Path(__file__).parent.resolve()


def run_script(script_name: str, args: list) -> bool:
    """运行工具脚本，返回是否成功"""
    script_path = SCRIPTS_DIR / script_name
    cmd = [sys.executable, str(script_path)] + args
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def stage0_unpack(zip_path: str, work_dir: Path) -> tuple:
    """阶段0：解包 + 素材审计"""
    print("=" * 60)
    print("📦 阶段0：解包 & 素材审计")
    print("=" * 60)

    extract_dir = work_dir / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    # 查找素材/和原图/目录
    assets_dir = None
    originals_dir = None

    for item in extract_dir.rglob("*"):
        if item.is_dir():
            if item.name == "素材":
                assets_dir = item
            elif item.name == "原图":
                originals_dir = item

    if not originals_dir:
        print("❌ 未找到「原图」文件夹！")
        return None, None, None

    # 统计原图
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
    originals = sorted([f for f in originals_dir.iterdir()
                        if f.suffix.lower() in exts and f.is_file()])
    print(f"   原图: {len(originals)} 张")

    # 统计素材
    assets = []
    if assets_dir:
        assets = sorted([f for f in assets_dir.iterdir()
                         if f.suffix.lower() == ".png" and f.is_file()])
        print(f"   素材: {len(assets)} 个")
        for a in assets:
            print(f"      - {a.name}")

    return extract_dir, originals_dir, assets_dir


def stage1_normalize(originals_dir: Path, work_dir: Path) -> Path:
    """阶段1：格式规范化"""
    print("\n" + "=" * 60)
    print("📐 阶段1：格式规范化（2K 标准）")
    print("=" * 60)

    norm_dir = work_dir / "normalized"
    success = run_script("normalize_resolution.py", [str(originals_dir), str(norm_dir)])

    if not success:
        print("⚠️  规范化部分失败，继续处理已完成的图片...")

    return norm_dir


def stage2_enhance(norm_dir: Path, work_dir: Path) -> Path:
    """阶段2：轻度优化"""
    print("\n" + "=" * 60)
    print("🎨 阶段2：轻度图片优化")
    print("=" * 60)

    enhance_dir = work_dir / "enhanced"
    success = run_script("enhance_images.py", [str(norm_dir), str(enhance_dir)])

    if not success:
        print("⚠️  优化部分失败，继续...")

    return enhance_dir


def stage3_overlay(enhance_dir: Path, config_path: str, work_dir: Path) -> Path:
    """阶段3：素材叠加 - 先各1张样板确认"""
    print("\n" + "=" * 60)
    print("🖼️  阶段3：素材叠加（样板确认模式）")
    print("=" * 60)

    final_dir = work_dir / "final"

    # 先做样板（横板1张 + 竖板1张）
    print("\n  🔍 生成样板...")
    sample_dir = work_dir / "samples"
    run_script("overlay_assets.py",
               [str(enhance_dir), config_path, str(sample_dir), "--limit", "1"])

    print("\n  ⚠️ 样板已生成，请确认效果后继续全量处理")
    print(f"  样板目录: {sample_dir}")

    # 在自动化测试中，确认后继续全量
    return final_dir


def stage3_full(enhance_dir: Path, config_path: str, work_dir: Path) -> Path:
    """阶段3全量：素材叠加所有图片"""
    print("\n" + "=" * 60)
    print("🖼️  阶段3全量：素材叠加所有图片")
    print("=" * 60)

    final_dir = work_dir / "final"
    success = run_script("overlay_assets.py",
                         [str(enhance_dir), config_path, str(final_dir)])

    if not success:
        print("⚠️  叠加部分失败")

    return final_dir


def stage4_package(final_dir: Path, output_dir: Path) -> Path:
    """阶段4：打包交付"""
    print("\n" + "=" * 60)
    print("📦 阶段4：打包交付")
    print("=" * 60)

    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    zip_name = f"场宣图_成品_{date_str}.zip"
    zip_path = output_dir / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(final_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(final_dir)
                zf.write(file_path, arcname)

    print(f"   ✅ 打包完成: {zip_path}")
    print(f"   大小: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
    return zip_path


def main():
    if len(sys.argv) < 3:
        print("用法: python pipeline.py <输入.zip> <配置.json> [--output-dir 成果/] [--auto-confirm]")
        print("  --auto-confirm  跳过样板确认，直接全量处理")
        sys.exit(1)

    zip_path = sys.argv[1]
    config_path = sys.argv[2]

    output_dir = Path("成果")
    auto_confirm = False
    for i, arg in enumerate(sys.argv):
        if arg == "--output-dir" and i + 1 < len(sys.argv):
            output_dir = Path(sys.argv[i + 1])
        if arg == "--auto-confirm":
            auto_confirm = True

    work_dir = Path("临时") / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    work_dir.mkdir(parents=True, exist_ok=True)

    print("🚀 明源场宣图 - 全链路处理管线")
    print(f"   输入: {zip_path}")
    print(f"   配置: {config_path}")
    print(f"   输出: {output_dir}\n")

    # 阶段0
    extracted, originals_dir, assets_dir = stage0_unpack(zip_path, work_dir)
    if not originals_dir:
        return

    # 阶段1
    norm_dir = stage1_normalize(originals_dir, work_dir)

    # 阶段2
    enhance_dir = stage2_enhance(norm_dir, work_dir)

    # 阶段3
    if auto_confirm:
        final_dir = stage3_full(enhance_dir, config_path, work_dir)
        # 阶段4
        zip_out = stage4_package(final_dir, output_dir)
    else:
        final_dir = stage3_overlay(enhance_dir, config_path, work_dir)
        # 等用户确认后，手动运行 stage3_full + stage4_package

    print("\n" + "=" * 60)
    print("🎉 管线执行完毕！")
    print(f"   工作目录: {work_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
