# Changelog

## v0.3.3 (2026-05-25) — HTML 多版本预览

### Features
- 新增 `generate_html_preview.py`：成品多版本浏览器预览页，自动分组/点击放大
- 集成到阶段4打包交付流程，纳入门禁B推送要求
- SKILL.md 描述和用途更新，包含"HTML多版本预览"

---

## v0.3.1 (2026-05-22) — README 工作流可视化

### Changes
- README 全面重写：Mermaid 流程图 + 四阶段图文详解
- 每阶段配过程预览图 + 效果展示（6张预览图已入库）
- Stage 0: 素材审计 + 原图审计图文说明
- Stage 1: 格式规范化四种裁切策略可视化
- Stage 2: 轻度优化前后亮度/对比度对比
- Stage 3: 叠加样板 + 全量成品抽检总览

---

## v0.3.0 (2026-05-22) — 安全加固版本

### Security
- CJK 字体门禁：所有脚本启动时验证中文字体可用性，缺失则阻塞
- 过程图推送铁律：预览图生成后必须主动发出，禁止文字替代
- EXIF 方向处理：手机竖拍图片自动旋转修正
- 图片完整性验证：处理前检测文件损坏

### Fixes
- normalize_resolution.py: 去除 os 未使用导入；正方形的 orientation 判定
- overlay_assets.py: 修复 margin=0 时使用默认边距；custom 位置逻辑；位置日志
- enhance_images.py: 支持更多图片格式（webp）；argparse CLI；跳过已处理文件
- generate_test_data.py: shutil 全局导入；--count/--seed 支持；CJK 字体严格验证
- pipeline.py: CJK 字体门禁；配置验证；--cleanup 清理；--task-name
- SKILL.md: 版本号一致性修复（v0.3.0）；死代码移除（raise 前 print）
- create_process_previews.py: 新增 stage1/2/3 预览生成函数

### Features
- EXIF 方向自动修正（normalize_resolution.py）
- 质量退化解检测（enhance_images.py）
- JSON 输出供 CI/脚本调用（normalize_resolution.py + checklist_validator.py）
- 素材重叠检测 + 位置日志（overlay_assets.py）
- 配置文件覆盖优化参数（enhance_images.py）
- 测试数据生成可指定数量/种子（generate_test_data.py）

### Quality
- checklist_validator.py 新增：文件完整性检查、文件大小合理性、命名规范、重复检测
- 所有脚本改用 argparse 参数解析（enhance_images.py + checklist_validator.py）
- 所有脚本增加进度指示（overlay_assets.py 带序号；enhance_images.py 带进度条）
- pipeline.py 新增 --cleanup 选项自动清理临时文件

### Repository
- CHANGELOG.md 独立日志文件
- README.md 更新至 v0.3.0
- .gitignore 增强排除规则
- 107项代码审计修复完成

---

## v0.2.0 (2026-05-21) — 过程预览系统

### Features
- create_process_previews.py: 各阶段自动生成可视化对比拼图
- 测试数据集: 覆盖所有常见比例的 28 个分辨率 + 4 个透明 PNG 素材
- 过程预览示例: 6 张实际运行截图

### Changes
- 仓库重构: 清晰目录划分（工具/测试数据/示例/日志）
- 相对路径配置示例
- 增强 .gitignore

---

## v0.0.1 (2026-05-15) — 初始版本

### Features
- 6 个核心工具脚本
- 四阶段管线：规范→优化→叠加→打包
- 检查清单验证器
- MIT 许可证
