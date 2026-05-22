#!/usr/bin/env python3
"""
明源场宣图 - 轻度图片优化脚本
统一调整曝光/白平衡/对比度/饱和度，不做破坏性处理

用法：
    python enhance_images.py <输入目录> [输出目录] [--config <config.json>]
    若省略输出目录，则原地覆盖

支持：
    - 自动白平衡（仅修正明显偏色）
    - 亮度 +5% / 对比 +10% / 色饱 +5%
    - EXIF 方向保留
    - 已优化文件自动跳过
    - JSON 配置覆盖默认参数
"""

import sys
import json
from pathlib import Path
from PIL import Image, ImageEnhance, ImageStat

# 默认优化参数
DEFAULT_PARAMS = {
    "brightness": 1.05,
    "contrast":   1.10,
    "color":      1.05,
    "sharpness":  1.00,
}

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def load_config(config_path) -> dict:
    """加载配置，与默认值合并"""
    params = dict(DEFAULT_PARAMS)
    if config_path and config_path.is_file():
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        enhance_cfg = cfg.get("enhance", {})
        for k in params:
            if k in enhance_cfg:
                params[k] = float(enhance_cfg[k])
    return params


def auto_white_balance(img: Image.Image, threshold: float = 0.03) -> Image.Image:
    """
    自动白平衡：基于通道均值的简单修正
    仅当通道偏差 > threshold 时才修正，幅度限制在 2%-8%
    """
    stat = ImageStat.Stat(img)
    r_mean, g_mean, b_mean = stat.mean[:3]
    avg = (r_mean + g_mean + b_mean) / 3.0

    if (abs(r_mean - avg) / avg < threshold and
        abs(g_mean - avg) / avg < threshold and
        abs(b_mean - avg) / avg < threshold):
        return img  # 无需修正

    r, g, b = img.split()
    r_factor = max(0.92, min(1.08, avg / max(r_mean, 1)))
    g_factor = max(0.92, min(1.08, avg / max(g_mean, 1)))
    b_factor = max(0.92, min(1.08, avg / max(b_mean, 1)))

    r = r.point(lambda x: min(255, int(x * r_factor)))
    g = g.point(lambda x: min(255, int(x * g_factor)))
    b = b.point(lambda x: min(255, int(x * b_factor)))

    return Image.merge("RGB", (r, g, b))


def get_image_quality_signature(img_path: Path) -> float:
    """计算图像质量签名：文件大小/像素数，用于检测质量退化"""
    with Image.open(img_path) as img:
        pixels = img.width * img.height
        size = img_path.stat().st_size
        return size / pixels if pixels > 0 else 0


def enhance_image(img_path: Path, output_dir: Path, params: dict = None) -> tuple:
    """
    对单张图片进行轻度优化
    返回 (success: bool, message: str)
    """
    if params is None:
        params = DEFAULT_PARAMS

    try:
        # 检查是否已处理（避免重复处理）
        out_path = output_dir / img_path.name
        if out_path.suffix.lower() not in (".jpg", ".jpeg"):
            out_path = out_path.with_suffix(".jpg")
        if out_path.exists() and out_path.stat().st_mtime >= img_path.stat().st_mtime:
            return True, "skip (already processed)"

        img = Image.open(img_path)

        # 保留 EXIF 信息
        exif_data = img.info.get("exif", b"")

        # 统一为 RGB
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # 处理前签名（用于质量退化检测）
        quality_before = get_image_quality_signature(img_path)

        # 1. 自动白平衡
        img = auto_white_balance(img)

        # 2. 亮度
        img = ImageEnhance.Brightness(img).enhance(params.get("brightness", 1.05))

        # 3. 对比度
        img = ImageEnhance.Contrast(img).enhance(params.get("contrast", 1.10))

        # 4. 色彩饱和度
        img = ImageEnhance.Color(img).enhance(params.get("color", 1.05))

        # 5. 锐度（默认不变）
        img = ImageEnhance.Sharpness(img).enhance(params.get("sharpness", 1.0))

        # 保存，保留原始 EXIF
        output_dir.mkdir(parents=True, exist_ok=True)
        img.save(out_path, "JPEG", quality=95, exif=exif_data)

        # 质量退化检查
        quality_after = get_image_quality_signature(out_path)
        if quality_before > 0 and quality_after / quality_before < 0.3:
            return False, f"quality degraded: {quality_before:.4f} → {quality_after:.4f}"

        return True, "ok"

    except Exception as e:
        return False, str(e)


def process_directory(input_dir: Path, output_dir: Path, params: dict = None):
    """处理目录内所有图片"""
    images = sorted([f for f in input_dir.iterdir()
                     if f.suffix.lower() in SUPPORTED_EXTS and f.is_file()])

    if not images:
        print(f"  目录为空或无图片: {input_dir}")
        return

    total = len(images)
    count_ok = 0
    count_skip = 0

    for idx, img_path in enumerate(images):
        progress = f"[{idx+1}/{total}]"
        print(f"  {progress} {img_path.name} ... ", end="", flush=True)
        success, msg = enhance_image(img_path, output_dir, params)
        if success:
            if msg.startswith("skip"):
                print(f"⏭️  ({msg})")
                count_skip += 1
            else:
                print("✅")
                count_ok += 1
        else:
            print(f"❌ {msg}")

    done = count_ok + count_skip
    print(f"  完成: {done}/{total} 张 (优化{count_ok} + 跳过{count_skip})\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="明源场宣图 - 轻度图片优化")
    parser.add_argument("input_dir", help="输入目录")
    parser.add_argument("output_dir", nargs="?", help="输出目录（省略则原地覆盖）")
    parser.add_argument("--config", help="JSON 配置文件路径")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir) if args.output_dir else input_dir
    config_path = Path(args.config) if args.config else None

    if not input_dir.is_dir():
        print(f"错误: 目录不存在: {input_dir}")
        sys.exit(1)

    params = load_config(config_path)

    print(f"🎨 轻度图片优化开始...")
    print(f"   参数: 亮度+{int((params['brightness']-1)*100)}% / "
          f"对比度+{int((params['contrast']-1)*100)}% / "
          f"饱和度+{int((params['color']-1)*100)}% / "
          f"锐度x{params['sharpness']:.2f}")
    if config_path:
        print(f"   配置文件: {config_path}")
    print()

    # 检查输入目录是否含有子目录
    subdirs = [d for d in input_dir.iterdir() if d.is_dir()]
    if subdirs:
        for subdir in sorted(subdirs):
            print(f"  📂 {subdir.name}/")
            out_sub = output_dir / subdir.name
            process_directory(subdir, out_sub)
    else:
        process_directory(input_dir, output_dir)

    print("🎨 优化完成！")


if __name__ == "__main__":
    main()
