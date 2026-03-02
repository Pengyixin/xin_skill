# 单独使用JIRA信息提取器

## 问题解决

如果你遇到以下错误：
```
  File "jira_info_extractor.py", line 20
    def __init__(self, config: Dict[str, str]):
                             ^
SyntaxError: invalid syntax
```

这是因为系统默认的`python`命令指向Python 2（不支持类型注解）。

## 解决方案

### 方法1：使用`py`命令（推荐）

```bash
# 在D:\skill\JIRA_Info_Extractor目录下
cd D:\skill\JIRA_Info_Extractor

# 使用py命令（Python 3）
py jira_info_extractor.py "SWPL-252994" --config config.json --format text
```

### 方法2：直接使用完整路径

```bash
py D:\skill\JIRA_Info_Extractor\jira_info_extractor.py "SWPL-252994" --config D:\skill\JIRA_Info_Extractor\config.json
```

### 方法3：修改Python别名

如果你想永久解决问题，可以在PowerShell或CMD中设置别名：

```bash
# PowerShell
New-Alias python py

# 或添加到PowerShell配置文件
echo "New-Alias python py" >> $PROFILE
```

## 快速使用示例

```bash
# 基本用法
py jira_info_extractor.py "SWPL-252994"

# 指定配置文件
py jira_info_extractor.py "SWPL-252994" --config config.json

# JSON格式输出
py jira_info_extractor.py "SWPL-252994" --format json

# 保存到文件
py jira_info_extractor.py "SWPL-252994" --output result.txt
```

## 验证是否正常工作

```bash
# 测试帮助信息
py jira_info_extractor.py --help

# 测试实际查询
py jira_info_extractor.py "SWPL-252994" --format text
```

脚本现在可以在`D:\skill\JIRA_Info_Extractor`目录下独立使用，不依赖原始的`commit_message_generator.py`。
