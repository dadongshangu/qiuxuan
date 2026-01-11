#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从邮件中提取图片并保存到CDN仓库
"""

import email
from email import policy
from pathlib import Path
import re
from datetime import datetime

# 项目目录
PROJECT_ROOT = Path(__file__).parent.parent
CHAT_DIR = PROJECT_ROOT / "assets" / "chat"
CDN_DIR = Path("E:/3.github/repositories/CDN/qiuxuan")

def extract_images_from_email(email_file_path):
    """从邮件文件中提取所有图片"""
    images = []
    
    try:
        with open(email_file_path, 'rb') as f:
            msg = email.message_from_bytes(f.read(), policy=policy.default)
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # 检查是否是图片
                if content_type.startswith('image/'):
                    filename = part.get_filename()
                    if filename:
                        # 解码文件名（可能包含编码）
                        try:
                            from email.header import decode_header
                            decoded_parts = decode_header(filename)
                            decoded_filename = ''
                            for part_bytes, encoding in decoded_parts:
                                if isinstance(part_bytes, bytes):
                                    if encoding:
                                        decoded_filename += part_bytes.decode(encoding)
                                    else:
                                        decoded_filename += part_bytes.decode('utf-8', errors='ignore')
                                else:
                                    decoded_filename += part_bytes
                            filename = decoded_filename
                        except:
                            pass
                        
                        # 获取图片数据
                        payload = part.get_payload(decode=True)
                        if payload:
                            images.append({
                                'filename': filename,
                                'data': payload,
                                'content_type': content_type
                            })
                            print(f"  找到图片: {filename} ({len(payload)} bytes, {content_type})")
                
                # 也检查附件中的图片
                elif "attachment" in content_disposition.lower():
                    filename = part.get_filename()
                    if filename:
                        # 解码文件名
                        try:
                            from email.header import decode_header
                            decoded_parts = decode_header(filename)
                            decoded_filename = ''
                            for part_bytes, encoding in decoded_parts:
                                if isinstance(part_bytes, bytes):
                                    if encoding:
                                        decoded_filename += part_bytes.decode(encoding)
                                    else:
                                        decoded_filename += part_bytes.decode('utf-8', errors='ignore')
                                else:
                                    decoded_filename += part_bytes
                            filename = decoded_filename
                        except:
                            pass
                        
                        # 检查文件扩展名
                        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                            payload = part.get_payload(decode=True)
                            if payload:
                                images.append({
                                    'filename': filename,
                                    'data': payload,
                                    'content_type': part.get_content_type() or 'image/jpeg'
                                })
                                print(f"  找到图片附件: {filename} ({len(payload)} bytes)")
        
        # 也检查内嵌图片（Content-ID引用的图片）
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type().startswith('image/'):
                    content_id = part.get('Content-ID', '')
                    if content_id:
                        filename = part.get_filename() or f"image_{content_id.strip('<>')}"
                        payload = part.get_payload(decode=True)
                        if payload:
                            # 检查是否已存在
                            if not any(img['filename'] == filename for img in images):
                                images.append({
                                    'filename': filename,
                                    'data': payload,
                                    'content_type': part.get_content_type()
                                })
                                print(f"  找到内嵌图片: {filename} ({len(payload)} bytes)")
    
    except Exception as e:
        print(f"  解析邮件失败: {e}")
        import traceback
        traceback.print_exc()
    
    return images

def map_images_to_references(images, chat_file):
    """根据聊天记录中的图片引用，映射图片文件"""
    # 读取聊天记录
    image_refs = []
    if chat_file.exists():
        with open(chat_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 查找所有图片引用
            pattern = r'图片(\d+)（可在附件中查看）'
            matches = re.findall(pattern, content)
            image_refs = [int(m) for m in matches]
    
    # 创建映射：图片编号 -> 图片文件
    image_map = {}
    
    # 如果图片数量匹配，按顺序映射
    if len(images) > 0:
        # 按文件名排序（如果可能）
        sorted_images = sorted(images, key=lambda x: x['filename'])
        
        # 为每个图片引用分配一个图片
        for i, img_num in enumerate(sorted(set(image_refs))):
            if i < len(sorted_images):
                image_map[img_num] = sorted_images[i]
        
        # 如果还有未映射的图片，继续分配
        used_indices = set()
        for img_num in sorted(set(image_refs)):
            if img_num in image_map:
                used_indices.add(image_refs.index(img_num) if img_num in image_refs else 0)
        
        # 为剩余的图片引用分配
        remaining_refs = sorted(set(image_refs) - set(image_map.keys()))
        remaining_images = [img for i, img in enumerate(sorted_images) if i not in used_indices]
        
        for i, img_num in enumerate(remaining_refs):
            if i < len(remaining_images):
                image_map[img_num] = remaining_images[i]
    
    return image_map

def save_images_to_cdn(images, image_map):
    """保存图片到CDN仓库"""
    CDN_DIR.mkdir(parents=True, exist_ok=True)
    
    saved_count = 0
    
    # 根据映射保存图片
    for img_num, img_data in image_map.items():
        # 确定文件扩展名
        original_filename = img_data['filename']
        ext = Path(original_filename).suffix.lower()
        if not ext or ext not in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
            # 根据content_type确定扩展名
            content_type = img_data.get('content_type', 'image/jpeg')
            if 'png' in content_type:
                ext = '.png'
            elif 'gif' in content_type:
                ext = '.gif'
            else:
                ext = '.jpg'
        
        # 生成文件名（根据文档中的引用）
        # 检查文档中实际使用的文件名
        target_filename = f"physics_question_{img_num}.png"  # 默认命名
        
        # 但我们需要根据实际引用来确定
        # 先保存为通用名称
        if img_num <= 3:
            # 前3个可能是物理题
            target_filename = f"question_{img_num}{ext}"
        else:
            target_filename = f"image_{img_num}{ext}"
        
        target_path = CDN_DIR / target_filename
        
        try:
            with open(target_path, 'wb') as f:
                f.write(img_data['data'])
            print(f"  保存: {target_filename} ({len(img_data['data'])} bytes)")
            saved_count += 1
        except Exception as e:
            print(f"  保存失败 {target_filename}: {e}")
    
    # 也保存所有未映射的图片（使用原始文件名）
    mapped_images = [img_data for img_data in image_map.values()]
    for img_data in images:
        if img_data not in mapped_images:
            original_filename = img_data['filename']
            target_path = CDN_DIR / original_filename
            try:
                with open(target_path, 'wb') as f:
                    f.write(img_data['data'])
                print(f"  保存（未映射）: {original_filename} ({len(img_data['data'])} bytes)")
                saved_count += 1
            except Exception as e:
                print(f"  保存失败 {original_filename}: {e}")
    
    return saved_count

def main():
    """主函数"""
    print("=" * 60)
    print("从邮件中提取图片")
    print("=" * 60)
    
    # 查找邮件文件
    email_file = CHAT_DIR / "mail.eml"
    if not email_file.exists():
        print(f"未找到邮件文件: {email_file}")
        return
    
    print(f"\n处理邮件文件: {email_file.name}")
    
    # 提取图片
    images = extract_images_from_email(email_file)
    print(f"\n总共找到 {len(images)} 张图片")
    
    if not images:
        print("未找到图片，请检查邮件文件")
        return
    
    # 映射图片到引用
    chat_file = CHAT_DIR / "email_chat_extracted.txt"
    image_map = map_images_to_references(images, chat_file)
    print(f"\n映射了 {len(image_map)} 张图片到引用")
    
    # 保存到CDN仓库
    print(f"\n保存图片到: {CDN_DIR}")
    saved_count = save_images_to_cdn(images, image_map)
    print(f"\n总共保存了 {saved_count} 张图片")
    
    print("\n完成！")
    print(f"\n下一步：")
    print(f"1. 检查 {CDN_DIR} 目录中的图片")
    print(f"2. 根据需要重命名图片文件")
    print(f"3. 提交到CDN仓库：")
    print(f"   cd E:/3.github/repositories/CDN")
    print(f"   git add qiuxuan/*")
    print(f"   git commit -m 'Add qiuxuan images from email'")
    print(f"   git push origin master")

if __name__ == "__main__":
    main()
