#!/usr/bin/env python3
"""
回归检测系统主程序
用于查找未回归公版的提交

核心逻辑：
1. 查询对应的verify或者close的jira里面是否需要回归公版，根据jira信息的issue.fields.customfield_11705，如果是"Confirmed Yes"，则是要回归的
2. 检测jira是否存在gerrit提交，若存在，确认此gerrit提交是否已经合并，若没有，走到步骤3
3. 确认是否有clone的jira，若存在，且如果关闭，需确认jira中是否有gerrit提交以及是否合并，如果还是没有，则说明此问题的patch代码还没回归

使用方法:
  python regression_detector.py [选项]

选项:
  --project PROJECT    指定JIRA项目(如SWPL)，默认为搜索所有项目
  --days DAYS         搜索最近多少天的issues，默认为30天
  --jira JIRA_KEY     检测单个JIRA issue
  --file FILE_PATH    从文件读取JIRA列表进行检测
  --label LABEL [LABEL ...] 按label搜索JIRA，如DECODER-CORE-20260126
  --output FORMAT     输出格式: json, csv, html, all (默认为all)
  --verbose           显示详细输出信息
  --help              显示帮助信息

示例:
  # 搜索最近30天verify/close的issues并检测
  python regression_detector.py --project SWPL --days 30
  
  # 检测单个JIRA
  python regression_detector.py --jira SWPL-252395
  
  # 从文件读取JIRA列表并生成HTML报告
  python regression_detector.py --file jira_list.txt --output html
  
  # 按label搜索并检测
  python regression_detector.py --label DECODER-CORE-20260126 --days 30
  
  # 按label搜索指定项目并检测
  python regression_detector.py --label DECODER-CORE-20260126 --project SWPL
"""

import argparse
import sys
import os
from datetime import datetime

# 添加项目目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from regression_system import (
    ConfigManager, 
    RegressionEngine, 
    ReportGenerator
)
from regression_system.email_sender import EmailSender


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="回归检测系统 - 查找未回归公版的提交",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
核心检测逻辑:
  1. 检查JIRA的customfield_11705字段是否为"Confirmed Yes"
  2. 检查关联的gerrit是否已合并
  3. 检查clone的jira是否有已回归的gerrit
  
