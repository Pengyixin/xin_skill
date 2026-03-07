---
name: gerrit-cherry-pick
description: Gerrit Cherry-Pick 工具是一个使用 Gerrit API 进行 cherry-pick 操作并生成 HTML 报告的 Python 工具。支持多种输入格式（Gerrit URL、Change Number、Change-Id、Commit Hash），完全通过 API 操作不依赖本地 git，批量处理变更并生成可视化报告，适用于代码迁移、分支同步和发布管理等场景。
---

# Gerrit Cherry-Pick 工具使用说明

## 1. 概述

### 1.1 主要功能
- **完全API驱动**: 不依赖本地git仓库，完全通过Gerrit REST API执行cherry-pick
- **多种标识符支持**: 支持Gerrit URL、Change Number、Change-Id、Commit Hash
- **批量处理**: 支持同时cherry-pick多个变更，自动解析和批量执行
- **保留Change-Id**: cherry-pick后保留原始的Change-Id便于追踪
- **可视化报告**: 生成美观的HTML报告，包含源提交信息和cherry-pick结果
- **智能错误处理**: 失败时也会生成报告，显示详细的错误原因

### 1.2 技术架构
- **语言**: Python 3（纯标准库，无外部依赖）
- **核心模块**:
  - `parse_change_identifier`: 多种格式标识符解析
  - `search_by_change_id`: 通过Change-Id搜索变更
  - `search_by_commit`: 通过commit hash搜索变更
  - `cherry_pick_change`: 执行cherry-pick操作
  - `generate_html_report_batch`: 生成HTML报告
- **认证方式**: 支持Digest和Basic认证

### 1.3 系统要求
- Python 3.6+
- 网络访问权限（可访问Gerrit服务器）
- 有效的Gerrit认证凭据（HTTP密码）
- 目标分支的推送权限

## 2. 快速入门

### 2.1 配置方式

工具支持多种配置方式，优先级：**环境变量 > 配置文件**

#### 方式一：环境变量（推荐）

设置以下环境变量：
```bash
export GERRIT_URL="https://scgit.amlogic.com"
export GERRIT_USERNAME="your_username"
export GERRIT_PASSWORD="your_http_password"
```

**优点**：
- 无需管理配置文件
- 支持临时切换账号：`GERRIT_USERNAME="other" python3 gerrit_cherry_pick.py ...`
- 敏感信息不会留在代码仓库中

**持久化配置**（添加到 ~/.bashrc 或 ~/.zshrc）：
```bash
echo 'export GERRIT_URL="https://scgit.amlogic.com"' >> ~/.bashrc
echo 'export GERRIT_USERNAME="your_username"' >> ~/.bashrc
echo 'export GERRIT_PASSWORD="your_http_password"' >> ~/.bashrc
source ~/.bashrc
```

#### 方式二：配置文件

创建 `config.json` 文件：
```json
{
  "gerrit": {
    "base_url": "https://scgit.amlogic.com",
    "username": "your_username",
    "password": "your_http_password"
  }
}
```

**配置文件查找顺序**：
1. 命令行参数指定的路径
2. `~/.gerrit/config.json`（全局配置）
3. `./config.json`（本地配置）

**混合使用**：环境变量会覆盖配置文件中的同名配置

**注意**: password应该是HTTP密码（在Gerrit设置中生成），不是你的登录密码。

### 2.2 基本用法

```bash
# 使用Gerrit URL进行cherry-pick
python3 gerrit_cherry_pick.py "https://scgit.amlogic.com/#/c/610496/" "amlogic-5.15-dev"

# 使用Change Number
python3 gerrit_cherry_pick.py "610496" "amlogic-5.15-dev"

# 使用Change-Id
python3 gerrit_cherry_pick.py "I4ea5aed44ace170e7ee83fcacbbca0ba4ffbb5d6" "amlogic-5.15-dev"

# 使用Commit Hash（完整或简写）
python3 gerrit_cherry_pick.py "3eb601ad7" "amlogic-5.15-dev"
```

