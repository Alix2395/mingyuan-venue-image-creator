#!/usr/bin/env python3
"""
明源场宣图 - 一键全链路处理管线

用法：
    python pipeline.py <输入zip文件> <配置.json> [--output-dir 成果/]
                     [--auto-confirm] [--cleanup]

流程：
    [阶段0] 解包zip + 素材审计（含CJK字体验证）
    [阶段1] 格式规范化 → 2K标准
    [阶段2] 轻度图片优化
    [阶段3] 素材叠加 → 先样板确认或全量
    [阶段4] 打包zip交付 + 清理临时文件
"""

import sys
import os
import json
import zipfile
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

SCRIPTS_DIR = Path(__file__).parent.resolve()

# CJK 字体候选
CJK_CANDIDATES = [
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/arphic/ukai.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
]


def check_cjk_fonts():
    """验证 CJK 字体可用"""
    from PIL import ImageFont
    available = [p for p in CJK_CANDIDATES
                 if Path(p).is_file() and ImageFont.truetype(p, 20)]
    if not available:
        print("❌ 无可用 CJK 字体！请先安装:")
        print("   apt-get install -y fonts-wqy-zenhei fonts-noto-cjk")
        sys.exit(1)
    print(f"✅ CJK 字体可用: {Path(available[0]).name}\n")


def validate_config(config_path: str) -> dict:
    """验证配置文件"""
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if not config.get("assets"):
        print("❌ 配置错误: assets 不能为空")
        sys.exit(1)

    for i, a in enumerate(config["assets"]):
        if "file" not in a:
            print(f"❌ 配置错误: assets[{i}] 缺少 file")
            sys.exit(1)

    print(f"✅ 配置验证通过: {len(config['assets'])} 个素材")
    return config


def run_script(script_name: str, args: list) -> bool:
    """运行工具脚本"""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.is_file():
        print(f"❌ 脚本不存在: {script_path}")
        return False
    cmd = [sys.executable, str(script_path)] + args
    result = subprocess.run(cmd)
    return result.returncode == 0


def stage0_unpack(zip_path: str, work_dir: Path):
    """阶段0：解包 + 素材审计"""
    print("=" * 60)
    print("📦 阶段0：解包 & 素材审计")
    print("=" * 60)

    extract_dir = work_dir / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)

    # 验证zip文件
    if not zipfile.is_zipfile(zip_path):
        print(f"❌ 无效的 zip 文件: {zip_path}")
        return None, None, None

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

    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
    originals = sorted([f for f in originals_dir.iterdir()
                        if f.suffix.lower() in exts and f.is_file()])
    print(f"   原图: {len(originals)} 张")

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
    success = run_script("normalize_resolution.py",
                         [str(originals_dir), str(norm_dir)])
    if not success:
        print("⚠️  规范化部分失败")
    return norm_dir


def stage2_enhance(norm_dir: Path, work_dir: Path) -> Path:
    """阶段2：轻度优化"""
    print("\n" + "=" * 60)
    print("🎨 阶段2：轻度图片优化")
    print("=" * 60)
    enhance_dir = work_dir / "enhanced"
    success = run_script("enhance_images.py",
                         [str(norm_dir), str(enhance_dir)])
    if not success:
        print("⚠️  优化部分失败")
    return enhance_dir


def stage3_overlay_sample(enhance_dir: Path, config_path: str, work_dir: Path) -> Path:
    """阶段3样板：先各1张确认"""
    print("\n" + "=" * 60)
    print("🖼️  阶段3：素材叠加（样板确认模式）")
    print("=" * 60)
    sample_dir = work_dir / "samples"
    run_script("overlay_assets.py",
               [str(enhance_dir), config_path, str(sample_dir), "--limit", "1"])
    print("\n  ⚠️ 样板已生成，请确认效果后继续全量处理")
    print(f"  样板目录: {sample_dir}")
    return sample_dir


def stage3_full(enhance_dir: Path, config_path: str, work_dir: Path) -> Path:
    """阶段3全量：叠加所有图片"""
    print("\n" + "=" * 60)
    print("🖼️  阶段3全量：素材叠加所有图片")
    print("=" * 60)
    final_dir = work_dir / "final"
    success = run_script("overlay_assets.py",
                         [str(enhance_dir), config_path, str(final_dir)])
    if not success:
        print("⚠️  叠加部分失败")
    return final_dir


