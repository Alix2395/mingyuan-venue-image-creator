#!/usr/bin/env python3
"""
明源场宣图 - 格式规范化脚本
将原图统一到2K标准：横板2560×1440，竖板1440×2560
等比智能裁切，居中保留主体，禁止拉伸变形

用法：
    python normalize_resolution.py <输入目录> <输出目录> [--json-output <路径>]

输出：自动按横竖分到 <输出目录>/横板/ 和 <输出目录>/竖板/
"""

import sys
import json
from pathlib import Path
from PIL import Image, ImageOps

# 2K 标准分辨率
HORIZONTAL_TARGET = (2560, 1440)   # 横板
VERTICAL_TARGET   = (1440, 2560)   # 竖板
RATIO_TOLERANCE   = 0.03           # 比例偏差容忍度
SUPPORTED_EXTS    = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".heic", ".heif"}


def detect_orientation(w: int, h: int) -> str:
    """判断横竖：w>h → horizontal，否则 vertical"""
    return "horizontal" if w > h else "vertical"


def is_similar_ratio(w: int, h: int, target_w: int, target_h: int) -> bool:
    """判断原图比例是否与目标比例近似（偏差 < RATIO_TOLERANCE）"""
    src_ratio = w / h
    tgt_ratio = target_w / target_h
    return abs(src_ratio - tgt_ratio) < RATIO_TOLERANCE


def resize_to_target(img: Image.Image, target: tuple) -> Image.Image:
    """直接缩放到目标分辨率"""
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

    img_resized = img.resize((new_w, new_h), Image.LANCZOS)

    # 居中裁剪
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img_cropped = img_resized.crop((left, top, left + target_w, top + target_h))

    return img_cropped


def handle_exif_orientation(img: Image.Image) -> Image.Image:
    """根据 EXIF 方向标签旋转图片（修正手机竖拍横存的问题）"""
    try:
        exif = img.getexif()
        orientation = exif.get(0x0112, 1)
        if orientation == 3:
            img = img.rotate(180, expand=True)
        elif orientation == 6:
            img = img.rotate(270, expand=True)
        elif orientation == 8:
            img = img.rotate(90, expand=True)
    except Exception:
        pass  # 无 EXIF 或解析失败，保持不变
    return img


def verify_image(img_path: Path) -> bool:
    """验证图片文件是否完整可打开"""
    try:
        with Image.open(img_path) as img:
            img.verify()  # 检查文件完整性
        return True
    except Exception:
        return False


def process_image(img_path: Path, output_dir: Path) -> dict:
    """
    处理单张图片
    返回结果字典
    """
    result = {
        "file": str(img_path),
        "status": "error",
        "error": "",
        "orientation": "",
        "method": "",
        "output": "",
    }

    try:
        if not verify_image(img_path):
            result["error"] = "图片文件损坏或无法打开"
            return result

        img = Image.open(img_path)

        # 处理 EXIF 方向
        img = handle_exif_orientation(img)

        # 统一转 RGB
        if img.mode == "RGBA":
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
            result_img = resize_to_target(img, target)
            method = "direct_resize"
        else:
            result_img = smart_resize_and_crop(img, tw, th)
            method = "smart_crop"

        # 保存
        out_subdir = output_dir / subdir
        out_subdir.mkdir(parents=True, exist_ok=True)
        out_path = (out_subdir / img_path.name).with_suffix(".jpg")
        result_img.save(out_path, "JPEG", quality=95)

        # 验证输出文件
        fsize = out_path.stat().st_size
        if fsize == 0:
            result["error"] = "输出文件为空"
            return result

        result["status"] = "ok"
        result["output"] = str(out_path)
        result["orientation"] = orient
        result["method"] = method
        result["output_size_kb"] = str(fsize // 1024)

    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    if len(sys.argv) < 3:
        print("用法: python normalize_resolution.py <输入目录> <输出目录> [--json-output <路径>]")
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    json_output = None
    for i, arg in enumerate(sys.argv):
        if arg == "--json-output" and i + 1 < len(sys.argv):
            json_output = Path(sys.argv[i + 1])

    if not input_dir.is_dir():
        print(f"错误: 输入目录不存在: {input_dir}")
        sys.exit(1)

    images = sorted([f for f in input_dir.iterdir() if f.suffix.lower() in SUPPORTED_EXTS and f.is_file()])

    if not images:
        print("错误: 输入目录中没有找到图片文件")
        sys.exit(1)

    print(f"📐 格式规范化开始...")
    print(f"   输入: {input_dir} ({len(images)} 张图片)")
    print(f"   目标: 横板 2560×1440 | 竖板 1440×2560")
    print(f"   输出: {output_dir}/\n")

    stats = {"horizontal": 0, "vertical": 0, "direct_resize": 0, "smart_crop": 0, "error": 0, "exif_fixed": 0}
    results = []

    for img_path in sorted(images):
        r = process_image(img_path, output_dir)
        if r["status"] == "ok":
            stats[r["orientation"]] += 1
            stats[r["method"]] += 1
            print(f"  ✅ {img_path.name} → [{r['orientation']}] {r['method']} ({r['output_size_kb']}KB)")
        else:
            stats["error"] += 1
            print(f"  ❌ {img_path.name}: {r['error']}")
        results.append(r)

    print(f"\n📊 规范化完成:")
    print(f"   横板: {stats['horizontal']} 张 (直缩 {stats['direct_resize']} / 裁剪 {stats['smart_crop']})")
    print(f"   竖板: {stats['vertical']} 张")
    print(f"   失败: {stats['error']} 张")
    print(f"   输出: {output_dir}/横板/ + {output_dir}/竖版/")

    # JSON 输出供脚本调用
    if json_output:
        with open(json_output, "w", encoding="utf-8") as f:
            json.dump({
                "stats": stats,
                "results": results,
                "total": len(images),
                "success": len(images) - stats["error"],
            }, f, ensure_ascii=False, indent=2)
        print(f"   JSON报告: {json_output}")

    sys.exit(0 if stats["error"] == 0 else 1)


if __name__ == "__main__":
    main()
