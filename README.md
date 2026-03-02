# 回归检测系统

用于查找未回归公版的提交，自动化检测JIRA issue是否需要回归公版以及相关的gerrit是否已合并。

## 功能特点

1. **智能检测**：自动检查JIRA的customfield_11705字段是否为"Confirmed Yes"
2. **Gerrit关联**：检测JIRA关联的gerrit提交是否已合并
3. **递归检测**：支持检测clone的jira，实现递归检测
4. **多格式报告**：支持JSON、CSV、HTML三种报告格式
5. **缓存机制**：避免重复检测，提高效率

## 系统架构

```
D:\huigui\
├── config.json                    # 配置文件（包含JIRA/Gerrit凭证）
├── regression_detector.py         # 主程序入口
├── regression_system/             # 核心系统模块
│   ├── __init__.py                # 包初始化
│   ├── config_manager.py          # 配置管理器
│   ├── utils.py                   # 工具函数
│   ├── jira_client.py             # JIRA客户端
│   ├── gerrit_client.py           # Gerrit客户端
│   ├── regression_engine.py       # 回归检测引擎
│   └── report_generator.py        # 报告生成器
├── reports/                       # 报告输出目录
├── logs/                          # 日志目录
└── data/                          # 数据目录
```

## 快速开始

### 1. 配置认证信息

确保 `D:\huigui\config.json` 文件包含正确的JIRA和Gerrit认证信息：

```json
{
  "jira": {
    "username": "your_jira_username",
    "password": "your_jira_password"
  },
  "gerrit": {
    "base_url": "https://scgit.amlogic.com",
    "username": "your_gerrit_username",
    "password": "your_gerrit_password"
  }
}
```

### 2. 使用方法

#### 搜索模式（推荐）
搜索最近30天verify/close状态的issues并检测：
```bash
python regression_detector.py --project SWPL --days 30
```

#### 单个JIRA检测
检测单个JIRA issue：
```bash
python regression_detector.py --jira SWPL-252395
```

#### 文件模式
从文件读取JIRA列表并检测：
```bash
python regression_detector.py --file jira_list.txt
```

#### Label搜索模式
按label搜索JIRA issues，支持多个label的OR查询：
```bash
# 搜索单个label
python regression_detector.py --label DECODER-CORE-20260209 --days 30

# 搜索多个label（OR关系）
python regression_detector.py --label DECODER-CORE-20260209 VDEC-VA20260209 --days 30

# 指定项目搜索
python regression_detector.py --label DECODER-CORE-20260209 VDEC-VA20260209 --project SWPL --days 30
```

#### JQL查询模式
直接使用完整的JQL语句查询：
```bash
# 使用JQL查询
python regression_detector.py --jql "labels = DECODER-CORE-20260209 AND status = Verified"

# 复杂的JQL查询
python regression_detector.py --jql "(labels = DECODER-CORE-20260209 OR labels = VDEC-VA20260209) AND assignee = Yinan.Zhang"

# 结合项目和时间范围
python regression_detector.py --jql "project = SWPL AND updated >= -30d AND status = Closed"
```

#### 发送邮件通知
检测完成后自动发送邮件通知：
```bash
# 发送邮件到指定收件人
python regression_detector.py --project SWPL --days 30 --email "user1@amlogic.com"

# 发送邮件到多个收件人
python regression_detector.py --project SWPL --days 30 --email "user1@amlogic.com,user2@amlogic.com"
```

**邮件配置说明：**
在 `config.json` 中配置邮件发送参数：
```json
{
  "email": {
    "smtp_host": "smtp.amlogic.com",
    "smtp_port": 25,
    "username": "",
    "password": "",
    "from": "regression-detector@amlogic.com",
    "to": []
  }
}
```

#### 指定输出格式
生成HTML格式报告：
```bash
python regression_detector.py --project SWPL --output html
```

### 3. 命令行参数

```
--project PROJECT    指定JIRA项目(如SWPL)，默认为搜索所有项目
--days DAYS         搜索最近多少天的issues，默认为30天
--jira JIRA_KEY     检测单个JIRA issue
--file FILE_PATH    从文件读取JIRA列表进行检测
--output FORMAT     输出格式: json, csv, html, all (默认为all)
--verbose           显示详细输出信息
--help              显示帮助信息
```

## 检测逻辑

系统按照以下步骤进行检测：

### 步骤1：检查是否需要回归公版
- 查询JIRA issue的customfield_11705字段
- 如果值为"Confirmed Yes"，则标记为需要回归
- 否则标记为不需要回归

### 步骤2：检查关联gerrit是否已合并
- 提取issue描述和评论中的gerrit链接
- 检查每个gerrit是否已合并
- 只要有一个gerrit已合并，就标记为已回归

### 步骤3：检查clone的jira
- 如果没有gerrit或gerrit未合并
- 递归检测clone的jira
- 如果clone的jira有已回归的gerrit，则标记为已回归
- 否则标记为未回归

## 输出报告

系统会生成三种格式的报告：

### 1. JSON报告
- 位置：`D:\huigui\reports\regression_report_YYYYMMDD_HHMMSS.json`
- 包含完整的检测结果和统计信息
- 适合程序处理和自动化分析

### 2. CSV报告
- 位置：`D:\huigui\reports\regression_report_YYYYMMDD_HHMMSS.csv`
- 表格格式，适合Excel导入
- 包含关键字段：JIRA、摘要、状态、回归状态等

### 3. HTML报告
- 位置：`D:\huigui\reports\regression_report_YYYYMMDD_HHMMSS.html`
- 可视化报告，适合浏览器查看
- 包含统计卡片、彩色状态标记、排序功能

## 示例文件

### jira_list.txt（示例）
```
SWPL-252395
SWPL-251234
SWPL-250987
TEST-123456
```

### 运行示例
```bash
# 搜索SWPL项目最近7天的issues
python regression_detector.py --project SWPL --days 7

# 检测单个JIRA并生成HTML报告
python regression_detector.py --jira SWPL-252395 --output html

# 从文件读取列表并生成所有格式报告
python regression_detector.py --file jira_list.txt --output all
```

## 错误处理

系统会处理以下错误情况：
- 网络连接失败：自动重试3次
- JIRA/Gerrit认证失败：提示检查配置
- 无效的JIRA key：跳过并记录错误
- 文件读取失败：提示文件路径错误

## 依赖要求

- Python 3.6+
- requests库：`pip install requests`
- 网络连接（访问JIRA和Gerrit）

## 注意事项

1. 确保配置文件中的认证信息正确
2. 网络连接稳定，避免检测中断
3. 对于大量issues，建议分批次检测
4. HTML报告需要现代浏览器查看
5. 系统会缓存检测结果，避免重复请求

## 技术支持

如有问题，请检查：
1. 配置文件是否正确
2. 网络是否可访问JIRA和Gerrit
3. Python环境是否安装requests库
4. 查看控制台输出的错误信息
