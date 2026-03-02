# Amlogic Confluence URL to ID 转换器

## 快速开始

```bash
# 1. 配置认证信息
cp .env.example .env
# 编辑 .env 文件

# 2. 转换 URL
./convert.py url "https://confluence.amlogic.com/display/SW/Your+Page+Title"
```

## 命令

| 命令 | 说明 |
|------|------|
| `url` | 转换一个或多个 URL |
| `file` | 从文件批量转换 URL |
| `config` | 交互式配置认证信息 |

## 示例

```bash
# 单个 URL
./convert.py url "https://confluence.amlogic.com/display/SW/AV2+bringup+Meetings"

# 多个 URL
./convert.py url \
  "https://confluence.amlogic.com/display/SW/Page1" \
  "https://confluence.amlogic.com/display/SW/Page2"

# 从文件
./convert.py file urls.txt
```

## 获取 API Token

1. 访问 https://id.atlassian.com/manage-profile/security/api-tokens
2. 点击 "Create API token"
3. 复制生成的 token
