# JIRA信息提取器

独立的JIRA信息提取工具，从`commit_message_generator.py`中提取的JIRA相关代码。

## 文件结构

```
JIRA_Info_Extractor/
├── jira_info_extractor.py    # 主脚本
├── config.json               # JIRA配置（用户名/密码）
├── test_jira_extractor.py    # 单元测试
└── README.md                 # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install requests
```

### 2. 配置JIRA认证

编辑`config.json`文件，填入你的JIRA用户名和密码：

```json
{
  "jira": {
    "username": "your_username",
    "password": "your_password"
  }
}
```

### 3. 基本使用

```bash
# 使用JIRA URL
python jira_info_extractor.py "https://jira.amlogic.com/browse/SWPL-252994"

# 使用issue key
python jira_info_extractor.py "SWPL-252994"
```

### 4. 指定配置文件

```bash
python jira_info_extractor.py "SWPL-252994" --config config.json
```

### 5. 输出格式

```bash
# 文本格式（默认）
python jira_info_extractor.py "SWPL-252994" --format text

# JSON格式
python jira_info_extractor.py "SWPL-252994" --format json
```

### 6. 保存到文件

```bash
python jira_info_extractor.py "SWPL-252994" --output result.txt
python jira_info_extractor.py "SWPL-252994" --format json --output result.json
```

## 功能特性

- ✅ 从JIRA URL提取issue key
- ✅ 获取JIRA issue详细信息
- ✅ 获取comments
- ✅ 提取Assignee和Reporter信息
- ✅ 从description中提取Root Cause和How to fix
- ✅ 支持文本和JSON输出格式
- ✅ 处理编码问题（支持中文）
- ✅ 单元测试

## 示例输出

### 文本格式

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
================================================================================
```

### JSON格式

完整的JSON数据结构，包含所有字段。

## 测试

运行单元测试：

```bash
python test_jira_extractor.py
```

## 从原始代码提取

这个工具是从`D:\skill\Commit_Message_Generator\commit_message_generator.py`中的`JIRAClient`类提取出来的，包含：

- JIRA API客户端
- issue key提取
- issue详情获取
- comments获取
- 信息提取和解析

## 许可证

MIT
