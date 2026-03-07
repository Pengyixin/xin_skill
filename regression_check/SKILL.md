---
name: regression-detector
description: 回归检测系统是一个自动化工具，用于检测 JIRA issue 是否已回归公版。系统通过三步检测逻辑（检查是否需要回归、检查关联 Gerrit 是否已合并、检查 Clone JIRA 的回归状态）判断 issue 的回归状态，支持多种搜索模式（单个 JIRA、文件列表、Label 搜索、JQL 查询），并可生成 JSON/CSV/HTML 格式的检测报告。使用环境变量 GERRIT_USERNAME/GERRIT_PASSWORD 和 JIRA_USERNAME/JIRA_PASSWORD 配置认证信息。
---

# 回归检测系统使用说明手册

## 1. 概述

### 1.1 主要功能
- **三步回归检测**：检查是否需要回归 → 检查 Gerrit 合并状态 → 检查 Clone JIRA 状态
- **多种搜索模式**：支持单个 JIRA、文件列表、Label 搜索、JQL 查询、默认搜索
- **多格式报告**：生成 JSON、CSV、HTML 格式的检测报告
- **邮件通知**：支持自动发送检测报告邮件
- **环境变量配置**：通过环境变量管理 JIRA 和 Gerrit 认证信息

### 1.2 技术架构
- **语言**：Python 3
- **核心模块**：
  - `RegressionEngine`：回归检测引擎，实现核心检测逻辑
  - `JIRAClient`：JIRA API 客户端
  - `GerritClient`：Gerrit API 客户端
  - `ReportGenerator`：报告生成器
  - `ConfigManager`：配置管理器
- **外部依赖**：
  - `requests`：HTTP 请求库
  - `pygerrit2`：Gerrit REST API 客户端

### 1.3 系统要求
- Python 3.6+
- 网络访问权限（可访问 JIRA 和 Gerrit 服务器）
- 有效的 JIRA 和 Gerrit 认证凭据（通过环境变量配置）

## 2. 快速入门

### 2.1 安装依赖
```bash
pip install requests pygerrit2
```

### 2.2 配置认证信息

通过环境变量配置认证信息：

```bash
# Gerrit 认证
export GERRIT_URL="https://scgit.amlogic.com"
export GERRIT_USERNAME="your_username"
export GERRIT_PASSWORD="your_password"

# JIRA 认证
export JIRA_USERNAME="your_username"
export JIRA_PASSWORD="your_password"
```

**说明**：
- 环境变量优先级高于 config.json 配置文件
- 若环境变量未设置，会回退到配置文件中的值

### 2.3 基本用法

```bash
# 检测单个 JIRA
python regression_detector.py --jira SWPL-252395

# 搜索最近 30 天 verify/close 的 issues
python regression_detector.py --project SWPL --days 30

# 按 label 搜索并检测
python regression_detector.py --label DECODER-CORE-20260126 --days 30

# 使用 JQL 查询
python regression_detector.py --jql "project = SWPL AND status = Verified"
```

### 2.4 帮助信息
```bash
python regression_detector.py --help
```

## 3. 使用方式

### 3.1 命令行参数

```
usage: regression_detector.py [-h] [--project PROJECT] [--days DAYS]
                              [--jira JIRA_KEY | --file FILE_PATH | --label LABEL [LABEL ...] | --jql JQL]
                              [--max-results MAX_RESULTS]
                              [--output {json,csv,html,all}] [--verbose]
                              [--email EMAIL] [--email-only]

回归检测系统 - 查找未回归公版的提交

options:
  -h, --help            显示帮助信息
  --project PROJECT     指定 JIRA 项目（如 SWPL）
  --days DAYS           搜索最近多少天的 issues，默认 30 天
  --jira JIRA_KEY       检测单个 JIRA issue
  --file FILE_PATH      从文件读取 JIRA 列表进行检测
  --label LABEL [LABEL ...]
                        按 label 搜索 JIRA
  --jql JQL             直接使用 JQL 查询
  --max-results MAX_RESULTS
                        最大搜索结果数，默认 1000
  --output {json,csv,html,all}
                        输出格式，默认 all
  --verbose             显示详细输出信息
  --email EMAIL         发送邮件通知，多个收件人用逗号分隔
  --email-only          仅发送邮件，不生成报告文件
```

### 3.2 环境变量
- `GERRIT_URL`：Gerrit 服务器地址
- `GERRIT_USERNAME`：Gerrit 用户名
- `GERRIT_PASSWORD`：Gerrit 密码
- `JIRA_USERNAME`：JIRA 用户名
- `JIRA_PASSWORD`：JIRA 密码

### 3.3 回归检测逻辑

#### 第一步：检查是否需要回归
- 检查 JIRA 的 `customfield_11705` 字段
- 如果值为 "Confirmed Yes"，则需要回归
- 如果 Resolution 为 "Won't Fix"，直接标记为不需要回归

#### 第二步：检查关联 Gerrit
- 从 JIRA description 和 comments 中提取 Gerrit URL
- 检查关联的 Gerrit change 是否已合并（MERGED 状态）
- 如果已合并，标记为已回归

