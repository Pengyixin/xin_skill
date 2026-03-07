---
name: confluence-page-structure-exporter
description: Confluence页面结构导出工具是一个自动化工具，用于获取指定Confluence页面的所有子页面标题，并保留其层级结构。用户已通过环境变量配置好Confluence认证信息（CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_PASSWORD），AI助手直接使用即可，无需询问账号密码。该工具支持递归扫描、多种输出格式（文本、JSON、Markdown），并提供完整的页面元数据和统计信息。
---

# Confluence页面结构导出工具技能说明

## 概述

这是一个基于Python的Confluence页面结构导出工具。用户已通过环境变量配置好Confluence认证信息，AI助手可以直接使用而无需询问账号密码。该工具能够获取Confluence页面的完整层级结构，包括所有子页面标题、URL、最后更新时间、版本等信息，并以多种格式输出结果。工具使用Confluence官方API获取子页面，确保页面顺序与Confluence中显示的实际顺序一致。

**重要提示**：用户已通过环境变量配置认证信息，AI助手使用时**不需要询问账号密码**，直接执行命令即可。

## 功能特性

### 核心功能
- **递归扫描**: 支持多层级递归扫描子页面，可配置最大深度
- **保持原始顺序**: 使用Confluence官方API获取子页面，保持页面在Confluence中的实际排序（手动排序或其他排序方式）
- **多种输出格式**: 支持文本、JSON和Markdown格式输出
- **完整元数据**: 包含页面标题、URL、最后更新时间、版本、空间信息等
- **层级结构保留**: 保持页面的父子关系，生成树状结构
- **性能统计**: 提供总页面数、最大深度、扫描耗时等统计信息

### 技术特性
- **正确的API使用**: 使用 `GET /rest/api/content/{pageId}/child/page` API获取子页面，确保顺序与Confluence一致
- **配置驱动**: 支持环境变量和配置文件两种认证方式，无硬编码凭证
- **错误恢复**: 单个页面获取失败不影响整体导出
- **进度显示**: 实时显示扫描进度和状态，包括获取的子页面数量
- **灵活参数**: 支持深度控制、输出格式选择等参数

## 前提条件

### 系统要求
- Python 3.6+ 及 `requests` 库
- 具有适当权限的Confluence账户
- 能够访问Confluence服务器的网络连接

### 依赖安装
```bash
pip install requests
```

## 认证配置

**AI助手注意**：用户已通过环境变量配置好认证信息，无需询问账号密码，直接使用即可。

### 环境变量配置（已配置）

用户已设置以下环境变量：

```bash
export CONFLUENCE_URL="https://confluence.yourcompany.com"
export CONFLUENCE_USERNAME="your_username"
export CONFLUENCE_PASSWORD="your_password"
# 可选：API Token
export CONFLUENCE_API_TOKEN="your_api_token"
```

### 配置文件方式（备选）

如环境变量未设置，可创建JSON配置文件（例如 `config.json`）：

```json
{
  "confluence": {
    "username": "你的用户名",
    "password": "你的密码", 
    "base_url": "https://confluence.你的公司.com"
  }
}
```

## AI助手使用方法

**AI助手注意**：用户已配置好环境变量，直接使用以下命令即可，**绝对不要询问账号密码**。

### 基本命令格式
```bash
py confluence_page_structure.py "<URL>" [-d <深度>] [-f <格式>] [-o <输出路径>]
```

### 必需参数
- `URL`: 要导出结构的Confluence页面URL

### 可选参数
- `-d, --depth`: 最大递归深度（默认：5）
- `-f, --format`: 输出格式：`txt`（文本）、`json`、`md`（Markdown）（默认：`txt`）
- `-o, --output`: 输出文件路径（可选，默认自动生成）
- `-c, --config`: 配置文件路径（可选，环境变量已配置时不需要）

### 使用流程
1. 用户会提供Confluence页面URL
2. **直接使用命令执行**，无需询问任何认证信息
3. 根据用户需求选择输出格式

## 使用示例

**AI助手注意**：所有示例均假设环境变量已配置好，直接执行即可。

### 示例1：基本用法（文本格式）
```bash
py confluence_page_structure.py "https://confluence.amlogic.com/display/~yixin.peng/Project+Documentation"
```

### 示例2：指定深度和JSON格式
```bash
py confluence_page_structure.py "https://confluence.amlogic.com/pages/viewpage.action?pageId=12345" -d 3 -f json
```

### 示例3：Markdown格式输出
```bash
py confluence_page_structure.py "https://confluence.amlogic.com/display/TEAM/Weekly+Reports" -f md
```

### 示例4：查看帮助
```bash
py confluence_page_structure.py --help
```

## 输出说明

### 1. 文本格式输出
包含清晰的层级结构和基本元数据，页面顺序与Confluence中显示的一致：
```
========================================
Confluence页面结构导出
生成时间: 2026-02-04 20:33:00
========================================
根页面: 项目文档
根页面URL: https://confluence.company.com/display/PROJECT/文档
最后更新: 2026-01-15T10:30:00.000+08:00
版本: v12
总页面数: 45
最大深度: 3

页面层级结构:

项目文档
├─ 需求文档 (v5, 2026-01-10)
│  ├─ 功能需求 (v3, 2026-01-08)
│  └─ 非功能需求 (v2, 2026-01-05)
├─ 设计文档 (v8, 2026-01-12)
└─ 测试文档 (v6, 2026-01-14)
```

