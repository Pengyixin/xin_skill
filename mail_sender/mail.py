import smtplib
import json
import argparse
import sys
from email.mime.text import MIMEText
from email.header import Header
from pathlib import Path

# 加载配置文件
def load_config(config_path='config.json'):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found: {config_path}")
        print("Please create config.json file. See README for example.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}")
        sys.exit(1)

config = load_config()
EMAIL_CONFIG = config['email']
 
def sync_issue_failed(issue_info, error_msg="", html_file=None, recipient=None, prepend_text=None, append_text=None):
    print(f"Trying to send email for issue: {issue_info}...")
    
    if html_file:
        # 从 HTML 文件读取内容
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                contents = f.read()
        except FileNotFoundError:
            print(f"Error: HTML file not found: {html_file}")
            return
        except Exception as e:
            print(f"Error reading HTML file: {e}")
            return
    else:
        # 使用默认模板
        contents = f"""
    Hi Yixin:<br/><br/>
    <b><font color='red'>eCode issue sync to jira failed</font></b><br/><br/>
    <b>Issue Info:</b> {issue_info}<br/>
    <b>Error Details:</b><br/>
    <pre>{error_msg}</pre>
    """
    
    # 在 HTML 内容前添加文字
    if prepend_text:
        contents = f"<p>{prepend_text}</p><br/>" + contents
    
    # 在 HTML 内容后添加文字
    if append_text:
        contents = contents + f"<br/><p>{append_text}</p>"
    message = MIMEText(contents, 'html', 'utf-8')
    sender_name = EMAIL_CONFIG['default_sender_name']
    sender_email = EMAIL_CONFIG['sender_email']
    message["From"] = str(Header(f"{sender_name}<{sender_email}>", 'utf-8'))
    message["To"] = recipient if recipient else EMAIL_CONFIG['default_recipient']
    message["Subject"] = f"Ecode issue sync to jira failed - {issue_info}"
   
    send_email(message, sender_email, EMAIL_CONFIG['sender_password'], EMAIL_CONFIG['smtp_server'])
 
def send_email(message, sender_email, sender_password, smtp_server):
    smtp_port = EMAIL_CONFIG['smtp_port']
    try:
        smtpObj = smtplib.SMTP(smtp_server, smtp_port)
        # 如果内部 smtp 不强制要求验证和 tls，可以按需注释放开下面两行
        smtpObj.ehlo()
        smtpObj.starttls()
        if sender_password:
            smtpObj.login(sender_email, sender_password)
            
        to_recipients = message.get("To", "").split(",")
        cc_recipients = message.get("CC", "").split(",") if "CC" in message else []
        all_recipients = [email.strip() for email in to_recipients + cc_recipients if email.strip()]
        
        smtpObj.sendmail(sender_email, all_recipients, message.as_string())
        print("Send email success!")
    except Exception as e:
        print(f"Error: Send email fail! {e}")

def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description='邮件发送工具 - 发送 HTML 格式邮件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 使用默认模板发送邮件
  python mail.py -i "Issue-123" -e "连接超时"
  
  # 使用 HTML 文件发送邮件
  python mail.py -i "Issue-456" -f email_template.html
  
  # 指定收件人
  python mail.py -i "Issue-789" -e "系统错误" -t admin@example.com
  
  # 指定配置文件路径
  python mail.py -i "Issue-000" -e "测试" -c /path/to/config.json
  
  # 在 HTML 前添加文字
  python mail.py -i "Issue-111" -f template.html --prepend "这是前置说明"
  
  # 在 HTML 后添加文字
  python mail.py -i "Issue-222" -f template.html --append "这是后置说明"
  
  # 前后都添加文字
  python mail.py -i "Issue-333" -f template.html --prepend "前置内容" --append "后置内容"
        '''
    )
    
    parser.add_argument('-i', '--issue', required=True,
                        help='Issue 信息/邮件主题标识 (必填)')
    parser.add_argument('-e', '--error', default='',
                        help='错误详情 (可选，与 -f 互斥)')
    parser.add_argument('-f', '--file', dest='html_file',
                        help='HTML 模板文件路径 (可选，与 -e 互斥)')
    parser.add_argument('-t', '--to', dest='recipient',
                        help='收件人邮箱 (可选，覆盖配置文件中的默认值)')
    parser.add_argument('-c', '--config', default='config.json',
                        help='配置文件路径 (默认: config.json)')
    parser.add_argument('--prepend', dest='prepend_text',
                        help='在 HTML 内容前添加的文字')
    parser.add_argument('--append', dest='append_text',
                        help='在 HTML 内容后添加的文字')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    
    args = parser.parse_args()
    
    # 如果指定了配置文件，重新加载
    global config, EMAIL_CONFIG
    if args.config != 'config.json':
        config = load_config(args.config)
        EMAIL_CONFIG = config['email']
    
    # 发送邮件
    sync_issue_failed(
        issue_info=args.issue,
        error_msg=args.error,
        html_file=args.html_file,
        recipient=args.recipient,
        prepend_text=args.prepend_text,
        append_text=args.append_text
    )

if __name__ == "__main__":
    main()