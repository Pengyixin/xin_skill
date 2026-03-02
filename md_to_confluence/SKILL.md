---
name: md-to-confluence-uploader
description: Markdown 到 Confluence 上传工具是一个自动化工具，用于将 Markdown 文件转换为 Confluence 页面格式并上传。支持创建新页面、更新现有页面、添加标签和创建层级结构。工具通过 Confluence REST API 实现自动化文档管理，支持多种配置方式（config.json、环境变量、命令行参数），并提供 dry-run 模式用于预览转换结果。跨平台支持 Windows/Linux/Mac。
---

# Markdown 到 Confluence 上传工具

## 概述

将 Markdown 文件自动转换为 Confluence 页面格式并上传。支持账号密码登录方式，可创建新页面或更新现有页面。

**GitHub**: https://github.com/anomalyco/md_to_confluence

## 核心功能

1. **Markdown 转换**: 自动将 Markdown 转换为 Confluence Storage Format
2. **页面管理**: 支持创建新页面和更新现有页面
3. **灵活配置**: 支持 config.json、环境变量和命令行参数三种配置方式
4. **标签支持**: 可为页面添加多个标签
5. **父子页面**: 支持创建带父页面的层级结构
6. **跨平台**: 支持 Windows、Linux、Mac

## 前置要求

- Python 3.6+
- pip 包管理器
- Atlassian 账户（需要 API Token）

### 安装步骤

```bash
cd /home/peng/.opencode/skill/md_to_confluence
python3 setup.py
```

## 配置方式

### 方式 1: config.json（推荐）

编辑 `config.json`：

```json
{
  "confluence": {
    "username": "your-email@company.com",
    "password": "your-api-token",
    "base_url": "https://confluence.company.com"
  }
}
```

### 方式 2: 环境变量

```bash
export CONFLUENCE_URL=https://confluence.company.com
export CONFLUENCE_USERNAME=your-email@company.com
export CONFLUENCE_PASSWORD=your-api-token
export CONFLUENCE_SPACE_KEY=YOURSPACE
```

### 方式 3: 命令行参数

在命令中直接指定：
```bash
--confluence-url https://confluence.company.com \
--username your-email@company.com \
--password your-api-token
```

**配置优先级**: 命令行 > 环境变量 > config.json

## 使用方法

### 方式 1：使用 Python 脚本（推荐）

```bash
cd /home/peng/.opencode/skill/md_to_confluence

# 创建新页面
python3 run.py /path/to/file.md --title "页面标题" --space-key YOURSPACE

# 更新现有页面
python3 run.py /path/to/file.md --page-id 659864614

# 预览转换结果
python3 run.py /path/to/file.md --title "测试" --dry-run
```

### 方式 2：手动激活虚拟环境

```bash
cd /home/peng/.opencode/skill/md_to_confluence
source venv/bin/activate
python md_to_confluence.py /path/to/file.md --title "页面标题" --space-key YOURSPACE
```

## 命令行参数

| 参数 | 说明 | 必需 |
|------|------|------|
| `markdown_file` | Markdown 文件路径 | ✅ |
| `--title, -t` | 页面标题 | 创建时必需 |
| `--space-key, -s` | Confluence 空间 key | 创建时必需 |
| `--parent-id, -p` | 父页面 ID | ❌ |
| `--page-id` | 现有页面 ID（用于更新） | 更新时必需 |
| `--label, -l` | 页面标签（可多次使用） | ❌ |
| `--config` | 配置文件路径（默认: config.json） | ❌ |
| `--cloud` | 使用 Atlassian Cloud 模式 | ❌ |
| `--dry-run` | 只打印转换结果，不上传 | ❌ |
| `--confluence-url` | Confluence URL | ❌ |
| `--username` | 用户名 | ❌ |
| `--password` | 密码或 API Token | ❌ |

## 完整示例

### 示例 1: 创建新页面

```bash
cd /home/peng/.opencode/skill/md_to_confluence

# 首次使用需要初始化
python3 setup.py

# 创建新页面
python3 run.py example.md \
  --title "任务计划" \
  --space-key VCODEC \
  --parent-id 12345678 \
  --label plan --label 2024
```

### 示例 2: 更新现有页面

```bash
python3 run.py example.md --page-id 659864614
```

### 示例 3: 使用自定义配置

```bash
python3 run.py doc.md \
  --title "API文档" \
  --config /path/to/custom-config.json \
  --space-key API
```

### 示例 4: 使用 Atlassian Cloud

```bash
python3 run.py doc.md \
  --title "文档" \
  --space-key DEV \
  --cloud \
  --username email@example.com \
  --password your-api-token
```

### 示例 5: 预览转换结果（不上传）

```bash
python3 run.py example.md --title "测试" --dry-run
```

## 支持的 Markdown 特性

- **标题**: H1-H6
- **文本格式**: 粗体、斜体、删除线、内联代码
- **列表**: 有序列表、无序列表、嵌套列表
- **代码块**: 支持语法高亮，自动转换为 Confluence 代码宏
- **表格**: 标准 Markdown 表格
- **链接和图片**: 支持 URL
- **信息面板**: 通过引用块标记 `[info]`、`[warning]`、`[note]`、`[tip]`
- **水平分割线**

## 信息面板语法

```markdown
> [info] 这是信息面板的内容

> [warning] 这是警告面板的内容

> [note] 这是注意面板的内容

> [tip] 这是提示面板的内容
```

## 故障排除

### 问题 1: 认证失败

**可能原因**:
- 检查 config.json 中的用户名和 API Token
- 确认 Confluence URL 是否正确
- Atlassian Cloud 需要使用 API Token 代替密码

**解决方案**:
```bash
# 检查配置文件
cat config.json

# 验证 Confluence URL 可访问
curl -I https://confluence.company.com
```

### 问题 2: 页面更新失败

**可能原因**:
- 确认页面 ID 正确
- 检查用户是否有编辑权限
- 确认 space key 正确

### 问题 3: Python 环境错误

**错误信息**: `ModuleNotFoundError` 或 `error: externally-managed-environment`

**解决方案**: 运行 `python3 setup.py` 创建虚拟环境

### 问题 4: 获取 API Token

1. 访问 https://id.atlassian.com/manage-profile/security/api-tokens
2. 点击 "Create API token"
3. 复制生成的 token

## 与 confluence-markdown-exporter 配合使用

你可以结合两个技能实现双向转换：

```bash
# 从 Confluence 导出
cd /home/peng/.opencode/skill/confluence_md_exporter
python3 run.py pages 12345678 --output-path ./temp.md

# 编辑后重新上传
cd /home/peng/.opencode/skill/md_to_confluence
python3 run.py ./temp.md --page-id 12345678
```

## 文件清单

```
/home/peng/.opencode/skill/md_to_confluence/
├── SKILL.md              # 技能文档
├── README.md             # 快速参考
├── md_to_confluence.py   # 主脚本
├── config.json           # 配置文件模板
├── requirements.txt       # Python依赖
├── example.md            # Markdown示例文件
├── setup.py              # 初始化脚本（创建虚拟环境）
├── run.py                # 便捷启动脚本
└── venv/                 # Python虚拟环境（运行 setup.py 后创建）
```

Base directory for this skill: file:///home/peng/.opencode/skill/md_to_confluence
