#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分支过滤器
从Confluence页面动态加载分支规则
"""

from typing import Dict, List, Optional
from .config_manager import ConfigManager
from .confluence_client import BranchManager


class BranchFilter:
    """分支过滤器 - 动态加载版本"""
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        初始化分支过滤器
        
        Args:
            config_manager: 配置管理器，如果为None则创建新的
        """
        if config_manager is None:
            config_manager = ConfigManager()
        
        self.config_manager = config_manager
        
        try:
            # 初始化分支管理器，从Confluence加载分支规则
            self.branch_manager = BranchManager(config_manager)
            print("✅ 分支过滤器初始化成功（从Confluence加载规则）")
            
            # 尝试加载分支规则
            self._load_branch_rules()
            
        except Exception as e:
            print(f"⚠️  无法从Confluence加载分支规则: {e}")
            print("  使用默认规则（仅SWPL项目支持）")
            # 回退到默认规则
            self._use_fallback_rules()
    
    def _load_branch_rules(self) -> None:
        """从Confluence加载分支规则"""
        # 获取回归分支规则
        self.regression_rules = {}
        
        rules = self.branch_manager.get_regression_branches()
        for rule in rules:
            if rule.project not in self.regression_rules:
                self.regression_rules[rule.project] = []
            self.regression_rules[rule.project].append(rule.branch_pattern)
        
        print(f"  从Confluence页面加载了 {len(rules)} 个分支规则")
        if self.regression_rules:
            for project, patterns in self.regression_rules.items():
                print(f"    项目 {project}: {patterns}")
    
    def _use_fallback_rules(self) -> None:
        """使用回退规则（当无法从Confluence加载时）"""
        # 仅支持SWPL项目作为回退
        self.regression_rules = {
            "SWPL": ["amlogic-main-dev", "amlogic-*-stable", "amlogic-main", "stable/*"],
        }
        
        # 常见的非回归分支模式（用于参考）
        # 这些分支不参与回归判定
        self.non_regression_patterns = [
            "test-*", "feature/*", "dev/*", "experiment/*",
            "bugfix/*", "patch/*", "hotfix/*", "temp/*",
            "*-test", "*-dev", "*-feature", "*-experimental"
        ]
    
    def is_regression_branch(self, project: str, branch: str) -> bool:
        """
        检查分支是否为回归分支
        
        Args:
            project: 项目名称 (来自gerrit，如platform/hardware/amlogic/media_modules)
            branch: 分支名称
        
        Returns:
            True如果是回归分支，False如果不是
        """
        if not branch or not project:
            return False
        
        # 使用BranchManager的check_branch_for_project方法，该方法包含智能项目映射
        try:
            return self.branch_manager.check_branch_for_project(project, branch)
        except Exception as e:
            # 如果出错，回退到原来的逻辑
            print(f"⚠️  BranchManager检查失败，使用回退逻辑: {e}")
            
            # 获取项目的回归分支规则
            branch_patterns = self.regression_rules.get(project, [])
            
            # 首先检查分支是否匹配任何回归分支模式
            for pattern in branch_patterns:
                if self._match_pattern(branch, pattern):
                    print(f"    ✅ 分支匹配回归模式: {project}/{branch} -> {pattern}")
                    return True
            
            # 如果没有匹配回归模式，尝试项目简写匹配
            # 提取项目简写（最后一个斜杠后的部分）
            project_short = project.split('/')[-1] if '/' in project else project
            
            if project_short != project:
                # 尝试使用项目简写匹配
                branch_patterns = self.regression_rules.get(project_short, [])
                for pattern in branch_patterns:
                    if self._match_pattern(branch, pattern):
                        print(f"    ✅ 分支匹配回归模式（简写）: {project_short}/{branch} -> {pattern}")
                        return True
            
            # 检查是否是非回归分支模式（特殊处理）
            # 但排除已经被识别为回归分支的情况
            # 注意：原始的NON_REGRESSION_PATTERNS已经被移除，现在只在回退模式下使用
            
            # 如果没有匹配任何回归模式，尝试回退逻辑
            # 只有在使用回退规则时才应用这些逻辑
            if hasattr(self, 'non_regression_patterns'):
                # 检查是否是非回归分支模式
                for pattern in self.non_regression_patterns:
                    if self._match_pattern(branch, pattern):
                        print(f"    ⚠️  分支匹配非回归模式: {project}/{branch} -> {pattern}")
                        return False
                
                # 检查分支是否包含非回归关键词
                non_regression_keywords = ["test-", "feature-", "bugfix-", "patch-", "hotfix-", "temp-"]
                for keyword in non_regression_keywords:
                    if branch.lower().startswith(keyword) or f"-{keyword}" in branch.lower():
                        print(f"    ⚠️  分支包含非回归关键词: {project}/{branch} (包含 '{keyword}')")
                        return False
            
            # 默认：不确定的情况下，假设不是回归分支
            print(f"    ❌ 分支不是回归分支: {project}/{branch}")
            return False
    
    def _match_pattern(self, branch: str, pattern: str) -> bool:
        """
        简单的通配符匹配
        
        Args:
            branch: 分支名称
            pattern: 模式（支持*通配符）
        
        Returns:
            是否匹配
        """
        if '*' in pattern:
            import re
            # 将*转换为正则表达式的.*
            regex_pattern = pattern.replace('*', '.*')
            return bool(re.match(regex_pattern, branch))
        else:
            return branch == pattern
    
    def get_regression_branches_for_project(self, project: str) -> List[str]:
        """
        获取项目的回归分支列表
        
        Args:
            project: 项目名称
        
        Returns:
            回归分支模式列表
        """
        return self.regression_rules.get(project, [])
    
    def reload_rules(self) -> None:
        """重新加载分支规则"""
        if hasattr(self, 'branch_manager'):
            self.branch_manager.reload_rules()
            self._load_branch_rules()
            print("✅ 分支规则已重新加载")
        else:
            print("⚠️  无法重新加载规则：使用回退模式")


# 创建全局实例
_branch_filter_instance = None

def get_branch_filter(config_manager: ConfigManager = None) -> BranchFilter:
    """获取分支过滤器实例"""
    global _branch_filter_instance
    if _branch_filter_instance is None:
        _branch_filter_instance = BranchFilter(config_manager)
    return _branch_filter_instance


if __name__ == "__main__":
    # 测试分支过滤器
    filter = BranchFilter()
    
    test_cases = [
        ("SWPL", "amlogic-main-dev", True),
        ("SWPL", "amlogic-5.15-stable", True),
        ("SWPL", "feature-branch", False),
        ("SWPL", "test-branch", False),
        ("VIDEO", "main", True),
        ("VIDEO", "stable/2025", True),
        ("VIDEO", "dev-branch", False),
        ("UNKNOWN", "main", False),
    ]
    
    print("\n测试分支匹配:")
    for project, branch, expected in test_cases:
        result = filter.is_regression_branch(project, branch)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {project}/{branch}: 期望{expected}, 实际{result}")