输出格式:
  - json: JSON格式报告，适合程序处理
  - csv: CSV格式报告，适合Excel导入
  - html: HTML格式报告，适合浏览器查看
  - all: 生成所有格式的报告
        """,
    )
    
    # 通用过滤参数
    parser.add_argument(
        "--project",
        type=str,
        help="指定JIRA项目(如SWPL)，默认为搜索所有项目"
    )
    
    # 定义操作模式组（这些是互斥的操作模式）
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--jira",
        type=str,
        help="检测单个JIRA issue，如SWPL-252395"
    )
    mode_group.add_argument(
        "--file",
        type=str,
        help="从文件读取JIRA列表进行检测"
    )
    mode_group.add_argument(
        "--label",
        type=str,
        nargs="+",  # 接受一个或多个label
        help="按label搜索JIRA，如DECODER-CORE-20260126"
    )
    mode_group.add_argument(
        "--jql",
        type=str,
        help="直接使用JQL查询，如'(labels = DECODER-CORE-20260209 OR labels = VDEC-VA20260209) && assignee = Yinan.Zhang'"
    )
    
    # 其他参数
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="搜索最近多少天的issues，默认为30天"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=1000,
        help="最大搜索结果数，默认为1000，最大1000"
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=["json", "csv", "html", "all"],
        default="all",
        help="输出格式，默认为all（生成所有格式）"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细输出信息"
    )
    parser.add_argument(
        "--email",
        type=str,
        help="发送邮件通知，多个收件人用逗号分隔"
    )
    parser.add_argument(
        "--email-only",
        action="store_true",
        help="仅发送邮件，不生成报告文件"
    )
    
    return parser.parse_args()


def print_banner():
    """打印程序横幅"""
    print("=" * 70)
    print("回归检测系统 v1.0.0")
    print("查找未回归公版的提交")
    print("=" * 70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def print_summary(results, summary, output_files):
    """打印检测摘要"""
    print("\n" + "=" * 70)
    print("检测完成")
    print("=" * 70)
    
    print(f"\n统计摘要:")
    print(f"  总计 Issues: {summary.total_issues}")
    print(f"  需要回归: {summary.needs_regression}")
    print(f"  已回归: {summary.regressed}")
    print(f"  未回归: {summary.not_regressed}")
    print(f"  不需要回归: {summary.not_required}")
    print(f"  错误: {summary.errors}")
    
    if summary.not_regressed > 0:
        print(f"\n⚠️  发现 {summary.not_regressed} 个未回归的issues:")
        for result in results:
            if result.regression_status and result.regression_status.value == "未回归":
                print(f"  - {result.jira_key}: {result.summary[:60]}...")
    
    if output_files:
        print(f"\n报告文件:")
        for format_name, filepath in output_files.items():
            print(f"  {format_name.upper()}: {filepath}")
    
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)


def main():
    """主函数"""
    args = parse_arguments()
    
    # 打印横幅
    print_banner()
    
    try:
        # 初始化配置管理器
        print("初始化配置...")
        config_manager = ConfigManager()
        config_manager.validate_config()
        
        # 初始化回归检测引擎
        print("初始化回归检测引擎...")
        engine = RegressionEngine(config_manager)
        
        # 初始化报告生成器
        print("初始化报告生成器...")
        report_generator = ReportGenerator()
        
        # 根据参数执行不同的检测模式
        results = []
        summary = None
        
        if args.jira:
            # 单个JIRA检测模式
            print(f"检测单个JIRA: {args.jira}")
            result = engine.check_single_jira(args.jira)
            results = [result]
            
            # 创建临时摘要
            from regression_system.regression_engine import RegressionSummary
            summary = RegressionSummary()
            summary.update(result)
            
        elif args.file:
            # 文件模式
            print(f"从文件读取JIRA列表: {args.file}")
            results, summary = engine.check_jira_list_file(args.file)
            
        elif args.label:
            # Label搜索模式
            print(f"按label搜索JIRA: {args.label}")
            
            # 默认搜索Verified/Closed/Resolved状态的issues
            default_statuses = ["Verified", "Closed", "Resolved"]
            
            results, summary = engine.search_by_labels_and_check(
                labels=args.label,
                project=args.project,
                statuses=default_statuses,
                days=args.days,
                max_results=args.max_results
            )
            
        elif args.jql:
            # JQL查询模式
            print(f"使用JQL查询: {args.jql}")
            
            results, summary = engine.search_by_jql_and_check(args.jql, max_results=args.max_results)
            
        else:
            # 默认搜索模式（verify/close状态）
            print(f"搜索verify/close状态的issues")
            if args.project:
                print(f"项目: {args.project}")
            print(f"时间范围: 最近{args.days}天")
            
            results, summary = engine.search_and_check(
                project=args.project,
                days=args.days,
                max_results=args.max_results
            )
        
        if not results:
            print("⚠️  未找到检测结果")
            return 1
        
        # 生成报告
        print(f"\n生成报告...")
        output_files = {}
        
        if args.output in ["json", "all"]:
            json_file = report_generator.generate_json_report(results, summary)
            output_files["json"] = json_file
        
        if args.output in ["csv", "all"]:
            csv_file = report_generator.generate_csv_report(results, summary)
            output_files["csv"] = csv_file
        
        # 构建生成报告使用的命令
        command = "python regression_detector.py"
        if args.project:
            command += f" --project {args.project}"
        if args.days != 30:
            command += f" --days {args.days}"
        if args.jira:
            command += f" --jira {args.jira}"
        if args.label:
            command += f" --label {' '.join(args.label)}"
        if args.jql:
            command += f' --jql "{args.jql}"'
        if args.file:
            command += f" --file {args.file}"
        if args.max_results != 1000:
            command += f" --max-results {args.max_results}"
        if args.output != "all":
            command += f" --output {args.output}"
        
        if args.output in ["html", "all"]:
            html_file = report_generator.generate_html_report(results, summary, command=command)
            output_files["html"] = html_file
        
        # 生成仅包含未回归的报告
        not_regressed_results = [r for r in results if r.regression_status and r.regression_status.value == "未回归"]
        
        if not_regressed_results:
            # 创建未回归结果的摘要
            from regression_system.regression_engine import RegressionSummary
            not_regressed_summary = RegressionSummary()
            for result in not_regressed_results:
                not_regressed_summary.update(result)
            
            print(f"\n生成未回归专项报告...")
            
            if args.output in ["json", "all"]:
                json_file = report_generator.generate_json_report(
                    not_regressed_results, not_regressed_summary, 
                    filename_prefix="not_regressed"
                )
                output_files["json_not_regressed"] = json_file
            
            if args.output in ["csv", "all"]:
                csv_file = report_generator.generate_csv_report(
                    not_regressed_results, not_regressed_summary,
                    filename_prefix="not_regressed"
                )
                output_files["csv_not_regressed"] = csv_file
            
            if args.output in ["html", "all"]:
                html_file = report_generator.generate_html_report(
                    not_regressed_results, not_regressed_summary,
                    filename_prefix="not_regressed",
                    command=command
                )
                output_files["html_not_regressed"] = html_file
        
        # 打印摘要
        print_summary(results, summary, output_files)
        
        # 发送邮件
        if args.email or config_manager.get_email_config().get('to'):
            email_config = config_manager.get_email_config()
            if not email_config.get('smtp_host'):
                print("⚠️  邮件配置缺失，跳过发送邮件")
            else:
                # 优先使用命令行参数，否则使用配置文件中的默认收件人
                if args.email:
                    to_addrs = [addr.strip() for addr in args.email.split(',')]
                else:
                    to_addrs = email_config.get('to', [])
                
                email_sender = EmailSender(
                    smtp_host=email_config.get('smtp_host', ''),
                    smtp_port=email_config.get('smtp_port', 25),
                    username=email_config.get('username', ''),
                    password=email_config.get('password', ''),
                    from_addr=email_config.get('from', 'regression-detector@amlogic.com')
                )
                
                # 构建邮件内容
                subject = f"回归检测报告 - 发现 {summary.not_regressed} 个未回归issues"
                
                # HTML邮件内容
                html_body = f"""
                <html>
                <head>
                    <style>
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #4CAF50; color: white; }}
                        .warning {{ color: #ff6600; font-weight: bold; }}
                        .success {{ color: #4CAF50; font-weight: bold; }}
                        .error {{ color: #f44336; font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <h2>回归检测报告</h2>
                    <p>检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    
                    <h3>统计摘要</h3>
                    <ul>
                        <li>总计 Issues: <strong>{summary.total_issues}</strong></li>
                        <li>需要回归: <strong>{summary.needs_regression}</strong></li>
                        <li>已回归: <span class="success">{summary.regressed}</span></li>
                        <li>未回归: <span class="warning">{summary.not_regressed}</span></li>
                        <li>不需要回归: <strong>{summary.not_required}</strong></li>
                        <li>错误: <span class="error">{summary.errors}</span></li>
                    </ul>
                """
                
                if summary.not_regressed > 0:
                    html_body += f"""
                    <h3>⚠️ 未回归的Issues</h3>
                    <table>
                        <tr>
                            <th>JIRA</th>
                            <th>摘要</th>
                            <th>回归状态</th>
                        </tr>
                    """
                    for result in results:
                        if result.regression_status and result.regression_status.value == "未回归":
                            html_body += f"""
                            <tr>
                                <td>{result.jira_key}</td>
                                <td>{result.summary[:80]}...</td>
                                <td class="warning">{result.regression_status.value}</td>
                            </tr>
                            """
                    html_body += "</table>"
                
                html_body += """
                <p>详细报告请查看附件或访问 reports 目录</p>
                </body>
                </html>
                """
                
                # 收集附件
                attachments = list(output_files.values()) if output_files else []
                
                # 发送邮件
                email_sender.send_email(
                    to_addrs=to_addrs,
                    subject=subject,
                    body=html_body,
                    attachments=attachments,
                    is_html=True
                )
        
        # 如果发现有未回归的issues，返回非零退出码
        if summary.not_regressed > 0:
            print(f"\n⚠️  警告: 发现 {summary.not_regressed} 个未回归的issues")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        return 130
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
