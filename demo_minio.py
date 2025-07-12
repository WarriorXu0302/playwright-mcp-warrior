#!/usr/bin/env python3
"""
MinIO存储功能演示 - 独立模式
支持将截图保存到MinIO对象存储服务的演示
"""

import os
import sys
import json
import base64
import logging
from datetime import datetime
from io import BytesIO

# 添加 python 目录到路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'python'))

from python.minio_storage import MinioStorage, get_minio_storage

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """加载MinIO配置"""
    try:
        with open('minio_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("配置文件 minio_config.json 不存在，使用默认配置")
        return {
            "endpoint": "127.0.0.1:9000",
            "access_key": "minioadmin",
            "secret_key": "minioadmin",
            "secure": False,
            "bucket_name": "playwright-screenshots",
            "region": "cn-north-1",
            "use_minio": True,
            "local_backup": True,
            "local_backup_dir": "/tmp/playwright-screenshots"
        }

def create_test_image():
    """创建测试图片"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # 创建一个800x600的图片
        width, height = 800, 600
        image = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(image)
        
        # 添加时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = f"MinIO存储演示图片 - {timestamp}"
        
        # 画一些图形
        draw.rectangle([50, 50, width-50, height-50], outline="blue", width=5)
        draw.ellipse([150, 150, width-150, height-150], outline="red", width=5)
        draw.line([50, 50, width-50, height-50], fill="green", width=3)
        draw.line([50, height-50, width-50, 50], fill="green", width=3)
        
        # 添加文字
        draw.text((width//2-150, height//2-10), text, fill="black")
        
        # 保存到内存
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        
        # 转换为 Base64
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # 保存一份到临时文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_filename = f"/tmp/minio_demo_image_{timestamp}.png"
        with open(test_filename, 'wb') as f:
            f.write(buffer.getvalue())
        
        logger.info(f"✅ 创建测试图片成功: {test_filename}")
        
        return test_filename, img_base64
    except ImportError:
        logger.warning("⚠️ 未安装PIL库，无法创建测试图片")
        logger.info("💡 提示: 使用 pip install Pillow 安装图像处理库")
        return None, None

def test_save_base64():
    """测试保存Base64格式的截图"""
    logger.info("📸 测试保存Base64格式的截图...")
    
    # 获取测试图片
    test_filename, img_base64 = create_test_image()
    
    if not test_filename or not img_base64:
        logger.error("❌ 无法获取测试图片，跳过测试")
        return None
    
    # 获取MinIO存储实例
    storage = get_minio_storage()
    
    # 保存截图
    # 不需要使用BytesIO，这里直接使用Base64字符串
    # 转换为正确的Base64格式（添加必要的前缀）
    if not img_base64.startswith('data:image'):
        img_base64 = f"data:image/png;base64,{img_base64}"
    
    filename = f"demo_base64_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    result = storage.save_screenshot(img_base64, filename)
    
    if result.get("success"):
        logger.info(f"✅ 保存截图成功: {filename}")
        if "url" in result:
            logger.info(f"🔗 MinIO URL: {result['url']}")
        if "local_path" in result:
            logger.info(f"📁 本地路径: {result['local_path']}")
    else:
        logger.error(f"❌ 保存截图失败: {result.get('error', '未知错误')}")
    
    return result

def test_save_file():
    """测试保存本地文件到MinIO"""
    logger.info("📁 测试保存本地文件到MinIO...")
    
    # 获取测试图片
    test_filename, _ = create_test_image()
    
    if not test_filename:
        logger.error("❌ 无法获取测试图片，跳过测试")
        return None
    
    # 获取MinIO存储实例
    storage = get_minio_storage()
    
    # 保存截图
    filename = f"demo_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    result = storage.save_screenshot_file(test_filename, filename)
    
    if result.get("success"):
        logger.info(f"✅ 保存文件成功: {filename}")
        if "url" in result:
            logger.info(f"🔗 MinIO URL: {result['url']}")
        if "backup_path" in result:
            logger.info(f"📁 备份路径: {result['backup_path']}")
    else:
        logger.error(f"❌ 保存文件失败: {result.get('error', '未知错误')}")
    
    return result

def simulate_playwright_screenshot():
    """模拟Playwright截图功能"""
    logger.info("🎭 模拟Playwright截图功能...")
    
    # 创建测试图片
    test_filename, img_base64 = create_test_image()
    
    if not test_filename or not img_base64:
        logger.error("❌ 无法创建测试图片")
        return
    
    # 模拟截图结果
    mock_result = {
        "data": img_base64,
        "path": test_filename,
        "timestamp": datetime.now().isoformat(),
        "url": "https://www.example.com",
        "title": "测试页面"
    }
    
    # 获取MinIO存储实例
    storage = get_minio_storage()
    
    # 从base64保存
    # 不需要使用BytesIO，这里直接使用Base64字符串
    # 转换为正确的Base64格式
    if img_base64 and not img_base64.startswith('data:image'):
        img_base64 = f"data:image/png;base64,{img_base64}"
        
    if img_base64:
        base64_result = storage.save_screenshot(img_base64, "playwright_mock_screenshot.png")
        if base64_result.get("success"):
            mock_result["minio_url"] = base64_result.get("url")
            mock_result["stored_in_minio"] = True
            mock_result["local_path"] = base64_result.get("local_path")
    
    # 显示结果
    logger.info("📸 模拟截图结果:")
    logger.info(f"   标题: {mock_result['title']}")
    logger.info(f"   URL: {mock_result['url']}")
    logger.info(f"   时间戳: {mock_result['timestamp']}")
    if "minio_url" in mock_result:
        logger.info(f"   MinIO URL: {mock_result['minio_url']}")
    if "local_path" in mock_result:
        logger.info(f"   本地路径: {mock_result['local_path']}")
    
    return mock_result

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 MinIO 存储功能演示")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    
    print("📋 MinIO配置:")
    print(f"   端点: {config['endpoint']}")
    print(f"   存储桶: {config['bucket_name']}")
    print(f"   本地备份: {'启用' if config.get('local_backup', True) else '禁用'}")
    if config.get('local_backup', True):
        print(f"   备份目录: {config.get('local_backup_dir', '/tmp/playwright-screenshots')}")
    
    # 确保备份目录存在
    backup_dir = config.get('local_backup_dir', '/tmp/playwright-screenshots')
    os.makedirs(backup_dir, exist_ok=True)
    
    print("\n" + "=" * 60)
    
    # 测试保存Base64图片
    base64_result = test_save_base64()
    
    print("\n" + "=" * 60)
    
    # 测试保存本地文件
    file_result = test_save_file()
    
    print("\n" + "=" * 60)
    
    # 模拟Playwright截图
    mock_result = simulate_playwright_screenshot()
    
    print("\n" + "=" * 60)
    
    # 总结测试结果
    print("\n📊 测试结果总结:")
    if base64_result:
        print(f"Base64保存: {'✅ 成功' if base64_result.get('success') else '❌ 失败'}")
    else:
        print("Base64保存: ⚠️ 跳过")
        
    if file_result:
        print(f"文件保存: {'✅ 成功' if file_result.get('success') else '❌ 失败'}")
    else:
        print("文件保存: ⚠️ 跳过")
        
    if mock_result:
        print(f"模拟截图: {'✅ 成功' if 'minio_url' in mock_result else '⚠️ 部分成功'}")
    else:
        print("模拟截图: ❌ 失败")
    
    print("\n💡 后续步骤:")
    print("1. 安装MinIO: docker run -d -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ':9001'")
    print("2. 安装Python客户端: pip install minio")
    print("3. 修改minio_config.json配置MinIO连接信息")
    print("4. 启动Playwright MCP集群: ./start.sh")
    print("5. 运行测试: python demo.py")
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("用户中断演示")
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}", exc_info=True) 