#### 第三步：检查 Clone JIRA
- 检查是否有 clone 的 JIRA issue
- 如果存在 clone 的 JIRA 且已关闭
- 检查 clone JIRA 中的 Gerrit 提交是否已合并
- 如果仍然没有合并的 Gerrit，标记为未回归

### 3.4 输出报告

系统会生成以下报告文件（位于 `reports/` 目录）：

| 文件名 | 格式 | 内容 |
|--------|------|------|
| `{timestamp}_report.json` | JSON | 完整检测报告 |
| `{timestamp}_report.csv` | CSV | 完整检测报告（Excel 可用） |
| `{timestamp}_report.html` | HTML | 可视化完整报告 |
| `{timestamp}_not_regressed_report.json` | JSON | 仅未回归 issues |
| `{timestamp}_not_regressed_report.csv` | CSV | 仅未回归 issues |
| `{timestamp}_not_regressed_report.html` | HTML | 仅未回归 issues |

### 3.5 回归状态说明

| 状态 | 说明 |
|------|------|
| 需要回归 | `customfield_11705` = "Confirmed Yes"，需要回归公版 |
| 已回归 | 需要回归且关联的 Gerrit 已合并 |
| 未回归 | 需要回归但无 Gerrit 或 Gerrit 未合并 |
| 不需要回归 | `customfield_11705` != "Confirmed Yes" 或 Resolution = "Won't Fix" |

### 3.6 操作模式

五种互斥的操作模式：

#### 模式 1：单个 JIRA 检测
```bash
python regression_detector.py --jira SWPL-252395
```

#### 模式 2：文件列表检测
```bash
# jira_list.txt 每行一个 JIRA key
python regression_detector.py --file jira_list.txt
```

#### 模式 3：Label 搜索
```bash
# 单个 label
python regression_detector.py --label DECODER-CORE-20260126 --days 30

# 多个 label
python regression_detector.py --label DECODER-CORE-20260126 VDEC-VA20260209 --project SWPL
```

#### 模式 4：JQL 查询
```bash
python regression_detector.py --jql "(labels = DECODER-CORE-20260209 OR labels = VDEC-VA20260209) AND assignee = Yinan.Zhang"
```

#### 模式 5：默认搜索（verify/close 状态）
```bash
# 搜索所有项目
python regression_detector.py --days 30

# 搜索指定项目
python regression_detector.py --project SWPL --days 30
```

## 4. 完整示例

### 示例 1: 检测单个 JIRA

```bash
python regression_detector.py --jira SWPL-252395 --output html
```

输出：生成 HTML 报告，显示该 JIRA 的回归状态

### 示例 2: 搜索最近 7 天的 issues

```bash
python regression_detector.py --project SWPL --days 7 --verbose
```

输出：控制台显示详细检测过程，生成所有格式报告

### 示例 3: 按 label 搜索并发送邮件

```bash
python regression_detector.py --label DECODER-CORE-20260126 --project SWPL --email user@amlogic.com
```

输出：生成报告并发送邮件通知

### 示例 4: 使用 JQL 复杂查询

```bash
python regression_detector.py --jql "project = SWPL AND status in (Verified, Closed) AND updated >= -7d AND labels = DECODER-CORE-20260209"
```

### 示例 5: 仅生成未回归报告

```bash
python regression_detector.py --project SWPL --days 30 --output html
```

系统会自动生成两份报告：
- 完整报告：包含所有检测的 issues
- 未回归专项报告：仅包含状态为"未回归"的 issues

### 示例 6: 从文件批量检测

```bash
# 创建 jira_list.txt，每行一个 JIRA key
echo "SWPL-252395" > jira_list.txt
echo "SWPL-252396" >> jira_list.txt
echo "SWPL-252397" >> jira_list.txt

# 批量检测
python regression_detector.py --file jira_list.txt --output all
```

## 5. 配置文件说明

配置文件 `config.json` 结构：

```json
{
  "jira": {
    "username": "用户名",
    "password": "密码"
  },
  "gerrit": {
    "base_url": "https://scgit.amlogic.com",
    "username": "用户名",
    "password": "密码"
  },
  "regression_branches": [
    {
      "project": "platform/hardware/amlogic/media_modules",
      "branch": "amlogic-main-dev",
      "description": "Media Modules 主开发分支"
    }
  ],
  "email": {
    "smtp_host": "smtp.amlogic.com",
    "smtp_port": 25,
    "username": "",
    "password": "",
    "from": "regression-detector@amlogic.com",
    "to": ["user@amlogic.com"]
  }
}
```

**注意**：环境变量优先级高于配置文件。

## 6. 故障排除

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 认证失败 | 环境变量未设置或错误 | 检查 `JIRA_USERNAME`、`JIRA_PASSWORD`、`GERRIT_USERNAME`、`GERRIT_PASSWORD` |
| 无法连接 JIRA | 网络问题 | 检查网络连接，确认可访问 JIRA 服务器 |
| 无法连接 Gerrit | 网络问题 | 检查网络连接，确认可访问 Gerrit 服务器 |
| 未找到 issues | 查询条件过于严格 | 调整 `--days` 或检查 `--project` 是否正确 |
| 邮件发送失败 | SMTP 配置错误 | 检查 config.json 中的 email 配置 |
| 报告生成失败 | 目录权限问题 | 检查 `reports/` 目录是否有写权限 |

