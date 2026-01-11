#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从邮件中提取微信聊天记录
支持HTML邮件文件和附件
"""

import os
import re
import email
from email.parser import Parser
from email import policy
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser
import html
import zipfile
import base64

# 项目目录
PROJECT_ROOT = Path(__file__).parent.parent
CHAT_DIR = PROJECT_ROOT / "assets" / "chat"
IMAGES_DIR = PROJECT_ROOT / "assets" / "images"

class ChatHTMLParser(HTMLParser):
    """解析HTML中的聊天记录"""
    def __init__(self):
        super().__init__()
        self.messages = []
        self.current_message = {}
        self.in_message = False
        self.current_text = ""
        self.current_tag = None
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        attrs_dict = dict(attrs)
        
        # 检测可能的聊天消息容器
        if tag in ['div', 'p', 'tr', 'td']:
            class_name = attrs_dict.get('class', '').lower()
            if any(keyword in class_name for keyword in ['message', 'chat', 'msg', 'time', 'content']):
                self.in_message = True
                self.current_message = {}
    
    def handle_endtag(self, tag):
        if self.in_message and tag in ['div', 'p', 'tr', 'td']:
            if self.current_text.strip():
                self.current_message['content'] = self.current_text.strip()
                if self.current_message:
                    self.messages.append(self.current_message.copy())
            self.current_text = ""
            self.current_message = {}
            self.in_message = False
        self.current_tag = None
    
    def handle_data(self, data):
        if self.in_message or self.current_tag in ['div', 'p', 'span', 'td']:
            # 清理文本
            text = data.strip()
            if text:
                # 检测时间戳格式
                time_pattern = r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}[\s,]\d{1,2}:\d{1,2}:\d{1,2})|(\d{4}年\d{1,2}月\d{1,2}日[\s,]\d{1,2}:\d{1,2}:\d{1,2})'
                if re.search(time_pattern, text):
                    self.current_message['timestamp'] = text
                # 检测发送者
                elif any(keyword in text for keyword in ['您', '我', '秋璇', '：', ':']):
                    if 'sender' not in self.current_message:
                        self.current_message['sender'] = text.split('：')[0].split(':')[0]
                
                self.current_text += text + " "

def parse_html_email(html_file_path):
    """解析HTML邮件文件"""
    messages = []
    
    with open(html_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 方法1: 使用HTML解析器
    parser = ChatHTMLParser()
    parser.feed(content)
    messages.extend(parser.messages)
    
    # 方法2: 使用正则表达式提取聊天记录
    # 匹配常见的时间戳格式
    time_patterns = [
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}[\s,]\d{1,2}:\d{1,2}:\d{1,2})',  # 2025-09-01 10:30:15
        r'(\d{4}年\d{1,2}月\d{1,2}日[\s,]\d{1,2}:\d{1,2}:\d{1,2})',    # 2025年9月1日 10:30:15
        r'(\d{1,2}:\d{2}:\d{2})',                                      # 10:30:15
    ]
    
    # 提取所有可能的消息块
    # 微信邮件通常包含表格或div结构
    message_blocks = re.findall(r'<[^>]*>(.*?)</[^>]*>', content, re.DOTALL)
    
    for block in message_blocks:
        # 清理HTML标签
        text = re.sub(r'<[^>]+>', '', block)
        text = html.unescape(text)
        text = text.strip()
        
        if len(text) > 5:
            # 查找时间戳
            timestamp = None
            for pattern in time_patterns:
                match = re.search(pattern, text)
                if match:
                    timestamp = match.group(1)
                    break
            
            # 查找发送者
            sender = None
            if '：' in text or ':' in text:
                parts = re.split('[：:]', text, 1)
                if len(parts) == 2:
                    sender = parts[0].strip()
                    content_text = parts[1].strip()
                else:
                    content_text = text
            else:
                content_text = text
            
            if content_text and len(content_text) > 3:
                messages.append({
                    'timestamp': timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'sender': sender or '未知',
                    'content': content_text
                })
    
    # 去重
    unique_messages = []
    seen = set()
    for msg in messages:
        content = msg.get('content', '')
        if content and content not in seen:
            seen.add(content)
            unique_messages.append(msg)
    
    return unique_messages

def parse_text_content(text_content):
    """解析纯文本格式的聊天记录"""
    messages = []
    lines = text_content.split('\n')
    
    current_message = {}
    current_content = []
    current_date = None  # 当前日期（从分隔符中提取）
    
    # 微信邮件格式：
    # —————  2025-10-7  —————
    # 孟秋璇  19:39
    # 消息内容
    # 孟祥志  22:15
    # 消息内容
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_content and current_message:
                current_message['content'] = '\n'.join(current_content)
                messages.append(current_message.copy())
                current_message = {}
                current_content = []
            continue
        
        # 匹配日期分隔符：—————  2025-10-7  —————
        date_sep_match = re.search(r'[—\-]+[\s]*(\d{4}[-/]\d{1,2}[-/]\d{1,2})[\s]*[—\-]+', line)
        if date_sep_match:
            current_date = date_sep_match.group(1)
            # 标准化日期格式
            current_date = re.sub(r'[/]', '-', current_date)
            parts = current_date.split('-')
            if len(parts) == 3:
                year, month, day = parts
                current_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            continue
        
        # 匹配发送者和时间：孟秋璇  19:39 或 孟祥志  22:15
        sender_time_match = re.search(r'^([^\s]+)\s+(\d{1,2}:\d{2})$', line)
        if sender_time_match:
            # 保存上一条消息
            if current_content and current_message:
                current_message['content'] = '\n'.join(current_content)
                messages.append(current_message.copy())
            
            # 新消息开始
            sender = sender_time_match.group(1)
            time_str = sender_time_match.group(2)
            
            # 构建完整时间戳
            if current_date:
                timestamp = f"{current_date} {time_str}:00"
            else:
                timestamp = datetime.now().strftime('%Y-%m-%d') + f" {time_str}:00"
            
            current_message = {
                'timestamp': timestamp,
                'sender': sender
            }
            current_content = []
            continue
        
        # 匹配标准时间戳格式
        time_pattern = r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}[\s,]\d{1,2}:\d{1,2}:\d{1,2})|(\d{4}年\d{1,2}月\d{1,2}日[\s,]\d{1,2}:\d{1,2}:\d{1,2})'
        time_match = re.search(time_pattern, line)
        
        if time_match:
            # 新消息开始
            if current_content and current_message:
                current_message['content'] = '\n'.join(current_content)
                messages.append(current_message.copy())
            
            current_message = {'timestamp': time_match.group(0)}
            current_content = []
            
            # 提取发送者
            parts = line.split(time_match.group(0), 1)
            if len(parts) > 1:
                sender_part = parts[0].strip()
                content_part = parts[1].strip()
                
                # 尝试提取发送者
                if '：' in sender_part or ':' in sender_part:
                    sender = sender_part.split('：')[0].split(':')[0].strip()
                    current_message['sender'] = sender
                    if content_part:
                        current_content.append(content_part)
                else:
                    # 可能是格式：时间 发送者 内容
                    words = sender_part.split()
                    if words:
                        current_message['sender'] = words[-1]
                        if content_part:
                            current_content.append(content_part)
        else:
            # 继续当前消息
            if current_message:
                current_content.append(line)
            else:
                # 可能是没有时间戳的消息，尝试识别发送者
                # 如果行首是已知的发送者名称
                if line and len(line) > 3:
                    # 检查是否是发送者名称（孟秋璇、孟祥志等）
                    known_senders = ['孟秋璇', '孟祥志', '秋璇', '四叔']
                    for sender_name in known_senders:
                        if line.startswith(sender_name):
                            # 这可能是新消息的开始
                            current_message = {
                                'timestamp': current_date + " 00:00:00" if current_date else datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'sender': sender_name
                            }
                            # 移除发送者名称，剩余是内容
                            content = line[len(sender_name):].strip()
                            if content:
                                current_content.append(content)
                            break
                    else:
                        # 不是发送者名称，可能是消息内容的一部分
                        if not current_message:
                            current_message = {
                                'timestamp': current_date + " 00:00:00" if current_date else datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'sender': '未知'
                            }
                        current_content.append(line)
    
    # 添加最后一条消息
    if current_content and current_message:
        current_message['content'] = '\n'.join(current_content)
        messages.append(current_message)
    
    return messages

def extract_from_email_file(email_file_path):
    """从邮件文件中提取内容"""
    all_messages = []
    
    # 尝试解析为.eml文件
    try:
        with open(email_file_path, 'rb') as f:
            msg = email.message_from_bytes(f.read(), policy=policy.default)
        
        # 提取邮件正文
        body = ""
        html_body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # 跳过附件部分（会在后面单独处理）
                if "attachment" in content_disposition.lower():
                    filename = part.get_filename()
                    if filename:
                        # 保存附件
                        attach_path = CHAT_DIR / filename
                        try:
                            with open(attach_path, 'wb') as attach_file:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    attach_file.write(payload)
                            print(f"  提取附件: {filename}")
                            
                            # 如果是文本或HTML附件，解析它
                            if filename.endswith(('.txt', '.html', '.htm')):
                                attach_messages = parse_attachment(attach_path)
                                all_messages.extend(attach_messages)
                        except Exception as e:
                            print(f"  保存附件失败 {filename}: {e}")
                    continue
                
                # 提取HTML正文（优先）
                if content_type == "text/html" and not html_body:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            # 尝试多种编码
                            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                                try:
                                    html_body = payload.decode(encoding)
                                    break
                                except:
                                    continue
                            if not html_body:
                                html_body = payload.decode('utf-8', errors='ignore')
                    except Exception as e:
                        print(f"  提取HTML正文失败: {e}")
                
                # 提取纯文本正文（作为备选）
                elif content_type == "text/plain" and not body:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            # 尝试多种编码
                            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                                try:
                                    body = payload.decode(encoding)
                                    break
                                except:
                                    continue
                            if not body:
                                body = payload.decode('utf-8', errors='ignore')
                    except Exception as e:
                        print(f"  提取文本正文失败: {e}")
        else:
            # 单部分邮件
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    content_type = msg.get_content_type()
                    if content_type == "text/html":
                        for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                            try:
                                html_body = payload.decode(encoding)
                                break
                            except:
                                continue
                        if not html_body:
                            html_body = payload.decode('utf-8', errors='ignore')
                    else:
                        for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                            try:
                                body = payload.decode(encoding)
                                break
                            except:
                                continue
                        if not body:
                            body = payload.decode('utf-8', errors='ignore')
            except Exception as e:
                print(f"  提取单部分邮件内容失败: {e}")
        
        # 优先解析HTML正文（通常包含更完整的格式）
        if html_body:
            print(f"  找到HTML正文 ({len(html_body)} 字符)")
            html_messages = parse_html_email_from_string(html_body)
            all_messages.extend(html_messages)
            print(f"  从HTML提取了 {len(html_messages)} 条消息")
        
        # 如果没有HTML或HTML提取失败，使用纯文本
        if body and (not html_body or len(all_messages) == 0):
            print(f"  找到文本正文 ({len(body)} 字符)")
            text_messages = parse_text_content(body)
            all_messages.extend(text_messages)
            print(f"  从文本提取了 {len(text_messages)} 条消息")
            
    except Exception as e:
        print(f"  解析邮件文件失败: {e}")
        import traceback
        traceback.print_exc()
        # 尝试作为HTML文件直接解析
        if email_file_path.suffix.lower() in ['.html', '.htm']:
            html_messages = parse_html_email(email_file_path)
            all_messages.extend(html_messages)
    
    return all_messages

def parse_html_email_from_string(html_content):
    """从HTML字符串解析聊天记录"""
    messages = []
    
    # 清理HTML
    text = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    
    # 提取文本内容
    text = re.sub(r'<[^>]+>', '\n', text)
    text = html.unescape(text)
    
    # 解析为文本格式
    messages = parse_text_content(text)
    
    return messages

def parse_attachment(attach_path):
    """解析附件文件"""
    messages = []
    
    ext = attach_path.suffix.lower()
    
    if ext == '.txt':
        with open(attach_path, 'r', encoding='utf-8') as f:
            content = f.read()
        messages = parse_text_content(content)
    elif ext in ['.html', '.htm']:
        messages = parse_html_email(attach_path)
    elif ext == '.zip':
        # 解压ZIP文件
        try:
            with zipfile.ZipFile(attach_path, 'r') as zip_ref:
                extract_dir = CHAT_DIR / attach_path.stem
                extract_dir.mkdir(exist_ok=True)
                zip_ref.extractall(extract_dir)
                
                # 解析解压后的文件
                for file in extract_dir.rglob('*'):
                    if file.is_file():
                        if file.suffix.lower() in ['.txt', '.html', '.htm']:
                            file_messages = parse_attachment(file)
                            messages.extend(file_messages)
        except Exception as e:
            print(f"  解压失败: {e}")
    
    return messages

def filter_by_date(messages, start_date="2025-09-01", end_date=None):
    """按日期过滤消息"""
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    filtered = []
    for msg in messages:
        timestamp = msg.get('timestamp', '')
        if not timestamp:
            continue
        
        # 提取日期
        date_match = re.search(r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})', timestamp)
        if date_match:
            year, month, day = date_match.groups()
            msg_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            if start_date <= msg_date <= end_date:
                filtered.append(msg)
        else:
            # 如果没有日期信息，保留（可能是格式问题）
            filtered.append(msg)
    
    return filtered

def main():
    """主函数"""
    print("=" * 60)
    print("邮件聊天记录提取工具")
    print("=" * 60)
    
    CHAT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    # 查找邮件文件
    email_files = []
    
    # 检查CHAT_DIR中的邮件文件
    for ext in ['.eml', '.html', '.htm', '.mhtml']:
        email_files.extend(list(CHAT_DIR.glob(f"*{ext}")))
    
    if not email_files:
        print(f"\n未找到邮件文件！")
        print(f"请将邮件文件（.eml, .html, .htm）放入: {CHAT_DIR}")
        print("\n操作步骤：")
        print("1. 在邮件客户端中，将微信发送的邮件另存为HTML文件")
        print("2. 或者直接复制邮件内容保存为.html文件")
        print("3. 将文件放入 assets/chat/ 目录")
        return
    
    print(f"\n找到 {len(email_files)} 个邮件文件")
    
    all_messages = []
    
    for email_file in email_files:
        print(f"\n处理文件: {email_file.name}")
        messages = extract_from_email_file(email_file)
        all_messages.extend(messages)
        print(f"  提取了 {len(messages)} 条消息")
    
    print(f"\n总共提取了 {len(all_messages)} 条消息")
    
    # 去重
    unique_messages = []
    seen = set()
    for msg in all_messages:
        content = msg.get('content', '')
        if content and content not in seen:
            seen.add(content)
            unique_messages.append(msg)
    
    print(f"去重后: {len(unique_messages)} 条消息")
    
    # 按日期过滤
    filtered_messages = filter_by_date(unique_messages, "2025-09-01")
    print(f"过滤后（2025-09-01至今）: {len(filtered_messages)} 条消息")
    
    # 按时间排序
    filtered_messages.sort(key=lambda x: x.get('timestamp', ''))
    
    # 保存为文本文件
    output_file = CHAT_DIR / "email_chat_extracted.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        for msg in filtered_messages:
            timestamp = msg.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            sender = msg.get('sender', '未知')
            content = msg.get('content', '')
            
            f.write(f"{timestamp} {sender} {content}\n")
    
    print(f"\n完成！已保存到: {output_file}")
    print(f"\n下一步：运行 py scripts/parse_chat.py 进行进一步处理")

if __name__ == "__main__":
    main()
