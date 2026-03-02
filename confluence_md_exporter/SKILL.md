---
name: confluence-markdown-exporter
description: Confluence Markdown导出工具（confluence-markdown-exporter）是一个基于开源Python包的工具，用于将Confluence页面导出为Markdown格式。支持导出单个页面、包含子页面的页面、整个空间，保留页面格式、表格、代码块等元素，适用于文档迁移到Obsidian、VSCode、GitHub等平台。跨平台支持 Windows/Linux/Mac。
---

# Confluence Markdown 导出工具

## 概述

confluence-markdown-exporter 是一个开源工具，通过 Atlassian API 将 Confluence 页面导出为 Markdown 格式。支持多种导出模式，保留页面结构和格式。

**GitHub**: https://github.com/Spenhouet/confluence-markdown-exporter

## 核心功能

1. **页面导出**: 导出单个 Confluence 页面为 Markdown
2. **递归导出**: 导出页面及其所有子页面
3. **空间导出**: 导出整个 Confluence 空间
4. **格式保留**: 保留标题、列表、表格、代码块等格式
5. **PlantUML 支持**: 将 PlantUML 图表转换为 Markdown 代码块
6. **跨平台**: 支持 Windows、Linux、Mac
7. **重试机制**: 网络不稳定时自动重试

## 前置要求

- Python 3.10+
- pip 包管理器
- Atlassian 账户（需要 API Token）

### 安装步骤

```bash
cd /home/peng/.opencode/skill/confluence_md_exporter
python3 setup.py
```

## 配置方式

### 方式 1: 环境变量（推荐用于脚本和自动化）

```bash
export ATLASSIAN_USERNAME=your-email@company.com
export ATLASSIAN_API_TOKEN=your-api-token
export ATLASSIAN_URL=https://confluence.company.com
```

### 方式 2: .env 文件

在项目目录创建 `.env` 文件：

```bash
cp .env.example .env
# 编辑 .env 文件填入信息
```

内容格式：
```
ATLASSIAN_USERNAME=your-email@company.com
ATLASSIAN_API_TOKEN=your-api-token
ATLASSIAN_URL=https://confluence.company.com
```

**获取 API Token**: 访问 https://id.atlassian.com/manage-profile/security/api-tokens

## 使用方法

**重要说明**：如果用户没有提供账号密码，系统会自动使用 `.env` 文件中的配置。

### 方式 1：使用 Python 脚本（推荐）

```bash
cd /home/peng/.opencode/skill/confluence_md_exporter

# 导出单个页面（自动使用 .env 中的认证信息）
python3 run.py pages 123456789

# 导出页面及其子页面
python3 run.py pages-with-descendants 123456789

# 导出整个空间
python3 run.py spaces YOURSPACE

# 指定输出目录
python3 run.py pages 123456789 --output-path ./docs

# 自定义重试次数
python3 run.py --retries 5 --retry-delay 3 pages 123456789
```

### 方式 2：手动激活虚拟环境

```bash
cd /home/peng/.opencode/skill/confluence_md_exporter
source venv/bin/activate
confluence-markdown-exporter pages 123456789
```

## 命令参考

### 全局选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--retries N` | 3 | 重试次数 |
| `--retry-delay N` | 2 | 重试间隔(秒) |
| `--help, -h` | - | 显示帮助 |

### 命令列表

| 命令 | 说明 |
|------|------|
| `pages` | 导出一个或多个页面 |
| `pages-with-descendants` | 导出页面及其所有子页面 |
| `spaces` | 导出一个或多个空间 |
| `all-spaces` | 导出所有空间 |
| `config` | 配置认证信息（交互式） |
| `version` | 显示版本 |

### pages 命令参数

```bash
python3 run.py pages [OPTIONS] PAGES...

参数:
  PAGES...              页面ID或URL（必需）

选项:
  --output-path PATH    输出目录路径
  --help                显示帮助
```

### pages-with-descendants 命令参数

