# Markdown 到 Confluence 上传工具

快速将 Markdown 文件上传到 Confluence 页面，支持 Windows/Linux/Mac。

## 快速开始

### 1. 初始化

```bash
cd /home/peng/.opencode/skill/md_to_confluence
python3 setup.py
```

### 2. 配置认证

编辑 `config.json`：

```json
{
  "confluence": {
    "username": "your-email@company.com",
    "password": "your-api-token",
    "base_url": "https://confluence.company.com"
  }
}
```

### 3. 上传页面

```bash
# 创建新页面
python3 run.py doc.md --title "测试" --space-key YOURSPACE

# 更新现有页面
python3 run.py doc.md --page-id 12345678

# 预览模式（不上传）
python3 run.py doc.md --title "测试" --dry-run
```

## 常用命令

| 场景 | 命令 |
|------|------|
| 创建页面 | `python3 run.py doc.md --title "标题" --space-key SPACE` |
| 创建子页面 | `python3 run.py doc.md --title "标题" --space-key SPACE --parent-id 123` |
| 添加标签 | `python3 run.py doc.md --title "标题" --space-key SPACE --label api --label doc` |
| 更新页面 | `python3 run.py doc.md --page-id 12345678` |
| 预览模式 | `python3 run.py doc.md --title "标题" --dry-run` |

## 获取 API Token

1. 访问 https://id.atlassian.com/manage-profile/security/api-tokens
2. 点击 "Create API token"
3. 复制生成的 token

## 故障排除

- **认证失败**: 检查 config.json 中的用户名和 API Token
- **权限错误**: 确认有页面编辑权限

详细文档请查看 [SKILL.md](./SKILL.md)