def stage4_package(final_dir: Path, output_dir: Path, task_name: str = "") -> Path:
    """阶段4：打包交付"""
    print("\n" + "=" * 60)
    print("📦 阶段4：打包交付")
    print("=" * 60)
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    suffix = f"_{task_name}" if task_name else ""
    zip_name = f"场宣图_成品_{date_str}{suffix}.zip"
    zip_path = output_dir / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(final_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(final_dir)
                zf.write(file_path, arcname)

    size_mb = zip_path.stat().st_size / 1024 / 1024
    print(f"   ✅ 打包完成: {zip_path} ({size_mb:.1f} MB)")
    return zip_path


def cleanup(work_dir: Path, keep_extracted: bool = False):
    """清理临时文件"""
    if not work_dir.exists():
        return
    if keep_extracted:
        # 只清理 final 和 samples（保留 extracted 供审计）
        for d in ["final", "samples", "normalized", "enhanced"]:
            p = work_dir / d
            if p.exists():
                shutil.rmtree(p)
                print(f"   🗑️  清理: {d}/")
    else:
        shutil.rmtree(work_dir)
        print(f"   🗑️  清理临时目录: {work_dir}")


def main():
    parser = argparse.ArgumentParser(description="明源场宣图 - 全链路处理管线")
    parser.add_argument("zip_path", help="输入 zip 文件")
    parser.add_argument("config_path", help="配置 JSON 文件")
    parser.add_argument("--output-dir", default="成果", help="输出目录 (默认: 成果/)")
    parser.add_argument("--auto-confirm", action="store_true",
                        help="跳过样板确认，直接全量处理")
    parser.add_argument("--cleanup", action="store_true",
                        help="处理完成后清理临时文件")
    parser.add_argument("--skip-cjk-check", action="store_true",
                        help="跳过 CJK 字体检查")
    parser.add_argument("--task-name", default="", help="任务名称（用于文件命名）")
    args = parser.parse_args()

    zip_path = Path(args.zip_path)
    config_path = Path(args.config_path)
    output_dir = Path(args.output_dir)

    if not zip_path.is_file():
        print(f"❌ zip 文件不存在: {zip_path}")
        sys.exit(1)
    if not config_path.is_file():
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)

    print("🚀 明源场宣图 - 全链路处理管线")
    print(f"   输入: {zip_path}")
    print(f"   配置: {config_path}")
    print(f"   输出: {output_dir}")
    print(f"   模式: {'自动全量' if args.auto_confirm else '样板确认'}")
    if args.task_name:
        print(f"   任务: {args.task_name}")
    print()

    # 门禁：CJK 字体检查
    if not args.skip_cjk_check:
        check_cjk_fonts()

    # 门禁：配置验证
    validate_config(str(config_path))

    work_dir = Path(f"临时/pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    work_dir.mkdir(parents=True, exist_ok=True)

    # 阶段0
    extracted, originals_dir, assets_dir = stage0_unpack(str(zip_path), work_dir)
    if not originals_dir:
        cleanup(work_dir)
        sys.exit(1)

    # 阶段1
    norm_dir = stage1_normalize(originals_dir, work_dir)

    # 阶段2
    enhance_dir = stage2_enhance(norm_dir, work_dir)

    # 阶段3
    if args.auto_confirm:
        final_dir = stage3_full(enhance_dir, str(config_path), work_dir)
        zip_out = stage4_package(final_dir, output_dir, args.task_name)
    else:
        stage3_overlay_sample(enhance_dir, str(config_path), work_dir)
        print("\n⚠️  样板已生成，请确认后手动运行全量处理")
        print(f"   工作目录: {work_dir}")
        print("   全量命令: python pipeline.py ... --auto-confirm")
        cleanup(work_dir, keep_extracted=True)
        sys.exit(0)

    # 阶段4已完成（在 auto-confirm 分支内）
    print(f"\n   ✅ 成品: {zip_out}")

    # 清理
    if args.cleanup:
        cleanup(work_dir)

    print("\n" + "=" * 60)
    print("🎉 管线执行完毕！")
    print(f"   工作目录: {work_dir}")
    print(f"   成品: {zip_out}")
    print("=" * 60)


if __name__ == "__main__":
    main()
