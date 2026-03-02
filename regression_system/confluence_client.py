#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Confluence客户端
用于访问Confluence页面获取回归分支信息
"""

import requests
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass
class BranchRule:
    """分支规则"""
    project: str
    branch_pattern: str
    description: str = ""
    
    def match(self, branch: str) -> bool:
        """检查分支是否匹配规则"""
        # 简单的通配符匹配：*表示任意字符
        pattern = self.branch_pattern
        if '*' in pattern:
            import re
            # 将*转换为正则表达式的.*
            regex_pattern = pattern.replace('*', '.*')
            return bool(re.match(regex_pattern, branch))
        else:
            return branch == pattern


class ConfluenceClient:
    """Confluence客户端"""
    
    def __init__(self, base_url: str = "https://confluence.amlogic.com", 
                 username: str = None, password: str = None):
        """
        初始化Confluence客户端
        
        Args:
            base_url: Confluence基础URL
            username: 用户名
            password: 密码
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        
        # 缓存页面内容
        self.page_cache: Dict[str, str] = {}
        
        print(f"✅ Confluence客户端初始化成功: {self.base_url}")
    
    def get_page_content(self, page_id: str) -> Optional[str]:
        """
        获取Confluence页面内容
        
        Args:
            page_id: 页面ID
        
        Returns:
            页面内容，如果获取失败则返回None
        """
        # 检查缓存
        if page_id in self.page_cache:
            print(f"  从缓存获取Confluence页面: {page_id}")
            return self.page_cache[page_id]
        
        try:
            # API端点：/rest/api/content/{page_id}?expand=body.view
            url = f"{self.base_url}/rest/api/content/{page_id}"
            params = {
                "expand": "body.view"
            }
            
            # 检测认证头，如果是OAuth则尝试不同的认证方式
            headers = {}
            
            # 尝试Basic认证
            if self.username and self.password:
                response = requests.get(
                    url,
                    params=params,
                    auth=(self.username, self.password),
                    timeout=30
                )
                
                # 检查响应头
                if 'WWW-Authenticate' in response.headers:
                    auth_header = response.headers['WWW-Authenticate']
                    if 'OAuth' in auth_header or 'Bearer' in auth_header:
                        print(f"   ⚠️  Confluence要求OAuth认证 (检测到: {auth_header})")
                        print(f"   尝试使用Bearer token认证...")
                        
                        # 尝试使用密码作为Bearer token
                        headers['Authorization'] = f"Bearer {self.password}"
                        response = requests.get(
                            url,
                            params=params,
                            headers=headers,
                            timeout=30
                        )
            else:
                response = requests.get(
                    url,
                    params=params,
                    timeout=30
                )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("body", {}).get("view", {}).get("value", "")
                self.page_cache[page_id] = content
                print(f"✅ 成功获取Confluence页面: {page_id}")
                return content
            else:
                print(f"❌ 获取Confluence页面失败: {page_id}, 状态码: {response.status_code}")
                if response.status_code == 401:
                    print(f"   认证失败，响应头: {dict(response.headers)}")
                return None
                
        except Exception as e:
            print(f"❌ 获取Confluence页面时发生错误: {e}")
            return None
    
    def parse_branch_rules_page(self, page_content: str) -> List[BranchRule]:
        """
        解析分支规则页面
        
        Args:
            page_content: 页面内容
        
        Returns:
            分支规则列表
        """
        rules = []
        
        # 先清理HTML标签（如果存在）
        import re
        
        # 移除常见的HTML标签
        clean_content = re.sub(r'<[^>]+>', ' ', page_content)
        # 移除多个空格和换行符
        clean_content = re.sub(r'\s+', ' ', clean_content)
        
        print(f"  清理后内容长度: {len(clean_content)} 字符")
        
        # 用户提供的格式示例:
        # Project: platform/hardware/amlogic/media_modules Branch: amlogic-main-dev
        # Project: platform/hardware/amlogic/media_modules Branch: amlogic-5.15-dev
        # Project: platform/hardware/amlogic/C2 Branch: main
        
        # 解析格式: Project: (项目路径) Branch: (分支名称)
        pattern = r'Project:\s*([^\n\r]+?)\s+Branch:\s*([^\n\r]+?)(?:\s|$)'
        matches = re.findall(pattern, clean_content, re.IGNORECASE)
        
        print(f"  找到 {len(matches)} 个Project: Branch格式匹配")
        
        for project, branch_pattern in matches:
            # 清理项目名称（去掉前后空格）
            project = project.strip()
            branch_pattern = branch_pattern.strip()
            
            # 提取项目简写（最后一个斜杠后的部分）
            project_short = project
            if '/' in project:
                project_short = project.split('/')[-1]
            
            # 创建规则
            rule = BranchRule(
                project=project_short,  # 使用简写，如media_modules, C2
                branch_pattern=branch_pattern,
                description=project     # 完整项目路径作为描述
            )
            rules.append(rule)
            
            print(f"    解析到: 项目={project_short} ({project}), 分支={branch_pattern}")
        
        # 如果没有找到Project: Branch格式，尝试其他格式
        if not rules:
            print(f"  未找到Project: Branch格式，尝试其他格式...")
            
            # 尝试表格格式
            lines = clean_content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('|') and line.endswith('|'):
                    cells = [cell.strip() for cell in line[1:-1].split('|')]
                    
                    if len(cells) >= 2 and cells[0] and not cells[0].startswith('--'):
                        if cells[0].lower() in ['项目', 'project', '项目名']:
                            continue
                        
                        project = cells[0]
                        branch_pattern = cells[1] if len(cells) > 1 else "*"
                        description = cells[2] if len(cells) > 2 else ""
                        
                        rule = BranchRule(
                            project=project,
                            branch_pattern=branch_pattern,
                            description=description
                        )
                        rules.append(rule)
        
        print(f"  总共解析到 {len(rules)} 个分支规则")
        return rules
    
    def get_branch_rules(self, page_id: str) -> List[BranchRule]:
        """
        获取分支规则
        
        Args:
            page_id: 页面ID
        
        Returns:
            分支规则列表
        """
        content = self.get_page_content(page_id)
        if not content:
            return []
        
        return self.parse_branch_rules_page(content)
    
    def is_regression_branch(self, project: str, branch: str, rules: List[BranchRule]) -> bool:
        """
        检查是否为回归分支（用户要求：不使用智能匹配）
        
        Args:
            project: 项目名称 (来自gerrit，如platform/hardware/amlogic/media_modules)
            branch: 分支名称
            rules: 分支规则列表 (来自Confluence，项目简写如media_modules，完整描述如platform/hardware/amlogic/media_modules)
        
        Returns:
            True如果是回归分支，False如果不是
        """
        if not branch or not project:
            return False
        
        # 用户要求：不使用智能映射，直接比较gerrit项目名称和Confluence规则
        print(f"    🔍 直接比较: gerrit项目='{project}', 分支='{branch}'")
        
        # 方法1：检查gerrit项目名称是否在规则描述中（规则描述是完整路径）
        for rule in rules:
            if project.lower() in rule.description.lower() or rule.description.lower() in project.lower():
                if rule.match(branch):
                    print(f"    ✅ 直接匹配成功: gerrit项目'{project}'匹配规则描述'{rule.description}', 分支'{branch}'匹配'{rule.branch_pattern}'")
                    return True
        
        # 方法2：检查gerrit项目名称的最后部分是否等于规则项目名称
        # gerrit项目名称: platform/hardware/amlogic/media_modules
        # 规则项目名称: media_modules
        if '/' in project:
            project_short = project.split('/')[-1]
            for rule in rules:
                if project_short.lower() == rule.project.lower():
                    if rule.match(branch):
                        print(f"    ✅ 简写匹配成功: gerrit项目简写'{project_short}'等于规则项目'{rule.project}', 分支'{branch}'匹配'{rule.branch_pattern}'")
                        return True
        
        # 方法3：如果规则项目名称是gerrit项目名称的一部分
        for rule in rules:
            if rule.project.lower() in project.lower():
                if rule.match(branch):
                    print(f"    ✅ 包含匹配成功: 规则项目'{rule.project}'在gerrit项目'{project}'中, 分支'{branch}'匹配'{rule.branch_pattern}'")
                    return True
        
        print(f"    ❌ 直接匹配失败: gerrit项目'{project}'/分支'{branch}' 不是回归分支")
        print(f"      可用规则: {[(r.project, r.branch_pattern, r.description[:30]+'...' if len(r.description) > 30 else r.description) for r in rules]}")
        return False
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.page_cache.clear()
        print("✅ Confluence缓存已清空")


