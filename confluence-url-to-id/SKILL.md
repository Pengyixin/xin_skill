---
name: confluence-url-to-id
description: Confluence URL 转页面 ID 工具是一个专门用于 Amlogic Confluence 的 URL 转换工具，可以将 Confluence 页面 URL 转换为页面 ID，便于与 confluence-markdown-exporter 等其他工具配合使用。支持批量转换和文件导入功能。使用环境变量配置认证信息，支持 Personal Access Token (PAT)、API Token 和密码三种认证方式。
---

# Confluence URL 转页面 ID 工具

## 概述

confluence-url-to-id 是一个专门用于 Amlogic Confluence 的 URL 转换工具，可以将 Confluence 页面 URL 转换为页面 ID，便于与 confluence-markdown-exporter 等其他工具配合使用。

## 核心功能

1. **URL 转 ID**: 将 Confluence 页面 URL 转换为页面 ID
2. **批量转换**: 支持多个 URL 同时转换
3. **文件导入**: 支持从文件批量读取 URL 列表
4. **环境变量配置**: 使用环境变量配置认证信息
5. **多种认证方式**: 支持 Personal Access Token (PAT)、API Token 和密码
6. **Amlogic 专用**: 针对 Amlogic Confluence 环境优化

## 前置要求

- Python 3.6+
- pip 包管理器
- Amlogic Confluence 账户
- 认证凭据（PAT、API Token 或密码）

### 安装依赖

```bash
cd /home/peng/.opencode/skill/confluence-url-to-id
pip install -r requirements.txt
```

## 配置方式

**重要说明**: 本工具使用环境变量配置认证信息，**不使用 .env 文件**。

### 必需的环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `CONFLUENCE_USERNAME` | 用户名（如 `john.doe` 或 `john.doe@company.com`） | 是 |
| `CONFLUENCE_API_TOKEN` | API Token 或 Personal Access Token | 是* |
| `CONFLUENCE_PASSWORD` | 密码（备选方案） | 是* |

*注：API Token 和 Password 二选一即可，优先使用 API Token

### 可选的环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `CONFLUENCE_URL` | Confluence 服务器地址 | `https://confluence.amlogic.com` |

### 向后兼容

以下旧的环境变量名仍然可用（新名称优先）：
- `ATLASSIAN_URL`（替代 `CONFLUENCE_URL`）
- `ATLASSIAN_USERNAME`（替代 `CONFLUENCE_USERNAME`）
- `ATLASSIAN_API_TOKEN`（替代 `CONFLUENCE_API_TOKEN`）
- `ATLASSIAN_PASSWORD`（替代 `CONFLUENCE_PASSWORD`）

### 配置示例

```bash
export CONFLUENCE_URL="https://confluence.amlogic.com"
export CONFLUENCE_USERNAME="your-username"
export CONFLUENCE_API_TOKEN="your-api-token-or-pat"
```

或使用密码：
```bash
export CONFLUENCE_URL="https://confluence.amlogic.com"
export CONFLUENCE_USERNAME="your-username"
export CONFLUENCE_PASSWORD="your-password"
```

## 认证方式说明

工具会自动检测认证类型：

1. **Personal Access Token (PAT)** - 长 token（>40字符），通过 Bearer Header 认证
2. **API Token** - 普通 API Token，通过 Basic Auth 认证
3. **Password** - 通过 Basic Auth 认证

## 使用方法

### 转换单个 URL

```bash
./convert.py url "https://confluence.amlogic.com/display/SW/AV2+bringup+Meetings"
```

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

### 交互式配置

```bash
./convert.py config
```

此命令会显示当前环境变量配置，并输出建议的环境变量设置命令。

## 命令参考

| 命令 | 说明 | 示例 |
|------|------|------|
| `url` | 转换一个或多个 URL | `./convert.py url "URL1" "URL2"` |
| `file` | 从文件批量转换 | `./convert.py file urls.txt` |
| `config` | 显示当前配置和环境变量导出命令 | `./convert.py config` |

## 支持的 URL 格式

- `https://confluence.amlogic.com/display/SPACE/Page+Title`
- `https://confluence.amlogic.com/pages/viewpage.action?pageId=123456`
- `https://confluence.amlogic.com/pages/viewpage.action?spaceKey=SPACE&title=Page+Title`

## 完整示例

### 示例 1: 获取页面 ID 后导出 Markdown

