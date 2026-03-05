"""
回归检测引擎
核心检测逻辑，实现三步检测算法
"""

import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .jira_client import JIRAClient, JiraIssue, RegressionStatus
from .gerrit_client import GerritClient
from .config_manager import ConfigManager


def calculate_days_since_verified(verified_date: str) -> int:
    """计算从verified日期到今天的天数"""
    if not verified_date:
        return 0
    try:
        # JIRA日期格式: 2026-01-15T00:00:00.000+0800
        verified_dt = datetime.strptime(verified_date[:19], "%Y-%m-%dT%H:%M:%S")
        now_dt = datetime.now()
        return (now_dt - verified_dt).days
    except:
        return 0


@dataclass
class RegressionResult:
    """回归检测结果"""
    jira_key: str
    summary: str
    status: str
    owner: str
    days_since_verified: int
    needs_regression: bool
    regression_status: RegressionStatus
    related_gerrits: List[str]
    gerrit_merged: bool
    clone_jiras: List[str]
    clone_results: List["RegressionResult"]  # 递归检测结果
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "jira_key": self.jira_key,
            "summary": self.summary,
            "status": self.status,
            "owner": self.owner,
            "days_since_verified": self.days_since_verified,
            "needs_regression": self.needs_regression,
            "regression_status": self.regression_status.value if self.regression_status else None,
            "related_gerrits": self.related_gerrits,
            "gerrit_merged": self.gerrit_merged,
            "clone_jiras": self.clone_jiras,
            "clone_count": len(self.clone_jiras),
            "has_error": self.error is not None,
            "error": self.error
        }


@dataclass
class RegressionSummary:
    """回归检测摘要"""
    total_issues: int = 0
    needs_regression: int = 0
    regressed: int = 0
    not_regressed: int = 0
    not_required: int = 0
    errors: int = 0
    
    def update(self, result: RegressionResult) -> None:
        """更新统计"""
        self.total_issues += 1
        
        if result.error:
            self.errors += 1
            return
        
        if not result.needs_regression:
            self.not_required += 1
        elif result.regression_status == RegressionStatus.REGRESSED:
            self.regressed += 1
        elif result.regression_status == RegressionStatus.NOT_REGRESSED:
            self.not_regressed += 1
        elif result.regression_status == RegressionStatus.NEEDS_REGRESSION:
            self.needs_regression += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_issues": self.total_issues,
            "needs_regression": self.needs_regression,
            "regressed": self.regressed,
            "not_regressed": self.not_regressed,
            "not_required": self.not_required,
            "errors": self.errors
        }


