---
name: gerrit-diff-fetcher
description: Gerrit Diff 获取工具是一个用于从 Gerrit 代码审查系统提取代码变更 diff 信息的 Python 工具。支持通过 Gerrit URL 或 change ID 获取完整的 commit message 和代码 diff 内容，适用于代码审查、问题分析和文档生成等场景。
---

# Gerrit Diff 获取工具使用说明

## 1. 概述

### 1.1 主要功能
- **Diff 信息提取**: 从 Gerrit change URL 或 change ID 提取完整的代码 diff
- **Commit Message 获取**: 提取完整的 commit message 信息
- **多格式支持**: 支持文本和文件输出格式
- **配置文件管理**: 通过配置文件管理 Gerrit 认证信息
- **批量处理**: 支持批量获取多个 change 的 diff 信息

### 1.2 技术架构
- **语言**: Python 3
- **核心模块**:
  - `GerritFetcher`: Gerrit API 客户端
  - `extract_change_id`: URL 解析函数
  - `extract_diff_content`: Diff 内容提取函数
- **外部依赖**:
  - `pygerrit2`: Gerrit REST API 客户端
  - `requests`: HTTP 请求库

### 1.3 系统要求
- Python 3.6+
- 网络访问权限（可访问 Gerrit 服务器）
- 有效的 Gerrit 认证凭据

## 2. 快速入门

### 2.1 安装依赖
```bash
pip install pygerrit2 requests
```

### 2.2 配置方式

工具支持两种配置方式，优先级：**环境变量 > 配置文件**

#### 方式一：环境变量（推荐）

设置以下环境变量：
```bash
export GERRIT_URL="https://scgit.amlogic.com"
export GERRIT_USERNAME="your_username"
export GERRIT_PASSWORD="your_password"
```

**优点**：
- 无需管理配置文件
- 支持临时切换账号：`GERRIT_USERNAME="other" python3 get_diff.py ...`
- 敏感信息不会留在代码仓库中

**持久化配置**（添加到 ~/.bashrc 或 ~/.zshrc）：
```bash
echo 'export GERRIT_URL="https://scgit.amlogic.com"' >> ~/.bashrc
echo 'export GERRIT_USERNAME="your_username"' >> ~/.bashrc
echo 'export GERRIT_PASSWORD="your_password"' >> ~/.bashrc
source ~/.bashrc
```

#### 方式二：配置文件

创建 `config.json` 文件：
```json
{
  "gerrit": {
    "base_url": "https://scgit.amlogic.com",
    "username": "your_username",
    "password": "your_password"
  }
}
```

**配置文件查找顺序**：
1. `~/.gerrit/config.json`（全局配置）
2. `./config.json`（本地配置）

**混合使用**：环境变量会覆盖配置文件中的同名配置

### 2.3 基本用法
```bash
# 使用 Gerrit URL 获取 diff
python3 get_diff.py "https://scgit.amlogic.com/#/c/642117/"

# 使用纯数字 change ID
python3 get_diff.py "642117"

# 指定输出文件
python3 get_diff.py "https://scgit.amlogic.com/#/c/642117/" --output my_diff.txt
```

## 3. 使用方式

### 3.1 命令行参数

```
usage: get_diff.py [-h] [--output OUTPUT] [url]

获取 Gerrit Change 的 diff 信息

positional arguments:
  url                   Gerrit change URL 或 change ID

options:
  -h, --help            显示帮助信息
  --output OUTPUT, -o OUTPUT
                        输出文件路径（如不指定则自动生成）
```

### 3.2 支持的 URL 格式

工具支持多种 Gerrit URL 格式：

| 格式 | 示例 |
|------|------|
| 标准格式 | `https://scgit.amlogic.com/#/c/642117/` |
| 简化格式 | `https://scgit.amlogic.com/c/642117` |
| 纯数字 | `642117` |
| 相对路径 | `gerrit/642117` |

### 3.3 输出说明

工具运行后会产生以下输出：