class BranchManager:
    """分支管理器"""
    
    def __init__(self, config_manager=None):
        """
        初始化分支管理器
        
        Args:
            config_manager: 配置管理器
        """
        if config_manager is None:
            from .config_manager import ConfigManager
            config_manager = ConfigManager()
        
        self.config_manager = config_manager
        self.confluence_config = config_manager.get_confluence_config()
        
        # 初始化Confluence客户端
        self.confluence_client = ConfluenceClient(
            base_url="https://confluence.amlogic.com",
            username=self.confluence_config.username,
            password=self.confluence_config.password
        )
        
        # 分支规则缓存
        self.branch_rules: Dict[str, List[BranchRule]] = {}
        self._load_rules()
        
        print("✅ 分支管理器初始化成功")
    
    def _load_rules(self) -> None:
        """加载分支规则"""
        pages = self.confluence_config.pages if hasattr(self.confluence_config, 'pages') else {}
        
        # 从branches页面加载分支规则
        branches_page_id = pages.get("branches")
        if branches_page_id:
            print(f"加载分支规则页面: {branches_page_id}")
            rules = self.confluence_client.get_branch_rules(branches_page_id)
            self.branch_rules["branches"] = rules
        
        # 从rules页面加载其他规则（如果有）
        rules_page_id = pages.get("rules")
        if rules_page_id:
            print(f"加载规则页面: {rules_page_id}")
            # 这里可以加载其他类型的规则
            pass
    
    def get_regression_branches(self) -> List[BranchRule]:
        """获取回归分支规则"""
        return self.branch_rules.get("branches", [])
    
    def check_branch_for_project(self, project: str, branch: str) -> bool:
        """
        检查分支是否为项目的回归分支
        
        Args:
            project: 项目名称
            branch: 分支名称
        
        Returns:
            True如果是回归分支，False如果不是
        """
        if not branch or not project:
            return False
        
        rules = self.get_regression_branches()
        return self.confluence_client.is_regression_branch(project, branch, rules)
    
    def get_projects_with_branches(self) -> Dict[str, List[str]]:
        """
        获取项目及其回归分支的映射
        
        Returns:
            项目->分支列表的字典
        """
        result = {}
        rules = self.get_regression_branches()
        
        for rule in rules:
            if rule.project not in result:
                result[rule.project] = []
            result[rule.project].append(rule.branch_pattern)
        
        return result
    
    def reload_rules(self) -> None:
        """重新加载规则"""
        self.confluence_client.clear_cache()
        self.branch_rules.clear()
        self._load_rules()
        print("✅ 分支规则已重新加载")


if __name__ == "__main__":
    # 测试Confluence客户端
    print("测试Confluence客户端...")
    
    from config_manager import ConfigManager
    
    config_manager = ConfigManager()
    branch_manager = BranchManager(config_manager)
    
    # 获取回归分支规则
    rules = branch_manager.get_regression_branches()
    print(f"\n找到 {len(rules)} 个回归分支规则:")
    
    for i, rule in enumerate(rules, 1):
        print(f"  {i}. 项目: {rule.project}, 分支: {rule.branch_pattern}, 描述: {rule.description}")
    
    # 测试分支检查
    test_cases = [
        ("SWPL", "amlogic-main-dev"),
        ("SWPL", "feature-branch"),
        ("VIDEO", "main"),
        ("TEST", "any-branch")
    ]
    
    print(f"\n测试分支检查:")
    for project, branch in test_cases:
        is_regression = branch_manager.check_branch_for_project(project, branch)
        print(f"  {project}/{branch}: {'✅ 回归分支' if is_regression else '❌ 非回归分支'}")
    
    # 获取项目分支映射
    projects = branch_manager.get_projects_with_branches()
    print(f"\n项目分支映射:")
    for project, branches in projects.items():
        print(f"  {project}: {branches}")
