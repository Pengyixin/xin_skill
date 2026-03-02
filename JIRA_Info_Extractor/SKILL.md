---
name: jira-info-extractor
description: JIRA信息提取器是一个独立的Python工具，专门用于从JIRA系统中提取issue的详细信息，包括自定义字段RootCause(customfield_11708)和HowToFix(customfield_11709)。该工具支持文本和JSON格式输出，无任何文字截断。
---

# JIRA信息提取器使用说明手册

## 1. 概述

### 1.1 主要功能
- **JIRA信息提取**：自动从JIRA issue URL或issue key提取完整信息
- **自定义字段支持**：专门提取RootCause(customfield_11708)和HowToFix(customfield_11709)字段
- **完整信息输出**：所有文字不截断，保证后期分析准确性
- **Assignee评论分析**：提取并显示所有Assignee评论（不限于最新一条）
- **多格式输出**：支持文本摘要和完整JSON格式输出
- **配置文件管理**：通过配置文件管理JIRA认证信息

### 1.2 技术架构
- **语言**：Python 3（兼容Python 2语法）
- **核心模块**：
  - `JIRAClient`：JIRA API客户端
  - `extract_issue_info`：信息提取函数
  - `print_jira_info`：格式化输出函数
- **外部依赖**：
  - `requests`：HTTP请求库
  - `argparse`：命令行参数解析

### 1.3 系统要求
- Python 2.7+ 或 Python 3.6+
- 网络访问权限（可访问企业内部JIRA系统）
- 有效的JIRA认证凭据

## 2. 快速入门

### 2.1 安装依赖
```bash
pip install requests
```

### 2.2 配置文件设置
1. 创建或修改 `config.json` 文件：
```json
{
  "jira": {
    "username": "your_username",
    "password": "your_password"
  }
}
```

2. 配置说明：
   - `jira.username`：JIRA用户名
   - `jira.password`：JIRA密码

### 2.3 基本用法
```bash
# 使用issue key（Python 3）
py jira_info_extractor.py "SWPL-252994"

# 使用JIRA URL
py jira_info_extractor.py "https://jira.amlogic.com/browse/SWPL-252994"

# 指定配置文件
py jira_info_extractor.py "SWPL-252994" --config config.json

# JSON格式输出
py jira_info_extractor.py "SWPL-252994" --format json

# 保存到文件
py jira_info_extractor.py "SWPL-252994" --output result.txt
```

## 3. 使用方式

### 3.1 命令行参数

```
usage: jira_info_extractor.py [-h] [--config CONFIG] [--format {text,json}]
                              [--output OUTPUT]
                              jira_input

从JIRA号提取相关信息

positional arguments:
  jira_input            JIRA issue URL或issue key (如: SWPL-252395)

options:
  -h, --help            显示帮助信息
  --config CONFIG, -c CONFIG
                        配置文件路径 (默认: ./config.json 或环境变量 COMMIT_CONFIG_PATH)
  --format {text,json}, -f {text,json}
                        输出格式: text (文本摘要) 或 json (完整JSON数据)
  --output OUTPUT, -o OUTPUT
                        输出文件路径 (如不指定则输出到控制台)
```

### 3.2 环境变量
- `COMMIT_CONFIG_PATH`：指定默认配置文件路径

### 3.3 输出说明

#### 3.3.1 文本格式输出
工具运行后会产生以下输出：

```
================================================================================
JIRA信息摘要:
================================================================================
Key:           SWPL-252994
摘要:           [T6X][Android 16][GTV] local video 4K H264 play failed by Amplayer...
状态:           Closed
优先级:         P0
类型:           Bug
创建时间:       2026-01-20T20:13:47.589+0800
更新时间:       2026-02-04T09:47:46.630+0800
Assignee:      Xiaohang Cui (Xiaohang.Cui@amlogic.com)
Reporter:      Chao Wu (Chao.Wu@amlogic.com)
标签:           AE_REF_highlight_260126, DECODER-CORE-20260126, ...
组件:           Video-Decoder
修复版本:       16.3.2601
评论总数:       8
Assignee评论数: 2

Root Cause (37 字符):
Spec?GXLX4/T6W/T6X??H.264 4K P60?L5.1

How to Fix (27 字符):
??GXLX4/T6W/T6X??H.264?L5.2

Assignee所有评论 (2 条):

评论 #1 (2026-01-29T13:41:33.189+0800):
[完整的Assignee评论内容，无截断]
----------------------------------------

评论 #2 (2026-01-30T12:07:54.873+0800):
[完整的Assignee评论内容，无截断]
----------------------------------------
================================================================================
```

