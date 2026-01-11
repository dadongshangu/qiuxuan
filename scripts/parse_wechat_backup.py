#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信备份文件解析脚本
解析微信PC版备份文件，提取聊天记录并转换为文本格式
"""

import os
import struct
import sqlite3
from pathlib import Path
from datetime import datetime
import json
import re
import mmap

# 微信备份目录
BACKUP_ROOT = Path(r"C:\Users\mmeng\Documents\xwechat_files\Backup\mengxiangzhi001\8a7ca2d8c851e71a7c9ce102bb3b7476\files\1")

# 项目目录
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "assets" / "chat"
IMAGES_DIR = PROJECT_ROOT / "assets" / "images"

# 目标联系人（秋璇的微信名或备注）
TARGET_CONTACT = "秋璇"

def find_sqlite_databases(backup_dir):
    """查找所有SQLite数据库文件"""
    db_files = []
    print("正在搜索SQLite数据库文件...")
    
    for root, dirs, files in os.walk(backup_dir):
        for file in files:
            file_path = Path(root) / file
            # 检查文件大小，跳过太小的文件
            try:
                if file_path.stat().st_size < 1024:  # 小于1KB的跳过
                    continue
            except:
                continue
            
            # 尝试打开验证是否为SQLite
            try:
                conn = sqlite3.connect(str(file_path))
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [t[0] for t in cursor.fetchall()]
                conn.close()
                
                if tables:
                    db_files.append({
                        'path': file_path,
                        'tables': tables,
                        'size': file_path.stat().st_size
                    })
                    print(f"  找到数据库: {file_path.name} ({len(tables)} 个表)")
            except:
                pass
    
    return db_files

def parse_wechat_backup_structure(backup_dir):
    """解析微信备份目录结构，查找聊天会话"""
    chat_sessions = []
    print("正在分析备份目录结构...")
    
    count = 0
    for item in backup_dir.iterdir():
        if item.is_dir():
            count += 1
            if count % 100 == 0:
                print(f"  已扫描 {count} 个目录...")
            
            # 检查是否有ChatPackage目录
            chat_pkg = item / "ChatPackage"
            index_dir = item / "Index"
            
            if chat_pkg.exists() and index_dir.exists():
                # 这是一个聊天会话目录
                session_id = item.name
                
                # 查找时间范围文件
                time_files = list(index_dir.glob("*.dat"))
                chat_files = list(chat_pkg.glob("*"))
                
                chat_sessions.append({
                    'session_id': session_id,
                    'path': item,
                    'chat_package': chat_pkg,
                    'index': index_dir,
                    'time_files': time_files,
                    'chat_files': chat_files
                })
    
    print(f"找到 {len(chat_sessions)} 个聊天会话")
    return chat_sessions

def read_binary_file(file_path, max_size=100*1024*1024):
    """读取二进制文件（限制大小避免内存问题）"""
    try:
        file_size = file_path.stat().st_size
        if file_size > max_size:
            print(f"  警告: 文件 {file_path.name} 太大 ({file_size/1024/1024:.1f}MB)，跳过")
            return None
        
        with open(file_path, 'rb') as f:
            return f.read()
    except Exception as e:
        print(f"  读取文件失败 {file_path.name}: {e}")
        return None

def try_parse_as_text(data):
    """尝试将二进制数据解析为文本"""
    if not data:
        return None
    
    # 尝试UTF-8编码
    try:
        text = data.decode('utf-8', errors='ignore')
        if len(text) > 10 and any(ord(c) > 127 for c in text[:100]):  # 包含中文
            return text
    except:
        pass
    
    # 尝试GBK编码
    try:
        text = data.decode('gbk', errors='ignore')
        if len(text) > 10 and any(ord(c) > 127 for c in text[:100]):
            return text
    except:
        pass
    
    return None

def extract_text_from_chat_file(chat_file_path):
    """从聊天文件中提取文本内容"""
    data = read_binary_file(chat_file_path)
    if not data:
        return []
    
    messages = []
    
    # 方法1: 尝试解析为文本
    text = try_parse_as_text(data)
    if text:
        # 尝试提取时间戳和消息内容
        # 查找类似时间戳的模式
        timestamp_pattern = r'(\d{10,13})'  # 10-13位数字（可能是时间戳）
        time_matches = re.findall(timestamp_pattern, text[:1000])
        
        # 查找可能的发送者名称
        if TARGET_CONTACT in text or "您" in text or "我" in text:
            # 尝试提取消息内容
            lines = text.split('\n')
            for line in lines:
                if len(line.strip()) > 5 and (TARGET_CONTACT in line or "您" in line or "我" in line):
                    messages.append({
                        'content': line.strip(),
                        'raw': text[:500]  # 保存原始文本的前500字符用于调试
                    })
    
    # 方法2: 查找SQLite数据库特征
    if data[:16] == b'SQLite format 3\x00':
        return extract_from_sqlite(chat_file_path)
    
    return messages

def extract_from_sqlite(db_path):
    """从SQLite数据库提取聊天记录"""
    messages = []
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        
        # 常见的微信聊天表名
        possible_tables = ['message', 'Chat', 'MSG', 'msg', 'Message']
        
        for table in tables:
            if any(pt.lower() in table.lower() for pt in possible_tables):
                try:
                    # 尝试查询消息
                    cursor.execute(f"SELECT * FROM {table} LIMIT 100")
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        # 查找可能包含消息内容的字段
                        for key, value in row_dict.items():
                            if value and isinstance(value, str) and len(value) > 5:
                                if TARGET_CONTACT in value or "您" in value:
                                    messages.append({
                                        'content': value,
                                        'table': table,
                                        'columns': columns
                                    })
                except Exception as e:
                    print(f"    查询表 {table} 失败: {e}")
        
        conn.close()
    except Exception as e:
        print(f"  解析SQLite失败: {e}")
    
    return messages

def process_backup_directory(backup_dir, output_file):
    """处理整个备份目录"""
    print("=" * 60)
    print("开始处理微信备份文件")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    all_messages = []
    
    # 方法1: 查找SQLite数据库
    print("\n[方法1] 查找SQLite数据库...")
    db_files = find_sqlite_databases(backup_dir)
    
    if db_files:
        print(f"\n找到 {len(db_files)} 个数据库文件，开始提取...")
        for db_info in db_files:
            print(f"\n处理数据库: {db_info['path'].name}")
            messages = extract_from_sqlite(db_info['path'])
            all_messages.extend(messages)
            print(f"  提取了 {len(messages)} 条消息")
    
    # 方法2: 解析目录结构
    print("\n[方法2] 解析目录结构...")
    sessions = parse_wechat_backup_structure(backup_dir)
    
    if sessions:
        print(f"\n找到 {len(sessions)} 个聊天会话，开始提取...")
        processed = 0
        for session in sessions:
            processed += 1
            if processed % 10 == 0:
                print(f"  已处理 {processed}/{len(sessions)} 个会话...")
            
            # 处理ChatPackage中的文件
            for chat_file in session['chat_files']:
                if chat_file.is_file():
                    messages = extract_text_from_chat_file(chat_file)
                    if messages:
                        all_messages.extend(messages)
    
    # 去重和排序
    print(f"\n总共提取了 {len(all_messages)} 条原始消息")
    
    # 去重（基于内容）
    unique_messages = []
    seen = set()
    for msg in all_messages:
        content = msg.get('content', '')
        if content and content not in seen:
            seen.add(content)
            unique_messages.append(msg)
    
    print(f"去重后: {len(unique_messages)} 条消息")
    
    # 写入输出文件
    output_path = OUTPUT_DIR / output_file
    print(f"\n正在写入文件: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, msg in enumerate(unique_messages, 1):
            content = msg.get('content', '').strip()
            if content:
                # 尝试提取时间戳
                timestamp = msg.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                sender = msg.get('sender', '未知')
                
                f.write(f"[{timestamp}] {sender}: {content}\n")
    
    print(f"\n完成！已保存 {len(unique_messages)} 条消息到 {output_path}")
    return output_path

def main():
    """主函数"""
    if not BACKUP_ROOT.exists():
        print(f"错误: 备份目录不存在: {BACKUP_ROOT}")
        print("请检查路径是否正确")
        return
    
    print(f"备份目录: {BACKUP_ROOT}")
    print(f"输出目录: {OUTPUT_DIR}")
    
    # 处理备份
    output_file = "wechat_backup_extracted.txt"
    result = process_backup_directory(BACKUP_ROOT, output_file)
    
    if result:
        print("\n" + "=" * 60)
        print("下一步:")
        print(f"1. 检查提取的文件: {result}")
        print("2. 如果格式正确，可以运行 parse_chat.py 进行进一步处理")
        print("3. 如果格式需要调整，请告诉我，我会优化脚本")
        print("=" * 60)

if __name__ == "__main__":
    main()
