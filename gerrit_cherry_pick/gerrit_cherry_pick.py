#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerrit Cherry-Pick Tool
使用Gerrit API进行cherry-pick操作并生成HTML报告
支持多种输入格式：Gerrit URL、Change-Id、Commit Hash
"""

import json
import re
import sys
import urllib.request
import urllib.error
from typing import Dict, Tuple, List, Optional, Any
from datetime import datetime
import base64


def load_config(config_path: str = "config.json") -> Dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_change_identifier(identifier: str) -> Tuple[str, str]:
    """
    解析变更标识符，支持多种格式：
    1. Gerrit URL: https://scgit.amlogic.com/#/c/610496/
    2. Change Number: 610496 (纯数字)
    3. Change-Id: I4ea5aed44ace170e7ee83fcacbbca0ba4ffbb5d6
    4. Commit hash (完整或简写): 3eb601ad7b1c8865678ae214c13718f7da3e585e 或 3eb601ad7
    
    返回: (类型, 值)
    """
    identifier = identifier.strip()
    
    # 1. 检查是否为纯数字 (Change Number)
    if re.match(r'^\d+$', identifier):
        return ('change_number', identifier)
    
    # 2. 检查是否为Gerrit URL
    url_patterns = [
        r'/c/(\d+)',  # 标准格式 /c/610496/
        r'#/c/(\d+)',  # 带#的格式 #/c/610496/
        r'change/(\d+)',  # change格式
    ]
    
    for pattern in url_patterns:
        match = re.search(pattern, identifier)
        if match:
            return ('change_number', match.group(1))
    
    # 3. 检查是否为Change-Id (以I开头，后跟40位十六进制)
    if identifier.startswith('I') and len(identifier) >= 41:
        # 完整的Change-Id格式
        if re.match(r'^I[0-9a-fA-F]{40}$', identifier):
            return ('change_id', identifier)
    
    # 4. 检查是否为Commit hash (40位十六进制或简写)
    if re.match(r'^[0-9a-fA-F]{7,40}$', identifier):
        return ('commit', identifier.lower())
    
    # 5. 如果都不匹配，尝试从commit message中提取Change-Id
    change_id_match = re.search(r'Change-Id:\s*(I[0-9a-fA-F]{40})', identifier)
    if change_id_match:
        return ('change_id', change_id_match.group(1))
    
    return ('unknown', identifier)


def search_by_change_id(base_url: str, change_id: str, username: str, 
                        password: str) -> Tuple[bool, Dict]:
    """通过Change-Id搜索变更"""
    # Change-Id需要转义
    encoded_id = change_id.replace('/', '%2F')
    url = f"{base_url}/a/changes/?q=change:{encoded_id}&o=CURRENT_REVISION"
    success, result = make_api_request(url, username, password, base_url)
    
    if not success:
        return False, result
    
    if isinstance(result, list) and len(result) > 0:
        return True, result[0]
    else:
        return False, {"error": True, "message": f"Change-Id {change_id} not found"}


def search_by_commit(base_url: str, commit_hash: str, username: str,
                     password: str) -> Tuple[bool, Dict]:
    """通过Commit hash搜索变更"""
    url = f"{base_url}/a/changes/?q=commit:{commit_hash}&o=CURRENT_REVISION"
    success, result = make_api_request(url, username, password, base_url)
    
    if not success:
        return False, result
    
    if isinstance(result, list) and len(result) > 0:
        return True, result[0]
    else:
        return False, {"error": True, "message": f"Commit {commit_hash} not found"}


def make_api_request(url: str, username: str, password: str, base_url: str,
                     method: str = 'GET', data: Optional[bytes] = None) -> Tuple[bool, Any]:
    """向Gerrit API发送请求并处理响应 - 使用Digest认证"""

    # 使用Digest认证 - 必须使用base_url添加密码，不是完整URL
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, base_url, username, password)

    # 创建支持Digest和Basic认证的opener
    auth_digest_handler = urllib.request.HTTPDigestAuthHandler(password_mgr)
    auth_basic_handler = urllib.request.HTTPBasicAuthHandler(password_mgr)

    opener = urllib.request.build_opener(auth_digest_handler, auth_basic_handler)

    try:
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header('Content-Type', 'application/json')

        with opener.open(req) as response:
            result = response.read().decode('utf-8')
            # Gerrit API返回的JSON有前缀")]}'"，需要移除
            if result.startswith(")]}'"):
                result = result[5:]

            return True, json.loads(result)

    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode('utf-8')
            if error_body.startswith(")]}'"):
                error_body = error_body[5:]
            error_data = json.loads(error_body)
            return False, {
                "error": True,
                "message": error_data.get('message', str(e)),
                "status": e.code,
                "details": error_data
            }
        except:
            return False, {
                "error": True,
                "message": str(e),
                "status": e.code,
                "details": {}
            }

    except Exception as e:
        return False, {"error": True, "message": str(e), "status": 0}


def get_change_details(base_url: str, change_id: str, username: str,
                       password: str) -> Tuple[bool, Dict]:
    """获取变更详情"""
    # 注意: DETAILED_ACCOUNTS 选项会导致400错误，所以不使用它
    url = f"{base_url}/a/changes/?q={change_id}&o=CURRENT_REVISION"
    success, result = make_api_request(url, username, password, base_url)

    if not success:
        return False, result

    if isinstance(result, list) and len(result) > 0:
        return True, result[0]
    else:
        return False, {"error": True, "message": "Change not found"}


def cherry_pick_change(base_url: str, change_id: str, target_branch: str,
                       username: str, password: str) -> Tuple[bool, Any]:
    """
    使用Gerrit API执行cherry-pick操作
    POST /changes/{change-id}/revisions/{rev-id}/cherrypick/
    """
    # 首先获取当前revision
    details_success, details = get_change_details(base_url, change_id, username, password)
    if not details_success:
        return False, details

    # 获取当前revision ID (通常是当前patch set)
    current_revision = details.get('current_revision', '')
    full_change_id = details.get('id', '')
    original_change_id = details.get('change_id', '')  # 获取原始Change-Id
    
    if not current_revision:
        return False, {"error": True, "message": "无法获取当前revision"}
    if not full_change_id:
        return False, {"error": True, "message": "无法获取完整change ID"}

    # 构建cherry-pick请求
    url = f"{base_url}/a/changes/{full_change_id}/revisions/{current_revision}/cherrypick/"

    # 构建commit message，保留原始Change-Id
    subject = details.get('subject', '')
    original_change_number = details.get('_number', '')
    cherry_pick_data = {
        "destination": target_branch,
        "message": subject + f"\n\nCherry-picked from change {original_change_number}\n\nChange-Id: {original_change_id}"
    }

    data = json.dumps(cherry_pick_data).encode('utf-8')

    success, result = make_api_request(url, username, password, base_url, method='POST', data=data)

    return success, result


def generate_html_report_batch(
    target_branch: str,
    results: List[Dict],
    success_count: int,
    failed_count: int,
    output_file: str = "cherry_pick_report.html"
) -> str:
    """生成批量cherry-pick的HTML报告"""
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_count = len(results)
    
    # 构建变更列表HTML
    changes_html = ""
    for idx, result in enumerate(results, 1):
        details = result.get('details', {})
        success = result.get('success', False)
        
        if success:
            cherry_pick_result = result.get('cherry_pick_result', {})
            new_change_id = ""
            if isinstance(cherry_pick_result, dict):
                new_change_id = cherry_pick_result.get('id', 'N/A')
            elif isinstance(cherry_pick_result, list) and len(cherry_pick_result) > 0:
                new_change_id = cherry_pick_result[0].get('id', 'N/A')
            
            # 获取原始Change-Id
            original_change_id = details.get('change_id', 'N/A') if details else 'N/A'
            
            status_html = f'<span class="status-success">成功</span>'
            result_html = f'''
            <div class="success-details">
                <p><strong>原始Change-Id:</strong> <code>{original_change_id}</code></p>
                <p><strong>新Change ID:</strong> {new_change_id}</p>
                <p class="note" style="font-size: 12px; color: #666; margin-top: 8px;">
                    注：Gerrit cherry-pick会创建新change（新Change Number），但会在commit message中引用原始Change-Id
                </p>
            </div>
            '''
        else:
            error_msg = result.get('error', '未知错误')
            status_html = f'<span class="status-failed">失败</span>'
            result_html = f'<div class="error-details"><strong>错误:</strong> {error_msg}</div>'
        
        changes_html += f"""
        <div class="change-item">
            <div class="change-header">
                <span class="change-number">#{idx}</span>
                <span class="change-subject">{details.get('subject', 'N/A') if details else '获取失败'}</span>
                {status_html}
            </div>
            <table class="change-table">
                <tr><th>源URL</th><td>{result.get('url', 'N/A')}</td></tr>
                <tr><th>Change Number</th><td>{details.get('_number', result.get('change_id', 'N/A')) if details else result.get('change_id', 'N/A')}</td></tr>
                <tr><th>原分支</th><td>{details.get('branch', 'N/A') if details else 'N/A'}</td></tr>
                <tr><th>项目</th><td>{details.get('project', 'N/A') if details else 'N/A'}</td></tr>
            </table>
            {result_html}
        </div>
        """
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gerrit Cherry-Pick 批量报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .header .timestamp {{
            opacity: 0.9;
            margin-top: 10px;
        }}
        .summary {{
            background: white;
            padding: 25px;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .summary h2 {{
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin-top: 20px;
        }}
        .stat-item {{
            flex: 1;
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            background: #f8f9fa;
        }}
        .stat-success {{
            background: #d4edda;
            color: #155724;
        }}
        .stat-failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        .change-item {{
            background: white;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .change-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }}
        .change-number {{
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
        }}
        .change-subject {{
            flex: 1;
            font-weight: 600;
            color: #333;
        }}
        .status-success {{
            background: #28a745;
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 14px;
        }}
        .status-failed {{
            background: #dc3545;
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 14px;
        }}
        .success-details {{
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
        }}
        .success-details code {{
            background: rgba(0,0,0,0.1);
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }}
        .change-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        .change-table th, .change-table td {{
            text-align: left;
            padding: 8px;
            border-bottom: 1px solid #eee;
        }}
        .change-table th {{
            width: 150px;
            color: #666;
            font-weight: 500;
        }}
        .error-details {{
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 30px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Gerrit Cherry-Pick 批量报告</h1>
        <div class="timestamp">生成时间: {timestamp}</div>
        <div style="margin-top: 15px;">目标分支: <strong>{target_branch}</strong></div>
    </div>

    <div class="summary">
        <h2>执行摘要</h2>
        <div class="stats">
            <div class="stat-item">
                <div style="font-size: 24px; font-weight: bold;">{total_count}</div>
                <div>总计</div>
            </div>
            <div class="stat-item stat-success">
                <div style="font-size: 24px; font-weight: bold;">{success_count}</div>
                <div>成功</div>
            </div>
            <div class="stat-item stat-failed">
                <div style="font-size: 24px; font-weight: bold;">{failed_count}</div>
                <div>失败</div>
            </div>
        </div>
    </div>

    <div class="changes-list">
        <h2 style="color: #333; margin-bottom: 20px;">详细结果</h2>
        {changes_html}
    </div>

    <div class="footer">
        <p>Generated by Gerrit Cherry-Pick Tool</p>
    </div>
</body>
</html>"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return output_file


def resolve_identifier(base_url: str, identifier: str, username: str, 
                       password: str) -> Tuple[bool, str, str]:
    """
    解析标识符并获取change number
    返回: (成功, change_number, 错误信息)
    """
    id_type, id_value = parse_change_identifier(identifier)
    
    print(f"  识别类型: {id_type}")
    print(f"  标识符: {id_value}")
    
    if id_type == 'change_number':
        # 直接是change number
        return True, id_value, ""
    
    elif id_type == 'change_id':
        # 通过Change-Id搜索
        print(f"  通过Change-Id搜索...")
        success, result = search_by_change_id(base_url, id_value, username, password)
        if not success:
            return False, "", result.get('message', '搜索失败')
        change_number = result.get('_number')
        if change_number:
            return True, str(change_number), ""
        return False, "", "无法获取Change Number"
    
    elif id_type == 'commit':
        # 通过commit hash搜索
        print(f"  通过Commit hash搜索...")
        success, result = search_by_commit(base_url, id_value, username, password)
        if not success:
            return False, "", result.get('message', '搜索失败')
        change_number = result.get('_number')
        if change_number:
            return True, str(change_number), ""
        return False, "", "无法获取Change Number"
    
    else:
        return False, "", f"无法识别的标识符格式: {identifier}"


def main():
    if len(sys.argv) < 3:
        print("""
