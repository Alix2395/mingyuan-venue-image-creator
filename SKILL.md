---
name: mingyuan-xuanchuan
description: 明源场宣图片批量规范化处理：生成/审计素材、2K 横竖规范化、轻度优化、PNG 素材叠加、过程预览与打包交付。
---

# 明源场宣图简易制作

> 版本: 0.3.1
> 作者: Alix（明源云海南）
> 用途: 批量场宣图片规范化处理——格式标准化 + 轻度优化 + 素材叠加 + 过程预览 + 打包交付
> 依赖: Python 3.8+, Pillow≥8.0, NumPy（可选）
> 仓库: https://github.com/Alix2395/mingyuan-venue-image-creator
>
> 🔴 铁律1：每次生成过程预览图后必须主动发出（见门禁B）
> 🔴 铁律2：任何中文渲染前必须先验证 CJK 字体可用（见门禁A）

---

## ⚠️ 铁律门禁（前置于所有阶段）

### 门禁A：CJK 字体门禁
每次在图片中渲染中文文本前，必须验证 CJK 字体可用：

```python
# CJK 字体可用性验证
from PIL import ImageFont
CJK_CANDIDATES = [
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/arphic/ukai.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
]
available = [p for p in CJK_CANDIDATES if ImageFont.truetype(p, 20)]
if not available:
    raise RuntimeError("阻塞: 无CJK字体，无法渲染中文，先安装 fonts-wqy-zenhei 或 fonts-noto-cjk")
```

如果 CJK 字体缺失，必须 **阻塞任务** 直到安装完成：
```bash
apt-get install -y fonts-wqy-zenhei fonts-noto-cjk
```

**禁止**：在无 CJK 字体的环境下渲染任何含中文的图片。

### 门禁B：过程图主动推送门禁
每个阶段生成的过程预览图，**必须立即主动发出**，禁止只汇报文字不附图：

```python
# 生成预览图后强制发送
image_path = "过程预览/stage_X_xxx.png"
# 在 Hermes Agent 中: send_message(message=f"MEDIA:{image_path}")
# 在其他环境: 手动发送该文件
```

**违规追溯：** 任何"图已生成但没发"的情况，视为流程违规，需立即补发并记录根因。

---

## 一、触发条件

以下任一关键词或场景触发本 skill：

**关键词触发：**
- 场宣图 / 场宣测试 / 场宣测试样张
- 明源场宣 / 明源活动logo / 明源528 / 明源528活动logo
- 明源宣传图 / 明源活动宣传
- 原图自行联网找高清风景壁纸，并把活动/logo素材叠加到 2560×1440 或 2K 横板
- 右上角logo / 右上角双logo / 右上角两个logo / 右下角logo / 国资右下角logo（且上下文涉及明源/场宣）
- 明源528 / 明源活动logo / 明源528活动logo
- 活动宣传图（明源地产场景）

**场景触发：**
- 用户发送 zip 压缩包（含 `素材/` `原图/` 两个文件夹）
- 用户要求对图片进行 2K 标准化 + 素材叠加
- 用户要求跑测试流程/演示模式
- 用户要求自检/版本发布（触发本技能审计+发布流程）

---

## 二、工作流总览

```text
用户提供zip(素材/ + 原图/)
    │
    ▼
[阶段0] 解包 & 素材审计
    │  确认素材数量、透明度、用户使用方式
    │  未说明则询问每张素材的放置位置
    │  输出: 素材审计图 + 原片审计图
    │
    ▼
[阶段1] 格式规范化 ── 2K标准
    │  横板 → 2560×1440 | 竖板 → 1440×2560
    │  等比智能裁切，居中保留主体
    │  输出: normalized/横板/ + normalized/竖版/
    │
    ▼
[阶段2] 轻度图片优化
    │  调整曝光 / 白平衡 / 对比度（保守参数）
    │  不做破坏性处理
    │  输出: enhanced/
    │
    ▼
[阶段3] 素材叠加 ── 先样板确认
    │  横板样板 ×1 发给用户确认
    │  ┌─ ✅ 确认 → 全量处理 ─┐
    │  │  🔄 调整 → 返回重做  │  ← 反馈闭环
    │  └────────────────────┘
    │  输出: final/
    │
    ▼
[阶段4] 打包交付
    │  分目录 → zip | 发送用户 | 日志留存
```

