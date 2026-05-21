# 明源场宣图简易制作 (Mingyuan Venue Image Creator)

> 批量场宣图片规范化处理工具链 —— 格式标准化 + 轻度优化 + 素材叠加 + 过程预览 + 打包交付

[![Version](https://img.shields.io/badge/version-0.2.0-blue)](https://github.com/Alix2395/mingyuan-venue-image-creator/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

---

## 📖 简介

**明源场宣图简易制作** 是一个专为场宣物料设计的批量图片处理工具链。它能自动完成：

- 📐 **格式规范化** — 统一至 2K 标准（横板 2560×1440，竖板 1440×2560），智能等比裁剪，无拉伸
- 🎨 **轻度优化** — 自动调整曝光/白平衡/对比度/饱和度，保持原图风格
- 🖼️ **素材叠加** — 批量叠加 PNG 素材（Logo/水印/二维码/徽章），完整保留透明度
- 📊 **过程预览** — 每个阶段自动生成可视化对比图，方便人工审核
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
# 一键全链路（带过程预览）
python 工具/pipeline.py 场宣素材.zip 示例/config.json --preview --auto-confirm

# 分步执行
python 工具/normalize_resolution.py 测试数据/原图 临时/normalized
python 工具/enhance_images.py 临时/normalized 临时/enhanced
python 工具/overlay_assets.py 临时/enhanced 示例/config.json 临时/final
python 工具/create_process_previews.py .   # 生成各阶段对比图
```

---

## 📂 仓库结构

```
mingyuan-venue-image-creator/
├── README.md                 # 本文档
├── SKILL.md                  # Hermes Agent 技能定义
├── LICENSE                   # MIT 许可证
├── .gitignore
├── 工具/                     # 核心处理脚本
│   ├── pipeline.py           #   一键全链路管线
│   ├── normalize_resolution.py  # 2K 规格标准化
│   ├── enhance_images.py     #   轻度图片优化
│   ├── overlay_assets.py     #   PNG 素材叠加
│   ├── generate_test_data.py #   测试数据生成器
│   ├── checklist_validator.py#   产出质量验证
│   └── create_process_previews.py # 过程预览拼图生成器
├── 测试数据/                 # 预置测试数据集
│   ├── 素材/                 #   4 个透明 PNG 素材
│   └── 原图/                 #   15 张覆盖各种比例的测试原图
├── 示例/                     # 使用示例
│   ├── config.json           #   示例配置文件（相对路径引用）
│   └── 过程预览/             #   各阶段过程预览示例图
└── 日志/                     # 任务日志（运行时生成）
```

---

## 📋 工作流

```
用户提供 zip（素材/ + 原图/）
  │
  ▼
[阶段0] 解包 & 审计 ── 素材数量/透明度/使用方式确认
  │                     自动生成 素材审计图 + 原片分辨率审计图
  ▼
[阶段1] 格式规范化 ── 2K 标准（2560×1440 / 1440×2560）
  │                     等比裁剪，无拉伸，居中保留主体
  │                     自动生成 规范化前后对比图
  ▼
[阶段2] 轻度优化 ── 曝光/白平衡/对比度/饱和度
  │                     参数保守，不破坏原片风格
  │                     自动生成 优化前后对比图
  ▼
[阶段3] 素材叠加 ── 横板×1 + 竖板×1 样板确认
  │                     确认后全量处理
  │                     自动生成 素材叠加样板图
  ▼
[阶段4] 打包交付 ── 横板/竖板分目录 → zip
                      日志留存
```

---

## 🛠️ 工具脚本

| 脚本 | 功能 | 新 v0.2 |
|------|------|---------|
| `工具/pipeline.py` | 一键全链路管线 | ✅ |
| `工具/normalize_resolution.py` | 格式规范化到 2K | ✅ |
| `工具/enhance_images.py` | 轻度图片优化 | ✅ |
| `工具/overlay_assets.py` | PNG 素材叠加 | ✅ |
| `工具/generate_test_data.py` | 生成测试数据（覆盖多种屏幕比例） | ✅ |
| `工具/checklist_validator.py` | 产出质量验证 | ✅ |
| `工具/create_process_previews.py` | **过程预览拼图生成器** | ⭐ 新增 |

---

## 📝 配置文件

```json
{
  "assets": [
    {
      "file": "测试数据/素材/logo_明源云.png",
      "position": "top-right",
      "scale": 0.55,
      "margin": 60
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

## 🧪 测试 & 演示模式

```bash
# 1. 生成测试数据（覆盖 16:9 / 4:3 / 3:4 / 9:16 / 1:1 / 超宽 / 超窄）
python 工具/generate_test_data.py --output 测试数据/

# 2. 跑全链路（带过程预览）
python 工具/pipeline.py 测试数据 示例/config.json --preview

# 3. 生成过程预览图
python 工具/create_process_previews.py .
# 产出 → 示例/过程预览/stage*.png

# 4. 验证产出质量
python 工具/checklist_validator.py 临时/final
```

过程预览示例（来自 v0.2 测试运行）：

| 阶段 | 预览图 |
|------|--------|
| Stage 0 素材审计 | `示例/过程预览/stage0_assets_audit.png` |
| Stage 0 原片审计 | `示例/过程预览/stage0_originals_audit.png` |
| Stage 1 规范化对比 | `示例/过程预览/stage1_normalize_compare_FIXED.png` |
| Stage 2 优化对比 | `示例/过程预览/stage2_enhance_compare_FIXED.png` |
| Stage 3 叠加样板 | `示例/过程预览/stage3_overlay_samples_FIXED.png` |
| Stage 3 全量总览 | `示例/过程预览/stage3_overlay_full_montage_FIXED.png` |

---

## 📦 发行版

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.2.0** | 2026-05-21 | 🚀 过程预览系统、测试数据集、仓库重构、示例文档 |
| **v0.0.1** | 2026-05-15 | 初始版本：6 个核心工具脚本 + 四阶段管线 + 检查清单 |

### v0.2.0 新增特性

- ⭐ **create_process_previews.py** — 各阶段自动生成可视化对比拼图，支持人工审核
- 📊 **测试数据集** — 15 张覆盖所有常见比例的测试原图 + 4 个透明 PNG 素材
- 🖼️ **过程预览示例** — 6 张实际运行截图，直观展示管线各阶段效果
- 📝 **仓库重构** — 清晰目录划分（工具/测试数据/示例/日志），相对路径配置
- 📋 **增强 .gitignore** — 更完整的排除规则

---

## 👤 作者

**Alix** — 明源云海南

---

## 📄 许可证

MIT License
