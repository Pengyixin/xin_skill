#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JIRA信息提取器
从给定的JIRA号提取相关信息
"""

import json
import os
import re
import sys
import argparse
import requests
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

class JIRAClient:
    """JIRA客户端"""
    
    def __init__(self, config):
        self.base_url = "https://jira.amlogic.com"
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self.session = requests.Session()
        if self.username and self.password:
            self.session.auth = (self.username, self.password)
    
    def extract_issue_key(self, jira_url):
        """从JIRA URL中提取issue key"""
        # 示例: https://jira.amlogic.com/browse/SWPL-252395
        pattern = r'https?://jira\.amlogic\.com/browse/([A-Z]+-\d+)'
        match = re.search(pattern, jira_url)
        if match:
            return match.group(1)
        
        # 尝试其他格式
        parsed = urlparse(jira_url)
        path_parts = parsed.path.split('/')
        for part in path_parts:
            if re.match(r'^[A-Z]+-\d+$', part):
                return part
        
        return None
    
    def get_issue_details(self, issue_key):
        """获取JIRA issue详细信息"""
        api_url = f"{self.base_url}/rest/api/2/issue/{issue_key}"
        
        try:
            response = self.session.get(api_url, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"错误: 获取JIRA issue失败: {e}")
            if hasattr(e.response, 'text'):
                print(f"响应内容: {e.response.text}")
            return {}
    
    def get_comments(self, issue_key):
        """获取JIRA issue的comments"""
        api_url = f"{self.base_url}/rest/api/2/issue/{issue_key}/comment"
        
        try:
            response = self.session.get(api_url, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            data = response.json()
            return data.get("comments", [])
        except requests.exceptions.RequestException as e:
            print(f"错误: 获取JIRA comments失败: {e}")
            return []
    
    def extract_issue_info(self, issue_data, comments=None):
        """从JIRA issue数据中提取关键信息"""
        fields = issue_data.get("fields", {})
        
        # 提取Assignee详细信息
        assignee_data = fields.get("assignee", {})
        assignee_info = {
            "displayName": assignee_data.get("displayName", ""),
            "emailAddress": assignee_data.get("emailAddress", ""),
            "active": assignee_data.get("active", False),
            "timeZone": assignee_data.get("timeZone", ""),
        }
        
        # 提取Reporter详细信息
        reporter_data = fields.get("reporter", {})
        reporter_info = {
            "displayName": reporter_data.get("displayName", ""),
            "emailAddress": reporter_data.get("emailAddress", ""),
        }
        
        info = {
            "key": issue_data.get("key", ""),
            "summary": fields.get("summary", ""),
            "description": fields.get("description", ""),
            "issue_type": fields.get("issuetype", {}).get("name", ""),
            "priority": fields.get("priority", {}).get("name", ""),
            "status": fields.get("status", {}).get("name", ""),
            "assignee": assignee_info,  # 现在是一个字典，不是字符串
            "reporter": reporter_info,   # 现在是一个字典，不是字符串
            "created": fields.get("created", ""),
            "updated": fields.get("updated", ""),
            "labels": fields.get("labels", []),
            "components": [c.get("name", "") for c in fields.get("components", [])],
            "fix_versions": [v.get("name", "") for v in fields.get("fixVersions", [])],
        }
        
        # 提取JIRA自定义字段: customfield_11708 (RootCause) 和 customfield_11709 (HowToFix)
        root_cause_custom = fields.get("customfield_11708", "")
        how_to_fix_custom = fields.get("customfield_11709", "")
        
        # 尝试从description中提取Root Cause和How to fix
        description = info["description"] or ""
        root_cause_desc = self._extract_section(description, ["Root Cause", "Root cause", "原因分析", "问题原因"])
        how_to_fix_desc = self._extract_section(description, ["How to fix", "Solution", "解决方案", "修复方案"])
        
        # 优先使用自定义字段，如果为空则使用从description中提取的内容
        info["root_cause"] = root_cause_custom if root_cause_custom else root_cause_desc
        info["how_to_fix"] = how_to_fix_custom if how_to_fix_custom else how_to_fix_desc
        
        # 添加原始自定义字段值（用于调试）
        info["root_cause_customfield"] = root_cause_custom
        info["how_to_fix_customfield"] = how_to_fix_custom
        
        # 提取Assignee的comments
        if comments:
            assignee_comments = self._extract_assignee_comments(comments, assignee_info["displayName"])
            info["assignee_comments"] = assignee_comments
            info["all_comments_count"] = len(comments)
            info["assignee_comments_count"] = len(assignee_comments)
        
        return info
    
    def _extract_assignee_comments(self, comments, assignee_name):
        """提取Assignee的comments"""
        assignee_comments = []
        for comment in comments:
            author = comment.get("author", {})
            author_name = author.get("displayName", "")
            
            if author_name.lower() == assignee_name.lower() or assignee_name.lower() in author_name.lower():
                assignee_comments.append({
                    "created": comment.get("created", ""),
                    "body": comment.get("body", ""),
                    "author": author_name
                })
        
        return assignee_comments
    
    def _extract_section(self, text, section_names):
        """从文本中提取特定部分"""
        if not text:
            return ""
        
        for section in section_names:
            pattern = rf"{section}[:：\s]*\n*(.*?)(?=\n\n|\n[A-Z][a-z]+:|$)"
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""

def load_config(config_path=None):
    """加载配置文件"""
    if config_path is None:
        config_path = os.environ.get("COMMIT_CONFIG_PATH", "./config.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 配置文件不存在: {config_path}")
        print("请提供包含JIRA用户名和密码的配置文件")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: 配置文件格式无效: {e}")
        sys.exit(1)

def get_jira_info(jira_input, config):
    """获取JIRA信息"""
    # 初始化JIRA客户端
    jira_config = config.get("jira", {})
    jira_client = JIRAClient(jira_config)
    
    # 判断输入是URL还是issue key
    if jira_input.startswith("http"):
        # 从URL提取issue key
        issue_key = jira_client.extract_issue_key(jira_input)
        if not issue_key:
            print(f"错误: 无法从URL中提取JIRA issue key: {jira_input}")
            return {}
    else:
        # 直接使用作为issue key
        issue_key = jira_input
    
    print(f"处理JIRA issue: {issue_key}")
    
    # 获取issue详细信息
    print("正在获取JIRA issue详细信息...")
    issue_data = jira_client.get_issue_details(issue_key)
    if not issue_data:
        print(f"错误: 无法获取JIRA issue信息: {issue_key}")
        return {}
    
    # 获取comments
    print("正在获取JIRA comments...")
    comments = jira_client.get_comments(issue_key)
    
    # 提取关键信息
    print("正在提取关键信息...")
    jira_info = jira_client.extract_issue_info(issue_data, comments)
    jira_info["comments_count"] = len(comments)
    
    return jira_info

def safe_print(text):
    """安全打印，处理编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 如果遇到编码问题，先编码为UTF-8再解码
        try:
            encoded = text.encode('utf-8', 'ignore').decode('utf-8')
            print(encoded)
        except:
            # 如果还是失败，打印替换版本
            print(text.encode('ascii', 'replace').decode('ascii'))

