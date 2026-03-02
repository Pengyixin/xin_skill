# JIRA信息提取器

从JIRA号或JIRA URL中提取相关信息的Python脚本。

## 功能

- 从JIRA URL中提取issue key
- 获取JIRA issue详细信息（summary, description, status, priority等）
- 获取issue的comments
- 提取Assignee和Reporter信息
- 从description中提取Root Cause和How to fix部分
- 支持文本和JSON两种输出格式

## 使用方法

### 基本用法

```bash
# 使用JIRA URL
python jira_info_extractor.py "https://jira.amlogic.com/browse/SWPL-252994"

# 使用issue key
python jira_info_extractor.py "SWPL-252994"
```

### 指定配置文件

```bash
python jira_info_extractor.py "SWPL-252994" --config config.json
```

### 指定输出格式

```bash
# 文本格式（默认）
python jira_info_extractor.py "SWPL-252994" --format text

# JSON格式
python jira_info_extractor.py "SWPL-252994" --format json
```

### 保存到文件

```bash
python jira_info_extractor.py "SWPL-252994" --output jira_info.txt
python jira_info_extractor.py "SWPL-252994" --format json --output jira_info.json
```

### 查看帮助

```bash
python jira_info_extractor.py --help
```

## 配置文件格式

配置文件应为JSON格式，包含JIRA认证信息：

```json
{
  "jira": {
    "username": "your_username",
    "password": "your_password"
  }
}
```

## 输出示例

### 文本格式输出

```
================================================================================
JIRA信息摘要:
================================================================================
Key:           SWPL-252994
摘要:           [T6X][Android 16][GTV] local video 4K H264 play failed by Amplayer. Frequency: 100%, 1217 code is ok
状态:           Closed
优先级:         P0
类型:           Bug
创建时间:       2026-01-20T20:13:47.589+0800
更新时间:       2026-02-04T09:47:46.630+0800
Assignee:      Xiaohang Cui (Xiaohang.Cui@amlogic.com)
Reporter:      Chao Wu (Chao.Wu@amlogic.com)
标签:           AE_REF_highlight_260126, DECODER-CORE-20260126, DECODER-CORE-CXH, MM-DECODER-2026-0126, MUST_FIX_REF, Regression_2026, block_T6X_16_CB, vf-checked, vf-checked-at-1768973189.004184, vf-checkout
组件:           Video-Decoder
修复版本:       16.3.2601
评论总数:       8
Assignee评论数: 2

Assignee最新评论 (2026-01-30T12:07:54.873+0800):
[~Chao.Wu]? ??????PB????https://jenkins-sh.amlogic.com/job/android/job/Android_16/job/Android_16_Trunk_GTVS_Patchbuild/11966/
================================================================================
```

### JSON格式输出

完整的JSON数据结构，包含所有提取的信息。

## 依赖

- Python 3.6+
- requests库

```bash
pip install requests
```

## 测试

运行单元测试：

```bash
python test_jira_extractor.py
```

## 从原始commit_message_generator.py中提取的功能

这个脚本是从`commit_message_generator.py`中的JIRA相关代码提取出来的，主要包含：

1. `JIRAClient`类 - JIRA API客户端
2. `extract_issue_key()` - 从URL提取issue key
3. `get_issue_details()` - 获取issue详细信息
4. `get_comments()` - 获取comments
5. `extract_issue_info()` - 提取关键信息
6. `_extract_section()` - 从description提取特定部分

## 许可证

MIT
