#!/usr/bin/env python3
"""
MinIO 存储工具 - 用于保存 Playwright 截图到 MinIO 对象存储服务
"""

import os
import base64
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MinioStorage:
    """MinIO 对象存储服务接口"""
    
    def __init__(self, config_file: str = "minio_config.json"):
        """
        初始化 MinIO 存储接口
        
        参数:
            config_file: MinIO配置文件路径
        """
        self.config = self._load_config(config_file)
        self.client = None
        self._initialize_client()
        self._ensure_bucket_exists()
        
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """加载 MinIO 配置"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), config_file)
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except FileNotFoundError:
            # 如果配置文件不存在，创建默认配置
            logger.warning(f"配置文件 {config_file} 不存在，创建默认配置")
            default_config = {
                "endpoint": "127.0.0.1:9000",
                "access_key": "minioadmin",
                "secret_key": "minioadmin",
                "secure": False,
                "bucket_name": "playwright-screenshots",
                "region": "cn-north-1"
            }
            # 保存默认配置
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            return default_config
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            raise
            
    def _initialize_client(self):
        """初始化 MinIO 客户端"""
        # 检查是否需要使用MinIO
        if not self.config.get("use_minio", True):
            logger.info("MinIO 功能已禁用，仅使用本地存储")
            self.client = None
            return
            
        try:
            from minio import Minio
            from minio.error import S3Error
            
            self.client = Minio(
                endpoint=self.config["endpoint"],
                access_key=self.config["access_key"],
                secret_key=self.config["secret_key"],
                secure=self.config.get("secure", False),
                region=self.config.get("region", "cn-north-1")
            )
            logger.info(f"MinIO 客户端初始化成功: {self.config['endpoint']}")
        except ImportError:
            logger.warning("未安装 minio 客户端库，将仅使用本地备份功能")
            logger.info("要启用MinIO功能，请使用 pip install minio 安装客户端库")
            self.client = None
        except Exception as e:
            logger.error(f"MinIO 客户端初始化失败: {e}")
            logger.info("将仅使用本地备份功能")
            self.client = None
            
        # 创建本地备份目录
        if self.config.get("local_backup", True):
            backup_dir = self.config.get("local_backup_dir", "/tmp/playwright-screenshots")
            os.makedirs(backup_dir, exist_ok=True)
            logger.info(f"本地备份目录: {backup_dir}")
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        if not self.client:
            logger.error("MinIO 客户端未初始化")
            return
            
        try:
            bucket_name = self.config["bucket_name"]
            bucket_exists = self.client.bucket_exists(bucket_name)
            
            if not bucket_exists:
                logger.info(f"存储桶 {bucket_name} 不存在，正在创建...")
                self.client.make_bucket(bucket_name, location=self.config.get("region", "cn-north-1"))
                logger.info(f"存储桶 {bucket_name} 创建成功")
            else:
                logger.info(f"存储桶 {bucket_name} 已存在")
                
        except Exception as e:
            logger.error(f"检查/创建存储桶失败: {e}")
            
    def save_screenshot(self, base64_data: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        保存 Base64 格式的截图到 MinIO
        
        参数:
            base64_data: Base64 编码的图像数据
            filename: 可选的文件名，如果未提供将使用时间戳生成
            
        返回:
            包含文件存储信息的字典
        """
        try:
            # 解码 Base64 数据
            if isinstance(base64_data, str):
                if base64_data.startswith('data:image'):
                    # 处理 data URI 格式的 Base64 数据
                    _, encoded = base64_data.split(',', 1)
                    image_data = base64.b64decode(encoded)
                else:
                    # 处理普通 Base64 数据
                    image_data = base64.b64decode(base64_data)
            else:
                # 处理已经是二进制数据的情况
                image_data = base64_data
                
            # 生成文件名
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"screenshot_{timestamp}.png"
            elif not filename.endswith('.png'):
                filename = f"{filename}.png"
                
            result = {
                "success": False,
                "filename": filename,
                "size": len(image_data)
            }
            
            # 本地备份
            local_saved = False
            if self.config.get("local_backup", True):
                try:
                    backup_dir = self.config.get("local_backup_dir", "/tmp/playwright-screenshots")
                    local_path = os.path.join(backup_dir, filename)
                    with open(local_path, 'wb') as f:
                        f.write(image_data)
                    result["local_path"] = local_path
                    local_saved = True
                    logger.info(f"截图已保存到本地: {local_path}")
                except Exception as e:
                    logger.warning(f"保存截图到本地失败: {e}")
            
            # 上传到 MinIO
            if self.client:
                try:
                    bucket_name = self.config["bucket_name"]
                    
                    # 使用BytesIO对象来支持read方法
                    from io import BytesIO
                    buffer = BytesIO(image_data)
                    buffer.seek(0)
                    
                    self.client.put_object(
                        bucket_name=bucket_name,
                        object_name=filename,
                        data=buffer,
                        length=len(image_data),
                        content_type="image/png"
                    )
                    
                    # 生成访问 URL
                    endpoint = self.config["endpoint"]
                    protocol = "https" if self.config.get("secure", False) else "http"
                    url = f"{protocol}://{endpoint}/{bucket_name}/{filename}"
                    
                    logger.info(f"截图已保存到 MinIO: {filename}")
                    
                    result.update({
                        "success": True,
                        "bucket": bucket_name,
                        "url": url,
                    })
                    return result
                except Exception as e:
                    logger.error(f"保存截图到 MinIO 失败: {e}")
                    # 如果本地保存成功，返回部分成功
                    if local_saved:
                        result["success"] = True
                        result["minio_error"] = str(e)
                        return result
                    else:
                        result["error"] = str(e)
                        return result
            elif local_saved:
                # 如果没有MinIO但本地保存成功
                result["success"] = True
                return result
            else:
                # 两者都失败
                result["error"] = "MinIO客户端未初始化且本地备份失败"
                return result
            
        except Exception as e:
            logger.error(f"保存截图失败: {e}")
            return {"success": False, "error": str(e)}
            
    def save_screenshot_file(self, file_path: str, object_name: Optional[str] = None) -> Dict[str, Any]:
        """
        将本地截图文件保存到 MinIO
        
        参数:
            file_path: 本地文件路径
            object_name: 对象存储中的文件名，如果未提供将使用原文件名
            
        返回:
            包含文件存储信息的字典
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return {"success": False, "error": f"文件不存在: {file_path}"}
                
            # 确定对象名
            if not object_name:
                object_name = os.path.basename(file_path)
                
            file_size = os.path.getsize(file_path)
            result = {
                "success": False,
                "filename": object_name,
                "source_path": file_path,
                "size": file_size
            }
            
            # 本地备份 (如果源文件不在备份目录)
            backup_dir = self.config.get("local_backup_dir", "/tmp/playwright-screenshots")
            backup_path = os.path.join(backup_dir, object_name)
            
            if self.config.get("local_backup", True) and file_path != backup_path:
                try:
                    import shutil
                    shutil.copy2(file_path, backup_path)
                    result["backup_path"] = backup_path
                    logger.info(f"截图已备份到本地: {backup_path}")
                except Exception as e:
                    logger.warning(f"备份截图到本地失败: {e}")
            
            # 上传到 MinIO
            if self.client:
                try:
                    bucket_name = self.config["bucket_name"]
                    
                    self.client.fput_object(
                        bucket_name=bucket_name,
                        object_name=object_name,
                        file_path=file_path,
                        content_type="image/png"
                    )
                    
                    # 生成访问 URL
                    endpoint = self.config["endpoint"]
                    protocol = "https" if self.config.get("secure", False) else "http"
                    url = f"{protocol}://{endpoint}/{bucket_name}/{object_name}"
                    
                    logger.info(f"截图文件已保存到 MinIO: {object_name}")
                    
                    result.update({
                        "success": True,
                        "bucket": bucket_name,
                        "url": url
                    })
                    return result
                    
                except Exception as e:
                    logger.error(f"保存截图文件到 MinIO 失败: {e}")
                    if file_path:
                        # 如果原始文件存在，返回部分成功
                        result["success"] = True
                        result["minio_error"] = str(e)
                        return result
                    else:
                        result["error"] = str(e)
                        return result
            else:
                # 没有MinIO客户端但有原始文件
                result["success"] = True
                result["minio_status"] = "未启用MinIO或MinIO客户端未初始化"
                return result
            
        except Exception as e:
            logger.error(f"保存截图文件失败: {e}")
            return {"success": False, "error": str(e)}
            
    def save_text_content(self, content: str, filename: str, content_type: str = "text/plain") -> Dict[str, Any]:
        """
        保存文本内容（HTML、JSON等）到 MinIO
        
        参数:
            content: 文本内容
            filename: 文件名
            content_type: 内容类型，默认为text/plain
            
        返回:
            包含文件存储信息的字典
        """
        try:
            # 检查内容
            if not content:
                return {"success": False, "error": "内容为空"}
                
            # 转换内容为字节
            content_bytes = content.encode('utf-8')
                
            result = {
                "success": False,
                "filename": filename,
                "size": len(content_bytes)
            }
            
            # 本地备份
            local_saved = False
            if self.config.get("local_backup", True):
                try:
                    backup_dir = self.config.get("local_backup_dir", "/tmp/playwright-screenshots")
                    local_path = os.path.join(backup_dir, filename)
                    with open(local_path, 'wb') as f:
                        f.write(content_bytes)
                    result["local_path"] = local_path
                    local_saved = True
                    logger.info(f"{content_type.split('/')[1].upper()}内容已保存到本地: {local_path}")
                except Exception as e:
                    logger.warning(f"保存内容到本地失败: {e}")
            
            # 上传到 MinIO
            if self.client:
                try:
                    bucket_name = self.config["bucket_name"]
                    
                    import io
                    self.client.put_object(
                        bucket_name=bucket_name,
                        object_name=filename,
                        data=io.BytesIO(content_bytes),
                        length=len(content_bytes),
                        content_type=content_type
                    )
                    
                    # 生成访问 URL
                    endpoint = self.config["endpoint"]
                    protocol = "https" if self.config.get("secure", False) else "http"
                    url = f"{protocol}://{endpoint}/{bucket_name}/{filename}"
                    
                    logger.info(f"{content_type.split('/')[1].upper()}内容已保存到 MinIO: {filename}")
                    
                    result.update({
                        "success": True,
                        "bucket": bucket_name,
                        "url": url,
                    })
                    return result
                except Exception as e:
                    logger.error(f"保存内容到 MinIO 失败: {e}")
                    # 如果本地保存成功，返回部分成功
                    if local_saved:
                        result["success"] = True
                        result["minio_error"] = str(e)
                        return result
                    else:
                        result["error"] = str(e)
                        return result
            elif local_saved:
                # 如果没有MinIO但本地保存成功
                result["success"] = True
                return result
            else:
                # 两者都失败
                result["error"] = "MinIO客户端未初始化且本地备份失败"
                return result
                
        except Exception as e:
            logger.error(f"保存内容失败: {e}")
            return {"success": False, "error": str(e)}
            
def get_minio_storage() -> MinioStorage:
    """获取 MinIO 存储实例"""
    return MinioStorage() 