class RegressionEngine:
    """回归检测引擎"""
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        初始化回归检测引擎
        
        Args:
            config_manager: 配置管理器，如果为None则创建新的
        """
        if config_manager is None:
            config_manager = ConfigManager()
        
        self.config_manager = config_manager
        self.jira_client = JIRAClient(config_manager.get_jira_config())
        self.gerrit_client = GerritClient(config_manager.get_gerrit_config())
        
        # 加载回归分支配置
        self.regression_branches = config_manager.get_regression_branches()
        if self.regression_branches:
            print(f"📋 已配置回归分支检测:")
            for i, rb in enumerate(self.regression_branches, 1):
                print(f"   {i}. Project: {rb.get('project')}, Branch: {rb.get('branch')}")
        else:
            print("⚠️  未配置回归分支，将检测所有合并的gerrit")
        
        # 缓存已检测的jira，避免重复检测
        self.cache: Dict[str, RegressionResult] = {}
        
        # 记录当前正在检测中的jira（防止循环检测）
        self._checking_jiras: set = set()
        
        print("✅ 回归检测引擎初始化成功")
    
    def _is_regression_branch_matched(self, gerrit_project: str, gerrit_branch: str) -> bool:
        """
        检查gerrit的分支是否匹配配置的回归分支
        
        Args:
            gerrit_project: gerrit项目名 (如 platform/hardware/amlogic/media_modules)
            gerrit_branch: gerrit分支名 (如 amlogic-main-dev)
        
        Returns:
            True如果匹配配置的回归分支，False如果不匹配
        """
        # 如果没有配置回归分支，允许所有
        if not self.regression_branches:
            return True
        
        for rb in self.regression_branches:
            config_project = rb.get('project', '')
            config_branch = rb.get('branch', '')
            
            # 项目匹配检查
            project_matched = False
            if config_project == gerrit_project:
                project_matched = True
            elif config_project in gerrit_project or gerrit_project in config_project:
                # 部分匹配（如 media_modules 匹配 platform/hardware/amlogic/media_modules）
                project_matched = True
            elif gerrit_project.endswith(config_project.split('/')[-1]):
                # 简写匹配（如 media_modules 匹配 platform/hardware/amlogic/media_modules）
                project_matched = True
            
            # 分支匹配检查（支持通配符 *）
            branch_matched = False
            if '*' in config_branch:
                import re
                regex_pattern = config_branch.replace('*', '.*')
                if re.match(regex_pattern, gerrit_branch):
                    branch_matched = True
            else:
                if config_branch == gerrit_branch:
                    branch_matched = True
            
            if project_matched and branch_matched:
                return True
        
        return False
    
    def check_single_jira(self, jira_key: str) -> RegressionResult:
        """
        检测单个JIRA issue的回归状态
        
        Args:
            jira_key: JIRA issue key
        
        Returns:
            回归检测结果
        """
        print(f"\n{'='*60}")
        print(f"检测JIRA: {jira_key}")
        print(f"{'='*60}")
        
        # 检查缓存
        if jira_key in self.cache:
            print(f"从缓存中获取结果: {jira_key}")
            return self.cache[jira_key]
        
        # 检查是否在检测中（防止循环检测）
        if jira_key in self._checking_jiras:
            print(f"⚠️  检测到循环依赖，跳过: {jira_key} 正在检测中")
            result = RegressionResult(
                jira_key=jira_key,
                summary="",
                status="",
                owner="",
                days_since_verified=0,
                needs_regression=False,
                regression_status=None,
                related_gerrits=[],
                gerrit_merged=False,
                clone_jiras=[],
                clone_results=[],
                error=f"循环依赖检测: {jira_key} 正在被检测"
            )
            return result
        
        # 标记为正在检测
        self._checking_jiras.add(jira_key)
        
        try:
            # 步骤1: 获取JIRA issue信息
            issue = self.jira_client.get_issue(jira_key)
            if not issue:
                result = RegressionResult(
                    jira_key=jira_key,
                    summary="",
                    status="",
                    owner="",
                    days_since_verified=0,
                    needs_regression=False,
                    regression_status=None,
                    related_gerrits=[],
                    gerrit_merged=False,
                    clone_jiras=[],
                    clone_results=[],
                    error=f"无法获取JIRA issue: {jira_key}"
                )
                self.cache[jira_key] = result
                return result
            
            # 步骤2: 检查是否需要回归公版
            if not issue.needs_regression:
                result = RegressionResult(
                    jira_key=issue.key,
                    summary=issue.summary,
                    status=issue.status,
                    owner=issue.assignee or "",
                    days_since_verified=calculate_days_since_verified(issue.verified_date),
                    needs_regression=False,
                    regression_status=RegressionStatus.NOT_REQUIRED,
                    related_gerrits=[],
                    gerrit_merged=False,
                    clone_jiras=[],
                    clone_results=[],
                    error=None
                )
                self.cache[jira_key] = result
                return result
            
            # 步骤3: 检查关联的gerrit是否已合并到回归分支
            gerrit_merged = False
            merged_to_regression_branch = False
            if issue.related_gerrits:
                print(f"检查 {len(issue.related_gerrits)} 个关联gerrit的合并状态...")
                
                for url in issue.related_gerrits:
                    change = self.gerrit_client.get_change_by_url(url)
                    if not change:
                        print(f"  ⚠️ 无法获取gerrit信息: {url}")
                        continue
                    
                    if change.is_merged():
                        gerrit_merged = True
                        print(f"  ✅ 找到已合并的gerrit: {url}")
                        print(f"     Project: {change.project}, Branch: {change.branch}")
                        
                        # 检查是否合并到配置的回归分支
                        if self._is_regression_branch_matched(change.project, change.branch):
                            merged_to_regression_branch = True
                            print(f"     ✅ 已合并到配置的回归分支")
                            break
                        elif self.regression_branches:
                            print(f"     ⚠️  已合并但未合并到配置的回归分支")
                    else:
                        print(f"  ⏳ gerrit未合并: {url} (状态: {change.status})")
            
            # 如果gerrit已合并到回归分支，标记为已回归
            if merged_to_regression_branch:
                result = RegressionResult(
                    jira_key=issue.key,
                    summary=issue.summary,
                    status=issue.status,
                    owner=issue.assignee or "",
                    days_since_verified=calculate_days_since_verified(issue.verified_date),
                    needs_regression=True,
                    regression_status=RegressionStatus.REGRESSED,
                    related_gerrits=issue.related_gerrits,
                    gerrit_merged=True,
                    clone_jiras=issue.clone_jiras,
                    clone_results=[],
                    error=None
                )
                self.cache[jira_key] = result
                return result
            elif gerrit_merged and self.regression_branches:
                # gerrit已合并但未合并到配置的回归分支
                print(f"  ⚠️  gerrit已合并但未合并到配置的回归分支")
            
            # 步骤4: 如果没有gerrit或gerrit未合并，检查clone的jira
            clone_results = []
            swpl_clone_regressed = False
            
            if issue.clone_jiras:
                print(f"检查 {len(issue.clone_jiras)} 个clone的jira...")
                
                # 首先过滤出SWPL项目的clone jira，并排除已经在检测中的（防止循环）
                swpl_clone_jiras = [
                    jira for jira in issue.clone_jiras 
                    if jira.startswith("SWPL-") and jira not in self._checking_jiras
                ]
                
                # 记录被跳过的jira（因为正在检测中，说明形成了循环依赖）
                skipped_jiras = [
                    jira for jira in issue.clone_jiras 
                    if jira.startswith("SWPL-") and jira in self._checking_jiras
                ]
                if skipped_jiras:
                    print(f"  ⏭️  跳过正在检测中的jira（避免循环）: {skipped_jiras}")
                
                if swpl_clone_jiras:
                    print(f"  只检测SWPL项目的clone jira: {swpl_clone_jiras}")
                    
                    for clone_jira in swpl_clone_jiras:
                        print(f"  递归检测clone jira: {clone_jira}")
                        clone_result = self.check_single_jira(clone_jira)
                        clone_results.append(clone_result)
                        
                        # 检查这个clone jira的状态
                        # 规则: 如果clone jira未关闭(Open/In Progress等)，则说明还未回归完成
                        #       如果clone jira已关闭，则需要检查是否有gerrit并且已经merged
                        
                        if clone_result.regression_status == RegressionStatus.REGRESSED:
                            swpl_clone_regressed = True
                            print(f"    ✅ 通过SWPL clone jira {clone_jira} 已回归")
                        elif clone_result.status in ["Closed", "Resolved", "Verified"]:
                            # clone jira已关闭，检查是否有gerrit且已合并
                            if clone_result.gerrit_merged:
                                swpl_clone_regressed = True
                                print(f"    ✅ 通过已关闭的SWPL clone jira {clone_jira} 已回归 (gerrit已合并)")
                            else:
                                print(f"    ⚠️  SWPL clone jira {clone_jira} 已关闭但无gerrit或gerrit未合并")
                        else:
                            # clone jira未关闭
                            print(f"    ⚠️  SWPL clone jira {clone_jira} 未关闭 ({clone_result.status})，说明还未回归完成")
                else:
                    print(f"  未找到SWPL项目的clone jira，跳过clone检测")
            else:
                print(f"  无clone的jira")
            
            # 确定最终状态
            if swpl_clone_regressed:
                final_status = RegressionStatus.REGRESSED
                print(f"  ✅ 通过SWPL clone jira已回归")
            else:
                final_status = RegressionStatus.NOT_REGRESSED
                print(f"  ❌ 未找到已回归的gerrit或SWPL clone jira")
            
            result = RegressionResult(
                jira_key=issue.key,
                summary=issue.summary,
                status=issue.status,
                owner=issue.assignee or "",
                days_since_verified=calculate_days_since_verified(issue.verified_date),
                needs_regression=True,
                regression_status=final_status,
                related_gerrits=issue.related_gerrits,
                gerrit_merged=gerrit_merged,
                clone_jiras=issue.clone_jiras,
                clone_results=clone_results,
                error=None
            )
            
            self.cache[jira_key] = result
            return result
            
        except Exception as e:
            print(f"❌ 检测JIRA {jira_key} 时发生错误: {e}")
            result = RegressionResult(
                jira_key=jira_key,
                summary="",
                status="",
                owner="",
                days_since_verified=0,
                needs_regression=False,
                regression_status=None,
                related_gerrits=[],
                gerrit_merged=False,
                clone_jiras=[],
                clone_results=[],
                error=f"检测错误: {str(e)}"
            )
            self.cache[jira_key] = result
            return result
        finally:
            # 检测完成，从集合中移除（防止循环检测）
            self._checking_jiras.discard(jira_key)
    
    def batch_check_jiras(self, jira_keys: List[str]) -> Tuple[List[RegressionResult], RegressionSummary]:
        """
        批量检测JIRA issues
        
        Args:
            jira_keys: JIRA issue key列表
        
        Returns:
            (检测结果列表, 统计摘要)
        """
        print(f"\n{'='*60}")
        print(f"批量检测 {len(jira_keys)} 个JIRA issues")
        print(f"{'='*60}")
        
        results = []
        summary = RegressionSummary()
        
        for i, jira_key in enumerate(jira_keys, 1):
            print(f"\n[{i}/{len(jira_keys)}] ", end="")
            result = self.check_single_jira(jira_key)
            results.append(result)
            summary.update(result)
            
            # 显示进度
            status_str = result.regression_status.value if result.regression_status else "错误"
            print(f"  结果: {status_str}")
        
        print(f"\n{'='*60}")
        print("批量检测完成")
        print(f"{'='*60}")
        print(f"总计: {summary.total_issues} 个issues")
        print(f"需要回归: {summary.needs_regression}")
        print(f"已回归: {summary.regressed}")
        print(f"未回归: {summary.not_regressed}")
        print(f"不需要回归: {summary.not_required}")
        print(f"错误: {summary.errors}")
        
        return results, summary
    
    def search_and_check(self, project: str = None, days: int = 30, max_results: int = 1000) -> Tuple[List[RegressionResult], RegressionSummary]:
        """
        搜索verify/close状态的issues并检测
        
        Args:
            project: 项目key（如SWPL），如果为None则搜索所有项目
            days: 搜索最近多少天的issues
            max_results: 最大搜索结果数
        
        Returns:
            (检测结果列表, 统计摘要)
        """
        print(f"\n{'='*60}")
        print(f"搜索并检测verify/close状态的issues")
        if project:
            print(f"项目: {project}")
        print(f"时间范围: 最近{days}天")
        print(f"最大结果数: {max_results}")
        print(f"{'='*60}")
        
        # 搜索issues
        issues = self.jira_client.search_verify_close_issues(project=project, days=days, max_results=max_results)
        
        if not issues:
            print("⚠️  未找到符合条件的issues")
            return [], RegressionSummary()
        
        print(f"找到 {len(issues)} 个符合条件的issues")
        
        if len(issues) >= max_results:
            print(f"⚠️  警告: 结果数量已达到最大值 {max_results}，可能还有更多结果未显示")
        
        # 提取jira keys
        jira_keys = [issue.key for issue in issues]
        
        # 批量检测
        return self.batch_check_jiras(jira_keys)
    
    def search_by_labels_and_check(self, labels: List[str], project: str = None, 
                                   statuses: List[str] = None, days: int = 0, max_results: int = 1000) -> Tuple[List[RegressionResult], RegressionSummary]:
        """
        根据label搜索issues并进行回归检测
        
        Args:
            labels: label列表，如["DECODER-CORE-20260126"]
            project: 项目key（如SWPL），如果为None则搜索所有项目
            statuses: 状态列表，如["Verified", "Closed", "Resolved"]，如果为None则搜索所有状态
            days: 搜索最近多少天的issues，0表示不限制
            max_results: 最大搜索结果数
        
        Returns:
            (检测结果列表, 统计摘要)
        """
        print(f"\n{'='*60}")
        print(f"根据label搜索并检测issues")
        print(f"Labels: {labels}")
        if project:
            print(f"项目: {project}")
        if statuses:
            print(f"状态: {statuses}")
        if days > 0:
            print(f"时间范围: 最近{days}天")
        print(f"最大结果数: {max_results}")
        print(f"{'='*60}")
        
        # 搜索issues
        issues = self.jira_client.search_by_labels(labels=labels, project=project, 
                                                  statuses=statuses, days=days, max_results=max_results)
        
        if not issues:
            print("⚠️  未找到符合条件的issues")
            return [], RegressionSummary()
        
        print(f"找到 {len(issues)} 个符合条件的issues")
        
        if len(issues) >= max_results:
            print(f"⚠️  警告: 结果数量已达到最大值 {max_results}，可能还有更多结果未显示")
        
        # 提取jira keys
        jira_keys = [issue.key for issue in issues]
        
        # 批量检测
        return self.batch_check_jiras(jira_keys)
    
    def search_by_jql_and_check(self, jql: str, max_results: int = 1000) -> Tuple[List[RegressionResult], RegressionSummary]:
        """
        使用JQL搜索issues并进行回归检测
        
        Args:
            jql: JIRA查询语言语句
            max_results: 最大搜索结果数
        
        Returns:
            (检测结果列表, 统计摘要)
        """
        print(f"\n{'='*60}")
        print(f"使用JQL查询并检测issues")
        print(f"JQL: {jql}")
        print(f"最大结果数: {max_results}")
        print(f"{'='*60}")
        
        # 搜索issues
        issues = self.jira_client.search_issues(jql=jql, max_results=max_results)
        
        if not issues:
            print("⚠️  未找到符合条件的issues")
            return [], RegressionSummary()
        
        print(f"找到 {len(issues)} 个符合条件的issues")
        
        if len(issues) >= max_results:
            print(f"⚠️  警告: 结果数量已达到最大值 {max_results}，可能还有更多结果未显示")
        
        # 提取jira keys
        jira_keys = [issue.key for issue in issues]
        
        # 批量检测
        return self.batch_check_jiras(jira_keys)
    
    def check_jira_list_file(self, file_path: str) -> Tuple[List[RegressionResult], RegressionSummary]:
        """
        从文件读取JIRA列表并检测
        
        Args:
            file_path: 包含JIRA列表的文件路径
        
        Returns:
            (检测结果列表, 统计摘要)
        """
        print(f"\n{'='*60}")
        print(f"从文件读取JIRA列表: {file_path}")
        print(f"{'='*60}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取JIRA keys
            import re
            jira_keys = re.findall(r'[A-Z]+-\d+', content)
            jira_keys = list(set(jira_keys))  # 去重
            
            print(f"从文件中提取到 {len(jira_keys)} 个唯一的JIRA keys")
            
            if not jira_keys:
                print("⚠️  文件中未找到JIRA keys")
                return [], RegressionSummary()
            
            # 批量检测
            return self.batch_check_jiras(jira_keys)
            
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return [], RegressionSummary()
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()
        print("✅ 缓存已清空")


if __name__ == "__main__":
    # 测试回归检测引擎
    print("测试回归检测引擎...")
    
    engine = RegressionEngine()
    
    # 测试单个JIRA检测
    test_jira = "SWPL-252395"  # 示例JIRA
    result = engine.check_single_jira(test_jira)
    
    print(f"\n单个JIRA检测结果:")
    print(f"  JIRA: {result.jira_key}")
    print(f"  摘要: {result.summary[:50]}...")
    print(f"  状态: {result.status}")
    print(f"  是否需要回归: {result.needs_regression}")
    print(f"  回归状态: {result.regression_status.value if result.regression_status else 'N/A'}")
    print(f"  关联gerrit数量: {len(result.related_gerrits)}")
    print(f"  gerrit是否合并: {result.gerrit_merged}")
    print(f"  clone jira数量: {len(result.clone_jiras)}")
    
    # 测试搜索并检测
    print(f"\n测试搜索并检测功能...")
    results, summary = engine.search_and_check(project="SWPL", days=7)
    
    print(f"\n搜索检测结果:")
    print(f"  总计: {summary.total_issues} 个issues")
    print(f"  需要回归: {summary.needs_regression}")
    print(f"  已回归: {summary.regressed}")
    print(f"  未回归: {summary.not_regressed}")
    print(f"  不需要回归: {summary.not_required}")
    print(f"  错误: {summary.errors}")