```bash
# 1. 配置环境变量
export CONFLUENCE_URL="https://confluence.amlogic.com"
export CONFLUENCE_USERNAME="your-username"
export CONFLUENCE_API_TOKEN="your-api-token-or-pat"

# 2. 获取页面 ID
cd /home/peng/.opencode/skill/confluence-url-to-id
./convert.py url "https://confluence.amlogic.com/display/SW/AV2+bringup+Meetings"
# 输出: 页面 ID: 655742723

# 3. 使用 ID 导出 Markdown
cd /home/peng/.opencode/skill/confluence_md_exporter
python3 run.py pages 655742723 --output-path ./output
```

### 示例 2: 批量转换后批量导出

```bash
# 1. 配置环境变量
export CONFLUENCE_URL="https://confluence.amlogic.com"
export CONFLUENCE_USERNAME="your-username"
export CONFLUENCE_API_TOKEN="your-api-token-or-pat"

# 2. 创建 URL 列表文件
cat > urls.txt << 'EOF'
https://confluence.amlogic.com/display/SW/Page1
https://confluence.amlogic.com/display/SW/Page2
https://confluence.amlogic.com/display/SW/Page3
EOF

# 3. 批量转换获取所有 ID
./convert.py file urls.txt

# 4. 使用 ID 列表导出所有页面
python3 run.py pages ID1 ID2 ID3 --output-path ./output
```

## 故障排除

### 问题 1: 认证失败 (401 Unauthorized)

**可能原因**:
1. Token 已过期或被撤销
2. 用户名不正确
3. 使用了错误的认证方式

**解决方案**:
1. 检查用户名是否为正确的邮箱或用户名
2. 重新生成 Personal Access Token
3. 确认 Token 是否有权限访问目标页面

**获取 Personal Access Token**:
1. 登录 Confluence 网页版
2. 点击右上角头像 → "个人设置" → "Personal Access Tokens"
3. 创建一个新的 token

### 问题 2: 页面不存在 (404 Not Found)

**解决方案**:
1. 确认 URL 正确
2. 检查用户是否有页面访问权限

### 问题 3: 无法解析 URL

**支持的 URL 格式**:
- `https://confluence.amlogic.com/display/SW/Page+Title`
- `https://confluence.amlogic.com/pages/viewpage.action?pageId=123456`
- `https://confluence.amlogic.com/pages/viewpage.action?spaceKey=SW&title=Page+Title`

### 问题 4: 未配置认证信息

**错误信息**: `❌ 错误: 未配置认证信息`

**解决方案**:
```bash
export CONFLUENCE_URL="https://confluence.amlogic.com"
export CONFLUENCE_USERNAME="your-username"
export CONFLUENCE_API_TOKEN="your-token"
```

## 与 confluence-markdown-exporter 配合使用

```bash
# 步骤 1: 配置环境变量
export CONFLUENCE_URL="https://confluence.amlogic.com"
export CONFLUENCE_USERNAME="your-username"
export CONFLUENCE_API_TOKEN="your-api-token-or-pat"

# 步骤 2: URL 转 ID
cd /home/peng/.opencode/skill/confluence-url-to-id
./convert.py url "https://confluence.amlogic.com/display/SW/AV2+bringup+Meetings"
# 输出: 页面 ID: 655742723

# 步骤 3: 使用 ID 导出 Markdown
cd /home/peng/.opencode/skill/confluence_md_exporter
python3 run.py pages 655742723 --output-path ./output
```

## 文件清单

```
/home/peng/.opencode/skill/confluence-url-to-id/
├── SKILL.md              # 技能文档（本文件）
├── README.md             # 快速参考
├── convert.py            # 主转换脚本（可执行）
├── test_auth.py          # 认证调试脚本
└── requirements.txt      # Python依赖
```

## 技术实现说明

### 认证机制

- **PAT 认证**: 通过 `Authorization: Bearer <token>` Header 发送请求
- **API Token/密码认证**: 通过 HTTP Basic Auth 发送请求

### 自动检测 PAT

工具通过 token 长度自动检测是否为 PAT：
- PAT 通常 > 40 字符
- 普通 API Token 通常较短

Base directory for this skill: file:///home/peng/.opencode/skill/confluence-url-to-id

Relative paths in this skill (e.g., scripts/, reference/) are relative to this base directory.
Note: file list is sampled.

<skill_files>
<file>/home/peng/.opencode/skill/confluence-url-to-id/convert.py</file>
<file>/home/peng/.opencode/skill/confluence-url-to-id/README.md</file>
<file>/home/peng/.opencode/skill/confluence-url-to-id/test_auth.py</file>
<file>/home/peng/.opencode/skill/confluence-url-to-id/requirements.txt</file>
</skill_files>
