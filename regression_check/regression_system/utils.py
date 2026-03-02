# -*- coding: utf-8 -*-
"""
工具函数模块
包含通用的工具函数
"""

import re
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlparse


def setup_logger(name: str, log_file: str = None, level=logging.INFO) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径，如果为None则只输出到控制台
        level: 日志级别
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 清除现有的处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果提供了日志文件）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def extract_jira_key(url: str) -> Optional[str]:
    """
    从JIRA URL中提取issue key
    
    Args:
        url: JIRA URL
    
    Returns:
        Optional[str]: 提取到的issue key，如果提取失败则返回None
    """
    # 示例: https://jira.amlogic.com/browse/SWPL-252395
    pattern = r'https?://jira\.amlogic\.com/browse/([A-Z]+-\d+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    
    # 尝试其他格式
    parsed = urlparse(url)
    path_parts = parsed.path.split('/')
    for part in path_parts:
        if re.match(r'^[A-Z]+-\d+$', part):
            return part
    
    return None


def extract_gerrit_change_id(url: str) -> Optional[str]:
    """
    从Gerrit URL中提取change ID
    
    Args:
        url: Gerrit URL
    
    Returns:
        Optional[str]: 提取到的change ID，如果提取失败则返回None
    """
    # 示例: https://scgit.amlogic.com/#/c/624081/
    patterns = [
        r'/#/c/(\d+)/',
        r'/c/(\d+)/',
        r'changeId=(\d+)',
        r'id=(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # 尝试从URL路径中提取
    parsed = urlparse(url)
    path_parts = parsed.path.split('/')
    for part in path_parts:
        if part.isdigit() and len(part) >= 4:  # 假设change ID至少4位
            return part
    
    return None


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """
    带退避策略的重试装饰器
    
    Args:
        func: 要重试的函数
        max_retries: 最大重试次数
        base_delay: 基础延迟时间（秒）
    
    Returns:
        函数执行结果
    """
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))
                    time.sleep(delay)
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    print(f"重试 {attempt + 1}/{max_retries}: {e}")
                else:
                    print(f"所有重试失败: {e}")
        
        raise last_exception
    
    return wrapper


def parse_custom_field(fields: Dict[str, Any], field_name: str) -> Any:
    """
    解析JIRA自定义字段
    
    Args:
        fields: JIRA字段字典
        field_name: 自定义字段名称
    
    Returns:
        字段值
    """
    # JIRA自定义字段通常以customfield_开头
    if field_name.startswith('customfield_'):
        return fields.get(field_name)
    
    # 尝试多种可能的字段名格式
    possible_names = [
        field_name,
        f"customfield_{field_name}",
        f"customfield_{field_name.lstrip('customfield_')}",
        field_name.upper(),
        field_name.lower()
    ]
    
    for name in possible_names:
        if name in fields:
            return fields.get(name)
    
    return None


def format_timestamp(timestamp: str) -> str:
    """
    格式化时间戳为可读格式
    
    Args:
        timestamp: ISO格式时间戳
    
    Returns:
        格式化后的时间字符串
    """
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp


def safe_get(dictionary: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    安全地获取嵌套字典的值
    
    Args:
        dictionary: 字典
        keys: 键路径列表
        default: 默认值
    
    Returns:
        找到的值或默认值
    """
    current = dictionary
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


if __name__ == "__main__":
    # 测试工具函数
    test_urls = [
        "https://jira.amlogic.com/browse/SWPL-252395",
        "http://jira.amlogic.com/browse/TEST-123",
        "invalid_url"
    ]
    
    print("测试JIRA key提取:")
    for url in test_urls:
        key = extract_jira_key(url)
        print(f"  {url} -> {key}")
    
    test_gerrit_urls = [
        "https://scgit.amlogic.com/#/c/624081/",
        "https://scgit.amlogic.com/c/12345/",
        "invalid_url"
    ]
    
    print("\n测试Gerrit change ID提取:")
    for url in test_gerrit_urls:
        change_id = extract_gerrit_change_id(url)
        print(f"  {url} -> {change_id}")