## 3. 使用方式

### 3.1 命令行参数

```
usage: gerrit_cherry_pick.py <identifiers> <target_branch> [config_file]

参数:
  identifiers     变更标识符，支持多种格式（空格或逗号分隔）
  target_branch   目标分支名称
  config_file     配置文件路径（可选，默认使用环境变量或标准配置文件）
```

### 3.2 支持的标识符格式

工具支持多种变更标识符格式：

| 格式 | 示例 | 说明 |
|------|------|------|
| Gerrit URL | `https://scgit.amlogic.com/#/c/610496/` | 完整的Gerrit变更页面URL |
| Change Number | `610496` | 纯数字格式 |
| Change-Id | `I4ea5aed44ace170e7ee83fcacbbca0ba4ffbb5d6` | commit message中的Change-Id |
| Commit Hash | `3eb601ad7` 或完整40位 | Git commit hash，支持简写 |

### 3.3 批量处理

支持同时处理多个变更，用逗号或空格分隔：

```bash
# 混合使用不同格式
python3 gerrit_cherry_pick.py "610496, I4ea5aed44ace170e7ee83fcacbbca0ba4ffbb5d6, 3eb601ad7" "amlogic-5.15-dev"
```

### 3.4 输出说明

工具运行后会产生以下输出：

```
============================================================
Gerrit Cherry-Pick 工具
============================================================
目标分支: amlogic-5.15-dev
待处理变更数: 1

加载配置...
  URL: https://scgit.amlogic.com
  用户名: yixin.peng

============================================================
处理变更 1/1: 3eb601ad7
============================================================
  识别类型: commit
  标识符: 3eb601ad7
  通过Commit hash搜索...
Change Number: 610496

获取变更详情...
主题: 264 lookup first framea
当前分支: amlogic-main-dev
项目: platform/hardware/amlogic/media_modules
Change-Id: I4ea5aed44ace170e7ee83fcacbbca0ba4ffbb5d6

执行cherry-pick到分支: amlogic-5.15-dev
✓ Cherry-pick 成功!
  新Change ID: platform%2Fhardware%2Famlogic%2Fmedia_modules~amlogic-5.15-dev~I4ea5aed44ace170e7ee83fcacbbca0ba4ffbb5d6

============================================================
生成汇总HTML报告...
✓ 报告已保存: cherry_pick_report_20250307_192355.html

============================================================
处理完成!
  成功: 1
  失败: 0
============================================================
```

### 3.5 HTML报告内容

生成的HTML报告包含：
- **执行摘要**: 成功/失败统计
- **快速汇总表**: 所有变更的简要信息表格
- **详细结果**: 每个变更的完整信息
  - 源URL/ID
  - Change Number
  - Commit Message
  - 原分支和目标分支
  - 项目信息
  - Cherry-pick状态
  - 新Change ID和Gerrit链接
  - 错误信息（如果失败）

## 4. 完整示例

### 示例 1: 使用不同格式的标识符

```bash
# 使用Gerrit URL
python3 gerrit_cherry_pick.py "https://scgit.amlogic.com/#/c/610496/" "amlogic-5.15-dev"

# 使用Change Number
python3 gerrit_cherry_pick.py "610496" "amlogic-5.15-dev"

# 使用Change-Id
python3 gerrit_cherry_pick.py "I4ea5aed44ace170e7ee83fcacbbca0ba4ffbb5d6" "amlogic-5.15-dev"

# 使用Commit Hash
python3 gerrit_cherry_pick.py "3eb601ad7b1c8865678ae214c13718f7da3e585e" "amlogic-5.15-dev"
```

### 示例 2: 批量cherry-pick多个变更

```bash
# 批量处理多个变更
python3 gerrit_cherry_pick.py "610496, 610497, I4ea5aed44ace170e7ee83fcacbbca0ba4ffbb5d6" "amlogic-5.15-dev"
```

### 示例 3: 临时覆盖用户名