```bash
python3 run.py pages-with-descendants [OPTIONS] PAGES...

参数:
  PAGES...              父页面ID或URL（必需）

选项:
  --output-path PATH    输出目录路径
  --help                显示帮助
```

### spaces 命令参数

```bash
python3 run.py spaces [OPTIONS] SPACES...

参数:
  SPACES...             空间key（必需）

选项:
  --output-path PATH    输出目录路径
  --help                显示帮助
```

## 完整示例

### 示例 1: 导出单个页面

```bash
cd /home/peng/.opencode/skill/confluence_md_exporter
export ATLASSIAN_USERNAME=your-email@company.com
export ATLASSIAN_API_TOKEN=your-api-token
export ATLASSIAN_URL=https://confluence.company.com
python3 run.py pages 659864614 --output-path /home/peng/av2
```

### 示例 2: 导出多个页面

```bash
python3 run.py pages 12345678 12345679 12345680 --output-path ./docs
```

### 示例 3: 导出页面及其子页面

```bash
python3 run.py pages-with-descendants 12345678 --output-path ./wiki-docs
```

### 示例 4: 导出整个空间

```bash
python3 run.py spaces VCODEC --output-path ./vcodec-docs
```

### 示例 5: 使用 .env 文件

```bash
cd /home/peng/.opencode/skill/confluence_md_exporter
cp .env.example .env
# 编辑 .env 文件添加认证信息
python3 run.py pages 12345678 --output-path ./output
```

### 示例 6: 网络不稳定时增加重试

```bash
python3 run.py --retries 5 --retry-delay 5 pages 123456789
```

## 支持的格式转换

- **标题**: H1-H6 转换为 Markdown 标题
- **文本格式**: 粗体、斜体、下划线、删除线
- **列表**: 有序列表、无序列表、嵌套列表
- **表格**: 转换为 Markdown 表格格式
- **代码块**: 支持语法高亮
- **链接**: 内部和外部链接
- **PlantUML**: 转换为 Markdown 代码块
- **信息面板**: 转换为引用块

## 输出结构

```
output/
├── page-title.md
├── page-title/
│   ├── attachments/
│   │   └── image.png
│   └── child-page.md
└── ...
```

## 故障排除

### 问题 1: 认证失败

**错误信息**: `401 Unauthorized`

**解决方案**:
1. 检查 ATLASSIAN_API_TOKEN 是否正确
2. 确认用户名是完整的邮箱地址
3. 验证 API Token 是否过期，重新生成

### 问题 2: 页面不存在

**错误信息**: `404 Not Found`

**解决方案**:
1. 确认 page-id 正确
2. 检查用户是否有页面访问权限
3. 验证 Confluence URL 正确

### 问题 3: 导出内容不完整

**可能原因**:
- 某些复杂的 Confluence 宏不支持
- 自定义插件内容无法转换

**解决方案**:
- 检查导出日志中的警告信息
- 手动编辑导出的 Markdown 文件

### 问题 4: Python 环境错误

**错误信息**: `ModuleNotFoundError` 或 `error: externally-managed-environment`

**解决方案**: 使用 `python3 setup.py` 脚本，自动管理虚拟环境

### 问题 5: 导出失败频繁

**解决方案**:
- 增加重试次数: `python3 run.py --retries 5 pages 123456789`
- 增加重试间隔: `python3 run.py --retry-delay 5 pages 123456789`

## 与 md-to-confluence-uploader 配合使用

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
/home/peng/.opencode/skill/confluence_md_exporter/
├── SKILL.md              # 技能文档
├── README.md             # 快速参考
├── requirements.txt      # Python依赖
├── setup.py              # 初始化脚本（创建虚拟环境）
├── run.py                # 便捷启动脚本
├── .env.example          # 环境变量模板
├── .env                  # 环境变量配置文件（需要创建）
└── venv/                 # Python虚拟环境（运行 setup.py 后创建）
```

Base directory for this skill: file:///home/peng/.opencode/skill/confluence_md_exporter
