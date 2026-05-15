#!/usr/bin/env python3
"""
明源场宣图 - 测试数据生成器
生成多种分辨率的测试原图 + 半透明PNG素材，用于管线测试

用法：
    python generate_test_data.py [--output 测试数据/]
"""

import sys
import os
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# 常见设备分辨率（模拟真实场景）
REAL_WORLD_RESOLUTIONS = [
    # 手机拍摄（常见）
    (3024, 4032),    # iPhone 12MP (竖)
    (4032, 3024),    # iPhone 12MP (横)
    (3000, 4000),    # Android 12MP (竖)
    (4000, 3000),    # Android 12MP (横)
    (2268, 4032),    # iPhone 超广角
    (4032, 2268),    # iPhone 超广角(横)
    # 相机常见
    (5472, 3648),    # 20MP 3:2
    (3648, 5472),    # 20MP 3:2 竖
    (6000, 4000),    # 24MP 3:2
    (4000, 6000),    # 24MP 3:2 竖
    (7360, 4912),    # 36MP 3:2
    (8256, 5504),    # 45MP 3:2
    # 16:9 常见
    (3840, 2160),    # 4K UHD
    (2160, 3840),    # 4K 竖
    (1920, 1080),    # FHD
    (1080, 1920),    # FHD 竖
    # 社交媒体截图/拼图
    (1125, 2436),    # iPhone X 截图
    (1242, 2688),    # iPhone XS Max
    # 接近目标比例的（测试直接缩放）
    (2560, 1440),    # 正好2K横
    (1440, 2560),    # 正好2K竖
    (5120, 2880),    # 正好2x2K横
    (2880, 5120),    # 正好2x2K竖
    (2500, 1420),    # 近似2K横
    (1420, 2500),    # 近似2K竖
    # 极限宽窄比
    (8000, 2000),    # 超宽
    (2000, 8000),    # 超窄
    (1000, 1000),    # 正方
    (1200, 1500),    # 4:5 竖
]


COLORS = [
    (70, 130, 180),   # 钢蓝
    (60, 179, 113),   # 海洋绿
    (218, 165, 32),   # 金菊
    (205, 92, 92),    # 印度红
    (147, 112, 219),  # 中紫
    (255, 127, 80),   # 珊瑚
    (100, 149, 237),  # 矢车菊蓝
    (240, 128, 128),  # 浅珊瑚
]


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
    try:
        # 尝试使用系统字体
        font_size = min(width, height) // 10
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except (IOError, OSError):
        font = ImageFont.load_default()
        font_size = min(width, height) // 15

    # 居中画文字
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

    # 半透明圆角矩形背景
    margin = 5
    draw.rounded_rectangle(
        [margin, margin, size * 2 - margin, size - margin],
        radius=15,
        fill=(255, 255, 255, 160),
        outline=(255, 255, 255, 200),
        width=2,
    )

    # 文字
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size // 3)
    except (IOError, OSError):
        font = ImageFont.load_default()

    text = "明源云"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size * 2 - tw) // 2
    y = (size - th) // 2
    draw.text((x, y), text, fill=(40, 80, 160, 230), font=font)

    return img


def create_watermark_asset(size: int = 300) -> Image.Image:
    """创建半透明水印素材"""
    img = Image.new("RGBA", (size, size // 4), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size // 6)
    except (IOError, OSError):
        font = ImageFont.load_default()

    text = "© 明源云海南 · 场宣专用"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) // 2
    y = (size // 4 - th) // 2
    draw.text((x, y), text, fill=(255, 255, 255, 100), font=font)

    return img


def create_qrcode_placeholder(size: int = 150) -> Image.Image:
    """创建模拟二维码占位素材"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 白色方形
    draw.rounded_rectangle([0, 0, size, size], radius=8, fill=(255, 255, 255, 200))

    # 模拟方块
    block = size // 8
    for i in range(3):
        for j in range(3):
            if (i + j) % 2 == 0:
                x = block * 2 + i * block
                y = block * 2 + j * block
                draw.rectangle([x, y, x + block, y + block], fill=(40, 40, 40, 200))

    return img


def main():
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("测试数据")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 清理旧数据
    assets_dir = output_dir / "素材"
    originals_dir = output_dir / "原图"
    for d in [assets_dir, originals_dir]:
        if d.exists():
            import shutil
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    print("🧪 明源场宣图 - 测试数据生成器")
    print("=" * 60)

    # 生成素材
    print("\n📌 生成素材...")
    logo = create_logo_asset(300)
    logo_path = assets_dir / "logo_明源云.png"
    logo.save(logo_path, "PNG")
    print(f"   ✅ {logo_path.name} (半透明Logo)")

    watermark = create_watermark_asset(500)
    wm_path = assets_dir / "watermark_copyright.png"
    watermark.save(wm_path, "PNG")
    print(f"   ✅ {wm_path.name} (版权水印)")

    qrcode = create_qrcode_placeholder()
    qr_path = assets_dir / "qrcode_placeholder.png"
    qrcode.save(qr_path, "PNG")
    print(f"   ✅ {qr_path.name} (二维码占位)")

    # 额外装饰素材
    deco = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    deco_draw = ImageDraw.Draw(deco)
    deco_draw.ellipse([5, 5, 115, 115], fill=(255, 200, 50, 180))
    try:
        df = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except (IOError, OSError):
        df = ImageFont.load_default()
    bbox = deco_draw.textbbox((0, 0), "NEW", font=df)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    deco_draw.text(((120 - tw)//2, (120 - th)//2), "NEW", fill=(255, 255, 255, 255), font=df)
    deco_path = assets_dir / "badge_new.png"
    deco.save(deco_path, "PNG")
    print(f"   ✅ {deco_path.name} (装饰徽章)")

    # 生成原图
    print(f"\n📷 生成原图 ({len(REAL_WORLD_RESOLUTIONS)} 个分辨率)...")
    for i, (w, h) in enumerate(REAL_WORLD_RESOLUTIONS):
        img = create_placeholder_image(w, h, i)
        # 命名：包含分辨率信息
        fname = f"IMG_{i+1:03d}_{w}x{h}.jpg"
        fpath = originals_dir / fname
        img.save(fpath, "JPEG", quality=85)

        orient = "横" if w >= h else "竖"
        if (i + 1) % 5 == 0:
            print(f"   [{i+1}/{len(REAL_WORLD_RESOLUTIONS)}] {fname} ({orient})")

    # 打包 zip
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
    print(f"   原图: {len(REAL_WORLD_RESOLUTIONS)} 张")
    print(f"\n🎉 测试数据生成完毕！可直接用于管线测试。")


if __name__ == "__main__":
    main()
