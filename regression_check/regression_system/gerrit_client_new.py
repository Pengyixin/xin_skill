#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerrit客户端 - 基于用户写的gerrit_client.py，兼容现有系统
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from requests.auth import HTTPDigestAuth
from pygerrit2.rest import GerritRestAPI

from .config_manager import GerritConfig
from .utils import retry_with_backoff


class GerritChangeStatus(Enum):
    """Gerrit change状态枚举"""
    NEW = "NEW"
    MERGED = "MERGED"
    ABANDONED = "ABANDONED"
    DRAFT = "DRAFT"


@dataclass
class GerritChange:
    """Gerrit change数据结构 - 与现有系统兼容"""
    change_id: str
    project: str
    branch: str
    subject: str
    status: str
    created: str
    updated: str
    submitted: Optional[str]
    owner: Dict[str, Any]
    labels: Dict[str, Any]
    current_revision: str
    revisions: Dict[str, Any]
    
    def is_merged(self) -> bool:
        """检查change是否已合并"""
        return self.status == GerritChangeStatus.MERGED.value
    
    def get_merge_time(self) -> Optional[str]:
        """获取合并时间"""
        return self.submitted
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "change_id": self.change_id,
            "project": self.project,
            "branch": self.branch,
            "subject": self.subject,
            "status": self.status,
            "created": self.created,
            "updated": self.updated,
            "submitted": self.submitted,
            "is_merged": self.is_merged(),
            "owner_name": self.owner.get("name") if self.owner else None,
            "owner_email": self.owner.get("email") if self.owner else None
        }


