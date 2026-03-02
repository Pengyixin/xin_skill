# Confluence Markdown Exporter

基于 [confluence-markdown-exporter](https://github.com/Spenhouet/confluence-markdown-exporter) 的 Confluence 导出工具，支持 Windows/Linux/Mac。

## 快速开始

### 1. 初始化

```bash
cd /home/peng/.opencode/skill/confluence_md_exporter
python3 setup.py
```

### 2. 配置认证

**方式 A: 环境变量（推荐用于脚本）**

```bash
export ATLASSIAN_USERNAME=your-email@company.com
export ATLASSIAN_API_TOKEN=your-api-token
export ATLASSIAN_URL=https://confluence.company.com
```

**方式 B: .env 文件**

```bash
cp .env.example .env
# 编辑 .env 填入你的信息
```

### 3. 导出页面

```bash
# 导出单个页面
python3 run.py pages 123456789 --output-path ./docs

# 导出页面及其子页面
python3 run.py pages-with-descendants 123456789 --output-path ./wiki-docs

# 导出整个空间
python3 run.py spaces YOURSPACE --output-path ./space-docs
```

## 常用命令

```bash
# 导出到指定目录
python3 run.py pages 659864614 --output-path /home/peng/av2

# 导出多个页面
python3 run.py pages 12345678 12345679 --output-path ./docs

# 递归导出
python3 run.py pages-with-descendants 12345678 --output-path ./wiki

# 设置重试次数
python3 run.py --retries 5 pages 123456789

# 显示帮助
python3 run.py --help
python3 run.py pages --help
```

## 获取 API Token

1. 访问 https://id.atlassian.com/manage-profile/security/api-tokens
2. 点击 "Create API token"
3. 复制生成的 token

## 故障排除

- **401 错误**: 检查 API Token 是否正确
- **404 错误**: 检查 page-id 是否正确
- **权限错误**: 确认有页面访问权限

详细文档请查看 [SKILL.md](SKILL.md)