## 7. AI 助手使用方法

### 7.1 工作流程

当用户需要进行回归检测时，AI 助手应该按照以下流程操作：

1. **解析用户请求**：
   - 确认检测模式（单个 JIRA、Label 搜索、JQL 查询等）
   - 确认时间范围和项目
   - 确认输出格式需求

2. **执行回归检测**：
   ```bash
   cd /home/peng/.opencode/skill/regression_check
   python regression_detector.py [参数]
   ```

3. **处理结果**：
   - 读取生成的报告文件
   - 向用户展示检测摘要
   - 重点提示未回归的 issues

### 7.2 典型使用场景

#### 场景 1：检测单个 JIRA 的回归状态
用户请求："请检查 SWPL-252395 是否已回归"

**AI 助手执行步骤**：
1. 运行 `python regression_detector.py --jira SWPL-252395 --output html`
2. 读取生成的 HTML 报告
3. 向用户展示回归状态摘要

#### 场景 2：搜索指定 Label 的未回归 issues
用户请求："帮我检查 label 为 DECODER-CORE-20260126 的 issues 哪些还没回归"

**AI 助手执行步骤**：
1. 运行 `python regression_detector.py --label DECODER-CORE-20260126 --days 30 --output html`
2. 查看 `reports/*_not_regressed_report.html`
3. 向用户展示未回归 issues 列表

#### 场景 3：定期检测并发送报告
用户请求："请检测最近一周 SWPL 项目的回归情况并发送邮件给 team"

**AI 助手执行步骤**：
1. 运行 `python regression_detector.py --project SWPL --days 7 --email team@amlogic.com`
2. 确认邮件发送成功
3. 向用户展示检测摘要

#### 场景 4：使用 JQL 进行复杂查询
用户请求："帮我检查 assignee 是 Yinan.Zhang 且状态为 Verified 的 issues"

**AI 助手执行步骤**：
1. 运行 `python regression_detector.py --jql "assignee = Yinan.Zhang AND status = Verified" --output html`
2. 读取报告并展示结果

### 7.3 信息解读

#### 检测报告字段说明

| 字段 | 说明 |
|------|------|
| JIRA Key | JIRA issue 编号 |
| Summary | 问题摘要 |
| Status | JIRA 状态（Verified/Closed/Resolved） |
| Owner | 负责人 |
| Days Since Verified | 从 verified 到今天的天数 |
| Needs Regression | 是否需要回归公版 |
| Regression Status | 回归状态（已回归/未回归/不需要回归） |
| Related Gerrits | 关联的 Gerrit change 数量 |
| Gerrit Merged | Gerrit 是否已合并 |
| Clone JIRAs | Clone 的 JIRA 数量 |

#### 重点关注
- **未回归状态**：需要督促相关人员进行回归
- **长时间未回归**：Days Since Verified 较大的 issues
- **无 Gerrit 关联**：需要确认是否有遗漏的提交

### 7.4 与其他技能配合使用

#### 与 JIRA 信息提取器配合使用
```bash
# 1. 获取 JIRA 详细信息
cd /home/peng/.opencode/skill/JIRA_Info_Extractor
python3 jira_info_extractor.py "SWPL-252395" --format json

# 2. 进行回归检测
cd /home/peng/.opencode/skill/regression_check
python regression_detector.py --jira SWPL-252395
```

#### 与 Gerrit Diff 获取工具配合使用
```bash
# 1. 进行回归检测，获取未回归 issues
python regression_detector.py --label DECODER-CORE-20260126 --output json

# 2. 对未回归的 issues，获取关联 Gerrit 的 diff
cd /home/peng/.opencode/skill/gerrit_opt
python3 get_diff.py "https://scgit.amlogic.com/#/c/616709/"
```

## 8. 文件清单

```
/home/peng/.opencode/skill/regression_check/
├── SKILL.md                    # 技能文档
├── README.md                   # 项目说明
├── config.json                 # 配置文件
├── regression_detector.py      # 主程序入口
├── requirements.txt            # Python 依赖
└── regression_system/          # 核心模块目录
    ├── __init__.py
    ├── config_manager.py       # 配置管理器
    ├── jira_client.py          # JIRA 客户端
    ├── gerrit_client.py        # Gerrit 客户端
    ├── regression_engine.py    # 回归检测引擎
    ├── report_generator.py     # 报告生成器
    ├── email_sender.py         # 邮件发送器
    ├── branch_filter.py        # 分支过滤器
    ├── confluence_client.py    # Confluence 客户端
    └── utils.py                # 工具函数
```

## 9. 退出码说明

| 退出码 | 含义 |
|--------|------|
| 0 | 检测完成，未发现未回归 issues |
| 1 | 检测完成，发现未回归 issues 或执行出错 |
| 130 | 用户中断操作 |

---

Base directory for this skill: file:///home/peng/.opencode/skill/regression_check
