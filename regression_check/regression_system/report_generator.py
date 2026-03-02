"""
报告生成器
生成回归检测结果的详细报告
"""

import json
import csv
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from .regression_engine import RegressionResult, RegressionSummary


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, output_dir: str = None):
        """
        初始化报告生成器
        
        Args:
            output_dir: 输出目录，如果为None则使用默认目录
        """
        if output_dir is None:
            output_dir = "./reports"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ 报告生成器初始化成功，输出目录: {self.output_dir}")
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def generate_json_report(self, results: List[RegressionResult], summary: RegressionSummary, 
                            filename: str = None, filename_prefix: str = None) -> str:
        """
        生成JSON格式报告
        
        Args:
            results: 检测结果列表
            summary: 统计摘要
            filename: 文件名，如果为None则自动生成
            filename_prefix: 文件名前缀
        
        Returns:
            报告文件路径
        """
        if filename is None:
            timestamp = self._get_timestamp()
            prefix = filename_prefix + "_" if filename_prefix else ""
            filename = f"{prefix}regression_report_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "summary": summary.to_dict(),
            "results": [result.to_dict() for result in results],
            "total_results": len(results)
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON报告已生成: {filepath}")
        return str(filepath)
    
    def generate_csv_report(self, results: List[RegressionResult], summary: RegressionSummary,
                           filename: str = None, filename_prefix: str = None) -> str:
        """
        生成CSV格式报告
        
        Args:
            results: 检测结果列表
            summary: 统计摘要
            filename: 文件名，如果为None则自动生成
            filename_prefix: 文件名前缀
        
        Returns:
            报告文件路径
        """
        if filename is None:
            timestamp = self._get_timestamp()
            prefix = filename_prefix + "_" if filename_prefix else ""
            filename = f"{prefix}regression_report_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        # 定义CSV字段
        fieldnames = [
            "jira_key",
            "owner",
            "summary",
            "status",
            "needs_regression",
            "regression_status",
            "related_gerrits_count",
            "gerrit_merged",
            "clone_jiras_count",
            "days_since_verified"
        ]
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                row = {
                    "jira_key": result.jira_key,
                    "owner": result.owner or "",
                    "summary": result.summary[:100],  # 限制长度
                    "status": result.status,
                    "needs_regression": "是" if result.needs_regression else "否",
                    "regression_status": result.regression_status.value if result.regression_status else "错误",
                    "related_gerrits_count": len(result.related_gerrits),
                    "gerrit_merged": "是" if result.gerrit_merged else "否",
                    "clone_jiras_count": len(result.clone_jiras),
                    "days_since_verified": result.days_since_verified
                }
                writer.writerow(row)
        
        print(f"✅ CSV报告已生成: {filepath}")
        return str(filepath)
    
    def generate_html_report(self, results: List[RegressionResult], summary: RegressionSummary,
                            filename: str = None, filename_prefix: str = None, command: str = "") -> str:
        """
        生成HTML格式报告
        
        Args:
            results: 检测结果列表
            summary: 统计摘要
            filename: 文件名，如果为None则自动生成
            filename_prefix: 文件名前缀
            command: 生成报告使用的命令
        
        Returns:
            报告文件路径
        """
        if filename is None:
            timestamp = self._get_timestamp()
            prefix = filename_prefix + "_" if filename_prefix else ""
            filename = f"{prefix}regression_report_{timestamp}.html"
        
        filepath = self.output_dir / filename
        
        # 生成HTML内容
        html_content = self._generate_html_content(results, summary, command)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML报告已生成: {filepath}")
        return str(filepath)
    
    def _generate_html_content(self, results: List[RegressionResult], summary: RegressionSummary, command: str = "") -> str:
        """生成HTML内容"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 统计颜色
        def get_status_color(status: str) -> str:
            status_colors = {
                "已回归": "#28a745",  # 绿色
                "未回归": "#dc3545",  # 红色
                "需要回归": "#ffc107",  # 黄色
                "不需要回归": "#6c757d",  # 灰色
                "错误": "#6c757d"  # 灰色
            }
            return status_colors.get(status, "#6c757d")
        
        # 统计各owner未回归的jira数
        owner_not_regressed = {}
        for result in results:
            if result.regression_status and result.regression_status.value == "未回归":
                owner = result.owner or "未分配"
                owner_not_regressed[owner] = owner_not_regressed.get(owner, 0) + 1
        
        # 按未回归数量排序
        owner_not_regressed_sorted = sorted(owner_not_regressed.items(), key=lambda x: x[1], reverse=True)
        
        owner_stats_html = ""
        for owner, count in owner_not_regressed_sorted:
            owner_stats_html += f"<li><strong>{owner}</strong>: {count}个</li>"
        
        if not owner_stats_html:
            owner_stats_html = "<li>无未回归的issues</li>"
        
        # 按已过天数降序排序
        sorted_results = sorted(results, key=lambda x: x.days_since_verified, reverse=True)
        
        # 生成结果行
        result_rows = ""
        for i, result in enumerate(sorted_results, 1):
            status = result.regression_status.value if result.regression_status else "错误"
            status_color = get_status_color(status)
            
            result_rows += f"""
            <tr>
                <td>{i}</td>
                <td><a href="https://jira.amlogic.com/browse/{result.jira_key}" target="_blank">{result.jira_key}</a></td>
                <td>{result.owner or "-"}</td>
                <td>{result.summary[:80]}...</td>
                <td>{result.status}</td>
                <td>{"是" if result.needs_regression else "否"}</td>
                <td style="color: {status_color}; font-weight: bold;">{status}</td>
                <td>{len(result.related_gerrits)}</td>
                <td>{"是" if result.gerrit_merged else "否"}</td>
                <td>{len(result.clone_jiras)}</td>
                <td>{result.days_since_verified}天</td>
            </tr>
            """
        
        # 完整的HTML模板
        html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>回归公版检测报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }}
        
        .header h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .header .timestamp {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .summary-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border: 1px solid #e9ecef;
        }}
        
        .summary-card h3 {{
            color: #495057;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .summary-card.total .value {{ color: #2c3e50; }}
        .summary-card.regressed .value {{ color: #28a745; }}
        .summary-card.not-regressed .value {{ color: #dc3545; }}
        .summary-card.needs-regression .value {{ color: #ffc107; }}
        
        .owner-stats {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .owner-stats h3 {{
            color: #dc3545;
            margin-bottom: 15px;
        }}
        
        .owner-list {{
            list-style: none;
            padding: 0;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .owner-list li {{
            background: #f8f9fa;
            padding: 10px 15px;
            border-radius: 5px;
            border-left: 4px solid #dc3545;
        }}
        .summary-card.not-required .value {{ color: #6c757d; }}
        .summary-card.errors .value {{ color: #6c757d; }}
        
        .results-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .results-table th {{
            background-color: #2c3e50;
            color: white;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        .results-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .results-table tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 15px;
            }}
            
            .summary {{
                grid-template-columns: 1fr;
            }}
            
            .results-table {{
                display: block;
                overflow-x: auto;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>回归公版检测报告</h1>
            <div class="timestamp">生成时间: {timestamp}</div>
        </div>
        
        <div class="summary">
            <div class="summary-card total">
                <h3>总计 Issues</h3>
                <div class="value">{total_issues}</div>
            </div>
            <div class="summary-card needs-regression">
                <h3>需要回归</h3>
                <div class="value">{needs_regression}</div>
            </div>
            <div class="summary-card regressed">
                <h3>已回归</h3>
                <div class="value">{regressed}</div>
            </div>
            <div class="summary-card not-regressed">
                <h3>未回归</h3>
                <div class="value">{not_regressed}</div>
            </div>
            <div class="summary-card not-required">
                <h3>不需要回归</h3>
                <div class="value">{not_required}</div>
            </div>
            <div class="summary-card errors">
                <h3>错误</h3>
                <div class="value">{errors}</div>
            </div>
        </div>
        
        <div class="owner-stats">
            <h3>各Owner未回归统计</h3>
            <ul class="owner-list">
                {owner_stats}
            </ul>
        </div>
        
        <h2>详细结果</h2>
        <table class="results-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>JIRA</th>
                    <th>Owner</th>
                    <th>摘要</th>
                    <th>状态</th>
                    <th>需回归</th>
                    <th>回归状态</th>
                    <th>Gerrit数</th>
                    <th>Gerrit合并</th>
                    <th>Clone数</th>
                    <th>已过天数</th>
                </tr>
            </thead>
            <tbody>
                {result_rows}
            </tbody>
        </table>
        
        <div class="footer">
            <p>回归检测系统 | 生成于 {timestamp}</p>
            <p>生成命令: <code>{command}</code></p>
            <p>注：此报告基于JIRA的customfield_11705字段和Gerrit合并状态进行检测</p>
        </div>
    </div>
    
    <script>
        // 简单的表格排序功能
        document.addEventListener('DOMContentLoaded', function() {{
            const table = document.querySelector('.results-table');
            const headers = table.querySelectorAll('th');
            let currentSort = {{ column: -1, ascending: true }};
            
            headers.forEach((header, index) => {{
                header.style.cursor = 'pointer';
                header.addEventListener('click', () => {{
                    sortTable(index);
                }});
            }});
            
            function sortTable(column) {{
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));
                
                // 判断排序方向
                const ascending = currentSort.column === column ? !currentSort.ascending : true;
                currentSort = {{ column, ascending }};
                
                rows.sort((a, b) => {{
                    const aText = a.children[column].textContent.trim();
                    const bText = b.children[column].textContent.trim();
                    
                    // 尝试转换为数字比较
                    const aNum = parseFloat(aText);
                    const bNum = parseFloat(bText);
                    
                    if (!isNaN(aNum) && !isNaN(bNum)) {{
                        return ascending ? aNum - bNum : bNum - aNum;
                    }}
                    
                    // 字符串比较
                    return ascending 
                        ? aText.localeCompare(bText) 
                        : bText.localeCompare(aText);
                }});
                
                // 重新排列行
                rows.forEach(row => tbody.appendChild(row));
                
                // 更新表头指示器
                headers.forEach((header, idx) => {{
                    header.textContent = header.textContent.replace(' ▲', '').replace(' ▼', '');
                    if (idx === column) {{
                        header.textContent += ascending ? ' ▲' : ' ▼';
                    }}
                }});
            }}
        }});
    </script>
</body>
</html>"""
        
        # 格式化HTML
        html = html_template.format(
            timestamp=timestamp,
            total_issues=summary.total_issues,
            needs_regression=summary.needs_regression,
            regressed=summary.regressed,
            not_regressed=summary.not_regressed,
            not_required=summary.not_required,
            errors=summary.errors,
            result_rows=result_rows,
            command=command,
            owner_stats=owner_stats_html
        )
        
        return html
