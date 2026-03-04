# 邮件发送工具 (Mail Sender)

邮件发送工具是一个轻量级的 Python 邮件发送模块，支持 SMTP 协议发送 HTML 格式邮件。支持配置文件管理、HTML 模板文件读取，适用于系统通知、告警邮件等场景。

## 功能特性

- ✉️ 支持 SMTP 协议发送邮件
- 🔒 支持 STARTTLS 加密传输
- 📄 支持 HTML 格式邮件内容
- 📁 支持从 HTML 文件读取邮件模板
- ⚙️ 配置文件管理邮箱账号和服务器设置
- 🖥️ 支持命令行直接调用
- 🐍 支持 Python 代码导入使用
- 🔧 纯 Python 实现，无需额外依赖

## 安装

无需安装，直接克隆或下载代码即可使用。

```bash
git clone <repository-url>
cd mail_sender
```

## 配置文件

首次使用前，需要创建 `config.json` 配置文件：

```json
{
  "email": {
    "sender_email": "your.email@example.com",
    "sender_password": "your_password",
    "smtp_server": "smtp.example.com",
    "smtp_port": 465,
    "default_recipient": "recipient@example.com",
    "default_sender_name": "Your Name"
  }
}
```

### 配置项说明

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `sender_email` | 发件人邮箱地址 | `user@company.com` |
| `sender_password` | 邮箱密码或授权码 | `your_password` |
| `smtp_server` | SMTP 服务器地址 | `smtp.company.com` |
| `smtp_port` | SMTP 服务器端口 | `465` 或 `25` |
| `default_recipient` | 默认收件人邮箱 | `admin@company.com` |
| `default_sender_name` | 发件人显示名称 | `System Admin` |

## 使用方法

### 方式一：命令行使用

#### 基本命令

```bash
python mail.py -i "Issue-123" -e "同步失败的详细信息"
```

#### 命令行参数

| 参数 | 简写 | 说明 | 是否必填 |
|------|------|------|----------|
| `--issue` | `-i` | Issue 信息/邮件主题标识 | 是 |
| `--error` | `-e` | 错误详情(纯文本) | 否 |
| `--file` | `-f` | HTML 模板文件路径 | 否 |
| `--to` | `-t` | 收件人邮箱 | 否 |
| `--config` | `-c` | 配置文件路径 | 否 |
| `--version` | - | 显示版本号 | 否 |

#### 使用示例

**示例 1：使用默认模板发送邮件**
```bash
python mail.py -i "Issue-123" -e "连接超时，请检查网络配置"
```

**示例 2：使用 HTML 文件发送邮件**
```bash
python mail.py -i "Issue-456" -f email_template.html
```

**示例 3：指定收件人**
```bash
python mail.py -i "Issue-789" -e "系统错误" -t admin@example.com
```

**示例 4：指定配置文件路径**
```bash
python mail.py -i "Issue-000" -e "测试" -c /path/to/config.json
```

**示例 5：查看帮助**
```bash
python mail.py -h
```

#### HTML 模板文件示例

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>通知</title>
</head>
<body>
    <h2 style="color: #333;">系统通知</h2>
    <p>这是自定义的 HTML 邮件内容。</p>
    <p style="color: red;">重要提醒！</p>
</body>
</html>
```

### 方式二：Python 代码导入使用

#### 1. 使用默认模板发送邮件

```python
from mail import sync_issue_failed

# 发送默认格式的邮件
sync_issue_failed(
    issue_info="Issue-123",
    error_msg="同步失败的详细信息"
)
```

#### 2. 使用 HTML 文件作为邮件内容

```python
from mail import sync_issue_failed

# 从 HTML 文件读取内容发送邮件
sync_issue_failed(
    issue_info="Issue-456",
    html_file="email_template.html"
)
```

#### 3. 直接使用 send_email 函数

```python
from email.mime.text import MIMEText
from email.header import Header
from mail import send_email, EMAIL_CONFIG

# 自定义邮件内容
message = MIMEText("<h1>自定义 HTML 内容</h1>", 'html', 'utf-8')
message["From"] = str(Header(f"系统<{EMAIL_CONFIG['sender_email']}>", 'utf-8'))
message["To"] = "recipient@example.com"
message["Subject"] = "自定义主题"

send_email(
    message,
    EMAIL_CONFIG['sender_email'],
    EMAIL_CONFIG['sender_password'],
    EMAIL_CONFIG['smtp_server']
)
```

### Python 代码调用方式

#### 1. 使用默认模板发送邮件

```python
from mail import sync_issue_failed

# 发送默认格式的邮件
sync_issue_failed(
    issue_info="Issue-123",
    error_msg="同步失败的详细信息"
)
```

#### 2. 使用 HTML 文件作为邮件内容

```python
from mail import sync_issue_failed

# 从 HTML 文件读取内容发送邮件
sync_issue_failed(
    issue_info="Issue-456",
    html_file="email_template.html"
)
```

**email_template.html 示例：**
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>通知</title>
</head>
<body>
    <h2 style="color: #333;">系统通知</h2>
    <p>这是自定义的 HTML 邮件内容。</p>
    <p style="color: red;">重要提醒！</p>
</body>
</html>
```

#### 3. 直接使用 send_email 函数

```python
from email.mime.text import MIMEText
from email.header import Header
from mail import send_email, EMAIL_CONFIG

# 自定义邮件内容
message = MIMEText("<h1>自定义 HTML 内容</h1>", 'html', 'utf-8')
message["From"] = str(Header(f"系统<{EMAIL_CONFIG['sender_email']}>", 'utf-8'))
message["To"] = "recipient@example.com"
message["Subject"] = "自定义主题"

send_email(
    message,
    EMAIL_CONFIG['sender_email'],
    EMAIL_CONFIG['sender_password'],
    EMAIL_CONFIG['smtp_server']
)
```

## 完整示例

```python
#!/usr/bin/env python3
from mail import sync_issue_failed

# 示例1: 系统告警邮件
sync_issue_failed(
    issue_info="数据库连接失败",
    error_msg="无法连接到 MySQL 服务器: Connection timeout"
)

# 示例2: 使用自定义 HTML 模板
sync_issue_failed(
    issue_info="定期报告",
    html_file="weekly_report.html"
)
```

## 注意事项

⚠️ **安全提醒：**
- 请将 `config.json` 添加到 `.gitignore`，避免提交敏感信息到代码库
- 建议使用应用专用密码（而非主密码）
- 生产环境建议使用环境变量或密钥管理服务

⚠️ **网络配置：**
- 如果使用 465 端口，代码会自动启用 SSL/TLS
- 如果使用 25 端口，可能需要根据内网环境调整代码
- 确保 SMTP 服务器地址和端口正确

## 依赖

- Python 3.6+
- 仅使用 Python 标准库（smtplib, email, json）

## 许可证

MIT License
