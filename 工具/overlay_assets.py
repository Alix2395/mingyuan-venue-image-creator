#!/usr/bin/env python3
"""
明源场宣图 - PNG素材叠加脚本
将半透明PNG素材精确叠加到图片指定位置，完整保留透明度

用法：
    python overlay_assets.py <输入目录> <配置文件.json> <输出目录> [--limit N]

配置文件格式见 SKILL.md 第六节

功能：
    - 支持 7 种预设位置 + 自定义坐标
    - 等比缩放素材
    - 透明度完整保留
    - 叠加位置日志输出
    - 素材重叠检测
"""

import sys
import json
from pathlib import Path
from PIL import Image

# 位置映射：名称 → (锚点类型, 默认右边距, 默认上边距)
# 边距用正值：正数表示左上偏移，负数表示右下偏移（从边界算起）
POSITION_MAP = {
    "top-left":      ("corner", 40, 40),          # 左上角
    "top-right":     ("corner", 40, 40),           # 右上角
    "bottom-left":   ("corner", 40, 40),           # 左下角
    "bottom-right":  ("corner", 40, 40),           # 右下角
    "center":        ("center", 0, 0),             # 正中央
    "top-center":    ("center", 0, 40),            # 顶部居中
    "bottom-center": ("center", 0, 40),            # 底部居中
}


def load_asset(asset_path: Path, scale: float) -> Image.Image:
    """加载素材并等比缩放，返回 RGBA 模式"""
    asset = Image.open(asset_path)
    if not asset_path.stat().st_size > 0:
        raise ValueError(f"素材文件为空: {asset_path}")

    if asset.mode != "RGBA":
        asset = asset.convert("RGBA")

    if scale != 1.0:
        new_w = max(1, int(asset.width * scale))
        new_h = max(1, int(asset.height * scale))
        asset = asset.resize((new_w, new_h), Image.LANCZOS)

    return asset


def calculate_position(bg_size: tuple, asset_size: tuple, position: str, margin: int) -> tuple:
    """
    计算素材放置坐标
    返回 (x, y) 左上角坐标
    """
    bg_w, bg_h = bg_size
    ast_w, ast_h = asset_size

    if position in POSITION_MAP:
        ptype, def_mx, def_my = POSITION_MAP[position]
        # margin=0 时使用默认值
        mx = def_mx if (margin is None or margin == 0) else margin
        my = def_my if (margin is None or margin == 0) else margin

        if ptype == "corner":
            if position == "top-left":
                x, y = mx, my
            elif position == "top-right":
                x, y = bg_w - ast_w - mx, my
            elif position == "bottom-left":
                x, y = mx, bg_h - ast_h - my
            elif position == "bottom-right":
                x, y = bg_w - ast_w - mx, bg_h - ast_h - my
            else:
                x, y = mx, my

        elif ptype == "center":
            if position == "top-center":
                x = (bg_w - ast_w) // 2
                y = my
            elif position == "bottom-center":
                x = (bg_w - ast_w) // 2
                y = bg_h - ast_h - my
            else:  # center
                x = (bg_w - ast_w) // 2
                y = (bg_h - ast_h) // 2
        else:
            x, y = mx, my

    elif position == "custom":
        # 期望配置中 margin 为 [x, y] 数组
        x, y = 0, 0  # 需要在配置中明确提供

    elif "," in position:
        # 尝试解析 "x,y" 格式
        parts = position.split(",")
        if len(parts) == 2:
            x, y = int(parts[0].strip()), int(parts[1].strip())
        else:
            x, y = bg_w - ast_w - 40, 40
    else:
        print(f"  ⚠️ 未知位置 '{position}'，使用右上角")
        x, y = bg_w - ast_w - 40, 40

    # 边界保护
    x = max(0, min(x, bg_w - ast_w))
    y = max(0, min(y, bg_h - ast_h))

    return x, y


