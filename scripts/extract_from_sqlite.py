#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从微信SQLite数据库提取聊天记录
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import re

# 微信数据目录
WECHAT_DATA = Path(r"C:\Users\mmeng\Documents\xwechat_files\mengxiangzhi001_8542\db_storage")

# 输出目录
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "chat"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_CONTACT = "秋璇"

def query_database(db_path, query):
    """查询数据库"""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        return results, columns
    except Exception as e:
        print(f"  查询失败: {e}")
        return None, None

def find_message_tables(db_path):
    """查找包含消息的表"""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        conn.close()
        
        # 查找可能包含消息的表
        message_tables = []
        for table in tables:
            if any(keyword in table.lower() for keyword in ['msg', 'message', 'chat', 'talk']):
                message_tables.append(table)
        
        return message_tables
    except Exception as e:
        print(f"  无法读取表: {e}")
        return []

def extract_messages_from_db(db_path):
    """从数据库提取消息"""
    print(f"\n处理数据库: {db_path.name}")
    
    # 查找消息表
    message_tables = find_message_tables(db_path)
    if not message_tables:
        print("  未找到消息表")
        return []
    
    print(f"  找到消息表: {message_tables}")
    
    all_messages = []
    
    for table in message_tables:
        try:
            # 获取表结构
            results, columns = query_database(db_path, f"SELECT * FROM {table} LIMIT 1")
            if not results:
                continue
            
            print(f"    表 {table} 的列: {columns}")
            
            # 查找可能包含联系人名称的列
            contact_col = None
            content_col = None
            time_col = None
            
            for col in columns:
                col_lower = col.lower()
                if any(x in col_lower for x in ['contact', 'user', 'name', 'talker', 'username']):
                    contact_col = col
                if any(x in col_lower for x in ['content', 'text', 'msg', 'message']):
                    content_col = col
                if any(x in col_lower for x in ['time', 'timestamp', 'create_time', 'date']):
                    time_col = col
            
            # 查询所有记录
            if content_col:
                query = f"SELECT * FROM {table}"
                if contact_col:
                    query += f" WHERE {contact_col} LIKE '%{TARGET_CONTACT}%'"
                query += " LIMIT 10000"
                
                results, _ = query_database(db_path, query)
                if results:
                    print(f"      找到 {len(results)} 条记录")
                    for row in results:
                        row_dict = dict(zip(columns, row))
                        content = row_dict.get(content_col, '')
                        if content and len(str(content)) > 5:
                            # 检查是否包含目标联系人
                            if TARGET_CONTACT in str(content) or any(x in str(content) for x in ["您", "我", "数学", "物理", "化学"]):
                                msg = {
                                    'content': str(content),
                                    'table': table,
                                    'timestamp': row_dict.get(time_col, datetime.now().timestamp() * 1000) if time_col else None,
                                    'sender': row_dict.get(contact_col, '未知') if contact_col else '未知'
                                }
                                all_messages.append(msg)
        except Exception as e:
            print(f"    处理表 {table} 时出错: {e}")
    
    return all_messages

def main():
    """主函数"""
    print("=" * 60)
    print("从SQLite数据库提取微信聊天记录")
    print("=" * 60)
    
    if not WECHAT_DATA.exists():
        print(f"微信数据目录不存在: {WECHAT_DATA}")
        return
    
    # 查找所有数据库文件
    db_files = list(WECHAT_DATA.rglob("*.db"))
    print(f"\n找到 {len(db_files)} 个数据库文件")
    
    all_messages = []
    
    for db_path in db_files:
        messages = extract_messages_from_db(db_path)
        all_messages.extend(messages)
    
    print(f"\n总共提取了 {len(all_messages)} 条消息")
    
    # 去重
    unique_messages = []
    seen = set()
    for msg in all_messages:
        content = msg['content']
        if content and content not in seen:
            seen.add(content)
            unique_messages.append(msg)
    
    print(f"去重后: {len(unique_messages)} 条消息")
    
    # 写入文件
    output_file = OUTPUT_DIR / "wechat_sqlite_extracted.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        for msg in unique_messages:
            timestamp = msg.get('timestamp')
            if timestamp:
                try:
                    if timestamp > 1e12:  # 毫秒时间戳
                        dt = datetime.fromtimestamp(timestamp / 1000)
                    else:  # 秒时间戳
                        dt = datetime.fromtimestamp(timestamp)
                    time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            sender = msg.get('sender', '未知')
            content = msg.get('content', '')
            
            f.write(f"[{time_str}] {sender}: {content}\n")
    
    print(f"\n完成！已保存到: {output_file}")

if __name__ == "__main__":
    main()
