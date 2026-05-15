#!/usr/bin/env python3
"""
明源场宣图 - PNG素材叠加脚本
将半透明PNG素材精确叠加到图片指定位置，完整保留透明度

用法：
    python overlay_assets.py <输入目录> <配置文件.json> <输出目录>

配置文件格式见 SKILL.md 第六节
"""

import sys
import json
from pathlib import Path
from PIL import Image


# 位置映射：名称 → (锚点类型, 默认边距)
POSITION_MAP = {
    "top-left":      ("corner", 40, 40),          # 左上角
    "top-right":     ("corner", -40, 40),          # 右上角（右边距用负值表示从右算）
    "bottom-left":   ("corner", 40, -40),          # 左下角
    "bottom-right":  ("corner", -40, -40),         # 右下角
    "center":        ("center", 0, 0),             # 正中央
    "top-center":    ("center", 0, 40),            # 顶部居中
    "bottom-center": ("center", 0, -40),           # 底部居中
}


def load_asset(asset_path: Path, scale: float) -> Image.Image:
    """
    加载素材并等比缩放
    返回 RGBA 模式的素材（保留透明度）
    """
    asset = Image.open(asset_path)

    # 确保 RGBA
    if asset.mode != "RGBA":
        asset = asset.convert("RGBA")

    # 等比缩放
    if scale != 1.0:
        new_w = int(asset.width * scale)
        new_h = int(asset.height * scale)
        asset = asset.resize((new_w, new_h), Image.LANCZOS)

    return asset


def calculate_position(bg_size: tuple, asset_size: tuple, position: str, margin: int) -> tuple:
    """
    计算素材放置坐标
    bg_size: (宽, 高) 背景图尺寸
    asset_size: (宽, 高) 素材尺寸
    position: 位置描述
    margin: 用户指定的边距（覆盖默认值）
    """
    bg_w, bg_h = bg_size
    ast_w, ast_h = asset_size

    if position in POSITION_MAP:
        ptype, def_mx, def_my = POSITION_MAP[position]
        mx = margin if margin else abs(def_mx)
        my = margin if margin else abs(def_my)

        if ptype == "corner":
            # 右上角/右下角的右距需要从右计算
            if "right" in position:
                x = bg_w - ast_w - mx
            else:
                x = mx

            if "bottom" in position:
                y = bg_h - ast_h - my
            else:
                y = my

        elif ptype == "center":
            x = (bg_w - ast_w) // 2 + (def_mx if def_mx > 0 else -abs(def_mx))
            y = (bg_h - ast_h) // 2 + (def_my if def_my > 0 else -abs(def_my))
        else:
            x, y = mx, my

    elif position == "custom":
        # 用户提供绝对坐标，margin 第一个值是 x，第二个要在配置中额外指定
        x, y = 0, 0  # 需要在配置中明确
    else:
        # 尝试解析 "x,y" 格式
        parts = position.split(",")
        if len(parts) == 2:
            x, y = int(parts[0].strip()), int(parts[1].strip())
        else:
            # fallback 右上角
            x, y = bg_w - ast_w - 40, 40

    # 边界保护
    x = max(0, min(x, bg_w - ast_w))
    y = max(0, min(y, bg_h - ast_h))

    return x, y


def overlay_single(bg_path: Path, asset_configs: list, output_dir: Path) -> bool:
    """
    对单张背景图叠加所有素材
    asset_configs: [{"file": "素材/xxx.png", "position": "top-right", "scale": 0.15, "margin": 40}, ...]
    """
    try:
        bg = Image.open(bg_path)

        # 统一为 RGBA 以支持透明叠加
        if bg.mode != "RGBA":
            bg = bg.convert("RGBA")

        # 依次叠加每个素材
        for cfg in asset_configs:
            asset_path = Path(cfg["file"])
            if not asset_path.is_file():
                print(f"    素材不存在: {asset_path}")
                continue

            scale = cfg.get("scale", 0.15)
            position = cfg.get("position", "top-right")
            margin = cfg.get("margin", 40)

            # 加载素材
            asset = load_asset(asset_path, scale)

            # 计算位置
            x, y = calculate_position(bg.size, asset.size, position, margin)

            # 叠加（使用 alpha 通道做 mask，保留透明度）
            bg.paste(asset, (x, y), asset)

        # 保存
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / bg_path.name
        if out_path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            out_path = out_path.with_suffix(".jpg")

        # 转换回 RGB 保存（如果需要保留PNG透明输出，可以修改）
        if bg.mode == "RGBA":
            rgb_bg = Image.new("RGB", bg.size, (255, 255, 255))
            rgb_bg.paste(bg, mask=bg.split()[3])
            bg = rgb_bg

        bg.save(out_path, "JPEG", quality=95)
        return True

    except Exception as e:
        print(f"    错误: {e}")
        return False


def process_directory(input_dir: Path, asset_configs: list, output_dir: Path, limit: int = None):
    """处理目录中所有图片"""
    extensions = {".jpg", ".jpeg", ".png"}
    images = sorted([f for f in input_dir.iterdir()
                     if f.suffix.lower() in extensions and f.is_file()])

    if limit:
        images = images[:limit]

    count_ok = 0
    for img_path in images:
        print(f"    {img_path.name} ... ", end="")
        if overlay_single(img_path, asset_configs, output_dir):
            print("✅")
            count_ok += 1
        else:
            print("❌")

    return count_ok, len(images)


def main():
    if len(sys.argv) < 4:
        print("用法: python overlay_assets.py <输入目录> <配置.json> <输出目录> [--limit N]")
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    config_path = Path(sys.argv[2])
    output_dir = Path(sys.argv[3])

    limit = None
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    if not input_dir.is_dir():
        print(f"错误: 目录不存在: {input_dir}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    assets = config.get("assets", [])
    if not assets:
        print("错误: 配置文件中无素材定义")
        sys.exit(1)

    print(f"🖼️  素材叠加开始...")
    print(f"   素材: {len(assets)} 个")
    for i, a in enumerate(assets):
        print(f"     素材{i+1}: {a['file']} → {a.get('position','?')} (缩放{a.get('scale',0.15)})")

    # 检查输入目录是否有子目录
    subdirs = [d for d in input_dir.iterdir() if d.is_dir()]
    total_ok, total = 0, 0

    if subdirs:
        for subdir in sorted(subdirs):
            print(f"\n  📂 {subdir.name}/")
            out_sub = output_dir / subdir.name
            ok, cnt = process_directory(subdir, assets, out_sub, limit)
            total_ok += ok
            total += cnt
    else:
        ok, cnt = process_directory(input_dir, assets, output_dir, limit)
        total_ok, total = ok, cnt

    print(f"\n🖼️  叠加完成: {total_ok}/{total} 张")
    return total_ok == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