```
================================================================================
Commit Message:
================================================================================
Mjpeg : CB1 Fix mjpeg display colour abnormal issue [1/1]

PD#SWPL-254798
PD#SWPL-255891

Problem:
Some parameters in struct vf_out are not copied to ge2d.

Solution:
Ensure that all the dst parameters are set to ge2d.

Verify:
S4

Change-Id: Ic5aaa2719984bc2d9a4faadd8a84599b04f40e58
Signed-off-by: zhentao.guo <zhentao.guo@amlogic.com>


================================================================================
Diff Content:
================================================================================
diff --git a/drivers/amvdec_ports/aml_vcodec_ge2d.c b/drivers/amvdec_ports/aml_vcodec_ge2d.c
index 076a42d..ef8260f 100644
--- a/drivers/amvdec_ports/aml_vcodec_ge2d.c
+++ b/drivers/amvdec_ports/aml_vcodec_ge2d.c
@@ -487,7 +487,6 @@
 		}
 
 		/* fill outbuf parms. */
-		memcpy(&out_buf->vf, vf_out, sizeof(struct vframe_s));
 		out_buf->flag		= 0;
 		out_buf->caller_data	= ge2d;
 
@@ -604,6 +603,8 @@
 		if (ge2d->work_mode & GE2D_MODE_CONVERT_NV16) {
 			vf_out->canvas0_config[1].height <<= 1;
 		}
+		memcpy(&out_buf->vf, vf_out, sizeof(struct vframe_s));
+
 		canvas_config_config(ctx->dev->cache.res[4].cid, &vf_out->canvas0_config[1]);
 		canvas_config_config(ctx->dev->cache.res[5].cid, &vf_out->canvas0_config[2]);
 		ge2d_config.dst_para.canvas_index =


================================================================================
Diff 信息已保存到: diff_642117.txt
```

### 3.4 提取的字段说明

| 字段名 | 描述 | 来源 |
|--------|------|------|
| change_id | Change ID | 从 URL 提取或用户提供 |
| commit_message | 完整提交信息 | commit API |
| diff_content | 代码 diff 内容 | patch API |
| project | 项目名称 | change info API |
| branch | 分支名称 | change info API |
| status | 状态（MERGED/NEW等） | change info API |

## 4. 完整示例

### 示例 1: 获取单个 change 的 diff

```bash
python3 get_diff.py "https://scgit.amlogic.com/#/c/642117/"
```

输出保存到 `diff_642117.txt`

### 示例 2: 指定输出文件名

```bash
python3 get_diff.py "https://scgit.amlogic.com/#/c/642117/" --output my_change.diff
```

### 示例 3: 使用 Python API

```python
from get_diff import get_diff, load_config

# 加载配置（环境变量优先）
config = load_config()
gerrit_config = config['gerrit']

# 获取 diff
result = get_diff(
    gerrit_url="https://scgit.amlogic.com/#/c/642117/",
    base_url=gerrit_config['base_url'],
    username=gerrit_config['username'],
    password=gerrit_config['password']
)

print("Commit Message:")
print(result['commit_message'])
print("\nDiff:")
print(result['diff_content'])
```

### 示例 4: 批量获取多个 changes

```python
from get_diff import get_diff, load_config, extract_change_id

# 加载配置
config = load_config()
gerrit_config = config['gerrit']

change_urls = [
    "https://scgit.amlogic.com/#/c/642117/",
    "https://scgit.amlogic.com/#/c/642118/",
    "https://scgit.amlogic.com/#/c/642119/"
]

for url in change_urls:
    try:
        result = get_diff(url, gerrit_config['base_url'], gerrit_config['username'], gerrit_config['password'])
        change_id = extract_change_id(url)
        
        with open(f'diff_{change_id}.txt', 'w') as f:
            f.write(f"Commit Message:\n{result['commit_message']}\n\n")
            f.write(f"Diff:\n{result['diff_content']}\n")
        
        print(f"✅ Saved diff for {change_id}")
    except Exception as e:
        print(f"❌ Failed for {url}: {e}")
```

## 5. 故障排除

### 5.1 常见错误及解决方案

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| GERRIT_URL 环境变量未设置 | 未配置环境变量且缺少配置文件 | 设置环境变量或创建 config.json |
| GERRIT_USERNAME 环境变量未设置 | 同上 | 同上 |
| GERRIT_PASSWORD 环境变量未设置 | 同上 | 同上 |
| 配置文件不存在 | 未创建 config.json | 创建配置文件并填入认证信息 |
| 401 Unauthorized | 用户名或密码错误 | 检查环境变量或 config.json 中的凭据 |
| 404 Not Found | Change ID 不存在 | 确认 change ID 正确且可访问 |
| ImportError | 缺少依赖包 | 运行 `pip install pygerrit2 requests` |
| SSL 证书错误 | 证书验证失败 | 检查网络连接或联系管理员 |

### 5.2 配置问题排查

**检查环境变量是否设置**：
```bash
echo $GERRIT_URL
echo $GERRIT_USERNAME
echo $GERRIT_PASSWORD
```

**验证配置文件路径**：
```bash
# 检查全局配置
ls -la ~/.gerrit/config.json

# 检查本地配置
ls -la ./config.json
```

**测试配置是否正确**：
```bash
# 使用环境变量
GERRIT_URL="..." GERRIT_USERNAME="..." GERRIT_PASSWORD="..." python3 get_diff.py "642117"

# 使用配置文件
unset GERRIT_URL GERRIT_USERNAME GERRIT_PASSWORD
python3 get_diff.py "642117"
```

### 5.2 网络问题

