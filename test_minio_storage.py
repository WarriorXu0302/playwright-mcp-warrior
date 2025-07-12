#!/usr/bin/env python3
"""
测试 MinIO 存储功能
用于验证截图保存到 MinIO 的功能
"""

import os
import sys
import time
import json
import base64
from datetime import datetime

# 添加 python 目录到路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'python'))

from python.minio_storage import MinioStorage, get_minio_storage
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_minio_config():
    """测试加载 MinIO 配置"""
    logger.info("测试 MinIO 配置...")
    storage = MinioStorage()
    
    # 打印配置信息
    config_items = {
        "endpoint": storage.config.get("endpoint"),
        "bucket_name": storage.config.get("bucket_name"),
        "use_minio": storage.config.get("use_minio"),
        "local_backup": storage.config.get("local_backup"),
        "local_backup_dir": storage.config.get("local_backup_dir"),
    }
    
    for key, value in config_items.items():
        logger.info(f"   {key}: {value}")
    
    return storage

def create_test_image() -> str:
    """创建一个测试图片"""
    import io
    from PIL import Image, ImageDraw, ImageFont
    
    # 创建一个测试图片
    width, height = 800, 600
    image = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(image)
    
    # 添加一些文字
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f"测试图片 - {timestamp}"
    
    # 添加一些图形
    draw.rectangle([50, 50, width-50, height-50], outline="blue", width=5)
    draw.ellipse([150, 150, width-150, height-150], outline="red", width=5)
    draw.line([50, 50, width-50, height-50], fill="green", width=3)
    draw.line([50, height-50, width-50, 50], fill="green", width=3)
    
    # 添加文字
    draw.text((width//2-100, height//2-10), text, fill="black")
    
    # 保存到内存
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    
    # 转换为 Base64
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # 保存一份到临时文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_filename = f"/tmp/test_image_{timestamp}.png"
    with open(test_filename, 'wb') as f:
        f.write(buffer.getvalue())
    
    logger.info(f"创建测试图片: {test_filename}")
    
    return test_filename, img_base64

def test_save_base64():
    """测试保存 Base64 格式的图片"""
    logger.info("测试保存 Base64 格式的图片...")
    
    # 创建测试图片
    test_filename, img_base64 = create_test_image()
    
    # 获取 MinIO 存储实例
    storage = get_minio_storage()
    
    # 保存 Base64 图片
    filename = f"test_base64_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    result = storage.save_screenshot(img_base64, filename)
    
    # 显示结果
    logger.info(f"保存结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    return result

def test_save_file():
    """测试保存本地文件"""
    logger.info("测试保存本地文件...")
    
    # 创建测试图片
    test_filename, _ = create_test_image()
    
    # 获取 MinIO 存储实例
    storage = get_minio_storage()
    
    # 保存本地文件
    object_name = f"test_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    result = storage.save_screenshot_file(test_filename, object_name)
    
    # 显示结果
    logger.info(f"保存结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    return result

def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("MinIO 存储功能测试")
    logger.info("=" * 50)
    
    # 测试配置加载
    storage = test_minio_config()
    
    logger.info("\n" + "=" * 50)
    
    # 测试保存 Base64 图片
    base64_result = test_save_base64()
    
    logger.info("\n" + "=" * 50)
    
    # 测试保存本地文件
    file_result = test_save_file()
    
    logger.info("\n" + "=" * 50)
    logger.info("测试完成")
    
    # 总结测试结果
    logger.info("\n测试结果摘要:")
    logger.info(f"Base64 图片保存: {'成功' if base64_result.get('success') else '失败'}")
    if base64_result.get('success'):
        if 'url' in base64_result:
            logger.info(f"   MinIO URL: {base64_result['url']}")
        if 'local_path' in base64_result:
            logger.info(f"   本地路径: {base64_result['local_path']}")
    else:
        logger.info(f"   错误: {base64_result.get('error', '未知错误')}")
    
    logger.info(f"本地文件保存: {'成功' if file_result.get('success') else '失败'}")
    if file_result.get('success'):
        if 'url' in file_result:
            logger.info(f"   MinIO URL: {file_result['url']}")
        if 'source_path' in file_result:
            logger.info(f"   源文件: {file_result['source_path']}")
        if 'backup_path' in file_result:
            logger.info(f"   备份路径: {file_result['backup_path']}")
    else:
        logger.info(f"   错误: {file_result.get('error', '未知错误')}")
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("用户中断测试")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True) 