```bash
# 使用配置文件中的URL和密码，但覆盖用户名
GERRIT_USERNAME="admin" python3 gerrit_cherry_pick.py "610496" "amlogic-5.15-dev"
```

### 示例 4: 指定自定义配置文件

```bash
# 使用指定的配置文件
python3 gerrit_cherry_pick.py "610496" "amlogic-5.15-dev" "/path/to/custom-config.json"
```

## 5. 故障排除

### 5.1 常见错误及解决方案

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| GERRIT_URL环境变量未设置 | 未配置环境变量且缺少配置文件 | 设置环境变量或创建config.json |
| GERRIT_USERNAME环境变量未设置 | 同上 | 同上 |
| GERRIT_PASSWORD环境变量未设置 | 同上 | 同上 |
| 401 Unauthorized | 用户名或密码错误 | 检查凭据，确认使用HTTP密码而非登录密码 |
| 404 Not Found | Change ID不存在 | 确认标识符正确且可访问 |
| Cherry-pick冲突 | 代码冲突无法自动合并 | 手动解决冲突或使用其他方式合并 |
| 目标分支不存在 | 分支名称错误或分支未创建 | 确认分支名称正确 |
| 权限不足 | 没有目标分支的推送权限 | 联系管理员获取权限 |

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
GERRIT_URL="..." GERRIT_USERNAME="..." GERRIT_PASSWORD="..." python3 gerrit_cherry_pick.py "610496" "main"

# 使用配置文件
unset GERRIT_URL GERRIT_USERNAME GERRIT_PASSWORD
python3 gerrit_cherry_pick.py "610496" "main"
```

### 5.3 网络问题

如果遇到网络连接问题：
1. 检查是否能正常访问Gerrit服务器
2. 确认网络代理配置正确
3. 验证防火墙设置

### 5.4 权限问题

如果遇到权限错误：
1. 确认账号有访问该change的权限
2. 检查密码是否正确（注意大小写）
3. 确认使用的是HTTP密码而非登录密码
4. 确认账号未被锁定或过期

## 6. AI助手使用方法

### 6.1 工作流程

当用户需要使用cherry-pick功能时，AI助手应该按照以下流程操作：

1. **解析用户请求**：
   - 提取变更标识符（URL/Change-Id/Commit Hash）
   - 确认目标分支
   - 确认配置方式

2. **执行cherry-pick**：
   ```bash
   cd /home/peng/.opencode/skill/gerrit_cherry_pick
   python3 gerrit_cherry_pick.py "<identifier>" "<target_branch>"
   ```

3. **处理结果**：
   - 显示执行摘要
   - 如果成功，提供新change的链接
   - 如果失败，分析错误原因并提供建议
   - 打开HTML报告供用户查看

### 6.2 典型使用场景

#### 场景 1：单个变更cherry-pick
用户请求："请把 change 610496 cherry-pick 到 amlogic-5.15-dev 分支"

**AI助手执行步骤**：
1. 运行 `python3 gerrit_cherry_pick.py "610496" "amlogic-5.15-dev"`
2. 检查执行结果
3. 向用户报告成功/失败状态和详细信息

#### 场景 2：批量cherry-pick
用户请求："把这几个change都cherry-pick到dev分支：610496, 610497, 610498"

**AI助手执行步骤**：
1. 批量执行cherry-pick
2. 生成汇总报告
3. 向用户展示所有变更的处理结果

#### 场景 3：使用不同标识符格式
用户请求："帮我cherry-pick这个commit 3eb601ad7到5.15分支"

**AI助手执行步骤**：
1. 识别标识符类型为commit hash
2. 通过API搜索对应的change
3. 执行cherry-pick操作
4. 报告结果

### 6.3 与其他技能配合使用

#### 与 gerrit-diff-fetcher 配合使用
```bash
# 1. 获取原change的diff信息
cd /home/peng/.opencode/skill/gerrit_diff
python3 get_diff.py "610496"

