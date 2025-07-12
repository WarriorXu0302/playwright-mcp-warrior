#!/usr/bin/env python3
"""
测试保存视觉数据到MinIO的功能
"""

import os
import sys
import json
from datetime import datetime

# 添加 python 目录到路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'python'))

from python.minio_storage import get_minio_storage
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_html():
    """创建测试用的HTML内容"""
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试页面</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #333; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; }
        .info { background-color: #f9f9f9; padding: 10px; margin-top: 20px; }
        .timestamp { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h1>MinIO视觉数据测试页面</h1>
        <p>这是一个用于测试MinIO保存HTML内容的示例页面。</p>
        <div class="info">
            <p>测试信息:</p>
            <ul>
                <li>生成时间: <span class="timestamp">%s</span></li>
                <li>测试ID: test-vision-123</li>
            </ul>
        </div>
    </div>
</body>
</html>
""" % datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return html

def create_test_json():
    """创建测试用的JSON数据"""
    data = {
        "accessibility": {
            "role": "document",
            "children": [
                {
                    "role": "heading",
                    "name": "MinIO视觉数据测试页面",
                    "level": 1
                },
                {
                    "role": "paragraph",
                    "name": "这是一个用于测试MinIO保存HTML内容的示例页面。"
                },
                {
                    "role": "list",
                    "children": [
                        {"role": "listitem", "name": "生成时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                        {"role": "listitem", "name": "测试ID: test-vision-123"}
                    ]
                }
            ]
        },
        "snapshot": {
            "timestamp": datetime.now().isoformat(),
            "url": "https://example.com/test",
            "title": "测试页面",
            "viewport": {"width": 1280, "height": 720},
            "elements": [
                {"tag": "h1", "text": "MinIO视觉数据测试页面", "visible": True},
                {"tag": "p", "text": "这是一个用于测试MinIO保存HTML内容的示例页面。", "visible": True},
                {"tag": "ul", "children": 2, "visible": True}
            ]
        },
        "metadata": {
            "test_id": "test-vision-123",
            "created_at": datetime.now().isoformat(),
            "browser": "chromium",
            "version": "1.0.0"
        }
    }
    return json.dumps(data, ensure_ascii=False, indent=2)

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 测试保存视觉数据到MinIO")
    print("=" * 60)
    
    # 获取MinIO存储实例
    storage = get_minio_storage()
    
    # 保存HTML内容
    html_content = create_test_html()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_filename = f"test_vision_{timestamp}.html"
    
    print(f"📄 保存HTML内容到: {html_filename}")
    html_result = storage.save_text_content(html_content, html_filename, "text/html")
    
    if html_result.get("success"):
        print("✅ HTML保存成功")
        if "url" in html_result:
            print(f"   MinIO URL: {html_result['url']}")
        if "local_path" in html_result:
            print(f"   本地路径: {html_result['local_path']}")
    else:
        print("❌ HTML保存失败")
        print(f"   错误: {html_result.get('error', '未知错误')}")
    
    # 保存JSON数据
    json_content = create_test_json()
    json_filename = f"test_vision_{timestamp}.json"
    
    print(f"\n📊 保存JSON数据到: {json_filename}")
    json_result = storage.save_text_content(json_content, json_filename, "application/json")
    
    if json_result.get("success"):
        print("✅ JSON保存成功")
        if "url" in json_result:
            print(f"   MinIO URL: {json_result['url']}")
        if "local_path" in json_result:
            print(f"   本地路径: {json_result['local_path']}")
    else:
        print("❌ JSON保存失败")
        print(f"   错误: {json_result.get('error', '未知错误')}")
    
    print("\n💡 提示: 若要查看本地保存的文件，请查看目录:")
    print(f"   {storage.config.get('local_backup_dir', '/tmp/playwright-screenshots')}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True) 