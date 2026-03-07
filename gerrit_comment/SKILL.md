---
name: gerrit-comment
description: Gerrit Comment 评论工具是一个用于在 Gerrit 代码审查系统上添加评论的 Python 工具。支持通过 Gerrit URL 或 change ID 在指定的 change 上添加普通评论，支持环境变量和配置文件管理认证信息，适用于代码审查反馈和自动化评论场景。
---

# Gerrit Comment 评论工具使用说明

## 1. 概述

### 1.1 主要功能
- **添加评论**: 通过 Gerrit API 在指定的 change 上添加评论
- **支持多种格式**: 支持普通评论和行级评论
- **配置文件管理**: 通过配置文件管理 Gerrit 认证信息
- **批量评论**: 支持批量在多个 changes 上添加评论

### 1.2 技术架构
- **语言**: Python 3
- **核心模块**:
  - `GerritCommenter`: Gerrit 评论客户端
  - `extract_change_id`: URL 解析函数
- **外部依赖**:
  - `pygerrit2`: Gerrit REST API 客户端
  - `requests`: HTTP 请求库

### 1.3 系统要求
- Python 3.6+
- 网络访问权限（可访问 Gerrit 服务器）
- 有效的 Gerrit 认证凭据

## 2. 快速入门

### 2.1 安装依赖
```bash
pip install pygerrit2 requests
```

### 2.2 配置方式

工具支持两种配置方式，优先级：**环境变量 > 配置文件**

#### 方式一：环境变量（推荐）

设置以下环境变量：
```bash
export GERRIT_URL="https://scgit.amlogic.com"
export GERRIT_USERNAME="your_username"
export GERRIT_PASSWORD="your_password"
```

**优点**：
- 无需管理配置文件
- 支持临时切换账号：`GERRIT_USERNAME="other" python3 gerrit_comment.py ...`
- 敏感信息不会留在代码仓库中

**持久化配置**（添加到 ~/.bashrc 或 ~/.zshrc）：
```bash
echo 'export GERRIT_URL="https://scgit.amlogic.com"' >> ~/.bashrc
echo 'export GERRIT_USERNAME="your_username"' >> ~/.bashrc
echo 'export GERRIT_PASSWORD="your_password"' >> ~/.bashrc
source ~/.bashrc
```

#### 方式二：配置文件

创建 `config.json` 文件：
```json
{
  "gerrit": {
    "base_url": "https://scgit.amlogic.com",
    "username": "your_username",
    "password": "your_password"
  }
}
```

**配置文件查找顺序**：
1. `~/.gerrit/config.json`（全局配置）
2. `./config.json`（本地配置）

**混合使用**：环境变量会覆盖配置文件中的同名配置

### 2.3 基本用法
```bash
# 使用 Gerrit URL 添加评论
python3 gerrit_comment.py "https://scgit.amlogic.com/#/c/644513/" "test commit"

# 使用纯数字 change ID
python3 gerrit_comment.py "644513" "test commit"
```

## 3. 使用方式

### 3.1 命令行参数

```
usage: gerrit_comment.py [-h] url message

在 Gerrit Change 上添加评论

positional arguments:
  url                   Gerrit change URL 或 change ID
  message               评论内容

options:
  -h, --help            显示帮助信息
```

### 3.2 支持的 URL 格式

工具支持多种 Gerrit URL 格式：

| 格式 | 示例 |
|------|------|
| 标准格式 | `https://scgit.amlogic.com/#/c/644513/` |
| 简化格式 | `https://scgit.amlogic.com/c/644513` |
| 纯数字 | `644513` |

### 3.3 输出说明

工具运行后会产生以下输出：

```
提取到 Change ID: 644513
✅ 评论添加成功！
   Change: 644513
   消息: test commit
```

## 4. 完整示例

### 示例 1: 在单个 change 上添加评论

```bash
python3 gerrit_comment.py "https://scgit.amlogic.com/#/c/644513/" "test commit"
```

### 示例 2: 使用 Python API

```python
from gerrit_comment import GerritCommenter, load_config

# 加载配置（环境变量优先）
config = load_config()
gerrit_config = config['gerrit']

# 创建 commenter
commenter = GerritCommenter(
    base_url=gerrit_config['base_url'],
    username=gerrit_config['username'],
    password=gerrit_config['password']
)

# 添加评论
result = commenter.add_comment("https://scgit.amlogic.com/#/c/644513/", "test commit")
print(f"评论添加成功: {result}")
```