---

## 三、阶段详解

### 测试/演示模式

当用户要求「测试流程」「每个步骤汇报」「发过程图片」时：

1. 每个阶段必须输出一张过程预览 PNG，**并立即发出**：
   - 阶段0：素材审计图 + 原图分辨率审计图
   - 阶段1：规范化前后对比图
   - 阶段2：优化前后对比图
   - 阶段3：素材叠加样板图
   - 阶段4：成品总览图 + zip 包
2. 过程图统一放入 `成果/<任务名>/过程预览/`
3. 发图方式：每张图单独发送，不要拼在文字里

### 阶段0：解包 & 素材审计

1. 接收 zip 压缩包 → 解压到临时工作目录
2. 读取 `素材/` 文件夹，列出所有 PNG 素材
3. 读取 `原图/` 文件夹，统计数量、检测分辨率
4. 询问每张素材的放置方式（如果用户未说明）

**位置映射门禁：**
- `bottom-center` 必须是底部居中，按 `x=(bg_w-asset_w)/2`、`y=bg_h-asset_h-margin`
- `top-center` 必须是顶部居中，按 `x=(bg_w-asset_w)/2`、`y=margin`
- 禁止把 top/bottom center 当成画面中心偏移

### 阶段1：格式规范化

| 判断条件 | 处理方式 |
|----------|---------|
| 宽>高（横板） | 目标 2560×1440 |
| 高>宽（竖板） | 目标 1440×2560 |
| 比例近似（偏差<3%） | 直接缩放 |
| 比例差异较大 | 等比缩放至短边贴合 → 居中裁剪长边 |

**禁止拉伸变形。**

### 阶段2：轻度优化

- 自动白平衡微调
- 亮度 +5%
- 对比度 +10%
- 色彩饱和度 +5%
- **禁止：** 锐化 / 降噪 / 大幅调色 / AI内容识别

### 阶段3：素材叠加

1. 先处理横板 1 张作为样板 → 发给用户确认
2. 用户确认后，全量处理所有图片

**位置映射：**
| 描述 | 计算方式 |
|------|----------|
| 右上角 | 距右边 40px, 距上边 40px |
| 右下角 | 距右边 40px, 距下边 40px |
| 左上角 | 距左边 40px, 距上边 40px |
| 左下角 | 距左边 40px, 距下边 40px |

### 阶段4：打包交付

1. 最终产物放入 `成果/` 目录
2. 打包 zip：`成果/场宣图_成品_YYYYMMDD_taskname.zip`
3. 发送用户，留任务日志

---

## 四、检查清单

```
□ [门禁A] CJK 字体已验证可用
□ [门禁B] 每个阶段的过程预览图已主动发出
□ [阶段0] 素材数量/使用方式已确认
□ [阶段0] 原图分辨率分布已统计
□ [阶段1] 全部处理为 2K 标准
□ [阶段1] 无拉伸变形（等比裁剪）
□ [阶段1] EXIF方向已处理
□ [阶段2] 所有图片已轻度优化，参数保守
□ [阶段3] 样板已确认
□ [阶段3] PNG 透明度未丢失
□ [阶段3] 素材位置正确
□ [阶段4] zip 打包成功
□ [阶段4] 日志已留存
□ [全局] 临时文件已清理
```

---

## 五、工具脚本

| 脚本 | 用途 | 输入 | 输出 |
|------|------|------|------|
| `工具/normalize_resolution.py` | 格式规范化到2K | 原图目录 | 横板/竖板目录 |
| `工具/enhance_images.py` | 轻度图片优化 | 规范化后目录 | 优化后目录 |
| `工具/overlay_assets.py` | PNG素材叠加 | 优化后图片+素材 | 最终成品目录 |
| `工具/pipeline.py` | 一键全链路 | zip包+配置 | 成果zip |
| `工具/generate_test_data.py` | 生成测试数据 | 参数配置 | 测试用zip |
| `工具/checklist_validator.py` | 产出质量验证 | 产出目录 | 验证报告 |
| `工具/create_process_previews.py` | 过程预览拼图生成 | 工作目录 | 各阶段对比PNG |

