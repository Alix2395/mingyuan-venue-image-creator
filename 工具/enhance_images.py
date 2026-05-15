#!/usr/bin/env python3
"""
明源场宣图 - 轻度图片优化脚本
统一调整曝光/白平衡/对比度/饱和度，不做破坏性处理

用法：
    python enhance_images.py <输入目录> [输出目录]
    若省略输出目录，则原地覆盖（输入目录内图片被替换）
"""

import sys
import os
from pathlib import Path
from PIL import Image, ImageEnhance, ImageStat


# 默认优化参数（保守值，避免破坏原图）
DEFAULT_PARAMS = {
    "brightness": 1.05,   # 亮度 +5%
    "contrast":   1.10,   # 对比度 +10%
    "color":      1.05,   # 色彩饱和度 +5%
    "sharpness":  1.00,   # 锐度不变（防止过度锐化）
}


def auto_white_balance(img: Image.Image) -> Image.Image:
    """
    自动白平衡：基于图像统计均值的简单修正
    不做大幅调整，仅修正明显偏色
    """
    stat = ImageStat.Stat(img)
    r_mean, g_mean, b_mean = stat.mean[:3]
    avg = (r_mean + g_mean + b_mean) / 3.0

    # 仅当通道偏差 > 3% 时才修正
    threshold = 0.03
    if (abs(r_mean - avg) / avg < threshold and
        abs(g_mean - avg) / avg < threshold and
        abs(b_mean - avg) / avg < threshold):
        return img  # 无需修正

    # 分离通道并平衡
    r, g, b = img.split()

    r_factor = avg / max(r_mean, 1)
    g_factor = avg / max(g_mean, 1)
    b_factor = avg / max(b_mean, 1)

    # 限制修正幅度在 2%-8% 之间
    r_factor = max(0.92, min(1.08, r_factor))
    g_factor = max(0.92, min(1.08, g_factor))
    b_factor = max(0.92, min(1.08, b_factor))

    r = r.point(lambda x: min(255, int(x * r_factor)))
    g = g.point(lambda x: min(255, int(x * g_factor)))
    b = b.point(lambda x: min(255, int(x * b_factor)))

    return Image.merge("RGB", (r, g, b))


def enhance_image(img_path: Path, output_dir: Path, params: dict = None) -> bool:
    """对单张图片进行轻度优化"""
    if params is None:
        params = DEFAULT_PARAMS

    try:
        img = Image.open(img_path)

        # 统一为 RGB
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

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

        # 保存
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / img_path.name
        if out_path.suffix.lower() not in (".jpg", ".jpeg"):
            out_path = out_path.with_suffix(".jpg")
        img.save(out_path, "JPEG", quality=95)
        return True

    except Exception as e:
        print(f"    错误: {e}")
        return False


def process_directory(input_dir: Path, output_dir: Path, params: dict = None):
    """递归处理目录内所有图片"""
    extensions = {".jpg", ".jpeg", ".png"}
    images = sorted([f for f in input_dir.iterdir()
                     if f.suffix.lower() in extensions and f.is_file()])

    if not images:
        print(f"  目录为空或无图片: {input_dir}")
        return

    count_ok = 0
    for img_path in images:
        print(f"    {img_path.name} ... ", end="")
        if enhance_image(img_path, output_dir, params):
            print("✅")
            count_ok += 1
        else:
            print("❌")

    print(f"  完成: {count_ok}/{len(images)} 张\n")


def main():
    if len(sys.argv) < 2:
        print("用法: python enhance_images.py <输入目录> [输出目录]")
        print("  若省略输出目录，则原地覆盖")
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else input_dir

    if not input_dir.is_dir():
        print(f"错误: 目录不存在: {input_dir}")
        sys.exit(1)

    print(f"🎨 轻度图片优化开始...")
    print(f"   参数: 亮度+5% / 对比度+10% / 饱和度+5% / 自动白平衡\n")

    # 检查输入目录是否含有子目录（如 横板/竖板）
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
