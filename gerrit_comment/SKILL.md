# Skill: gerrit-comment

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

### 2.2 配置文件设置
创建或修改 `config.json` 文件：
```json
{
  "gerrit": {
    "base_url": "https://scgit.amlogic.com",
    "username": "your_username",
    "password": "your_password"
  }
}
```

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
from gerrit_comment import GerritCommenter
import json

# 加载配置
with open('config.json', 'r') as f:
    config = json.load(f)['gerrit']

# 创建 commenter
commenter = GerritCommenter(
    base_url=config['base_url'],
    username=config['username'],
    password=config['password']
)

# 添加评论
result = commenter.add_comment("https://scgit.amlogic.com/#/c/644513/", "test commit")
print(f"评论添加成功: {result}")
```

## 5. 故障排除

### 5.1 常见错误及解决方案

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 配置文件不存在 | 未创建 config.json | 创建配置文件并填入认证信息 |
| 401 Unauthorized | 用户名或密码错误 | 检查 config.json 中的凭据 |
| 404 Not Found | Change ID 不存在 | 确认 change ID 正确且可访问 |
| ImportError | 缺少依赖包 | 运行 `pip install pygerrit2 requests` |

### 5.2 权限问题

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
