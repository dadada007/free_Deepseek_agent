# -*- coding: utf-8 -*-
"""
邮件自动化工具集 - 支持发送邮件、读取邮件、批量发送、附件支持
"""

import os
import json
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import policy
from email.parser import BytesParser
from datetime import datetime


_EMAIL_CONFIG = {
    'smtp_host': None, 'smtp_port': 587, 'imap_host': None,
    'imap_port': 993, 'username': None, 'password': None, 'use_ssl': True,
}


def _set_email_config(args: dict) -> str:
    try:
        global _EMAIL_CONFIG
        for key in ['smtp_host', 'smtp_port', 'imap_host', 'imap_port', 'username', 'password', 'use_ssl']:
            if key in args:
                _EMAIL_CONFIG[key] = args[key]
        if not _EMAIL_CONFIG['imap_host'] and _EMAIL_CONFIG['smtp_host']:
            _EMAIL_CONFIG['imap_host'] = _EMAIL_CONFIG['smtp_host'].replace('smtp', 'imap')
        return json.dumps({'success': True, 'message': '邮件配置已更新'}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 配置失败: {e}"


def _send_email(args: dict) -> str:
    try:
        to = args.get('to', '')
        subject = args.get('subject', '无主题')
        body = args.get('body', '')
        is_html = args.get('html', False)
        attachments = args.get('attachments', [])
        if not to:
            return "❌ 请提供收件人地址"
        if not body:
            return "❌ 请提供邮件内容"
        config = _EMAIL_CONFIG
        if not config['smtp_host'] or not config['username'] or not config['password']:
            return "❌ 请先设置邮件配置: set_email_config"
        msg = MIMEMultipart()
        msg['From'] = config['username']
        msg['To'] = to
        msg['Subject'] = subject
        if is_html:
            msg.attach(MIMEText(body, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
        for att_path in attachments:
            if not os.path.exists(att_path):
                return f"❌ 附件不存在: {att_path}"
            with open(att_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                from email.encoders import encode_base64
                encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(att_path)}"')
                msg.attach(part)
        if config.get('use_ssl', True):
            server = smtplib.SMTP_SSL(config['smtp_host'], config['smtp_port'])
        else:
            server = smtplib.SMTP(config['smtp_host'], config['smtp_port'])
            server.starttls()
        server.login(config['username'], config['password'])
        server.send_message(msg)
        server.quit()
        return json.dumps({'success': True, 'message': '邮件发送成功', 'to': to, 'subject': subject}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 发送邮件失败: {e}"


def _read_emails(args: dict) -> str:
    try:
        limit = args.get('limit', 10)
        folder = args.get('folder', 'INBOX')
        unread_only = args.get('unread_only', False)
        config = _EMAIL_CONFIG
        if not config['imap_host'] or not config['username'] or not config['password']:
            return "❌ 请先设置邮件配置: set_email_config"
        if config.get('use_ssl', True):
            mail = imaplib.IMAP4_SSL(config['imap_host'], config['imap_port'])
        else:
            mail = imaplib.IMAP4(config['imap_host'], config['imap_port'])
        mail.login(config['username'], config['password'])
        mail.select(folder)
        if unread_only:
            status, messages = mail.search(None, 'UNSEEN')
        else:
            status, messages = mail.search(None, 'ALL')
        if status != 'OK':
            return f"❌ 搜索邮件失败: {status}"
        msg_ids = messages[0].split()
        if not msg_ids:
            return "📭 收件箱为空"
        msg_ids = msg_ids[-limit:] if len(msg_ids) > limit else msg_ids
        emails = []
        for msg_id in reversed(msg_ids):
            status, data = mail.fetch(msg_id, '(RFC822)')
            if status != 'OK':
                continue
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email, policy=policy.default)
            emails.append({
                'id': msg_id.decode(), 'from': msg.get('From', ''),
                'subject': msg.get('Subject', '无主题'), 'date': msg.get('Date', ''),
            })
        mail.close()
        mail.logout()
        return json.dumps({'folder': folder, 'total': len(emails), 'emails': emails}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 读取邮件失败: {e}"


def _batch_send_email(args: dict) -> str:
    try:
        to_list = args.get('to', [])
        subject = args.get('subject', '无主题')
        body = args.get('body', '')
        if not to_list:
            return "❌ 请提供收件人列表"
        if not body:
            return "❌ 请提供邮件内容"
        results = []
        for email_addr in to_list:
            result = _send_email({'to': email_addr, 'subject': subject, 'body': body})
            results.append({'to': email_addr, 'result': result})
        return json.dumps({'success': True, 'total': len(to_list), 'results': results}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 批量发送失败: {e}"


def _get_email_config(args: dict) -> str:
    config = _EMAIL_CONFIG
    safe_config = {
        'smtp_host': config['smtp_host'], 'smtp_port': config['smtp_port'],
        'imap_host': config['imap_host'], 'username': config['username'],
        'password': '***已设置***' if config['password'] else '未设置',
        'configured': bool(config['smtp_host'] and config['username'] and config['password'])
    }
    return json.dumps(safe_config, ensure_ascii=False, indent=2)


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="set_email_config", description="设置邮件配置", parameters={"type": "object", "properties": {"smtp_host": {"type": "string"}, "username": {"type": "string"}, "password": {"type": "string"}}}, func=_set_email_config)
    tools.register(name="send_email", description="发送邮件。参数: to, subject, body, attachments", parameters={"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}, "attachments": {"type": "array"}}}, func=_send_email)
    tools.register(name="read_emails", description="读取收件箱邮件。参数: limit, folder, unread_only", parameters={"type": "object", "properties": {"limit": {"type": "integer"}, "folder": {"type": "string"}, "unread_only": {"type": "boolean"}}}, func=_read_emails)
    tools.register(name="batch_send_email", description="批量发送邮件。参数: to(收件人列表), subject, body", parameters={"type": "object", "properties": {"to": {"type": "array"}, "subject": {"type": "string"}, "body": {"type": "string"}}}, func=_batch_send_email)
    tools.register(name="get_email_config", description="查看当前邮件配置状态", parameters={"type": "object", "properties": {}}, func=_get_email_config)
    return 5


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["set_email_config", "send_email", "read_emails", "batch_send_email", "get_email_config"]:
        tools.TOOLS.pop(name, None)