**关键特性**：
- 所有文字完整显示，无任何截断
- 显示所有Assignee评论，不只最新一条
- 包含自定义字段RootCause和HowToFix
- 完整的issue基本信息

#### 3.3.2 JSON格式输出
JSON格式包含完整数据结构：

```json
{
  "key": "SWPL-252994",
  "summary": "[T6X][Android 16][GTV] local video 4K H264 play failed by Amplayer...",
  "description": "完整的描述内容...",
  "issue_type": "Bug",
  "priority": "P0",
  "status": "Closed",
  "assignee": {
    "displayName": "Xiaohang Cui",
    "emailAddress": "Xiaohang.Cui@amlogic.com",
    "active": true,
    "timeZone": "Asia/Shanghai"
  },
  "reporter": {
    "displayName": "Chao Wu",
    "emailAddress": "Chao.Wu@amlogic.com"
  },
  "created": "2026-01-20T20:13:47.589+0800",
  "updated": "2026-02-04T09:47:46.630+0800",
  "labels": ["AE_REF_highlight_260126", "DECODER-CORE-20260126", ...],
  "components": ["Video-Decoder"],
  "fix_versions": ["16.3.2601"],
  "root_cause": "Spec?GXLX4/T6W/T6X??H.264 4K P60?L5.1",
  "how_to_fix": "??GXLX4/T6W/T6X??H.264?L5.2",
  "root_cause_customfield": "Spec?GXLX4/T6W/T6X??H.264 4K P60?L5.1",
  "how_to_fix_customfield": "??GXLX4/T6W/T6X??H.264?L5.2",
  "assignee_comments": [
    {
      "created": "2026-01-29T13:41:33.189+0800",
      "body": "完整的评论内容...",
      "author": "Xiaohang Cui"
    },
    {
      "created": "2026-01-30T12:07:54.873+0800",
      "body": "完整的评论内容...",
      "author": "Xiaohang Cui"
    }
  ],
  "all_comments_count": 8,
  "assignee_comments_count": 2,
  "comments_count": 8
}
```

### 3.4 提取的字段说明

| 字段名 | 描述 | 来源 |
|--------|------|------|
| key | JIRA issue key | issue.key |
| summary | 问题摘要 | fields.summary |
| description | 详细描述 | fields.description |
| issue_type | 问题类型 | fields.issuetype.name |
| priority | 优先级 | fields.priority.name |
| status | 状态 | fields.status.name |
| assignee | 负责人信息 | fields.assignee |
| reporter | 报告人信息 | fields.reporter |
| created | 创建时间 | fields.created |
| updated | 更新时间 | fields.updated |
| labels | 标签列表 | fields.labels |
| components | 组件列表 | fields.components |
| fix_versions | 修复版本 | fields.fixVersions |
| root_cause | 根本原因 | customfield_11708 或从description提取 |
| how_to_fix | 解决方案 | customfield_11709 或从description提取 |
| assignee_comments | Assignee的所有评论 | 从comments中过滤 |
| all_comments_count | 总评论数 | comments.length |
| assignee_comments_count | Assignee评论数 | 过滤后的评论数 |

### 3.5 错误处理

#### 常见错误及解决方案：

1. **配置文件不存在**
   ```
   错误: 配置文件不存在: ./config.json
   ```
   **解决方案**：创建配置文件或使用 `--config` 参数指定

2. **JIRA认证失败**
   ```
   错误: 获取JIRA issue失败: 401 Client Error
   ```
   **解决方案**：检查 `config.json` 中的JIRA用户名和密码

3. **Python版本问题**
   ```
     File "jira_info_extractor.py", line 20
       def __init__(self, config: Dict[str, str]):
                                ^
   SyntaxError: invalid syntax
   ```
   **解决方案**：使用`py`命令（Python 3）而不是`python`命令

4. **网络连接问题**
   ```
   错误: 获取JIRA issue失败: Connection refused
   ```
   **解决方案**：检查网络连接，确保可以访问JIRA系统

### 3.6 高级功能

#### 3.6.1 自定义字段优先
- 优先使用JIRA自定义字段`customfield_11708`（RootCause）
- 优先使用JIRA自定义字段`customfield_11709`（HowToFix）
- 如果自定义字段为空，则从description中提取对应部分