# 2. 执行cherry-pick
cd /home/peng/.opencode/skill/gerrit_cherry_pick
python3 gerrit_cherry_pick.py "610496" "amlogic-5.15-dev"

# 3. 获取新change的diff进行对比
cd /home/peng/.opencode/skill/gerrit_diff
python3 get_diff.py "<new-change-number>"
```

#### 与 JIRA信息提取器配合使用
```bash
# 1. 获取JIRA信息
cd /home/peng/.opencode/skill/JIRA_Info_Extractor
python3 jira_info_extractor.py "SWPL-254798"

# 2. 执行关联的change的cherry-pick
cd /home/peng/.opencode/skill/gerrit_cherry_pick
python3 gerrit_cherry_pick.py "I4ea5aed44ace170e7ee83fcacbbca0ba4ffbb5d6" "amlogic-5.15-dev"
```

## 7. 文件清单

```
/home/peng/.opencode/skill/gerrit_cherry_pick/
├── SKILL.md              # 技能文档
├── README.md             # 快速参考文档
├── config.json           # Gerrit认证配置（示例）
├── gerrit_cherry_pick.py # 主脚本
└── cherry_pick_report_*.html # 生成的HTML报告
```

## 8. API参考

### load_config(config_path) 函数

加载配置，优先级：**环境变量 > 配置文件**

**支持的环境变量**：
- `GERRIT_URL` / `GERRIT_BASE_URL`: Gerrit服务器地址
- `GERRIT_USERNAME`: 用户名
- `GERRIT_PASSWORD`: HTTP密码

**配置文件路径**（按优先级查找）：
1. 传入的config_path参数
2. `~/.gerrit/config.json`（全局配置）
3. `./config.json`（本地配置）

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

### parse_change_identifier(identifier) 函数

解析变更标识符，支持多种格式。

**参数**：
- `identifier`: 变更标识符字符串

**返回值**：`(类型, 值)` 元组

**支持的类型**：
- `change_number`: Change Number（纯数字）
- `change_id`: Change-Id（以I开头的40位十六进制）
- `commit`: Commit hash（7-40位十六进制）
- `unknown`: 无法识别的格式

### cherry_pick_change(base_url, change_id, target_branch, username, password) 函数

使用Gerrit API执行cherry-pick操作。

**参数**：
- `base_url`: Gerrit服务器基础URL
- `change_id`: Change Number或完整change ID
- `target_branch`: 目标分支名称
- `username`: Gerrit用户名
- `password`: Gerrit HTTP密码

**返回值**：`(成功标志, 结果字典/错误信息)`

### generate_html_report_batch(base_url, target_branch, results, success_count, failed_count, output_file) 函数

生成批量cherry-pick的HTML报告。

**参数**：
- `base_url`: Gerrit服务器URL
- `target_branch`: 目标分支
- `results`: 处理结果列表
- `success_count`: 成功数量
- `failed_count`: 失败数量
- `output_file`: 输出文件路径（可选）

**返回值**：生成的HTML文件路径

## 9. 注意事项

1. **Change-Id保留**: cherry-pick操作会创建一个新的Gerrit change（新的Change Number），但会保留原始commit message中的Change-Id。

2. **权限要求**: 执行cherry-pick需要有目标分支的推送权限。

3. **冲突处理**: 如果cherry-pick有冲突，操作会失败并在报告中显示错误信息，需要手动解决。

4. **分支存在性**: 目标分支必须已经存在，否则会报错。

5. **Commit Hash**: 使用简写的commit hash时，需要确保hash足够唯一以准确识别变更。

6. **HTTP密码**: 必须使用Gerrit中生成的HTTP密码，不是登录密码。

## 10. 更新日志

### v1.0.0
- 初始版本发布
- 支持通过Gerrit API执行cherry-pick
- 支持多种输入格式（URL/Change-Id/Commit Hash）
- 支持批量处理
- 生成可视化HTML报告
- 纯Python标准库实现，无外部依赖

---

Base directory for this skill: file:///home/peng/.opencode/skill/gerrit_cherry_pick
