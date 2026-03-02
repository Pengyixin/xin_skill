"""
邮件发送模块
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from pathlib import Path


class EmailSender:
    """邮件发送器"""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str = "", 
                 password: str = "", from_addr: str = ""):
        """
        初始化邮件发送器
        
        Args:
            smtp_host: SMTP服务器地址
            smtp_port: SMTP服务器端口
            username: SMTP用户名
            password: SMTP密码
            from_addr: 发件人地址
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
    
    def send_email(self, to_addrs: List[str], subject: str, body: str,
                   attachments: List[str] = None, is_html: bool = False) -> bool:
        """
        发送邮件
        
        Args:
            to_addrs: 收件人列表
            subject: 邮件主题
            body: 邮件正文
            attachments: 附件路径列表
            is_html: 是否为HTML格式
        
        Returns:
            是否发送成功
        """
        if not to_addrs:
            print("⚠️  未指定收件人，跳过发送邮件")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = self.from_addr
        msg['To'] = ', '.join(to_addrs)
        msg['Subject'] = subject
        
        # 添加正文
        if is_html:
            msg.attach(MIMEText(body, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 添加附件
        if attachments:
            for file_path in attachments:
                self._add_attachment(msg, file_path)
        
        # 发送邮件
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                # 如果需要认证
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.sendmail(self.from_addr, to_addrs, msg.as_string())
            
            print(f"✅ 邮件发送成功: {subject}")
            print(f"   收件人: {', '.join(to_addrs)}")
            return True
            
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str) -> None:
        """添加附件"""
        try:
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            
            encoders.encode_base64(part)
            
            filename = Path(file_path).name
            part.add_header('Content-Disposition', f'attachment; filename={filename}')
            msg.attach(part)
            
        except Exception as e:
            print(f"⚠️  添加附件失败 {file_path}: {e}")