使用方法:
    python gerrit_cherry_pick.py <identifiers> <target_branch> [config_file]

支持的标识符格式:
    1. Gerrit URL:      https://scgit.amlogic.com/#/c/610496/
    2. Change-Id:       I4ea5aed44ace170e7ee83fcacbbca0ba4ffbb5d6
    3. Commit Hash:     3eb601ad7b1c8865678ae214c13718f7da3e585e 或 3eb601ad7
    4. Commit Message:  (自动提取其中的Change-Id)

示例:
    # 使用Gerrit URL
    python gerrit_cherry_pick.py "https://scgit.amlogic.com/#/c/610496/" "main"
    
    # 使用Change-Id
    python gerrit_cherry_pick.py "I4ea5aed44ace170e7ee83fcacbbca0ba4ffbb5d6" "main"
    
    # 使用Commit hash (简写也支持)
    python gerrit_cherry_pick.py "3eb601ad7" "main"
    
    # 批量处理 (逗号或空格分隔)
    python gerrit_cherry_pick.py "610496, I4ea5aed44ace170e7ee83fcacbbca0ba4ffbb5d6, 3eb601ad7" "main"

参数:
    identifiers     - 变更标识符，支持URL/Change-Id/Commit Hash
    target_branch   - 目标分支名称
    config_file     - 配置文件路径 (可选, 默认: config.json)
        """)
        sys.exit(1)

    # 支持多个标识符，空格或逗号分隔
    identifiers_input = sys.argv[1]
    identifiers = [id.strip() for id in identifiers_input.replace(',', ' ').split() if id.strip()]
    target_branch = sys.argv[2]
    config_file = sys.argv[3] if len(sys.argv) > 3 else "config.json"

    print("=" * 60)
    print("Gerrit Cherry-Pick 工具")
    print("=" * 60)
    print(f"目标分支: {target_branch}")
    print(f"待处理变更数: {len(identifiers)}")

    # 加载配置
    print(f"\n加载配置文件: {config_file}")
    try:
        config = load_config(config_file)
    except Exception as e:
        print(f"错误: 无法加载配置文件 - {e}")
        sys.exit(1)

    base_url = config['gerrit']['base_url'].rstrip('/')
    username = config['gerrit']['username']
    password = config['gerrit']['password']

    # 存储所有结果
    all_results = []
    total_success = 0
    total_failed = 0

    # 处理每个标识符
    for idx, identifier in enumerate(identifiers, 1):
        print(f"\n{'='*60}")
        print(f"处理变更 {idx}/{len(identifiers)}: {identifier}")
        print('='*60)

        # 解析标识符
        resolve_success, change_number, error_msg = resolve_identifier(
            base_url, identifier, username, password
        )
        
        if not resolve_success:
            print(f"✗ 错误: {error_msg}")
            all_results.append({
                'url': identifier,
                'change_id': None,
                'success': False,
                'error': error_msg,
                'details': {},
                'cherry_pick_result': {}
            })
            total_failed += 1
            continue

        print(f"Change Number: {change_number}")

        # 获取变更详情
        print(f"\n获取变更详情...")
        details_success, change_details = get_change_details(
            base_url, change_number, username, password
        )

        if not details_success:
            print(f"✗ 错误: 无法获取变更详情 - {change_details.get('message', '未知错误')}")
            all_results.append({
                'url': identifier,
                'change_id': change_number,
                'success': False,
                'error': change_details.get('message', '获取详情失败'),
                'details': {},
                'cherry_pick_result': {}
            })
            total_failed += 1
            continue

        print(f"主题: {change_details.get('subject', 'N/A')}")
        print(f"当前分支: {change_details.get('branch', 'N/A')}")
        print(f"项目: {change_details.get('project', 'N/A')}")
        print(f"Change-Id: {change_details.get('change_id', 'N/A')}")

        # 执行cherry-pick
        print(f"\n执行cherry-pick到分支: {target_branch}")
        cherry_pick_success, cherry_pick_result = cherry_pick_change(
            base_url, change_number, target_branch, username, password
        )

        if cherry_pick_success:
            print("✓ Cherry-pick 成功!")
            if isinstance(cherry_pick_result, dict):
                new_id = cherry_pick_result.get('id', 'N/A')
            elif isinstance(cherry_pick_result, list) and len(cherry_pick_result) > 0:
                new_id = cherry_pick_result[0].get('id', 'N/A')
            else:
                new_id = 'N/A'
            print(f"  新Change ID: {new_id}")
            total_success += 1
        else:
            print("✗ Cherry-pick 失败")
            error_msg = '未知错误'
            if isinstance(cherry_pick_result, dict):
                error_msg = cherry_pick_result.get('message', '未知错误')
            elif isinstance(cherry_pick_result, str):
                error_msg = cherry_pick_result
            print(f"  错误: {error_msg}")
            total_failed += 1

        all_results.append({
            'url': identifier,
            'change_id': change_number,
            'success': cherry_pick_success,
            'error': None if cherry_pick_success else (cherry_pick_result.get('message', '未知错误') if isinstance(cherry_pick_result, dict) else str(cherry_pick_result)),
            'details': change_details,
            'cherry_pick_result': cherry_pick_result
        })

    # 生成汇总报告
    print("\n" + "=" * 60)
    print("生成汇总HTML报告...")
    report_file = generate_html_report_batch(
        target_branch,
        all_results,
        total_success,
        total_failed
    )
    print(f"✓ 报告已保存: {report_file}")

    print("\n" + "=" * 60)
    print("处理完成!")
    print(f"  成功: {total_success}")
    print(f"  失败: {total_failed}")
    print("=" * 60)

    # 返回退出码
    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    main()