如果遇到网络连接问题：
1. 检查是否能正常访问 Gerrit 服务器
2. 确认网络代理配置正确
3. 验证防火墙设置

### 5.3 权限问题

如果遇到权限错误：
1. 确认账号有访问该 change 的权限
2. 检查密码是否正确（注意大小写）
3. 确认账号未被锁定或过期

## 6. AI 助手使用方法

### 6.1 工作流程

当用户需要获取 Gerrit diff 信息时，AI 助手应该按照以下流程操作：

1. **解析用户请求**：
   - 提取 Gerrit URL 或 change ID
   - 确认输出需求（显示/保存/分析）

2. **执行 diff 获取**：
   ```bash
   cd /home/peng/.opencode/skill/gerrit_opt
   python3 get_diff.py "GERRIT_URL"
   ```

3. **处理结果**：
   - 显示 diff 摘要
   - 根据需求分析代码变更
   - 提取关键信息（问题/解决方案/验证平台等）

### 6.2 典型使用场景

#### 场景 1：获取并显示 diff 信息
用户请求："请帮我获取 https://scgit.amlogic.com/#/c/642117/ 的 diff"

**AI 助手执行步骤**：
1. 运行 `python3 get_diff.py "https://scgit.amlogic.com/#/c/642117/"`
2. 读取生成的 diff 文件
3. 向用户展示关键变更摘要

#### 场景 2：分析代码变更
用户请求："分析 change 642117 修改了什么问题"

**AI 助手执行步骤**：
1. 获取 diff 信息
2. 分析 commit message 中的 Problem/Solution
3. 查看代码变更的具体内容
4. 总结修改的影响和目的

#### 场景 3：批量获取多个 changes
用户请求："帮我获取这几个 change 的 diff：642117, 642118, 642119"

**AI 助手执行步骤**：
1. 使用 Python API 批量处理
2. 为每个 change 生成单独的 diff 文件
3. 汇总所有变更的统计信息

### 6.3 与其他技能配合使用

#### 与 JIRA 信息提取器配合使用
```bash
# 1. 获取 JIRA 信息
cd /home/peng/.opencode/skill/JIRA_Info_Extractor
python3 jira_info_extractor.py "SWPL-254798" --format json

# 2. 获取关联的 Gerrit diff
cd /home/peng/.opencode/skill/gerrit_opt
python3 get_diff.py "642117"
```

#### 与 Commit Message 规则配合使用
1. 获取 Gerrit diff 中的 commit message
2. 根据 commit-message-rule 技能验证格式
3. 提供改进建议

## 7. 文件清单

```
/home/peng/.opencode/skill/gerrit_opt/
├── SKILL.md              # 技能文档
├── config.json           # Gerrit 认证配置
├── gerrit_client.py      # Gerrit 客户端类
├── get_diff.py           # 便捷获取 diff 的脚本
└── diff_*.txt            # 生成的 diff 文件
```

## 8. API 参考

### load_config() 函数

加载配置，优先级：**环境变量 > 配置文件**

**支持的环境变量**：
- `GERRIT_URL` / `GERRIT_BASE_URL`: Gerrit 服务器地址
- `GERRIT_USERNAME`: 用户名
- `GERRIT_PASSWORD`: 密码/Token

**配置文件路径**（按优先级查找）：
1. `~/.gerrit/config.json`（全局配置）
2. `./config.json`（本地配置）

**返回值**：
```python
{
    'gerrit': {
        'base_url': '...',
        'username': '...',
        'password': '...'
    }
}
```

**使用示例**：
```python
from get_diff import load_config

config = load_config()
print(config['gerrit']['base_url'])
```

### extract_change_id(url) 函数

从 Gerrit URL 中提取 change ID。

**参数**：
- `url`: Gerrit change URL 或 change ID

**返回值**：Change ID 字符串

**示例**：
```python
from get_diff import extract_change_id

change_id = extract_change_id("https://scgit.amlogic.com/#/c/642117/")
print(change_id)  # 输出: 642117
```

### get_diff(gerrit_url, base_url, username, password) 函数

获取 Gerrit change 的 diff 信息。

**参数**：
- `gerrit_url`: Gerrit change URL 或 change ID
- `base_url`: Gerrit 服务器基础 URL
- `username`: Gerrit 用户名
- `password`: Gerrit 密码

**返回值**：
```python
{
    'change_id': '642117',
    'commit_message': '...',
    'diff_content': '...'
}
```

### extract_diff_content(patch_text) 函数

从 patch 文本中提取 diff 内容。

**参数**：
- `patch_text`: 完整的 patch 文本

**返回值**：diff 内容字符串

## 9. 更新日志

### v1.0.0
- 初始版本发布
- 支持基本的 diff 获取功能
- 支持多种 URL 格式
- 提供配置文件管理

---

Base directory for this skill: file:///home/peng/.opencode/skill/gerrit_opt
