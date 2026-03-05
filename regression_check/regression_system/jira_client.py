# -*- coding: utf-8 -*-
"""
JIRA客户端
用于查询JIRA issue信息和检测回归状态
"""

import requests
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .config_manager import JiraConfig
from .utils import extract_jira_key, retry_with_backoff, parse_custom_field, safe_get


class JiraStatus(Enum):
    """JIRA状态枚举"""
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    VERIFIED = "Verified"
    REOPENED = "Reopened"


class RegressionStatus(Enum):
    """回归状态枚举"""
    NEEDS_REGRESSION = "需要回归"  # customfield_11705 == "Confirmed Yes"
    REGRESSED = "已回归"           # 有关联gerrit且已合并
    NOT_REGRESSED = "未回归"       # 需要回归但没有gerrit或gerrit未合并
    NOT_REQUIRED = "不需要回归"     # customfield_11705 != "Confirmed Yes"


@dataclass
class JiraIssue:
    """JIRA issue数据结构"""
    key: str
    summary: str
    status: str
    issue_type: str
    priority: str
    assignee: Optional[str]
    reporter: Optional[str]
    created: str
    updated: str
    verified_date: str
    description: str
    labels: List[str]
    components: List[str]
    custom_fields: Dict[str, Any]
    comments: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
    
    # 回归相关字段
    needs_regression: bool = False
    regression_status: Optional[RegressionStatus] = None
    related_gerrits: List[str] = None
    clone_jiras: List[str] = None
    
    def __post_init__(self):
        """初始化后处理，确保列表不为None"""
        if self.related_gerrits is None:
            self.related_gerrits = []
        if self.clone_jiras is None:
            self.clone_jiras = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "key": self.key,
            "summary": self.summary,
            "status": self.status,
            "issue_type": self.issue_type,
            "priority": self.priority,
            "assignee": self.assignee,
            "reporter": self.reporter,
            "created": self.created,
            "updated": self.updated,
            "description": self.description[:200] if self.description else "",  # 限制长度
            "labels": self.labels,
            "components": self.components,
            "needs_regression": self.needs_regression,
            "regression_status": self.regression_status.value if self.regression_status else None,
            "related_gerrits": self.related_gerrits,
            "clone_jiras": self.clone_jiras,
            "has_comments": len(self.comments) > 0,
            "comment_count": len(self.comments)
        }


