#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信聊天记录解析脚本
支持解析文本、HTML等格式的聊天记录，并生成学习总结文档
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import html
from html.parser import HTMLParser

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
CHAT_DIR = PROJECT_ROOT / "assets" / "chat"
IMAGES_DIR = PROJECT_ROOT / "assets" / "images"
DOCS_DIR = PROJECT_ROOT / "docs"
CLASS_RECORDS_DIR = DOCS_DIR / "class_records"

# 学科关键词
SUBJECT_KEYWORDS = {
    "数学": ["数学", "代数", "几何", "函数", "方程", "不等式", "数列", "三角函数", "导数", "积分", "概率", "统计"],
    "物理": ["物理", "力学", "运动", "力", "能量", "动量", "电", "磁", "光", "波", "热", "原子", "核"],
    "化学": ["化学", "元素", "化合物", "反应", "离子", "分子", "原子", "有机", "无机", "酸碱", "氧化还原"]
}

# 提问关键词
QUESTION_KEYWORDS = ["?", "？", "什么", "为什么", "怎么", "如何", "哪个", "哪些", "请", "能否", "可以"]


class ChatMessage:
    """聊天消息类"""
    def __init__(self, timestamp: str, sender: str, content: str, images: List[str] = None):
        self.timestamp = timestamp
        self.sender = sender
        self.content = content
        self.images = images or []
        self.is_question = False
        self.subject = None
        
    def analyze(self, teacher_name: str = "您"):
        """分析消息，判断是否为提问，识别学科"""
        # 判断是否为提问
        if self.sender == teacher_name:
            if any(keyword in self.content for keyword in QUESTION_KEYWORDS):
                self.is_question = True
        
        # 识别学科
        for subject, keywords in SUBJECT_KEYWORDS.items():
            if any(keyword in self.content for keyword in keywords):
                self.subject = subject
                break
        
        return self.is_question, self.subject