### 2. JSON格式输出
包含完整数据结构，适合程序化处理：
```json
{
  "metadata": {
    "generated_at": "2026-02-04T20:33:00",
    "root_page": {
      "id": "12345",
      "title": "项目文档",
      "url": "https://confluence.company.com/display/PROJECT/文档",
      "last_updated": "2026-01-15T10:30:00.000+08:00",
      "version": 12
    },
    "statistics": {
      "total_pages": 45,
      "max_depth": 3
    }
  },
  "hierarchy": {
    "id": "12345",
    "title": "项目文档",
    "children": [...]
  },
  "flat_list": [...]
}
```

### 3. Markdown格式输出
包含完整元数据和层级结构的Markdown文档：
```markdown
# Confluence页面结构: 项目文档

> **根页面**: [项目文档](https://confluence.company.com/display/PROJECT/文档)  
> **最后更新**: 2026-01-15T10:30:00.000+08:00  
> **版本**: v12  
> **生成时间**: 2026-02-04 20:33:00  
> **总页面数**: 45  
> **最大深度**: 3  

---

## 项目文档
- **URL**: https://confluence.company.com/display/PROJECT/文档
- **最后更新**: 2026-01-15T10:30:00.000+08:00
- **版本**: v12

### 子页面结构

- **需求文档** (最后更新: 2026-01-10, 版本: v5, [链接](...))
  - **功能需求** (最后更新: 2026-01-08, 版本: v3, [链接](...))
  - **非功能需求** (最后更新: 2026-01-05, 版本: v2, [链接](...))
- **设计文档** (最后更新: 2026-01-12, 版本: v8, [链接](...))
- **测试文档** (最后更新: 2026-01-14, 版本: v6, [链接](...))
```

## AI助手使用场景

**AI助手注意**：用户已配置环境变量，以下场景直接执行命令即可。

### 场景1：文档结构审计
```bash
py confluence_page_structure.py "项目主页URL" -f md
```

### 场景2：知识库迁移准备
```bash
py confluence_page_structure.py "知识库根页面URL" -d 10 -f json
```

### 场景3：定期文档备份
```bash
py confluence_page_structure.py "团队空间主页URL" -o 文档结构_$(date +%Y%m%d).txt
```

### 场景4：权限管理辅助
```bash
py confluence_page_structure.py "需要设置权限的页面URL"
```

### 场景2：知识库迁移准备
```bash
# 导出知识库完整结构作为迁移清单
py confluence_page_structure.py "知识库根页面URL" -d 10 -f json
```

### 场景3：定期文档备份
```bash
# 定期备份团队文档结构
py confluence_page_structure.py "团队空间主页URL" -o 文档结构_$(date +%Y%m%d).txt
```

### 场景4：权限管理辅助
```bash
# 导出页面层级结构，辅助设置权限
py confluence_page_structure.py "需要设置权限的页面URL"
```

## 错误处理指南

### 常见错误及解决方案

#### 1. 配置错误
```
配置错误: 环境变量未设置且未提供配置文件
```
**AI助手操作**：如遇到此错误，提示用户已配置环境变量，直接重试即可。无需询问账号密码。

#### 2. 认证失败
```
搜索页面失败: HTTP 401
```
**解决方案**: 检查环境变量中的用户名和密码是否正确。

#### 3. 页面不存在
```
未找到页面: page_title (space: space_key)
```
**解决方案**: 检查URL是否正确，确保页面存在且有访问权限。

#### 4. 网络问题
```
获取页面信息时出错: timed out
```
**解决方案**: 检查网络连接，确保可以访问Confluence服务器。

#### 5. 权限不足
```
获取子页面时出错: HTTP 403
```
**解决方案**: 确保账户有足够的权限访问目标页面及其子页面。

## 技术特点

### 1. 页面顺序保持
工具使用Confluence官方API `GET /rest/api/content/{pageId}/child/page` 获取子页面，该API返回的页面顺序与Confluence中显示的实际顺序一致。这确保了导出的页面结构准确反映了Confluence中的组织方式，无论是手动排序、字母顺序还是其他排序方式。

### 2. 性能优化
- **深度控制**: 默认最大深度为5，避免过深递归
- **分页获取**: 支持分页获取所有子页面，每次获取100条结果
- **网络考虑**: 工具会进行多次API调用，确保网络稳定
- **进度显示**: 实时显示扫描进度和获取的子页面数量

### 3. 输出格式选择
- **文本格式**: 适合人类阅读，文件较小
- **JSON格式**: 适合程序处理，包含完整数据
- **Markdown格式**: 适合分享和文档化

## 文件结构

```
Confluence_Page_Structure_Exporter/
├── confluence_page_structure.py    # 主转换脚本
├── config.example.json             # 配置模板
├── README.md                       # 用户文档
├── skill.md                        # 此AI文档
└── test_structure.py               # 测试脚本
```

## 扩展可能性

### 1. 功能扩展
- 添加图片和附件信息导出
- 支持页面内容摘要生成
- 添加页面更新频率分析

### 2. 性能优化
- 添加API调用缓存
- 支持并发页面获取
- 添加增量导出功能

### 3. 集成功能
- 与Git集成，自动提交结构变更
- 添加计划任务支持
- 提供Web界面或API

## 联系和支持

- **工具位置**: `d:\skill\Confluence_Page_Structure_Exporter\`
- **主要脚本**: `confluence_page_structure.py`
- **用户文档**: `README.md`

**AI助手注意**：用户使用此工具时，认证信息已通过环境变量配置好，直接执行命令即可，**绝对不要询问账号密码**。

如有问题，请检查：
1. 环境变量是否正确设置（CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_PASSWORD）
2. 网络连接是否正常
3. Confluence账户权限是否足够
4. 目标页面是否存在且可访问

---


