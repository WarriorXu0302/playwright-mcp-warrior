#!/usr/bin/env python3
"""
Playwright MCP Vision+MinIO 集成演示
演示如何将Playwright的视觉快照和结构化数据保存到MinIO
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

# 添加 python 目录到路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'python'))

from python.mcp_manager_sse import SSEClient, TestTask, MCPManager
from python.minio_storage import get_minio_storage, MinioStorage
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_file: str = "cluster_config.json") -> Dict[str, Any]:
    """加载集群配置"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"配置文件 {config_file} 不存在")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"配置文件格式错误: {e}")
        sys.exit(1)

def test_snapshot_to_minio(client: SSEClient) -> Dict[str, Any]:
    """测试将快照保存到MinIO"""
    logger.info("测试将快照保存到MinIO...")
    
    # 先导航到一个页面
    navigate_result = client.call_tool('browser_navigate', {
        'url': 'https://www.baidu.com'
    })
    
    if not navigate_result:
        logger.error("导航失败")
        return {"success": False, "error": "导航失败"}
    
    # 等待页面加载
    time.sleep(2)
    
    # 获取快照
    logger.info("获取页面快照...")
    snapshot_result = client.call_tool('browser_snapshot', {})
    
    if not snapshot_result or isinstance(snapshot_result, dict) and snapshot_result.get('isError', False):
        logger.error("获取快照失败")
        return {"success": False, "error": "获取快照失败"}
    
    # 检查快照数据
    snapshot_data = None
    html_content = None
    json_data = None
    
    if isinstance(snapshot_result, dict):
        # 尝试获取结构化内容
        structured_content = snapshot_result.get("structuredContent")
        if structured_content:
            # 保存结构化JSON数据
            json_data = json.dumps(structured_content)
            logger.info("获取到结构化JSON数据")
        
        # 尝试获取HTML内容
        content_items = snapshot_result.get("content", [])
        for item in content_items:
            if item.get("type") == "text":
                html_content = item.get("text", "")
                logger.info(f"获取到HTML内容 ({len(html_content)} 字符)")
                break
                
        # 如果有accessibility数据
        if "accessibility" in snapshot_result:
            snapshot_data = json.dumps(snapshot_result["accessibility"])
            logger.info("获取到accessibility快照数据")
        
        # 尝试获取视觉数据或截图数据
        if "snapshot" in snapshot_result:
            snapshot_data = json.dumps(snapshot_result["snapshot"])
            logger.info("获取到视觉快照数据")
    
    # 保存到MinIO
    if html_content or json_data or snapshot_data:
        try:
            minio = get_minio_storage()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_base = f"baidu_snapshot_{timestamp}"
            
            storage_urls = {}
            
            # 保存HTML内容
            if html_content:
                html_filename = f"{filename_base}.html"
                logger.info(f"保存HTML内容到MinIO: {html_filename}")
                html_result = minio.save_text_content(html_content, html_filename, "text/html")
                if html_result.get("success"):
                    storage_urls["html"] = html_result.get("url")
                    logger.info(f"HTML内容保存成功: {html_result.get('url', html_result.get('local_path'))}")
                else:
                    logger.error(f"HTML内容保存失败: {html_result.get('error', '未知错误')}")
            
            # 保存JSON结构化数据
            if json_data:
                json_filename = f"{filename_base}.json"
                logger.info(f"保存JSON数据到MinIO: {json_filename}")
                json_result = minio.save_text_content(json_data, json_filename, "application/json")
                if json_result.get("success"):
                    storage_urls["json"] = json_result.get("url")
                    logger.info(f"JSON数据保存成功: {json_result.get('url', json_result.get('local_path'))}")
                else:
                    logger.error(f"JSON数据保存失败: {json_result.get('error', '未知错误')}")
            
            # 保存快照数据
            if snapshot_data:
                snapshot_filename = f"{filename_base}_snapshot.json"
                logger.info(f"保存快照数据到MinIO: {snapshot_filename}")
                snapshot_result_minio = minio.save_text_content(snapshot_data, snapshot_filename, "application/json")
                if snapshot_result_minio.get("success"):
                    storage_urls["snapshot"] = snapshot_result_minio.get("url")
                    logger.info(f"快照数据保存成功: {snapshot_result_minio.get('url', snapshot_result_minio.get('local_path'))}")
                else:
                    logger.error(f"快照数据保存失败: {snapshot_result_minio.get('error', '未知错误')}")
            
            # 更新结果
            snapshot_result["minio_urls"] = storage_urls
            snapshot_result["stored_in_minio"] = bool(storage_urls)
            
        except Exception as e:
            logger.error(f"保存快照到MinIO失败: {e}")
    
    # 截图作为对比
    logger.info("获取页面截图...")
    screenshot_result = client.call_tool('browser_take_screenshot', {
        'filename': f"baidu_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    })
    
    if screenshot_result:
        logger.info("截图获取成功")
        try:
            # 保存截图到MinIO
            minio = get_minio_storage()
            
            # 检查是否有base64数据
            base64_data = None
            for key in ['base64', 'data', 'imageData', 'content']:
                if key in screenshot_result:
                    base64_data = screenshot_result[key]
                    break
            
            # 如果有base64数据
            if base64_data:
                screenshot_filename = f"baidu_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                screenshot_minio_result = minio.save_screenshot(base64_data, screenshot_filename)
                if screenshot_minio_result.get('success'):
                    screenshot_result['minio_url'] = screenshot_minio_result.get('url')
                    screenshot_result['stored_in_minio'] = True
                    logger.info(f"截图保存到MinIO成功: {screenshot_minio_result.get('url', screenshot_minio_result.get('local_path'))}")
                else:
                    logger.error(f"截图保存到MinIO失败: {screenshot_minio_result.get('error', '未知错误')}")
                    
        except Exception as e:
            logger.error(f"保存截图到MinIO失败: {e}")
    
    return {
        "success": True,
        "snapshot": snapshot_result,
        "screenshot": screenshot_result
    }

def main():
    """主函数"""
    print("\n🚀 Playwright MCP Vision+MinIO 集成演示")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    
    # 获取第一个实例
    instances = config["cluster"]["instances"]
    if not instances:
        print("❌ 配置文件中没有找到实例")
        return
        
    instance = instances[0]
    
    print(f"🔗 连接到MCP实例: {instance['id']} ({instance['url']})")
    client = SSEClient(instance['url'])
    
    # 初始化连接
    if not client.initialize():
        print("❌ 初始化失败")
        return
    
    print("✅ 初始化成功")
    
    # 测试将快照保存到MinIO
    print("\n📋 测试将快照保存到MinIO...")
    result = test_snapshot_to_minio(client)
    
    # 显示结果
    if result.get("success"):
        print("✅ 测试成功")
        
        # 显示MinIO URL
        snapshot = result.get("snapshot", {})
        if isinstance(snapshot, dict) and "minio_urls" in snapshot:
            print("\n📊 快照保存到MinIO:")
            urls = snapshot["minio_urls"]
            if "html" in urls:
                print(f"   - HTML内容: {urls['html']}")
            if "json" in urls:
                print(f"   - JSON数据: {urls['json']}")
            if "snapshot" in urls:
                print(f"   - 快照数据: {urls['snapshot']}")
                
        # 显示截图URL
        screenshot = result.get("screenshot", {})
        if isinstance(screenshot, dict) and "minio_url" in screenshot:
            print("\n📸 截图保存到MinIO:")
            print(f"   - 图片: {screenshot['minio_url']}")
    else:
        print("❌ 测试失败")
        print(f"   错误: {result.get('error', '未知错误')}")
    
    print("\n💡 提示: 若要查看本地保存的文件，请查看目录:")
    print(f"   {get_minio_storage().config.get('local_backup_dir', '/tmp/playwright-screenshots')}")
    
    # 关闭连接
    client.close()
    print("\n🎉 演示完成")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  用户中断，退出演示")
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}", exc_info=True) 