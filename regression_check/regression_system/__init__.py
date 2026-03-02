# -*- coding: utf-8 -*-
"""
回归检测系统 - 主包
用于查找未回归公版的提交
"""

__version__ = "1.0.0"
__author__ = "Regression Detection Team"

from .config_manager import ConfigManager
from .jira_client import JIRAClient, JiraIssue, RegressionStatus
from .gerrit_client import GerritClient, GerritChange
from .regression_engine import RegressionEngine, RegressionResult, RegressionSummary
from .report_generator import ReportGenerator
from .utils import setup_logger, extract_jira_key, extract_gerrit_change_id

__all__ = [
    "ConfigManager",
    "JIRAClient", 
    "JiraIssue",
    "RegressionStatus",
    "GerritClient",
    "GerritChange",
    "RegressionEngine",
    "RegressionResult", 
    "RegressionSummary",
    "ReportGenerator",
    "setup_logger",
    "extract_jira_key", 
    "extract_gerrit_change_id"
]