**参考文件：**
- `references/test-workflow-with-real-images.md` — 真实图片替代测试数据方案
- `references/test-with-picsum.md` — picsum.photos 下载示例
- `references/CHANGELOG.md` — 版本变更日志
- `references/README.md` — 仓库 README 副本
- `references/v0.3.0-audit-methodology.md` — 107项深度自检方法论
- `references/github-readme-image-workflow.md` — GitHub Release 资产发布 + Mermaid 流程图规则

---

## 六、配置文件格式

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
    "color": 1.05,
    "sharpness": 1.0
  }
}
```

---

## 七、日志留存格式

```markdown
# 任务日志 - YYYY-MM-DD HH:MM

- 原图总数: X 张（横板 M / 竖板 N）
- 素材使用: [素材1 → 右上角, 素材2 → 右下角]
- 处理耗时: X 分钟
- 成品: 成果/场宣图_成品_YYYYMMDD_taskname.zip
- 用户反馈: [记录后续修改]
```

---

## 八、GitHub 发布流程

### 代码发布

```bash
# 1. 拉取最新
git pull origin master --rebase

# 2. 更新版本号（SKILL.md 顶栏版本字段）
# 3. 提交
git add -A && git commit -m "vX.Y.Z: 变更说明"

# 4. 打标签
git tag vX.Y.Z

# 5. 推送
git push origin master --tags
```

### README 图片发布（门禁C）

**铁律：GitHub README 中所有图片必须使用 Release 资产 URL，禁止使用相对路径。**

原因：GitHub 在 README 中渲染相对路径图片时，若路径含中文/特殊字符或目录层级复杂，图片会显示为断裂链接。

**正确做法：**

#### 方案A：通过 GitHub API 创建 Release + 上传资产（推荐）

```bash
TOKEN=你的GitHubToken
RID=$(curl -s -X POST -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/OWNER/REPO/releases \
  -d '{"tag_name":"vX.Y.Z", "name":"vX.Y.Z — 标题"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 逐个上传图片资产
for f in image1.png image2.png; do
  curl -s -X POST -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: image/png" \
    "https://uploads.github.com/repos/OWNER/REPO/releases/${RID}/assets?name=${f}" \
    --data-binary @"${f}"
done
```

#### 方案B：复制图片到 assets/ 目录后通过 raw.githubusercontent.com 引用

```markdown
![图片说明](https://raw.githubusercontent.com/OWNER/REPO/master/assets/workflow/xxx.png)
```

**注意：**
- 图片文件名必须全英文，不含中文/空格/特殊字符
- README 中引用格式：`![说明](https://github.com/OWNER/REPO/releases/download/vX.Y.Z/xxx.png)`
- 图片作为 Release 资产上传后，访问路径固定为 `releases/download/vX.Y.Z/xxx.png`
- 每次更新图片需重新上传到 Release（同名覆盖）或创建新 Release

### Mermaid 流程图注意事项

在 GitHub README 中嵌入 Mermaid 流程图时，必须遵守以下规则：

1. **禁止使用 HTML 标签** — `<br/>`、`<br>` 等会导致渲染失败（红色报错）。用 `→`、空格、精简文字代替换行
2. **禁止挂在空的目标节点** — `C -.->|label` 缺少目标节点会报错。应补透明节点：`C -.->|label| CL[" "]` + `style CL fill:transparent,stroke:none`
3. **子图与节点命名冲突** — 子图名 `B[xxx]` 与外部节点 `B` 冲突时，改用 `B0[xxx]`
4. **方向选择** — 流水线式流程用 `LR`（横向），层级结构用 `TD`（纵向）
5. **闭环结构** — 关键决策点（如样板确认）必须有 → 反馈回路，展示完整的确认/调整闭环

### 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.3.1 | 2026-05-22 | README 图片发布门禁（Release 资产）、Mermaid 流程图规则、样板确认反馈闭环 |
| v0.3.0 | 2026-05-22 | 107项审计修复、CJK字体门禁、过程图推送铁律、质量加固 |
| v0.2.0 | 2026-05-21 | 过程预览系统、测试数据集、仓库重构 |
| v0.0.1 | 2026-05-15 | 初始版本 |

---

> 版本: 0.3.1 | 作者: Alix（明源云海南） | 更新时间: 2026-05-22
