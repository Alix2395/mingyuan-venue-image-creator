# 明源场宣图简易制作 (Mingyuan Venue Image Creator)

> 批量场宣图片规范化处理工具 —— 格式标准化 + 轻度优化 + 素材叠加 + 打包交付

[![Version](https://img.shields.io/badge/version-0.0.1-blue)](https://github.com/Alix2395/mingyuan-venue-image-creator/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

---

## 📖 简介

**明源场宣图简易制作** 是一个专为场宣物料设计的批量图片处理工具链。它能自动完成：

- 📐 **格式规范化** — 统一至 2K 标准（横板 2560×1440，竖板 1440×2560），智能等比裁剪
- 🎨 **轻度优化** — 自动调整曝光/白平衡/对比度/饱和度，保持原图风格
- 🖼️ **素材叠加** — 批量叠加 PNG 素材（Logo/水印/二维码等），完整保留透明度
- 📦 **一键打包** — 全链路自动化，产出直接可用

---

## 🚀 快速开始

### 1. 环境要求

```bash
pip install Pillow numpy
```

### 2. 准备素材

将你的原图和素材按以下结构放入 zip：

```
场宣素材.zip
├── 素材/           # PNG素材（Logo、水印、二维码等）
│   ├── logo.png
│   ├── watermark.png
│   └── ...
└── 原图/           # 待处理原图（任意分辨率）
    ├── photo1.jpg
    ├── photo2.jpg
    └── ...
```

### 3. 运行

```bash
# 一键全链路
python 工具/pipeline.py 场宣素材.zip config.json --auto-confirm
```

---

## 📋 工作流

```
用户提供 zip（素材/ + 原图/）
  │
  ▼
[阶段0] 解包 & 审计 → 确认素材使用方式
  │
  ▼
[阶段1] 格式规范化 → 2K 标准（等比裁剪，无拉伸）
  │
  ▼
[阶段2] 轻度优化 → 曝光/白平衡/对比度
  │
  ▼
[阶段3] 素材叠加 → 样板确认 → 全量处理
  │
  ▼
[阶段4] 打包交付 → zip 成品
```

---

## 🛠️ 工具脚本

| 脚本 | 功能 |
|------|------|
| `工具/normalize_resolution.py` | 格式规范化到 2K |
| `工具/enhance_images.py` | 轻度图片优化 |
| `工具/overlay_assets.py` | PNG 素材叠加 |
| `工具/pipeline.py` | 一键全链路 |
| `工具/generate_test_data.py` | 生成测试数据 |
| `工具/checklist_validator.py` | 产出质量验证 |

---

## 📝 配置文件

```json
{
  "assets": [
    {
      "file": "素材/logo.png",
      "position": "top-right",
      "scale": 0.15,
      "margin": 40
    }
  ],
  "enhance": {
    "brightness": 1.05,
    "contrast": 1.10,
    "color": 1.05
  }
}
```

**位置选项：** `top-left` `top-right` `bottom-left` `bottom-right` `center` `top-center` `bottom-center`

---

## 🧪 测试

```bash
# 生成测试数据
python 工具/generate_test_data.py --output 测试/

# 运行全链路测试
python 工具/normalize_resolution.py 测试/原图 测试/normalized
python 工具/enhance_images.py 测试/normalized 测试/enhanced
python 工具/overlay_assets.py 测试/enhanced config.json 测试/final

# 验证质量
python 工具/checklist_validator.py 测试/final
```

---

## 📦 发行版

- **v0.0.1** (2026-05-15) — 初始版本
  - 6 个核心工具脚本
  - 完整四阶段管线
  - 检查清单质量验证
  - 测试数据生成器

---

## 👤 作者

**Alix** — 明源云海南

---

## 📄 许可证

MIT License
