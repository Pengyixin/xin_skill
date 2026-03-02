# JIRA 回归检测脚本使用指南

## 虚拟环境已创建

虚拟环境已创建在 `venv` 目录下，依赖已安装完成。

## 使用方法

### 激活虚拟环境

```bash
source venv/bin/activate
```

### 运行脚本

```bash
# 搜索最近30天verify/close的issues并检测
python regression_detector.py --project SWPL --days 30

# 检测单个JIRA
python regression_detector.py --jira SWPL-252395

# 从文件读取JIRA列表
python regression_detector.py --file jira_list.txt

# 生成HTML报告
python regression_detector.py --project SWPL --output html
```

### 退出虚拟环境

```bash
deactivate
```

---

## 如何自己创建虚拟环境（手动操作）

### 1. 创建虚拟环境

```bash
python3 -m venv venv
```

### 2. 激活虚拟环境

```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install requests pygerrit2
```

### 4. 运行脚本

```bash
python regression_detector.py --help
```

### 5. 退出虚拟环境

```bash
deactivate
```

## 依赖说明

- **requests**: HTTP 库，用于调用 JIRA 和 Gerrit API
- **pygerrit2**: Gerrit REST API 客户端

## 配置文件

运行前请确保 `config.json` 包含正确的 JIRA 和 Gerrit 认证信息：

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