def print_jira_info(jira_info, output_format="text"):
    """打印JIRA信息"""
    if not jira_info:
        safe_print("错误: 未获取到JIRA信息")
        return
    
    if output_format == "json":
        # JSON格式输出
        safe_print(json.dumps(jira_info, indent=2, ensure_ascii=False))
    else:
        # 文本格式输出
        safe_print("\n" + "="*80)
        safe_print("JIRA信息摘要:")
        safe_print("="*80)
        safe_print(f"Key:           {jira_info.get('key', 'N/A')}")
        safe_print(f"摘要:           {jira_info.get('summary', 'N/A')}")
        safe_print(f"状态:           {jira_info.get('status', 'N/A')}")
        safe_print(f"优先级:         {jira_info.get('priority', 'N/A')}")
        safe_print(f"类型:           {jira_info.get('issue_type', 'N/A')}")
        safe_print(f"创建时间:       {jira_info.get('created', 'N/A')}")
        safe_print(f"更新时间:       {jira_info.get('updated', 'N/A')}")
        
        assignee = jira_info.get("assignee", {})
        safe_print(f"Assignee:      {assignee.get('displayName', 'N/A')} ({assignee.get('emailAddress', 'N/A')})")
        
        reporter = jira_info.get("reporter", {})
        safe_print(f"Reporter:      {reporter.get('displayName', 'N/A')} ({reporter.get('emailAddress', 'N/A')})")
        
        safe_print(f"标签:           {', '.join(jira_info.get('labels', []))}")
        safe_print(f"组件:           {', '.join(jira_info.get('components', []))}")
        safe_print(f"修复版本:       {', '.join(jira_info.get('fix_versions', []))}")
        
        safe_print(f"评论总数:       {jira_info.get('comments_count', 0)}")
        safe_print(f"Assignee评论数: {jira_info.get('assignee_comments_count', 0)}")
        
        root_cause = jira_info.get("root_cause", "")
        if root_cause:
            safe_print(f"\nRoot Cause ({len(root_cause)} 字符):")
            safe_print(root_cause)
        
        how_to_fix = jira_info.get("how_to_fix", "")
        if how_to_fix:
            safe_print(f"\nHow to Fix ({len(how_to_fix)} 字符):")
            safe_print(how_to_fix)
        
        # 显示Assignee的所有comments
        assignee_comments = jira_info.get("assignee_comments", [])
        if assignee_comments:
            safe_print(f"\nAssignee所有评论 ({len(assignee_comments)} 条):")
            for i, comment in enumerate(assignee_comments, 1):
                safe_print(f"\n评论 #{i} ({comment.get('created', 'N/A')}):")
                comment_body = comment.get("body", "")
                safe_print(comment_body)
                safe_print("-" * 40)
        
        safe_print("="*80)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='从JIRA号提取相关信息')
    parser.add_argument('jira_input', help='JIRA issue URL或issue key (如: SWPL-252395)')
    parser.add_argument('--config', '-c', default=None, 
                       help='配置文件路径 (默认: ./config.json 或环境变量 COMMIT_CONFIG_PATH)')
    parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                       help='输出格式: text (文本摘要) 或 json (完整JSON数据)')
    parser.add_argument('--output', '-o', default=None,
                       help='输出文件路径 (如不指定则输出到控制台)')
    
    args = parser.parse_args()
    
    print(f"配置文件: {args.config or '使用默认/环境变量'}")
    print(f"JIRA输入: {args.jira_input}")
    print(f"输出格式: {args.format}")
    
    # 加载配置
    config = load_config(args.config)
    
    # 获取JIRA信息
    jira_info = get_jira_info(args.jira_input, config)
    
    if jira_info:
        # 输出结果
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                if args.format == "json":
                    json.dump(jira_info, f, indent=2, ensure_ascii=False)
                else:
                    # 对于文本格式，需要构建输出字符串
                    import io
                    import sys
                    old_stdout = sys.stdout
                    sys.stdout = io.StringIO()
                    
                    print_jira_info(jira_info, args.format)
                    
                    output_str = sys.stdout.getvalue()
                    sys.stdout = old_stdout
                    
                    f.write(output_str)
            print(f"结果已保存到: {args.output}")
        else:
            print_jira_info(jira_info, args.format)
    else:
        print("未能获取JIRA信息，请检查输入和配置")
        sys.exit(1)

if __name__ == "__main__":
    main()