class GerritFetcher:
    """
    基于用户写的GerritFetcher类
    Responsible for fetching commit information and patch diffs from Gerrit.
    """

    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize GerritFetcher.

        Args:
            base_url: Base URL of the Gerrit server.
            username: Gerrit username.
            password: Gerrit password.
        """
        self.base_url = base_url
        self.auth = HTTPDigestAuth(username, password)
        self.rest = GerritRestAPI(url=base_url, auth=self.auth)

    @staticmethod
    def extract_change_id(url: str) -> str:
        """
        Extract change-id from Gerrit URL.

        Args:
            url: Gerrit change URL.

        Returns:
            Change ID string.
        """
        match = re.search(r"/c/(\d+)", url)
        if not match:
            raise ValueError(f"Cannot extract change-id from URL: {url}")
        return match.group(1)

    @staticmethod
    def extract_diff_content(patch_text: str) -> str:
        """
        Extract diff content from patch text.

        Args:
            patch_text: Full patch text.

        Returns:
            Diff content string.
        """
        diff_start_marker = 'diff --git'
        start_index = patch_text.find(diff_start_marker)
        if start_index == -1:
            return "Diff content not found"
        return patch_text[start_index:]

    @staticmethod
    def replace_cf_cb_tags(text: str) -> str:
        """
        Replace CF/CB tags with [X] to avoid confusion.

        Args:
            text: Input text.

        Returns:
            Text with tags replaced.
        """
        return re.sub(r'\b(CF|CB)\d+\b', '[X]', text)

    def fetch_commit_and_diff(self, gerrit_url: str) -> Tuple[str, str]:
        """
        Fetch commit message and diff content.
        
        Args:
            gerrit_url: Gerrit change URL.
            
        Returns:
            Tuple[commit_message, diff_content]
        """
        change_id = self.extract_change_id(gerrit_url)
        commit_info = self.rest.get(f"/changes/{change_id}/revisions/current/commit")
        commit_message = self.replace_cf_cb_tags(commit_info['message'])

        patch_diff = self.rest.get(f"/changes/{change_id}/revisions/current/patch")
        diff_content = self.extract_diff_content(patch_diff)

        return commit_message, diff_content


class GerritClient:
    """
    Gerrit客户端 - 兼容现有系统，但使用GerritFetcher实现
    """
    
    def __init__(self, config: GerritConfig):
        """
        初始化Gerrit客户端
        
        Args:
            config: Gerrit配置
        """
        self.config = config
        self.base_url = config.base_url.rstrip('/')
        
        # 使用用户写的GerritFetcher
        self.fetcher = GerritFetcher(
            base_url=self.base_url,
            username=config.username,
            password=config.password
        )
        
        # 缓存change信息
        self._change_cache = {}
        
        print(f"✅ Gerrit客户端初始化成功 (使用GerritFetcher): {self.base_url}")
    
    @retry_with_backoff
    def _get_change_info(self, change_id: str) -> Optional[Dict[str, Any]]:
        """
        获取change信息
        
        Args:
            change_id: Gerrit change ID
        
        Returns:
            change信息字典，如果获取失败则返回None
        """
        # 检查缓存
        if change_id in self._change_cache:
            return self._change_cache[change_id]
        
        try:
            # 使用GerritRestAPI获取change信息
            change_info = self.fetcher.rest.get(f"/changes/{change_id}")
            self._change_cache[change_id] = change_info
            return change_info
        except Exception as e:
            print(f"❌ 获取change信息失败: {change_id}, 错误: {e}")
            return None
    
    def get_change_by_id(self, change_id: str) -> Optional[GerritChange]:
        """
        通过change ID获取change信息
        
        Args:
            change_id: Gerrit change ID
        
        Returns:
            GerritChange对象，如果获取失败则返回None
        """
        print(f"获取Gerrit change: {change_id}")
        
        change_info = self._get_change_info(change_id)
        if not change_info:
            return None
        
        # 转换为GerritChange对象
        try:
            change = GerritChange(
                change_id=change_info.get("id", ""),
                project=change_info.get("project", ""),
                branch=change_info.get("branch", ""),
                subject=change_info.get("subject", ""),
                status=change_info.get("status", ""),
                created=change_info.get("created", ""),
                updated=change_info.get("updated", ""),
                submitted=change_info.get("submitted"),
                owner=change_info.get("owner", {}),
                labels=change_info.get("labels", {}),
                current_revision=change_info.get("current_revision", ""),
                revisions=change_info.get("revisions", {})
            )
            
            print(f"✅ 成功获取change: {change.change_id} - {change.subject[:50]}...")
            print(f"  状态: {change.status}, 是否合并: {change.is_merged()}")
            
            return change
        except Exception as e:
            print(f"❌ 解析change数据失败: {e}")
            return None
    
    def get_change_by_url(self, url: str) -> Optional[GerritChange]:
        """
        通过URL获取change信息
        
        Args:
            url: Gerrit change URL
        
        Returns:
            GerritChange对象，如果获取失败则返回None
        """
        print(f"通过URL获取Gerrit change: {url}")
        
        try:
            change_id = self.fetcher.extract_change_id(url)
        except ValueError as e:
            print(f"❌ 无法从URL提取change ID: {e}")
            return None
        
        return self.get_change_by_id(change_id)
    
    def is_change_merged(self, change_identifier: str) -> bool:
        """
        检查change是否已合并
        
        Args:
            change_identifier: change ID或URL
        
        Returns:
            是否已合并
        """
        # 判断输入是URL还是change ID
        if "scgit.amlogic.com" in change_identifier or change_identifier.startswith("http"):
            change = self.get_change_by_url(change_identifier)
        else:
            change = self.get_change_by_id(change_identifier)
        
        if not change:
            return False
        
        return change.is_merged()
    
    def get_change_status(self, change_identifier: str) -> Optional[str]:
        """
        获取change状态
        
        Args:
            change_identifier: change ID或URL
        
        Returns:
            状态字符串，如果获取失败则返回None
        """
        # 判断输入是URL还是change ID
        if "scgit.amlogic.com" in change_identifier or change_identifier.startswith("http"):
            change = self.get_change_by_url(change_identifier)
        else:
            change = self.get_change_by_id(change_identifier)
        
        if not change:
            return None
        
        return change.status
    
    def search_changes(self, query: str, max_results: int = 50) -> List[GerritChange]:
        """
        搜索changes
        
        Args:
            query: 搜索查询字符串
            max_results: 最大结果数量
        
        Returns:
            GerritChange列表
        """
        print(f"搜索Gerrit changes: {query}")
        
        changes = []
        
        try:
            # 使用GerritRestAPI搜索
            search_results = self.fetcher.rest.get(f"/changes/?q={query}&n={max_results}")
            
            if not isinstance(search_results, list):
                print(f"❌ 搜索响应格式异常: {type(search_results)}")
                return changes
            
            for change_data in search_results:
                try:
                    change = GerritChange(
                        change_id=change_data.get("id", ""),
                        project=change_data.get("project", ""),
                        branch=change_data.get("branch", ""),
                        subject=change_data.get("subject", ""),
                        status=change_data.get("status", ""),
                        created=change_data.get("created", ""),
                        updated=change_data.get("updated", ""),
                        submitted=change_data.get("submitted"),
                        owner=change_data.get("owner", {}),
                        labels=change_data.get("labels", {}),
                        current_revision=change_data.get("current_revision", ""),
                        revisions=change_data.get("revisions", {})
                    )
                    changes.append(change)
                except Exception as e:
                    print(f"❌ 解析change数据失败: {e}")
            
            print(f"✅ 搜索完成，找到 {len(changes)} 个changes")
            
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
        
        return changes
    
    def search_changes_by_jira(self, jira_key: str) -> List[GerritChange]:
        """
        搜索与JIRA关联的changes
        
        Args:
            jira_key: JIRA issue key
        
        Returns:
            关联的GerritChange列表
        """
        # Gerrit中通常通过commit message或topic关联JIRA
        queries = [
            f'message:{jira_key}',
            f'topic:{jira_key}',
            f'bug:{jira_key}'
        ]
        
        all_changes = []
        for query in queries:
            changes = self.search_changes(query, max_results=20)
            all_changes.extend(changes)
        
        # 去重
        unique_changes = []
        seen_ids = set()
        for change in all_changes:
            if change.change_id not in seen_ids:
                seen_ids.add(change.change_id)
                unique_changes.append(change)
        
        print(f"找到 {len(unique_changes)} 个与JIRA {jira_key} 关联的changes")
        return unique_changes
    
    def batch_check_merged(self, change_urls: List[str]) -> Dict[str, bool]:
        """
        批量检查changes是否已合并
        
        Args:
            change_urls: change URL列表
        
        Returns:
            字典：change URL -> 是否已合并
        """
        results = {}
        
        print(f"批量检查 {len(change_urls)} 个changes的合并状态")
        
        for i, url in enumerate(change_urls, 1):
            print(f"  检查 {i}/{len(change_urls)}: {url}")
            is_merged = self.is_change_merged(url)
            results[url] = is_merged
        
        # 统计
        merged_count = sum(1 for is_merged in results.values() if is_merged)
        print(f"✅ 批量检查完成: {merged_count}/{len(change_urls)} 个已合并")
        
        return results
    
    def fetch_commit_and_diff(self, gerrit_url: str) -> Tuple[str, str]:
        """
        获取commit消息和diff内容（用户写的功能）
        
        Args:
            gerrit_url: Gerrit change URL
        
        Returns:
            Tuple[commit_message, diff_content]
        """
        return self.fetcher.fetch_commit_and_diff(gerrit_url)


if __name__ == "__main__":
    # 测试Gerrit客户端
    from config_manager import ConfigManager
    
    print("测试Gerrit客户端...")
    config_manager = ConfigManager()
    gerrit_config = config_manager.get_gerrit_config()
    
    client = GerritClient(gerrit_config)
    
    # 测试获取change
    test_url = "https://scgit.amlogic.com/#/c/503681/"
    change = client.get_change_by_url(test_url)
    
    if change:
        print(f"\nChange信息:")
        print(f"  ID: {change.change_id}")
        print(f"  项目: {change.project}")
        print(f"  分支: {change.branch}")
        print(f"  标题: {change.subject[:50]}...")
        print(f"  状态: {change.status}")
        print(f"  是否合并: {change.is_merged()}")
        print(f"  创建时间: {change.created}")
        print(f"  合并时间: {change.submitted}")
    
    # 测试批量检查
    test_urls = [
        "https://scgit.amlogic.com/#/c/503681/",
        "https://scgit.amlogic.com/#/c/123456/"  # 可能不存在的change
    ]
    
    results = client.batch_check_merged(test_urls)
    print(f"\n批量检查结果:")
    for url, is_merged in results.items():
        print(f"  {url} -> {'已合并' if is_merged else '未合并'}")
