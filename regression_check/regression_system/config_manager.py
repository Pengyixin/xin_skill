# -*- coding: utf-8 -*-
"""
配置文件管理器
用于读取和管理回归检测系统的配置
"""

import json
import os
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class JiraConfig:
    """JIRA配置"""
    username: str
    password: str
    base_url: str = "https://jira.amlogic.com"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JiraConfig":
        return cls(
            username=data.get("username", ""),
            password=data.get("password", ""),
            base_url=data.get("base_url", "https://jira.amlogic.com")
        )


@dataclass
class GerritConfig:
    """Gerrit配置"""
    username: str
    password: str
    base_url: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GerritConfig":
        return cls(
            username=data.get("username", ""),
            password=data.get("password", ""),
            base_url=data.get("base_url", "https://scgit.amlogic.com")
        )


@dataclass
class AIConfig:
    """AI配置"""
    openai_api_key: str
    ai_base_url: str
    ai_model: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIConfig":
        return cls(
            openai_api_key=data.get("openai_api_key", ""),
            ai_base_url=data.get("ai_base_url", ""),
            ai_model=data.get("ai_model", "DeepSeek-V3-2")
        )


@dataclass
class ConfluenceConfig:
    """Confluence配置"""
    username: str
    password: str
    page_id: str
    process_rules: bool
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfluenceConfig":
        return cls(
            username=data.get("username", ""),
            password=data.get("password", ""),
            page_id=data.get("page_id", ""),
            process_rules=data.get("process_rules", False)
        )


class ConfigManager:
    """配置文件管理器"""
    
    DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config_data = None
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
                
            print(f"✅ 配置文件加载成功: {self.config_path}")
            
        except json.JSONDecodeError as e:
            print(f"❌ 配置文件格式错误: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            sys.exit(1)
    
    def get_jira_config(self) -> JiraConfig:
        """获取JIRA配置"""
        jira_data = self._config_data.get("jira", {})
        if not jira_data:
            print("⚠️  JIRA配置为空，请检查配置文件")
        return JiraConfig.from_dict(jira_data)
    
    def get_gerrit_config(self) -> GerritConfig:
        """获取Gerrit配置"""
        gerrit_data = self._config_data.get("gerrit", {})
        if not gerrit_data:
            print("⚠️  Gerrit配置为空，请检查配置文件")
        return GerritConfig.from_dict(gerrit_data)
    
    def get_ai_config(self) -> AIConfig:
        """获取AI配置"""
        ai_data = self._config_data.get("ai", {})
        if not ai_data:
            print("⚠️  AI配置为空，请检查配置文件")
        return AIConfig.from_dict(ai_data)
    
    def get_confluence_config(self) -> ConfluenceConfig:
        """获取Confluence配置"""
        confluence_data = self._config_data.get("confluence", {})
        if not confluence_data:
            print("⚠️  Confluence配置为空，请检查配置文件")
        return ConfluenceConfig.from_dict(confluence_data)
    
    def get_email_config(self):
        """获取邮件配置"""
        return self._config_data.get("email", {})
    
    def get_regression_branches(self) -> list:
        """
        获取需要检测的回归分支配置
        
        Returns:
            回归分支配置列表，每个元素包含 project 和 branch
            示例: [{"project": "platform/hardware/amlogic/media_modules", "branch": "amlogic-main-dev"}]
        """
        return self._config_data.get("regression_branches", [])
    
    def get_all_config(self):
        """获取所有配置"""
        return self._config_data
    
    def validate_config(self) -> bool:
        """验证配置是否完整"""
        issues = []
        
        # 检查JIRA配置
        jira_config = self.get_jira_config()
        if not jira_config.username or not jira_config.password:
            issues.append("JIRA用户名或密码未配置")
        
        # 检查Gerrit配置
        gerrit_config = self.get_gerrit_config()
        if not gerrit_config.username or not gerrit_config.password:
            issues.append("Gerrit用户名或密码未配置")
        
        if issues:
            print("❌ 配置验证失败:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        
        print("✅ 配置验证通过")
        return True
    
    def print_config_summary(self) -> None:
        """打印配置摘要"""
        print("\n" + "="*60)
        print("配置摘要")
        print("="*60)
        
        jira_config = self.get_jira_config()
        gerrit_config = self.get_gerrit_config()
        
        print(f"JIRA配置:")
        print(f"  - 用户名: {jira_config.username}")
        print(f"  - 基础URL: {jira_config.base_url}")
        
        print(f"\nGerrit配置:")
        print(f"  - 用户名: {gerrit_config.username}")
        print(f"  - 基础URL: {gerrit_config.base_url}")
        
        print("="*60)


if __name__ == "__main__":
    # 测试配置管理器
    config_manager = ConfigManager()
    config_manager.print_config_summary()
    config_manager.validate_config()