## 5. 故障排除

### 5.1 常见错误及解决方案

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| GERRIT_URL 环境变量未设置 | 未配置环境变量且缺少配置文件 | 设置环境变量或创建 config.json |
| GERRIT_USERNAME 环境变量未设置 | 同上 | 同上 |
| GERRIT_PASSWORD 环境变量未设置 | 同上 | 同上 |
| 配置文件不存在 | 未创建 config.json | 创建配置文件并填入认证信息 |
| 401 Unauthorized | 用户名或密码错误 | 检查环境变量或 config.json 中的凭据 |
| 404 Not Found | Change ID 不存在 | 确认 change ID 正确且可访问 |
| ImportError | 缺少依赖包 | 运行 `pip install pygerrit2 requests` |

### 5.2 配置问题排查

**检查环境变量是否设置**：
```bash
echo $GERRIT_URL
echo $GERRIT_USERNAME
echo $GERRIT_PASSWORD
```

**验证配置文件路径**：
```bash
# 检查全局配置
ls -la ~/.gerrit/config.json

# 检查本地配置
ls -la ./config.json
```

**测试配置是否正确**：
```bash
# 使用环境变量
GERRIT_URL="..." GERRIT_USERNAME="..." GERRIT_PASSWORD="..." python3 gerrit_comment.py "644513" "test"

# 使用配置文件
unset GERRIT_URL GERRIT_USERNAME GERRIT_PASSWORD
python3 gerrit_comment.py "644513" "test"
```

### 5.3 权限问题

如果遇到权限错误：
1. 确认账号有评论该 change 的权限
2. 检查密码是否正确（注意大小写）
3. 确认账号未被锁定或过期

## 6. AI 助手使用方法

### 6.1 工作流程

当用户需要在 Gerrit change 上添加评论时，AI 助手应该按照以下流程操作：

1. **解析用户请求**：
   - 提取 Gerrit URL 或 change ID
   - 提取评论内容

2. **执行评论添加**：
   ```bash
   cd /home/peng/.opencode/skill/gerrit_comment
   python3 gerrit_comment.py "GERRIT_URL" "评论内容"
   ```

3. **处理结果**：
   - 确认评论是否成功添加
   - 向用户反馈结果

### 6.2 典型使用场景

#### 场景 1：添加普通评论
用户请求："请在 https://scgit.amlogic.com/#/c/644513/ 上评论 'test commit'"

**AI 助手执行步骤**：
1. 运行 `python3 gerrit_comment.py "https://scgit.amlogic.com/#/c/644513/" "test commit"`
2. 向用户确认评论已添加

## 7. 文件清单

```
/home/peng/.opencode/skill/gerrit_comment/
├── SKILL.md              # 技能文档
├── config.json           # Gerrit 认证配置
└── gerrit_comment.py     # 评论功能实现
```

## 8. API 参考

### load_config() 函数

加载配置，优先级：**环境变量 > 配置文件**

**支持的环境变量**：
- `GERRIT_URL` / `GERRIT_BASE_URL`: Gerrit 服务器地址
- `GERRIT_USERNAME`: 用户名
- `GERRIT_PASSWORD`: 密码/Token

**配置文件路径**（按优先级查找）：
1. `~/.gerrit/config.json`（全局配置）
2. `./config.json`（本地配置）

**返回值**：
```python
{
    'gerrit': {
        'base_url': '...',
        'username': '...',
        'password': '...'
    }
}
```

**使用示例**：
```python
from gerrit_comment import load_config

config = load_config()
print(config['gerrit']['base_url'])
```

### GerritCommenter 类

#### 构造函数
```python
GerritCommenter(base_url: str, username: str, password: str)
```

#### 方法

**extract_change_id(url: str) -> str**
- 从 URL 中提取 change ID
- 支持多种 URL 格式

**add_comment(gerrit_url: str, message: str) -> bool**
- 在指定 change 上添加评论
- 返回：是否成功

---

Base directory for this skill: file:///home/peng/.opencode/skill/gerrit_comment

Relative paths in this skill (e.g., scripts/, reference/) are relative to this base directory.