def check_overlap(placements: list, new_xy: tuple, new_size: tuple, asset_name: str):
    """检测素材是否重叠（辅助调试）"""
    nx, ny = new_xy
    nw, nh = new_size
    for name, (ox, oy), (ow, oh) in placements:
        if nx < ox + ow and nx + nw > ox and ny < oy + oh and ny + nh > oy:
            overlap_w = min(nx + nw, ox + ow) - max(nx, ox)
            overlap_h = min(ny + nh, oy + oh) - max(ny, oy)
            print(f"  ⚠️ {asset_name} 与 {name} 重叠 "
                  f"(交叠区域: {overlap_w}×{overlap_h}px)")


def overlay_single(bg_path: Path, asset_configs: list, output_dir: Path) -> tuple:
    """
    对单张背景图叠加所有素材
    返回 (success, placements)
    """
    placements = []

    try:
        bg = Image.open(bg_path)
        if bg.mode != "RGBA":
            bg = bg.convert("RGBA")

        for cfg in asset_configs:
            asset_path = Path(cfg["file"])
            if not asset_path.is_file():
                print(f"    素材不存在: {asset_path}")
                continue

            scale = cfg.get("scale", 0.15)
            position = cfg.get("position", "top-right")
            margin = cfg.get("margin", 40)

            asset = load_asset(asset_path, scale)
            x, y = calculate_position(bg.size, asset.size, position, margin)

            # 重叠检测
            check_overlap(placements, (x, y), asset.size, asset_path.name)
            placements.append((asset_path.name, (x, y), asset.size))

            # 叠加（使用 alpha 通道做 mask）
            bg.paste(asset, (x, y), asset)

            print(f"      📍 {asset_path.name} → ({x},{y}) 缩放={scale}")

        # 保存
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / bg_path.name
        if out_path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            out_path = out_path.with_suffix(".jpg")

        # 转 RGB 保存
        rgb_bg = Image.new("RGB", bg.size, (255, 255, 255))
        rgb_bg.paste(bg, mask=bg.split()[3])
        rgb_bg.save(out_path, "JPEG", quality=95)

        return True, placements

    except Exception as e:
        print(f"    错误: {e}")
        return False, []


def process_directory(input_dir: Path, asset_configs: list, output_dir: Path, limit: int = None):
    """处理目录中所有图片"""
    extensions = {".jpg", ".jpeg", ".png"}
    images = sorted([f for f in input_dir.iterdir()
                     if f.suffix.lower() in extensions and f.is_file()])

    if limit:
        images = images[:limit]

    total = len(images)
    count_ok = 0
    for idx, img_path in enumerate(images):
        print(f"  [{idx+1}/{total}] {img_path.name} ...")
        success, placements = overlay_single(img_path, asset_configs, output_dir)
        if success:
            print(f"  ✅ (叠加 {len(placements)} 个素材)")
            count_ok += 1
        else:
            print("  ❌")

    return count_ok, total


def validate_config(config: dict) -> bool:
    """验证配置文件完整性"""
    assets = config.get("assets", [])
    if not assets:
        print("❌ 配置错误: assets 为空")
        return False
    for i, a in enumerate(assets):
        if "file" not in a:
            print(f"❌ 配置错误: assets[{i}] 缺少 file 字段")
            return False
        if not Path(a["file"]).is_file():
            print(f"⚠️ 配置警告: assets[{i}] 文件不存在: {a['file']}")
            # 不阻塞，继续处理其他素材
    return True


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

    if not validate_config(config):
        sys.exit(1)

    assets = config.get("assets", [])
    print(f"🖼️  素材叠加开始...")
    print(f"   素材: {len(assets)} 个")
    for i, a in enumerate(assets):
        print(f"     素材{i+1}: {a['file']} → {a.get('position','?')} "
              f"(缩放{a.get('scale',0.15)})")

    # 处理子目录
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

    # 输出位置日志到 JSON
    log_path = output_dir.parent / "overlay_positions.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "assets": [{"name": Path(a["file"]).name, "position": a.get("position", ""),
                        "scale": a.get("scale", 0.15), "margin": a.get("margin", 40)}
                       for a in assets],
            "total_processed": total_ok,
        }, f, ensure_ascii=False, indent=2)
    print(f"   叠加位置日志: {log_path}")

    sys.exit(0 if total_ok == total else 1)


if __name__ == "__main__":
    main()