class JIRAClient:
    """JIRA客户端"""
    
    def __init__(self, config: JiraConfig):
        """
        初始化JIRA客户端
        
        Args:
            config: JIRA配置
        """
        self.config = config
        self.base_url = config.base_url.rstrip('/')
        self.session = requests.Session()
        
        if config.username and config.password:
            self.session.auth = (config.username, config.password)
        
        # 设置请求头
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # 自定义字段映射
        self.custom_field_mapping = {
            "needs_regression": "customfield_11705",  # 是否需要回归公版
            "clone_jira": "customfield_xxxxx",  # clone的jira字段（需要确认）
        }
        
        print(f"✅ JIRA客户端初始化成功: {self.base_url}")
    
    @retry_with_backoff
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        发送HTTP请求到JIRA API
        
        Args:
            method: HTTP方法
            endpoint: API端点
            **kwargs: 其他请求参数
        
        Returns:
            响应数据，如果失败则返回None
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            if response.status_code == 204:  # No Content
                return None
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ JIRA API请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"响应状态码: {e.response.status_code}")
                print(f"响应内容: {e.response.text[:200]}")
            return None
    
    def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        """
        获取JIRA issue详细信息
        
        Args:
            issue_key: JIRA issue key（如SWPL-252395）
        
        Returns:
            JiraIssue对象，如果获取失败则返回None
        """
        print(f"获取JIRA issue: {issue_key}")
        
        # 获取issue基本信息
        issue_data = self._make_request("GET", f"/rest/api/2/issue/{issue_key}")
        if not issue_data:
            print(f"❌ 无法获取issue: {issue_key}")
            return None
        
        # 获取comments
        comments_data = self._make_request("GET", f"/rest/api/2/issue/{issue_key}/comment")
        comments = comments_data.get("comments", []) if comments_data else []
        
        # 获取links（可能需要单独的API）
        # links_data = self._make_request("GET", f"/rest/api/2/issue/{issue_key}/remotelink")
        # links = links_data if links_data else []
        links = []  # 暂时留空
        
        # 解析issue数据
        fields = issue_data.get("fields", {})
        
        # 提取assignee信息
        assignee_data = fields.get("assignee", {})
        assignee = assignee_data.get("displayName") if assignee_data else None
        
        # 提取reporter信息
        reporter_data = fields.get("reporter", {})
        reporter = reporter_data.get("displayName") if reporter_data else None
        
        # 提取verified日期（当状态为Verified或Closed时的日期）
        resolution_date = fields.get("resolutiondate", "")
        status_change_date = fields.get("statuschangedate", "")
        verified_date = resolution_date or status_change_date or ""
        
        # 提取components
        components_data = fields.get("components", [])
        components = [c.get("name", "") for c in components_data if c.get("name")]
        
        # 创建JiraIssue对象
        issue = JiraIssue(
            key=issue_data.get("key", ""),
            summary=fields.get("summary", ""),
            status=fields.get("status", {}).get("name", ""),
            issue_type=fields.get("issuetype", {}).get("name", ""),
            priority=fields.get("priority", {}).get("name", ""),
            assignee=assignee,
            reporter=reporter,
            created=fields.get("created", ""),
            updated=fields.get("updated", ""),
            verified_date=verified_date,
            description=fields.get("description", ""),
            labels=fields.get("labels", []),
            components=components,
            custom_fields=fields,  # 保存原始字段以便后续查询自定义字段
            comments=comments,
            links=links
        )
        
        # 检查是否需要回归公版
        self._check_regression_status(issue)
        
        # 提取关联的gerrit链接
        self._extract_related_gerrits(issue)
        
        # 提取clone的jira
        self._extract_clone_jiras(issue)
        
        print(f"✅ 成功获取issue: {issue.key} - {issue.summary[:50]}...")
        return issue
    
    def _check_regression_status(self, issue: JiraIssue) -> None:
        """
        检查issue是否需要回归公版
        
        Args:
            issue: JiraIssue对象
        """
        # 检查customfield_11705字段
        needs_regression_field = parse_custom_field(issue.custom_fields, "11705")
        print(f'pyx {needs_regression_field}')
        if needs_regression_field and 'value' in needs_regression_field:
            field_value = needs_regression_field['value']
            print(f'pyx222 {field_value}')
            if field_value == "Confirmed Yes":
                issue.needs_regression = True
                issue.regression_status = RegressionStatus.NEEDS_REGRESSION
                print(f"  ⚠️  {issue.key} 需要回归公版 (customfield_11705=Confirmed Yes)")
            else:
                issue.needs_regression = False
                issue.regression_status = RegressionStatus.NOT_REQUIRED
                print(f"  ✓ {issue.key} 不需要回归公版")
        else:
            issue.needs_regression = False
            issue.regression_status = RegressionStatus.NOT_REQUIRED
            print(f"  ✓ {issue.key} 不需要回归公版 (customfield_11705未找到)")
    
    def _extract_related_gerrits(self, issue: JiraIssue) -> None:
        """
        从issue中提取关联的gerrit链接
        
        Args:
            issue: JiraIssue对象
        """
        gerrit_urls = []
        
        # 从description中提取
        if issue.description:
            # 匹配Gerrit URL模式
            patterns = [
                r'https?://scgit\.amlogic\.com/[^\s<>"\'()]+',
                r'gerrit[^\s<>"\'()]+',
                r'/#/c/\d+/',
                r'change-id:[^\s]+'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, issue.description, re.IGNORECASE)
                for match in matches:
                    url = match.group(0)
                    if "scgit.amlogic.com" in url:
                        gerrit_urls.append(url)
        
        # 从comments中提取
        for comment in issue.comments:
            body = comment.get("body", "")
            if body:
                # 匹配Gerrit URL模式
                matches = re.finditer(r'https?://scgit\.amlogic\.com/[^\s<>"\'()]+', body)
                for match in matches:
                    url = match.group(0)
                    if url not in gerrit_urls:
                        gerrit_urls.append(url)
        
        # 去重
        issue.related_gerrits = list(set(gerrit_urls))
        
        if issue.related_gerrits:
            print(f"  🔗 {issue.key} 找到 {len(issue.related_gerrits)} 个关联gerrit")
            for gerrit in issue.related_gerrits[:3]:  # 只显示前3个
                print(f"    - {gerrit}")
    
    def _extract_clone_jiras(self, issue: JiraIssue) -> None:
        """
        提取clone的jira
        
        Args:
            issue: JiraIssue对象
        """
        clone_jiras = []
        
        # 方法1: 检查issue links (Cloners类型)
        issue_links = issue.custom_fields.get("issuelinks", [])
        for link in issue_links:
            link_type = link.get("type", {}).get("name", "").lower()
            if "clone" in link_type or "duplicate" in link_type:
                inward = link.get("inwardIssue", {})
                outward = link.get("outwardIssue", {})
                #print(f'ppyyxx link_type: {link_type}, inward: {inward}, outward: {outward}')
                if inward:
                    inward_key = inward.get("key", "")
                    if inward_key and inward_key != issue.key:
                        clone_jiras.append(inward_key)
                '''
                if outward:
                    outward_key = outward.get("key", "")
                    if outward_key and outward_key != issue.key:
                        clone_jiras.append(outward_key)
                '''
        # 方法2: 检查自定义字段
        for key, value in issue.custom_fields.items():
            if key.startswith("customfield_"):
                if isinstance(value, dict):
                    if "value" in value:
                        val_str = str(value["value"]).lower()
                        if "clone" in val_str or "复制" in val_str or "克隆" in val_str:
                            # 尝试提取JIRA key
                            jira_keys = re.findall(r'[A-Z]+-\d+', str(value))
                            clone_jiras.extend(jira_keys)
                elif isinstance(value, str):
                    if "clone" in value.lower() or "复制" in value.lower() or "克隆" in value.lower():
                        jira_keys = re.findall(r'[A-Z]+-\d+', value)
                        clone_jiras.extend(jira_keys)
        
        # 方法3: 从description中提取
        if issue.description:
            matches = re.finditer(r'[A-Z]+-\d+', issue.description)
            for match in matches:
                jira_key = match.group(0)
                if jira_key != issue.key and jira_key not in clone_jiras:
                    # 检查是否包含"clone"、"复制"等关键词
                    context = issue.description[max(0, match.start()-50):min(len(issue.description), match.end()+50)]
                    clone_keywords = ["clone", "复制", "克隆", "copy", "duplicate", "cloned from", "cloned to"]
                    if any(keyword.lower() in context.lower() for keyword in clone_keywords):
                        clone_jiras.append(jira_key)
        
        # 方法4: 从comments中提取
        for comment in issue.comments:
            body = comment.get("body", "")
            if body:
                matches = re.finditer(r'[A-Z]+-\d+', body)
                for match in matches:
                    jira_key = match.group(0)
                    if jira_key != issue.key and jira_key not in clone_jiras:
                        context = body[max(0, match.start()-30):min(len(body), match.end()+30)]
                        clone_keywords = ["clone", "复制", "克隆", "copy", "duplicate", "cloned from", "cloned to"]
                        if any(keyword.lower() in context.lower() for keyword in clone_keywords):
                            clone_jiras.append(jira_key)
        
        # 方法5: 检查summary (有些issue的summary会包含"CLONE -")
        if issue.summary and "clone" in issue.summary.lower():
            matches = re.findall(r'[A-Z]+-\d+', issue.summary)
            clone_jiras.extend(matches)
        
        # 去重
        issue.clone_jiras = list(set([j for j in clone_jiras if j and j != issue.key]))
        
        if issue.clone_jiras:
            print(f"  📋 {issue.key} 找到 {len(issue.clone_jiras)} 个clone jira")
            for clone in issue.clone_jiras:
                print(f"    - {clone}")
    
    def search_issues(self, jql: str, max_results: int = 100) -> List[JiraIssue]:
        """
        使用JQL搜索issues
        
        Args:
            jql: JIRA查询语言
            max_results: 最大结果数量
        
        Returns:
            JiraIssue列表
        """
        print(f"搜索JIRA issues: {jql}")
        
        issues = []
        start_at = 0
        max_results = min(max_results, 1000)  # 限制最大结果
        
        while len(issues) < max_results:
            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": min(50, max_results - len(issues)),  # 每次最多50个
                "fields": "summary,status,issuetype,priority,assignee,reporter,created,updated,description,labels,components"
            }
            
            search_data = self._make_request("GET", "/rest/api/2/search", params=params)
            if not search_data:
                break
            
            issue_list = search_data.get("issues", [])
            if not issue_list:
                break
            
            for issue_data in issue_list:
                issue_key = issue_data.get("key")
                if issue_key:
                    # 获取完整issue信息
                    issue = self.get_issue(issue_key)
                    if issue:
                        issues.append(issue)
                
                if len(issues) >= max_results:
                    break
            
            start_at += len(issue_list)
            
            # 检查是否还有更多结果
            total = search_data.get("total", 0)
            if start_at >= total or len(issues) >= max_results:
                break
        
        print(f"✅ 搜索完成，找到 {len(issues)} 个issues")
        return issues
    
    def search_verify_close_issues(self, project: str = None, days: int = 30, max_results: int = 1000) -> List[JiraIssue]:
        """
        搜索verify或close状态的issues
        
        Args:
            project: 项目key（如SWPL），如果为None则搜索所有项目
            days: 搜索最近多少天的issues
            max_results: 最大搜索结果数
        
        Returns:
            JiraIssue列表
        """
        status_condition = 'status in ("Verified", "Closed", "Resolved")'
        project_condition = f'project = "{project}"' if project else ""
        date_condition = f'updated >= -{days}d' if days > 0 else ""
        
        conditions = [status_condition]
        if project_condition:
            conditions.append(project_condition)
        if date_condition:
            conditions.append(date_condition)
        
        jql = " AND ".join(conditions)
        jql += " ORDER BY updated DESC"
        
        print(f"搜索verify/close状态的issues: {jql}")
        return self.search_issues(jql, max_results=max_results)
    
    def search_by_labels(self, labels: List[str], project: str = None, 
                         statuses: List[str] = None, days: int = 0, max_results: int = 1000) -> List[JiraIssue]:
        """
        根据label搜索issues
        
        Args:
            labels: label列表，如["DECODER-CORE-20260126"]
            project: 项目key（如SWPL），如果为None则搜索所有项目
            statuses: 状态列表，如["Verified", "Closed", "Resolved"]，如果为None则搜索所有状态
            days: 搜索最近多少天的issues，0表示不限制
            max_results: 最大搜索结果数
        
        Returns:
            JiraIssue列表
        """
        # 构建label条件
        label_conditions = []
        for label in labels:
            # 处理label中的特殊字符
            clean_label = label.replace('"', '\\"').replace("'", "\\'")
            label_conditions.append(f'labels = "{clean_label}"')
        
        if len(labels) > 1:
            label_condition = f'({" OR ".join(label_conditions)})'
        else:
            label_condition = label_conditions[0] if label_conditions else ""
        
        # 其他条件
        project_condition = f'project = "{project}"' if project else ""
        
        status_condition = ""
        if statuses:
            status_list = ', '.join([f'"{status}"' for status in statuses])
            status_condition = f'status in ({status_list})'
        
        date_condition = f'updated >= -{days}d' if days > 0 else ""
        
        # 组合所有条件
        conditions = []
        if label_condition:
            conditions.append(label_condition)
        if project_condition:
            conditions.append(project_condition)
        if status_condition:
            conditions.append(status_condition)
        if date_condition:
            conditions.append(date_condition)
        
        if not conditions:
            jql = ""  # 如果没有条件，搜索所有issues
        else:
            jql = " AND ".join(conditions)
        
        jql += " ORDER BY updated DESC"
        
        print(f"按label搜索issues: {jql}")
        return self.search_issues(jql, max_results=max_results)
    
    def update_regression_status(self, issue: JiraIssue, gerrit_merged: bool) -> None:
        """
        更新issue的回归状态
        
        Args:
            issue: JiraIssue对象
            gerrit_merged: 关联的gerrit是否已合并
        """
        if not issue.needs_regression:
            issue.regression_status = RegressionStatus.NOT_REQUIRED
            return
        
        if issue.related_gerrits and gerrit_merged:
            issue.regression_status = RegressionStatus.REGRESSED
            print(f"  ✅ {issue.key} 已回归（gerrit已合并）")
        else:
            issue.regression_status = RegressionStatus.NOT_REGRESSED
            print(f"  ❌ {issue.key} 未回归（需要回归但无gerrit或gerrit未合并）")


if __name__ == "__main__":
    # 测试JIRA客户端
    from config_manager import ConfigManager
    
    print("测试JIRA客户端...")
    config_manager = ConfigManager()
    jira_config = config_manager.get_jira_config()
    
    client = JIRAClient(jira_config)
    
    # 测试搜索功能
    test_jql = 'project = SWPL AND status in ("Verified", "Closed") AND updated >= -7d'
    issues = client.search_issues(test_jql, max_results=5)
    
    print(f"\n测试结果: 找到 {len(issues)} 个issues")
    for issue in issues[:3]:  # 只显示前3个
        print(f"\nIssue: {issue.key}")
        print(f"  摘要: {issue.summary[:50]}...")
        print(f"  状态: {issue.status}")
        print(f"  是否需要回归: {issue.needs_regression}")
        print(f"  回归状态: {issue.regression_status.value if issue.regression_status else 'N/A'}")
        print(f"  关联gerrit数量: {len(issue.related_gerrits)}")
        print(f"  clone jira数量: {len(issue.clone_jiras)}")