class ChatParser:
    """聊天记录解析器"""
    
    def __init__(self, teacher_name: str = "您", student_name: str = "秋璇"):
        self.teacher_name = teacher_name
        self.student_name = student_name
        self.messages: List[ChatMessage] = []
        
    def parse_text_file(self, file_path: Path) -> List[ChatMessage]:
        """解析文本格式的聊天记录"""
        messages = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试匹配常见的文本格式
        # 格式1: 2025-09-01 10:30:15 发送者 消息内容
        pattern1 = r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+([^\s]+)\s+(.+?)(?=\d{4}-\d{2}-\d{2}|\Z)'
        matches = re.findall(pattern1, content, re.DOTALL)
        
        for match in matches:
            timestamp, sender, content = match
            content = content.strip()
            messages.append(ChatMessage(timestamp, sender, content))
        
        # 如果格式1没有匹配到，尝试其他格式
        if not messages:
            # 格式2: [2025-09-01 10:30:15] 发送者: 消息内容
            pattern2 = r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s+([^:]+):\s+(.+?)(?=\[\d{4}-\d{2}-\d{2}|\Z)'
            matches = re.findall(pattern2, content, re.DOTALL)
            
            for match in matches:
                timestamp, sender, content = match
                content = content.strip()
                messages.append(ChatMessage(timestamp, sender, content))
        
        return messages
    
    def parse_html_file(self, file_path: Path) -> List[ChatMessage]:
        """解析HTML格式的聊天记录"""
        messages = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简单的HTML解析，提取消息
        # 这里需要根据实际HTML格式调整
        # 示例：<div class="message"><span class="time">2025-09-01 10:30:15</span><span class="sender">发送者</span><span class="content">内容</span></div>
        
        # 提取时间戳
        time_pattern = r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
        # 提取发送者和内容
        message_pattern = r'<[^>]*class="[^"]*sender[^"]*"[^>]*>([^<]+)</[^>]*>.*?<[^>]*class="[^"]*content[^"]*"[^>]*>([^<]+)</[^>]*>'
        
        # 简化处理：提取所有可能的文本内容
        # 实际使用时可能需要根据具体HTML结构调整
        lines = content.split('\n')
        current_time = None
        current_sender = None
        current_content = []
        
        for line in lines:
            # 查找时间戳
            time_match = re.search(time_pattern, line)
            if time_match:
                if current_time and current_sender and current_content:
                    messages.append(ChatMessage(
                        current_time,
                        current_sender,
                        '\n'.join(current_content)
                    ))
                current_time = time_match.group(1)
                current_content = []
            
            # 提取文本内容（去除HTML标签）
            text = re.sub(r'<[^>]+>', '', line).strip()
            if text:
                current_content.append(text)
        
        if current_time and current_sender and current_content:
            messages.append(ChatMessage(
                current_time,
                current_sender,
                '\n'.join(current_content)
            ))
        
        return messages
    
    def parse_file(self, file_path: Path) -> List[ChatMessage]:
        """根据文件扩展名选择解析方法"""
        ext = file_path.suffix.lower()
        if ext == '.txt':
            return self.parse_text_file(file_path)
        elif ext in ['.html', '.htm']:
            return self.parse_html_file(file_path)
        elif ext == '.json':
            return self.parse_json_file(file_path)
        else:
            # 默认尝试文本格式
            return self.parse_text_file(file_path)
    
    def parse_json_file(self, file_path: Path) -> List[ChatMessage]:
        """解析JSON格式的聊天记录"""
        messages = []
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 根据实际JSON结构调整
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    timestamp = item.get('time', item.get('timestamp', ''))
                    sender = item.get('sender', item.get('from', ''))
                    content = item.get('content', item.get('text', ''))
                    images = item.get('images', [])
                    messages.append(ChatMessage(timestamp, sender, content, images))
        
        return messages
    
    def load_chat_records(self):
        """加载所有聊天记录文件"""
        if not CHAT_DIR.exists():
            print(f"聊天记录目录不存在: {CHAT_DIR}")
            return
        
        chat_files = list(CHAT_DIR.glob("*"))
        if not chat_files:
            print(f"未找到聊天记录文件，请将文件放入: {CHAT_DIR}")
            return
        
        all_messages = []
        for file_path in chat_files:
            if file_path.is_file():
                print(f"正在解析: {file_path.name}")
                try:
                    messages = self.parse_file(file_path)
                    all_messages.extend(messages)
                    print(f"  解析了 {len(messages)} 条消息")
                except Exception as e:
                    print(f"  解析失败: {e}")
        
        # 按时间排序
        all_messages.sort(key=lambda x: x.timestamp)
        self.messages = all_messages
        
        # 分析每条消息
        for msg in self.messages:
            msg.analyze(self.teacher_name)
        
        print(f"总共加载了 {len(self.messages)} 条消息")
    
    def filter_by_date(self, start_date: str = "2025-09-01", end_date: str = None):
        """按日期过滤消息"""
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        filtered = []
        for msg in self.messages:
            msg_date = msg.timestamp.split()[0] if ' ' in msg.timestamp else msg.timestamp[:10]
            if start_date <= msg_date <= end_date:
                filtered.append(msg)
        
        return filtered


class DocumentGenerator:
    """文档生成器"""
    
    def __init__(self, parser: ChatParser):
        self.parser = parser
        
    def generate_subject_summary(self, subject: str, messages: List[ChatMessage]):
        """生成学科总结文档"""
        doc_path = DOCS_DIR / f"{subject}总结.md"
        
        # 按日期分组
        by_date = {}
        questions = []
        knowledge_points = []
        error_points = []
        
        for msg in messages:
            if msg.subject == subject:
                date = msg.timestamp.split()[0] if ' ' in msg.timestamp else msg.timestamp[:10]
                if date not in by_date:
                    by_date[date] = []
                by_date[date].append(msg)
                
                if msg.is_question:
                    questions.append(msg)
        
        # 生成文档内容
        content = f"# {subject}学习总结\n\n"
        content += "## 时间线\n\n"
        
        # 按月份组织
        current_month = None
        for date in sorted(by_date.keys()):
            month = date[:7]  # YYYY-MM
            if month != current_month:
                if current_month is not None:
                    content += "\n---\n\n"
                content += f"### {month}\n\n"
                current_month = month
            
            content += f"**{date}**\n\n"
            for msg in by_date[date]:
                content += f"- [{msg.timestamp}] {msg.sender}: {msg.content[:100]}...\n"
            content += "\n"
        
        content += "\n---\n\n"
        content += "## 重点问题\n\n"
        
        for i, q in enumerate(questions[:10], 1):  # 最多显示10个问题
            content += f"### 问题{i}\n\n"
            content += f"**日期**：{q.timestamp}\n\n"
            content += f"**问题**：{q.content}\n\n"
            # 查找对应的回答
            answer = self._find_answer(q, messages)
            if answer:
                content += f"**解答**：{answer.content}\n\n"
            content += f"**知识点**：_待补充_\n\n"
            content += "---\n\n"
        
        # 保存文档
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"已生成: {doc_path}")
    
    def _find_answer(self, question: ChatMessage, messages: List[ChatMessage]) -> Optional[ChatMessage]:
        """查找问题的回答"""
        q_index = messages.index(question)
        # 查找问题后的第一条学生消息
        for i in range(q_index + 1, min(q_index + 5, len(messages))):
            if messages[i].sender == self.parser.student_name:
                return messages[i]
        return None
    
    def generate_class_records(self, messages: List[ChatMessage]):
        """生成上课记录"""
        # 按月份分组
        by_month = {}
        
        for msg in messages:
            if msg.is_question:
                date = msg.timestamp.split()[0] if ' ' in msg.timestamp else msg.timestamp[:10]
                month = date[:7]  # YYYY-MM
                if month not in by_month:
                    by_month[month] = []
                by_month[month].append(msg)
        
        for month, questions in by_month.items():
            doc_path = CLASS_RECORDS_DIR / f"{month}.md"
            
            content = f"# {month}上课记录\n\n"
            
            # 按日期分组
            by_date = {}
            for q in questions:
                date = q.timestamp.split()[0] if ' ' in q.timestamp else q.timestamp[:10]
                if date not in by_date:
                    by_date[date] = []
                by_date[date].append(q)
            
            for date in sorted(by_date.keys()):
                content += f"## {date}\n\n"
                for q in by_date[date]:
                    content += f"### 提问内容\n\n{q.content}\n\n"
                    answer = self._find_answer(q, messages)
                    if answer:
                        content += f"### 学生回答\n\n{answer.content}\n\n"
                    content += f"### 知识点\n\n_待补充_\n\n"
                    content += f"### 教学分析\n\n"
                    content += f"**回答质量评估**：_待补充_\n\n"
                    content += f"**理解程度分析**：_待补充_\n\n"
                    content += f"**需要加强的方面**：_待补充_\n\n"
                    content += f"**后续建议**：_待补充_\n\n"
                    content += "---\n\n"
            
            # 本月总结
            content += "## 本月总结\n\n"
            content += f"### 提问次数统计\n\n"
            content += f"- 总提问次数：{len(questions)}\n"
            
            subjects_count = {}
            for q in questions:
                if q.subject:
                    subjects_count[q.subject] = subjects_count.get(q.subject, 0) + 1
            
            for subject, count in subjects_count.items():
                content += f"- {subject}相关：{count}\n"
            
            content += "\n### 学习进展\n\n_待补充_\n\n"
            content += "### 重点关注\n\n_待补充_\n\n"
            
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"已生成: {doc_path}")


def main():
    """主函数"""
    print("=" * 50)
    print("微信聊天记录解析工具")
    print("=" * 50)
    
    # 创建必要的目录
    CHAT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    CLASS_RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 初始化解析器
    parser = ChatParser(teacher_name="您", student_name="秋璇")
    
    # 加载聊天记录
    parser.load_chat_records()
    
    if not parser.messages:
        print("\n未找到聊天记录，请先导出聊天记录到 assets/chat/ 目录")
        return
    
    # 过滤日期范围
    filtered_messages = parser.filter_by_date("2025-09-01")
    print(f"过滤后（2025-09-01至今）: {len(filtered_messages)} 条消息")
    
    # 生成文档
    generator = DocumentGenerator(parser)
    
    # 生成各学科总结
    for subject in ["数学", "物理", "化学"]:
        subject_messages = [m for m in filtered_messages if m.subject == subject]
        if subject_messages:
            generator.generate_subject_summary(subject, filtered_messages)
    
    # 生成上课记录
    question_messages = [m for m in filtered_messages if m.is_question]
    if question_messages:
        generator.generate_class_records(filtered_messages)
    
    print("\n处理完成！")


if __name__ == "__main__":
    main()
