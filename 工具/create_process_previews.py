#!/usr/bin/env python3
"""
明源场宣图 - 过程预览拼图生成器

用途：测试/演示模式下，把各阶段输出做成可发给用户的 PNG 过程图。
不替代主处理脚本，只负责视觉化对比。

用法：
    python create_process_previews.py <base_dir>

约定目录：
    <base_dir>/测试数据/原图
    <base_dir>/测试数据/素材
    <base_dir>/临时/normalized
    <base_dir>/临时/enhanced
    <base_dir>/临时/final
    <base_dir>/过程预览
"""

from __future__ import annotations

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

BG = "#F8FAFC"
BLUE = "#1E40AF"
PURPLE = "#7C3AED"
GREEN = "#0D9488"
TEXT = "#111827"
BORDER = "#CBD5E1"

FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size: int, bold: bool = False):
    path = FONT_BOLD if bold else FONT_REG
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def fit(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.contain(img.convert("RGB"), size, Image.LANCZOS)


def draw_card(canvas: Image.Image, xy: tuple[int, int], size: tuple[int, int], title: str):
    d = ImageDraw.Draw(canvas)
    x, y = xy
    w, h = size
    d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill="white", outline=BORDER, width=2)
    d.text((x + 18, y + 14), title, fill=BLUE, font=font(24, True))


def stage0_assets(base: Path) -> Path:
    assets = sorted((base / "测试数据" / "素材").glob("*.png"))
    out_dir = base / "过程预览"
    out_dir.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", (1600, 520), BG)
    d = ImageDraw.Draw(canvas)
    d.text((40, 28), "Stage 0 素材审计：透明 PNG 素材", fill=BLUE, font=font(36, True))
    x = 60
    for f in assets:
        im = Image.open(f).convert("RGBA")
        checker = Image.new("RGBA", im.size, (245, 245, 245, 255))
        cd = ImageDraw.Draw(checker)
        for yy in range(0, im.height, 20):
            for xx in range(0, im.width, 20):
                if (xx // 20 + yy // 20) % 2 == 0:
                    cd.rectangle([xx, yy, xx + 20, yy + 20], fill=(220, 220, 220, 255))
        checker.alpha_composite(im)
        tile = fit(checker, (310, 230))
        canvas.paste(tile, (x, 120))
        d.text((x, 365), f.name, fill=TEXT, font=font(20))
        d.text((x, 392), f"{im.width}×{im.height} / {im.mode}", fill=GREEN, font=font(20))
        x += 375
    out = out_dir / "stage0_assets_audit.png"
    canvas.save(out)
    return out


def stage0_originals(base: Path, limit: int = 12) -> Path:
    imgs = sorted((base / "测试数据" / "原图").glob("*.jpg"))[:limit]
    out_dir = base / "过程预览"
    out_dir.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", (1920, 1280), BG)
    d = ImageDraw.Draw(canvas)
    d.text((40, 26), "Stage 0 原图审计：多分辨率/横竖比例输入样本", fill=BLUE, font=font(36, True))
    cols, tw, th, gap = 4, 430, 310, 35
    for idx, f in enumerate(imgs):
        im = Image.open(f)
        thumb = fit(im, (tw, th - 60))
        x = 60 + (idx % cols) * (tw + gap)
        y = 110 + (idx // cols) * (th + gap)
        d.rounded_rectangle([x - 8, y - 8, x + tw + 8, y + th + 8], radius=18, fill="white", outline=BORDER, width=2)
        canvas.paste(thumb, (x + (tw - thumb.width) // 2, y))
        orient = "horizontal" if im.width >= im.height else "vertical"
        d.text((x, y + th - 54), f.name[:32], fill=TEXT, font=font(20))
        d.text((x, y + th - 28), f"{im.width}×{im.height} / {orient}", fill=PURPLE, font=font(20))
    out = out_dir / "stage0_originals_audit.png"
    canvas.save(out)
    return out


def compare_pair(title: str, left_path: Path, right_path: Path, out: Path, left_label: str, right_label: str) -> Path:
    canvas = Image.new("RGB", (1800, 980), BG)
    d = ImageDraw.Draw(canvas)
    d.text((40, 28), title, fill=BLUE, font=font(38, True))
    for i, (p, label) in enumerate([(left_path, left_label), (right_path, right_label)]):
        x = 70 + i * 860
        draw_card(canvas, (x, 100), (790, 780), label)
        im = Image.open(p)
        thumb = fit(im, (740, 650))
        canvas.paste(thumb, (x + 25 + (740 - thumb.width) // 2, 160))
        d.text((x + 25, 825), f"{p.name} / {im.width}×{im.height}", fill=TEXT, font=font(22))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: python create_process_previews.py <base_dir>")
        return 1
    base = Path(sys.argv[1])
    outs = [stage0_assets(base), stage0_originals(base)]
    for p in outs:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