#### 3.6.2 完整信息保证
- 所有文本内容完整输出，无任何截断
- 特别保证Assignee评论的完整性
- RootCause和HowToFix字段完整显示

#### 3.6.3 编码处理
- 自动处理中文字符编码问题
- 使用`safe_print`函数确保在各种终端正常显示

#### 3.6.4 单元测试
包含完整的单元测试文件`test_jira_extractor.py`：
- 测试issue key提取
- 测试RootCause和HowToFix提取
- 测试Assignee评论过滤

### 3.7 最佳实践

1. **配置管理**
   - 将配置文件放在安全位置
   - 使用环境变量管理敏感信息
   - 定期更新认证信息

2. **Python版本**
   - 推荐使用`py`命令（Python 3）
   - 如果使用`python`命令遇到语法错误，请切换到Python 3

3. **输出格式选择**
   - 文本格式：快速查看摘要信息
   - JSON格式：程序化处理或完整数据导出

4. **集成使用**
   ```bash
   # 与其他工具结合使用
   python jira_info_extractor.py "SWPL-252994" --format json | jq '.root_cause'
   
   # 保存到文件后处理
   python jira_info_extractor.py "SWPL-252994" --output jira_data.json
   ```


## 4. 故障排除

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 无法解析JIRA URL | URL格式不正确 | 使用完整的JIRA issue URL或直接使用issue key |
| 输出乱码 | 终端编码问题 | 脚本已包含编码处理，确保终端支持UTF-8 |
| 运行速度慢 | 网络延迟或JIRA响应慢 | 检查网络连接，考虑本地缓存 |
| 认证频繁失败 | 密码过期或权限变更 | 更新配置文件中的认证信息 |
| 部分字段缺失 | JIRA字段名变更 | 检查JIRA系统的自定义字段名 |

## 5. AI 助手使用方法

### 5.1 工作流程
当用户要求生成 commit message 或需要 JIRA 信息时，AI 助手应该按照以下流程操作：

1. **自动提取 JIRA 信息**：
   ```bash
   cd /home/peng/.opencode/skill/JIRA_Info_Extractor
   python3 jira_info_extractor.py "TV-XXXXXX"
   ```

2. **解析提取的信息**：
   - 从输出中提取：key, summary, priority, components, root_cause, how_to_fix, assignee_comments
   - 根据组件确定合适的模块名（tsplayer, videodec, mediasync 等）
   - 根据优先级确定 CB/CF 分类级别

3. **生成 commit message**（配合 commit-message-rule 技能）：
   - 使用提取的信息填写 commit message 模板
   - 根据 components 和 issue 内容确定测试场景
   - 从 summary 或 tags 中提取验证平台信息

### 5.2 典型使用场景

#### 场景 1：生成 commit message
用户请求："请帮我将jira TV-174693生成一份commit message信息"

**AI 助手执行步骤**：
1. 运行 `python3 jira_info_extractor.py "TV-174693"`
2. 解析输出，获取必要字段
3. 加载 `commit-message-rule` 技能
4. 根据规则生成标准 commit message

#### 场景 2：JIRA 信息查询
用户请求："查询 TV-174693 的详细信息"

**AI 助手执行步骤**：
1. 运行 `python3 jira_info_extractor.py "TV-174693" --format json`
2. 解析 JSON 输出
3. 以结构化方式展示关键信息

### 5.3 信息映射规则

| JIRA 字段 | Commit Message 字段 | 映射规则 |
|-----------|-------------------|----------|
| components | 模块名 | DVB→mediasync, Video-Decoder→videodec, 其他根据内容判断 |
| priority | CB/CF 级别 | P0→CB0, P1→CB1, P2→CB2, 功能相关→CF |
| summary | 问题描述 | 直接使用或简化描述 |
| root_cause | Root Cause | 直接使用 |
| how_to_fix | Solution | 直接使用 |
| assignee_comments | 补充信息 | 提取关键修复细节 |
| tags/labels | 验证平台 | 从标签中提取平台信息 |

### 5.4 错误处理
如果脚本执行失败：
1. 检查配置文件是否存在且格式正确
2. 验证 JIRA 网络连接
3. 确认 JIRA ID 格式正确
4. 如仍失败，提示用户提供必要信息

## 6. 支持与反馈

如遇问题或需要功能改进，请：
1. 检查日志输出中的错误信息
2. 验证配置文件的正确性
3. 确保网络连接和系统权限
4. 使用`--format json`查看完整数据结构
5. 联系工具维护者获取支持

---

