#!/usr/bin/env python3
"""
明源场宣图 - 测试数据生成器
生成多种分辨率的测试原图 + 半透明PNG素材，用于管线测试

用法：
    python generate_test_data.py [--output 测试数据/] [--count 28] [--seed 42]

改进：
    - 可指定生成数量
    - 固定种子保证可重现
    - shutil 全局导入
    - CJK 字体严格验证
"""

import sys
import os
import shutil
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# CJK 字体候选（硬性要求）
CJK_CANDIDATES = [
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/arphic/ukai.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
]

# 常见设备分辨率
REAL_WORLD_RESOLUTIONS = [
    (3024, 4032), (4032, 3024), (3000, 4000), (4000, 3000),
    (2268, 4032), (4032, 2268),
    (5472, 3648), (3648, 5472), (6000, 4000), (4000, 6000),
    (7360, 4912), (8256, 5504),
    (3840, 2160), (2160, 3840), (1920, 1080), (1080, 1920),
    (1125, 2436), (1242, 2688),
    (2560, 1440), (1440, 2560), (5120, 2880), (2880, 5120),
    (2500, 1420), (1420, 2500),
    (8000, 2000), (2000, 8000), (1000, 1000), (1200, 1500),
]

COLORS = [
    (70, 130, 180), (60, 179, 113), (218, 165, 32),
    (205, 92, 92), (147, 112, 219), (255, 127, 80),
    (100, 149, 237), (240, 128, 128),
]


def get_cjk_font(size: int):
    """获取 CJK 字体，不存在则抛出异常"""
    for p in CJK_CANDIDATES:
        try:
            return ImageFont.truetype(p, size)
        except (IOError, OSError):
            continue
    raise RuntimeError("❌ 无可用 CJK 字体！中文将渲染为豆腐块。请安装 fonts-wqy-zenhei")


def create_placeholder_image(width: int, height: int, index: int) -> Image.Image:
    """生成带编号和色彩标记的占位图片"""
    img = Image.new("RGB", (width, height), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    color = COLORS[index % len(COLORS)]

    # 背景色块（左侧）
    bar_width = width // 8
    for x in range(bar_width):
        draw.line([(x, 0), (x, height)], fill=color)

    # 分辨率文字
    text = f"IMG_{index+1:03d}\n{width}x{height}"
    font_size = min(width, height) // 10
    font = get_cjk_font(font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (width - tw) // 2
    y = (height - th) // 2
    draw.text((x, y), text, fill=(60, 60, 60), font=font)

    # 边框
    border = max(1, min(width, height) // 100)
    draw.rectangle([border, border, width - border, height - border],
                   outline=color, width=border * 2)

    return img


def create_logo_asset(size: int = 200) -> Image.Image:
    """创建半透明Logo素材"""
    img = Image.new("RGBA", (size * 2, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 5
    draw.rounded_rectangle(
        [margin, margin, size * 2 - margin, size - margin],
        radius=15, fill=(255, 255, 255, 160),
        outline=(255, 255, 255, 200), width=2,
    )
    font = get_cjk_font(size // 3)
    text = "明源云"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size * 2 - tw) // 2, (size - th) // 2),
              text, fill=(40, 80, 160, 230), font=font)
    return img


def create_watermark_asset(size: int = 300) -> Image.Image:
    """创建半透明水印素材"""
    img = Image.new("RGBA", (size, size // 4), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_cjk_font(size // 6)
    text = "© 明源云海南 · 场宣专用"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) // 2, (size // 4 - th) // 2),
              text, fill=(255, 255, 255, 100), font=font)
    return img


def create_qrcode_placeholder(size: int = 150) -> Image.Image:
    """创建模拟二维码占位素材"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, size, size], radius=8, fill=(255, 255, 255, 200))
    block = size // 8
    for i in range(3):
        for j in range(3):
            if (i + j) % 2 == 0:
                x = block * 2 + i * block
                y = block * 2 + j * block
                draw.rectangle([x, y, x + block, y + block], fill=(40, 40, 40, 200))
    return img


def main():
    import random

    output_dir = Path("测试数据")
    count = 28
    seed = 42

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--output" and i + 1 < len(sys.argv):
            output_dir = Path(sys.argv[i + 1])
            i += 2
        elif arg == "--count" and i + 1 < len(sys.argv):
            count = int(sys.argv[i + 1])
            i += 2
        elif arg == "--seed" and i + 1 < len(sys.argv):
            seed = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    output_dir.mkdir(parents=True, exist_ok=True)
    random.seed(seed)

    assets_dir = output_dir / "素材"
    originals_dir = output_dir / "原图"
    for d in [assets_dir, originals_dir]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    print("🧪 明源场宣图 - 测试数据生成器")
    print("=" * 60)

    # 生成素材
    print("\n📌 生成素材...")
    logo = create_logo_asset(300)
    logo.save(assets_dir / "logo_明源云.png", "PNG")
    print("   ✅ logo_明源云.png (半透明Logo)")

    watermark = create_watermark_asset(500)
    watermark.save(assets_dir / "watermark_copyright.png", "PNG")
    print("   ✅ watermark_copyright.png (版权水印)")

    qrcode = create_qrcode_placeholder()
    qrcode.save(assets_dir / "qrcode_placeholder.png", "PNG")
    print("   ✅ qrcode_placeholder.png (二维码占位)")

    deco = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    deco_draw = ImageDraw.Draw(deco)
    deco_draw.ellipse([5, 5, 115, 115], fill=(255, 200, 50, 180))
    df = get_cjk_font(24)
    bbox = deco_draw.textbbox((0, 0), "NEW", font=df)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    deco_draw.text(((120 - tw)//2, (120 - th)//2), "NEW", fill=(255, 255, 255, 255), font=df)
    deco.save(assets_dir / "badge_new.png", "PNG")
    print("   ✅ badge_new.png (装饰徽章)")

    # 生成原图
    resolutions = REAL_WORLD_RESOLUTIONS[:count] if count else REAL_WORLD_RESOLUTIONS
    print(f"\n📷 生成原图 ({len(resolutions)} 张)...")
    for i, (w, h) in enumerate(resolutions):
        img = create_placeholder_image(w, h, i)
        fname = f"IMG_{i+1:03d}_{w}x{h}.jpg"
        img.save(originals_dir / fname, "JPEG", quality=85)
        if (i + 1) % 5 == 0 or i == len(resolutions) - 1:
            orient = "横" if w >= h else "竖"
            print(f"   [{i+1}/{len(resolutions)}] {fname} ({orient})")

    # 打包
    zip_path = output_dir / "场宣测试数据.zip"
    print(f"\n📦 打包测试数据...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".zip"):
                    continue
                fp = Path(root) / file
                zf.write(fp, fp.relative_to(output_dir))

    print(f"   ✅ 测试数据包: {zip_path}")
    print(f"   素材: 4 个")
    print(f"   原图: {len(resolutions)} 张 (seed={seed})")
    print(f"\n🎉 测试数据生成完毕！可直接用于管线测试。")


if __name__ == "__main__":
    main()
