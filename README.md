# 明源场宣图简易制作 (Mingyuan Venue Image Creator)

> 批量场宣图片规范化处理工具链 —— 格式标准化 + 轻度优化 + 素材叠加 + 过程预览 + 打包交付

[![Version](https://img.shields.io/badge/version-0.3.0-blue)](https://github.com/Alix2395/mingyuan-venue-image-creator/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

---

## 📖 简介

**明源场宣图简易制作** 是一个专为场宣物料设计的批量图片处理工具链。它能自动完成：

- 📐 **格式规范化** — 统一至 2K 标准（横板 2560×1440，竖板 1440×2560），智能等比裁剪，无拉伸
- 🎨 **轻度优化** — 自动调整曝光/白平衡/对比度/饱和度，保持原图风格
- 🖼️ **素材叠加** — 批量叠加 PNG 素材（Logo/水印/二维码/徽章），完整保留透明度
- 📊 **过程预览** — 每个阶段自动生成可视化对比图
- 📦 **一键打包** — 全链路自动化，产出直接可用

---

## 🚀 快速开始

### 1. 环境要求

```bash
pip install Pillow
apt-get install -y fonts-wqy-zenhei  # CJK 字体（中文渲染必需）
```

### 2. 准备素材

将原图和素材按以下结构放入 zip：

```
场宣素材.zip
├── 素材/           # PNG素材（Logo、水印、二维码等）
│   ├── logo.png
│   └── ...
└── 原图/           # 待处理原图（任意分辨率/格式）
    ├── photo1.jpg
    └── ...
```

### 3. 运行

```bash
# 一键全链路（自动全量）
python 工具/pipeline.py 场宣素材.zip 示例/config.json --auto-confirm

# 分步执行
python 工具/normalize_resolution.py 测试数据/原图 临时/normalized
python 工具/enhance_images.py 临时/normalized 临时/enhanced
python 工具/overlay_assets.py 临时/enhanced 示例/config.json 临时/final
python 工具/checklist_validator.py 临时/final
```

---

## 📦 版本日志

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.3.0** | 2026-05-22 | 🔒 安全加固：107项审计修复、CJK字体门禁、EXIF处理、退化解检测 |
| **v0.2.0** | 2026-05-21 | 🚀 过程预览系统、测试数据集、仓库重构 |
| **v0.0.1** | 2026-05-15 | 初始版本 |

### v0.3.0 更新内容

**安全加固：**
- 🔒 CJK 字体门禁 — 所有脚本启动时验证中文字体可用性，缺失则阻塞
- 🔒 过程图推送铁律 — 预览图生成后必须主动发出
- 🔒 EXIF 方向处理 — 手机竖拍图片自动旋转修正（normalize_resolution.py）
- 🔒 图片完整性验证 — 处理前检测文件损坏（verify_image）

**脚本优化：**
- normalize_resolution.py: 新增 EXIF 方向处理、文件完整性检测、JSON 输出
- enhance_images.py: 新增 argparse 参数解析、重复处理跳过、质量退化解检测、EXIF 保留
- overlay_assets.py: 修复 margin=0 边界问题、新增重叠检测、位置日志输出
- checklist_validator.py: 新增文件完整性/大小/命名规范/重复检测
- generate_test_data.py: 新增 --count/--seed 参数、shutil 全局导入
- pipeline.py: 新增 CJK 字体门禁、配置验证、--cleanup 清理、--task-name

**仓库：**
- CHANGELOG.md 独立日志
- README.md 更新至 v0.3.0
- .gitignore 增强排除规则

---

## 🛠️ 工具脚本

| 脚本 | 功能 | v0.3 |
|------|------|------|
| `工具/pipeline.py` | 一键全链路管线 | ✅ 加固 |
| `工具/normalize_resolution.py` | 格式规范化到 2K | ✅ EXIF+验证 |
| `工具/enhance_images.py` | 轻度图片优化 | ✅ 跳过+退化解 |
| `工具/overlay_assets.py` | PNG 素材叠加 | ✅ 重叠检测 |
| `工具/generate_test_data.py` | 测试数据生成 | ✅ seed支持 |
| `工具/checklist_validator.py` | 产出质量验证 | ✅ 多维度检查 |
| `工具/create_process_previews.py` | 过程预览拼图生成 | ✅ CJK字体 |

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
  "output_quality": 95,
  "enhance": {
    "brightness": 1.05,
    "contrast": 1.10,
    "color": 1.05
  }
}
```

**位置选项：** `top-left` `top-right` `bottom-left` `bottom-right` `center` `top-center` `bottom-center`

---

## 👤 作者

**Alix** — 明源云海南

---

## 📄 许可证

MIT License
