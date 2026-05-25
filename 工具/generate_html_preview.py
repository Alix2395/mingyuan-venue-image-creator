#!/usr/bin/env python3
"""
明源场宣图 - HTML 多版本预览生成器

扫描 final/ 目录成品图片，按背景分组、变体分类，
生成浏览器可打开的 HTML 预览页，方便用户对比不同变体。

用法：
    python generate_html_preview.py <final_dir> [--output preview.html] [--title "标题"]

输出：
    preview.html — 独立 HTML 文件（无需网络，浏览器直接打开）
"""

import argparse
import os
import re
from pathlib import Path
from urllib.parse import quote


def auto_detect_groups(final_dir: Path):
    """
    自动扫描 final/ 目录，按背景和变体分组图片。

    文件名解析规则（支持多种命名模式）：
      output_{背景}_{变体}.png/jpg
      {背景}_{变体}.png/jpg
      {前缀}_{背景}_{变体}.png/jpg

    返回: {背景: {变体: [filepath, ...], ...}, ...}
    """
    # 收集所有图片文件
    extensions = {'.png', '.jpg', '.jpeg'}
    images = []
    for f in sorted(final_dir.iterdir()):
        if f.suffix.lower() in extensions:
            images.append(f)

    if not images:
        return {}

    # 尝试智能分组
    # 策略1：文件名含至少2个下划线 → 最后一段是变体名，去掉变体后剩余为背景
    groups = {}
    ungrouped = []

    pattern_variant = re.compile(r'^(.+)_([^_]+)\.(png|jpg|jpeg)$', re.IGNORECASE)

    for f in images:
        stem = f.stem  # 不含扩展名
        # 去掉常见前缀
        key = stem
        for prefix in ['output_', 'final_', '成品_']:
            if key.startswith(prefix):
                key = key[len(prefix):]
                break

        m = pattern_variant.match(key)
        if m and m.group(1) and m.group(2):
            bg = m.group(1)
            variant = m.group(2)
            groups.setdefault(bg, {})
            groups[bg].setdefault(variant, [])
            groups[bg][variant].append(str(f))
        else:
            ungrouped.append(str(f))

    # 把未分组的也加入
    if ungrouped:
        groups.setdefault('其他', {'未分组': ungrouped})

    return groups


def generate_preview(final_dir: Path, output_path: Path, title: str = "场宣图成品预览"):
    """生成HTML预览页"""

    groups = auto_detect_groups(final_dir)

    if not groups:
        print(f"⚠️  未在 {final_dir} 中找到图片文件")
        return False

    # 统计信息
    total_images = sum(
        len(files) for bg in groups.values()
        for files in bg.values()
    )
    total_bg = len(groups)
    total_variants = sum(len(variants) for variants in groups.values())

    # 列出图片文件以便生成相对路径
    # 我们需要从 output_path 到 final_dir 的相对路径
    try:
        rel_base = os.path.relpath(final_dir, output_path.parent)
    except ValueError:
        rel_base = str(final_dir)

    # 构建分组HTML
    groups_html = ""

    for bg_name, variants in groups.items():
        # 背景标题
        is_other = (bg_name == '其他')
        if is_other:
            bg_label = "其他"
        else:
            bg_label = bg_name

        groups_html += f"""
    <div class="bg-group">
        <h2>🏙️ {bg_label}</h2>
        <div class="variant-row">"""

        for var_name, files in variants.items():
            groups_html += f"""
            <div class="variant">
                <h3>{var_name}</h3>"""

            for img_file in files:
                # 计算相对路径
                img_rel = os.path.relpath(img_file, output_path.parent)
                img_encoded = quote(img_rel.replace('\\', '/'))

                # 获取文件信息
                try:
                    from PIL import Image
                    img = Image.open(img_file)
                    dims = f"{img.size[0]}×{img.size[1]}"
                except Exception:
                    dims = ""

                size_kb = os.path.getsize(img_file) // 1024

                groups_html += f"""
                <img src="{img_encoded}" alt="{bg_label} - {var_name}" loading="lazy"
                     onclick="preview(this.src)" onerror="this.style.display='none'">
                <div class="img-info">{dims} | {size_kb}KB</div>"""

            groups_html += """
            </div>"""

        groups_html += """
        </div>
    </div>"""

    # 生成完整HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, 'Microsoft YaHei', sans-serif;
        background: #1a1a2e; color: #eee; padding: 30px; }}
h1 {{ text-align: center; margin-bottom: 8px; font-size: 26px; color: #e8b840; }}
.subtitle {{ text-align: center; margin-bottom: 36px; color: #999; font-size: 14px; }}
.bg-group {{ margin-bottom: 40px; background: #16213e; border-radius: 12px; padding: 24px; }}
.bg-group h2 {{ font-size: 18px; margin-bottom: 16px; color: #e8b840;
                border-bottom: 1px solid #333; padding-bottom: 10px; }}
.variant-row {{ display: flex; gap: 16px; flex-wrap: wrap; }}
.variant {{ flex: 1; min-width: 280px; max-width: 500px; }}
.variant h3 {{ font-size: 13px; margin-bottom: 6px; color: #aaa;
               background: #0f3460; display: inline-block; padding: 2px 10px;
               border-radius: 4px; }}
.variant img {{ width: 100%; border-radius: 6px; border: 1px solid #333;
               cursor: pointer; transition: transform 0.15s; }}
.variant img:hover {{ transform: scale(1.03); }}
.img-info {{ font-size: 12px; color: #777; margin-top: 4px; }}
#preview-overlay {{ display: none; position: fixed; top: 0; left: 0;
    width: 100%; height: 100%; background: rgba(0,0,0,0.92); z-index: 100;
    cursor: pointer; justify-content: center; align-items: center; }}
#preview-overlay img {{ max-width: 94vw; max-height: 94vh; object-fit: contain; }}
.footer {{ margin-top: 40px; text-align: center; color: #666; font-size: 13px; }}
.footer p {{ margin: 4px 0; }}
</style>
</head>
<body>

<h1>🏢 {title}</h1>
<p class="subtitle">{total_bg} 组背景 · {total_variants} 个变体 · 共 {total_images} 张 | 点击图片放大预览</p>

<div id="gallery">
{groups_html}
</div>

<div id="preview-overlay" onclick="this.style.display='none'">
    <img id="preview-img" src="" alt="预览">
</div>

<div class="footer">
    <p>由 mingyuan-xuanchuan · generate_html_preview.py 自动生成</p>
</div>

<script>
function preview(src) {{
    document.getElementById('preview-img').src = src;
    document.getElementById('preview-overlay').style.display = 'flex';
}}
document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') {{
        document.getElementById('preview-overlay').style.display = 'none';
    }}
}});
</script>

</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding='utf-8')

    print(f"✅ HTML 预览已生成: {output_path}")
    print(f"   共 {total_bg} 组背景 / {total_variants} 个变体 / {total_images} 张图片")
    return True


def main():
    parser = argparse.ArgumentParser(description="生成场宣图HTML预览页")
    parser.add_argument("final_dir", type=str, help="成品图片目录")
    parser.add_argument("--output", "-o", type=str, default="preview.html",
                        help="输出HTML文件路径 (default: preview.html)")
    parser.add_argument("--title", "-t", type=str, default="场宣图成品预览",
                        help="页面标题")
    args = parser.parse_args()

    final_dir = Path(args.final_dir)
    if not final_dir.is_dir():
        print(f"❌ 目录不存在: {final_dir}")
        return 1

    success = generate_preview(final_dir, Path(args.output), args.title)
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
