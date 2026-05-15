#!/usr/bin/env python3
"""
明源场宣图 - 格式规范化脚本
将原图统一到2K标准：横板2560×1440，竖板1440×2560
等比智能裁切，居中保留主体，禁止拉伸变形

用法：
    python normalize_resolution.py <输入目录> <输出目录>

输出：自动按横竖分到 <输出目录>/横板/ 和 <输出目录>/竖板/
"""

import sys
import os
from pathlib import Path
from PIL import Image, ImageOps

# 2K 标准分辨率
HORIZONTAL_TARGET = (2560, 1440)   # 横板
VERTICAL_TARGET   = (1440, 2560)   # 竖板
RATIO_TOLERANCE   = 0.03           # 比例偏差容忍度（3%以内视为相同比例）


def detect_orientation(w: int, h: int) -> str:
    """判断横竖：w>h → horizontal，否则 vertical，等宽视为横板"""
    return "horizontal" if w >= h else "vertical"


def is_similar_ratio(w: int, h: int, target_w: int, target_h: int) -> bool:
    """判断原图比例是否与目标比例极其近似"""
    src_ratio = w / h
    tgt_ratio = target_w / target_h
    return abs(src_ratio - tgt_ratio) < RATIO_TOLERANCE


def resize_to_target(img: Image.Image, target: tuple) -> Image.Image:
    """直接缩放到目标分辨率（比例接近时使用）"""
    return img.resize(target, Image.LANCZOS)


def smart_resize_and_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    智能等比缩放 + 居中裁剪：
    1. 等比缩放到短边贴合目标
    2. 居中裁剪长边至目标尺寸
    不会拉伸变形
    """
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # 原图更宽 → 高度对齐后裁剪宽度
        new_h = target_h
        new_w = int(src_w * target_h / src_h)
    else:
        # 原图更高 → 宽度对齐后裁剪高度
        new_w = target_w
        new_h = int(src_h * target_w / src_w)

    # 等比缩放
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)

    # 居中裁剪
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img_cropped = img_resized.crop((left, top, left + target_w, top + target_h))

    return img_cropped


def process_image(img_path: Path, output_dir: Path) -> tuple:
    """
    处理单张图片：
    返回 (success, target_path, orientation, method)
    """
    try:
        img = Image.open(img_path)
        # 统一转 RGB（去掉 alpha 通道以便后续处理，但保留透明度信息备用）
        if img.mode == "RGBA":
            # 有透明度：合成到白底
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        w, h = img.size
        orient = detect_orientation(w, h)
        target = HORIZONTAL_TARGET if orient == "horizontal" else VERTICAL_TARGET
        tw, th = target
        subdir = "横板" if orient == "horizontal" else "竖版"

        if is_similar_ratio(w, h, tw, th):
            result = resize_to_target(img, target)
            method = "direct_resize"
        else:
            result = smart_resize_and_crop(img, tw, th)
            method = "smart_crop"

        # 保存
        out_subdir = output_dir / subdir
        out_subdir.mkdir(parents=True, exist_ok=True)
        out_path = out_subdir / img_path.name
        # 统一输出为 .jpg（保留原扩展名逻辑）
        out_path = out_path.with_suffix(".jpg")
        result.save(out_path, "JPEG", quality=95)

        return (True, str(out_path), orient, method)

    except Exception as e:
        return (False, str(img_path), str(e), "error")


def main():
    if len(sys.argv) < 3:
        print("用法: python normalize_resolution.py <输入目录> <输出目录>")
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    if not input_dir.is_dir():
        print(f"错误: 输入目录不存在: {input_dir}")
        sys.exit(1)

    # 支持的图片格式
    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".heic", ".heif"}
    images = [f for f in input_dir.iterdir() if f.suffix.lower() in extensions and f.is_file()]

    if not images:
        print("错误: 输入目录中没有找到图片文件")
        sys.exit(1)

    print(f"📐 格式规范化开始...")
    print(f"   输入: {input_dir} ({len(images)} 张图片)")
    print(f"   目标: 横板 2560×1440 | 竖板 1440×2560")
    print(f"   输出: {output_dir}/\n")

    stats = {"horizontal": 0, "vertical": 0, "direct_resize": 0, "smart_crop": 0, "error": 0}
    results = []

    for img_path in sorted(images):
        print(f"  处理: {img_path.name} ... ", end="")
        success, path_or_err, orient, method = process_image(img_path, output_dir)

        if success:
            stats[orient] += 1
            stats[method] += 1
            print(f"✅ [{orient}] {method}")
            results.append({"file": str(img_path), "output": path_or_err, "orientation": orient, "method": method, "status": "ok"})
        else:
            stats["error"] += 1
            print(f"❌ {orient}")
            results.append({"file": str(img_path), "error": path_or_err, "status": "error"})

    print(f"\n📊 规范化完成:")
    print(f"   横板: {stats['horizontal']} 张 (直缩 {stats['direct_resize']} / 裁剪 {stats['smart_crop']})")
    print(f"   竖板: {stats['vertical']} 张")
    print(f"   失败: {stats['error']} 张")
    print(f"   输出: {output_dir}/横板/ + {output_dir}/竖版/")

    return stats["error"] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
