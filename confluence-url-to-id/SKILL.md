---
name: confluence-url-to-id
description: Confluence URL 转页面 ID 工具是一个专门用于 Amlogic Confluence 的 URL 转换工具，可以将 Confluence 页面 URL 转换为页面 ID，便于与 confluence-markdown-exporter 等其他工具配合使用。支持批量转换和文件导入功能。
---

# Confluence URL 转页面 ID 工具

## 概述

confluence-url-to-id 是一个专门用于 Amlogic Confluence 的 URL 转换工具，可以将 Confluence 页面 URL 转换为页面 ID，便于与 confluence-markdown-exporter 等其他工具配合使用。

## 核心功能

1. **URL 转 ID**: 将 Confluence 页面 URL 转换为页面 ID
2. **批量转换**: 支持多个 URL 同时转换
3. **文件导入**: 支持从文件批量读取 URL 列表
4. **交互式配置**: 提供交互式配置认证信息
5. **Amlogic 专用**: 针对 Amlogic Confluence 环境优化

## 前置要求

- Python 3.6+
- pip 包管理器
- Amlogic Confluence 账户（需要 API Token）

### 安装依赖

```bash
cd /home/peng/.opencode/skill/confluence-url-to-id
pip install -r requirements.txt
```

## 配置方式

> **重要说明**：本工具已预配置 Amlogic Confluence 认证信息。如果用户没有显式提供账号信息，工具将自动使用 `.env` 文件中的默认配置。

### 方式 1: 使用默认配置（推荐）

工具已预配置，无需额外设置，直接使用：

```bash
cd /home/peng/.opencode/skill/confluence-url-to-id
./convert.py url "https://confluence.amlogic.com/display/SW/AV2+bringup+Meetings"
```

系统将自动使用 `.env` 文件中的默认认证信息。

### 方式 2: 环境变量

如需使用其他账号，可通过环境变量覆盖：

```bash
export ATLASSIAN_USERNAME=your-email@amlogic.com
export ATLASSIAN_API_TOKEN=your-api-token
export ATLASSIAN_URL=https://confluence.amlogic.com
```

### 方式 3: .env 文件

编辑或创建 `.env` 文件：

```bash
# 查看当前配置
cat .env

# 或编辑配置
vim .env
```

内容格式：
```
ATLASSIAN_USERNAME=your-email@amlogic.com
ATLASSIAN_API_TOKEN=your-api-token
ATLASSIAN_URL=https://confluence.amlogic.com
```

### 方式 4: 交互式配置

```bash
./convert.py config
```

**获取 API Token**: 访问 https://id.atlassian.com/manage-profile/security/api-tokens

## 使用方法

**无需配置，开箱即用**：本工具已预配置 Amlogic Confluence 认证信息，直接执行命令即可。

### 转换单个 URL

```bash
cd /home/peng/.opencode/skill/confluence-url-to-id
./convert.py url "https://confluence.amlogic.com/display/SW/AV2+bringup+Meetings"
```

> 系统会自动读取 `.env` 文件中的默认认证信息并显示：`使用配置的账户: xxx@amlogic.com`

**输出示例**：
```
页面标题: AV2 bringup Meetings
空间: SW
页面 ID: 655742723
URL: https://confluence.amlogic.com/display/SW/AV2+bringup+Meetings
```

### 转换多个 URL

```bash
./convert.py url \
  "https://confluence.amlogic.com/display/SW/Page1" \
  "https://confluence.amlogic.com/display/SW/Page2"
```

### 从文件批量转换

```bash
# urls.txt 文件每行一个 URL
./convert.py file urls.txt
```

## 命令参考

| 命令 | 说明 | 示例 |
|------|------|------|
| `url` | 转换一个或多个 URL | `./convert.py url "URL1" "URL2"` |
| `file` | 从文件批量转换 | `./convert.py file urls.txt` |
| `config` | 交互式配置认证信息 | `./convert.py config` |

## 完整示例

### 示例 1: 获取页面 ID 后导出 Markdown

```bash
# 1. 获取页面 ID
cd /home/peng/.opencode/skill/confluence-url-to-id
./convert.py url "https://confluence.amlogic.com/display/SW/AV2+bringup+Meetings"

# 输出: 页面 ID: 655742723

# 2. 使用 ID 导出 Markdown
cd /home/peng/.opencode/skill/confluence_md_exporter
python3 run.py pages 655742723 --output-path /home/peng/av2
```

### 示例 2: 批量转换后批量导出

```bash
# 1. 创建 URL 列表文件
cat > urls.txt << 'EOF'
https://confluence.amlogic.com/display/SW/Page1
https://confluence.amlogic.com/display/SW/Page2
https://confluence.amlogic.com/display/SW/Page3
EOF

# 2. 批量转换获取所有 ID
./convert.py file urls.txt

# 3. 使用 ID 列表导出所有页面
python3 run.py pages ID1 ID2 ID3 --output-path ./output
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
1. 确认 URL 正确
2. 检查用户是否有页面访问权限

### 问题 3: URL 格式不支持

**错误信息**: `无法解析 URL`

**支持的 URL 格式**:
- `https://confluence.amlogic.com/display/SW/Page+Title`
- `https://confluence.amlogic.com/pages/viewpage.action?pageId=123456`
- `https://confluence.amlogic.com/pages/viewpage.action?spaceKey=SW&title=Page+Title`

## 与 confluence-markdown-exporter 配合使用

```bash
# 步骤 1: URL 转 ID
cd /home/peng/.opencode/skill/confluence-url-to-id
./convert.py url "https://confluence.amlogic.com/display/SW/AV2+bringup+Meetings"

# 步骤 2: 使用 ID 导出 Markdown
cd /home/peng/.opencode/skill/confluence_md_exporter
python3 run.py pages 655742723 --output-path /home/peng/av2
```

## 文件清单

```
/home/peng/.opencode/skill/confluence-url-to-id/
├── SKILL.md              # 技能文档
├── README.md             # 快速参考
├── convert.py            # 主转换脚本（可执行）
├── requirements.txt      # Python依赖
├── .env.example          # 环境变量模板
└── .env                  # 环境变量配置文件（已预配置，可直接使用）
```

Base directory for this skill: file:///home/peng/.opencode/skill/confluence-url-to-id

Relative paths in this skill (e.g., scripts/, reference/) are relative to this base directory.
Note: file list is sampled.

<skill_files>
<file>/home/peng/.opencode/skill/confluence-url-to-id/convert.py</file>
<file>/home/peng/.opencode/skill/confluence-url-to-id/README.md</file>
<file>/home/peng/.opencode/skill/confluence-url-to-id/.env.example</file>
<file>/home/peng/.opencode/skill/confluence-url-to-id/requirements.txt</file>
</skill_files>
