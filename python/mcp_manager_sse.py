#!/usr/bin/env python3
"""
支持 SSE 协议的 MCP 管理器 - 集成版本
基于官方 Playwright MCP 镜像优化
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from queue import Queue, Empty
from typing import Dict, List, Optional, Any

import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestTask:
    """测试任务"""
    id: str
    name: str
    url: str
    actions: List[Dict[str, Any]]
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    assigned_instance: Optional[str] = None

@dataclass
class MCPInstance:
    """MCP 实例信息"""
    id: str
    url: str
    port: int
    status: str = "unknown"  # unknown, healthy, unhealthy
    last_check: float = 0
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    health_check_failures: int = 0
    session_id: Optional[str] = None
    
class SSEClient:
    """支持 SSE 协议的 MCP 客户端"""
    
    def __init__(self, url: str):
        self.url = url
        self.session = requests.Session()
        self.session_id = None
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
    def parse_sse_response(self, response_text: str) -> Optional[Dict]:
        """解析 SSE 格式的响应"""
        lines = response_text.strip().split('\n')
        
        for line in lines:
            if line.startswith('data: '):
                data_str = line[6:]
                try:
                    return json.loads(data_str)
                except json.JSONDecodeError:
                    logger.warning(f"无法解析 JSON: {data_str}")
                    return None
        
        return None
        
    def initialize(self) -> bool:
        """初始化连接"""
        try:
            init_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "tools": {
                            "listChanged": True
                        }
                    },
                    "clientInfo": {"name": "mcp-manager", "version": "1.0"}
                }
            }
            
            response = self.session.post(self.url, json=init_data, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result and 'result' in result:
                    # 保存 session ID
                    self.session_id = response.headers.get('mcp-session-id')
                    if self.session_id:
                        self.headers["mcp-session-id"] = self.session_id
                    
                    # 发送 initialized 通知
                    self.send_initialized()
                    return True
                    
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            
        return False
        
    def send_initialized(self):
        """发送 initialized 通知"""
        try:
            notification_data = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
            
            self.session.post(self.url, json=notification_data, headers=self.headers, timeout=5)
        except:
            pass
            
    def health_check(self) -> bool:
        """健康检查 - 多层验证策略"""
        try:
            # 方法1: 简单的HTTP连接检查
            try:
                response = self.session.get(self.url.replace('/mcp', ''), timeout=2)
                if response.status_code in [200, 404, 405]:
                    return True
            except:
                pass
            
            # 方法2: 使用 initialize 方法检查
            try:
                init_data = {
                    "jsonrpc": "2.0",
                    "id": 999,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "health-check", "version": "1.0"}
                    }
                }
                
                response = self.session.post(self.url, json=init_data, headers=self.headers, timeout=3)
                
                if response.status_code == 200:
                    result = self.parse_sse_response(response.text)
                    if result and ('result' in result or 'error' in result):
                        return True
            except:
                pass
            
            # 方法3: 使用 tools/list 作为最后检查
            try:
                list_data = {
                    "jsonrpc": "2.0",
                    "id": 999,
                    "method": "tools/list",
                    "params": {}
                }
                
                response = self.session.post(self.url, json=list_data, headers=self.headers, timeout=3)
                
                if response.status_code == 200:
                    result = self.parse_sse_response(response.text)
                    if result and ('result' in result or 'error' in result):
                        return True
            except:
                pass
            
            return False
        except Exception as e:
            logger.debug(f"健康检查失败: {e}")
            return False
    
    def list_tools(self) -> Optional[List[Dict[str, Any]]]:
        """获取可用工具列表"""
        try:
            list_data = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/list",
                "params": {}
            }
            
            response = self.session.post(self.url, json=list_data, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result and 'result' in result:
                    return result['result'].get('tools', [])
                    
        except Exception as e:
            logger.error(f"获取工具列表失败: {e}")
            
        return None
            
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict]:
        """调用工具 - 支持 2025-06-18 协议版本"""
        try:
            call_data = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            response = self.session.post(self.url, json=call_data, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result:
                    # 检查是否有错误
                    if 'error' in result:
                        logger.error(f"工具调用协议错误: {result['error']}")
                        return None
                    
                    # 检查结果
                    if 'result' in result:
                        tool_result = result['result']
                        
                        # 检查工具执行错误
                        if tool_result.get('isError', False):
                            logger.error(f"工具执行错误: {tool_result}")
                            return None
                        
                        # 处理内容
                        content = tool_result.get('content', [])
                        structured_content = tool_result.get('structuredContent')
                        
                        # 优先返回结构化内容
                        if structured_content:
                            return structured_content
                        
                        # 处理非结构化内容
                        if content:
                            # 提取文本内容
                            text_content = []
                            for item in content:
                                if item.get('type') == 'text':
                                    text_content.append(item.get('text', ''))
                            
                            if text_content:
                                return {'text': '\n'.join(text_content)}
                        
                        return tool_result
                    
        except Exception as e:
            logger.error(f"工具调用失败: {e}")
            
        return None
        
    def execute_task(self, task: TestTask) -> Dict[str, Any]:
        """执行测试任务 - 支持 2025-06-18 协议版本"""
        results = []
        
        try:
            for action in task.actions:
                action_type = action['type']
                action_result = {"action": action_type, "success": False, "data": None}
                
                if action_type == 'navigate':
                    result = self.call_tool('browser_navigate', {
                        'url': action['url']
                    })
                    if result:
                        action_result["success"] = True
                        action_result["data"] = result
                    results.append(action_result)
                    
                elif action_type == 'screenshot':
                    screenshot_args = {}
                    if 'filename' in action:
                        screenshot_args['filename'] = action['filename']
                    
                    result = self.call_tool('browser_take_screenshot', screenshot_args)
                    if result:
                        # 尝试保存到MinIO
                        try:
                            from minio_storage import get_minio_storage
                            
                            # 检查是否有base64数据
                            base64_data = None
                            if isinstance(result, dict):
                                # 尝试从不同字段获取base64数据
                                for key in ['base64', 'data', 'imageData', 'content']:
                                    if key in result:
                                        base64_data = result[key]
                                        break
                                
                                # 如果有文件路径，尝试使用文件路径上传
                                file_path = None
                                for key in ['path', 'filePath', 'screenshot_path']:
                                    if key in result:
                                        file_path = result[key]
                                        break
                                
                                if base64_data:
                                    # 获取MinIO存储实例
                                    minio = get_minio_storage()
                                    filename = action.get('filename', None)
                                    # 保存到MinIO
                                    minio_result = minio.save_screenshot(base64_data, filename)
                                    if minio_result.get('success', False):
                                        # 更新结果，添加MinIO URL
                                        result['minio_url'] = minio_result.get('url')
                                        result['stored_in_minio'] = True
                                        
                                elif file_path:
                                    # 如果有文件路径但没有base64数据
                                    minio = get_minio_storage()
                                    filename = action.get('filename', None)
                                    minio_result = minio.save_screenshot_file(file_path, filename)
                                    if minio_result.get('success', False):
                                        # 更新结果，添加MinIO URL
                                        result['minio_url'] = minio_result.get('url')
                                        result['stored_in_minio'] = True
                        except ImportError:
                            pass
                        except Exception as e:
                            logger.warning(f"保存截图到MinIO失败: {e}")
                            
                        action_result["success"] = True
                        action_result["data"] = result
                    results.append(action_result)
                    
                elif action_type == 'snapshot':
                    result = self.call_tool('browser_snapshot', {})
                    if result:
                        # 尝试保存快照到MinIO
                        try:
                            from minio_storage import get_minio_storage
                            
                            # 获取快照数据
                            snapshot_data = None
                            html_content = None
                            json_data = None
                            
                            if isinstance(result, dict):
                                # 尝试获取结构化内容
                                structured_content = result.get("structuredContent")
                                if structured_content:
                                    # 保存结构化JSON数据
                                    json_data = json.dumps(structured_content)
                                
                                # 尝试获取HTML内容
                                content_items = result.get("content", [])
                                for item in content_items:
                                    if item.get("type") == "text":
                                        html_content = item.get("text", "")
                                        break
                                        
                                # 如果有accessibility数据
                                if "accessibility" in result:
                                    snapshot_data = json.dumps(result["accessibility"])
                                
                                # 尝试获取视觉数据或截图数据
                                if "snapshot" in result:
                                    snapshot_data = json.dumps(result["snapshot"])
                                    
                            # 保存到MinIO
                            if html_content or json_data or snapshot_data:
                                minio = get_minio_storage()
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                                filename_base = action.get('filename', f"snapshot_{timestamp}")
                                
                                # 保存HTML内容
                                if html_content:
                                    html_filename = f"{filename_base}.html"
                                    html_result = minio.save_text_content(html_content, html_filename, "text/html")
                                    if html_result.get("success"):
                                        if not "minio_urls" in result:
                                            result["minio_urls"] = {}
                                        result["minio_urls"]["html"] = html_result.get("url")
                                
                                # 保存JSON结构化数据
                                if json_data:
                                    json_filename = f"{filename_base}.json"
                                    json_result = minio.save_text_content(json_data, json_filename, "application/json")
                                    if json_result.get("success"):
                                        if not "minio_urls" in result:
                                            result["minio_urls"] = {}
                                        result["minio_urls"]["json"] = json_result.get("url")
                                
                                # 保存快照数据
                                if snapshot_data:
                                    snapshot_filename = f"{filename_base}_snapshot.json"
                                    snapshot_result = minio.save_text_content(snapshot_data, snapshot_filename, "application/json")
                                    if snapshot_result.get("success"):
                                        if not "minio_urls" in result:
                                            result["minio_urls"] = {}
                                        result["minio_urls"]["snapshot"] = snapshot_result.get("url")
                                
                                # 标记已存储到MinIO
                                if "minio_urls" in result and result["minio_urls"]:
                                    result["stored_in_minio"] = True
                        except ImportError:
                            pass
                        except Exception as e:
                            logger.warning(f"保存快照到MinIO失败: {e}")
                                
                        action_result["success"] = True
                        action_result["data"] = result
                    results.append(action_result)
                    
                elif action_type == 'click':
                    result = self.call_tool('browser_click', {
                        'element': action.get('element', '元素'),
                        'ref': action['ref']
                    })
                    if result:
                        action_result["success"] = True
                        action_result["data"] = result
                    results.append(action_result)
                    
                elif action_type == 'type':
                    result = self.call_tool('browser_type', {
                        'element': action.get('element', '输入框'),
                        'ref': action['ref'],
                        'text': action['text']
                    })
                    if result:
                        action_result["success"] = True
                        action_result["data"] = result
                    results.append(action_result)
                    
                elif action_type == 'wait':
                    time.sleep(action.get('time', 1))
                    action_result["success"] = True
                    action_result["data"] = "completed"
                    results.append(action_result)
                    
                elif action_type == 'close':
                    # 关闭操作通过关闭标签页实现
                    result = self.call_tool('browser_tab_close', {})
                    if result:
                        action_result["success"] = True
                        action_result["data"] = result
                    results.append(action_result)
                    
                elif action_type == 'list_tools':
                    # 轻量级操作：获取工具列表
                    result = self.list_tools()
                    if result:
                        action_result["success"] = True
                        action_result["data"] = f"获取到 {len(result)} 个工具"
                    results.append(action_result)
                    
                elif action_type == 'health_check':
                    # 轻量级操作：健康检查
                    result = self.health_check()
                    action_result["success"] = result
                    action_result["data"] = "健康检查通过" if result else "健康检查失败"
                    results.append(action_result)
                    
                else:
                    logger.warning(f"未知操作类型: {action_type}")
                    action_result["data"] = f"未知操作类型: {action_type}"
                    results.append(action_result)
            
            # 检查是否有失败的操作
            failed_actions = [r for r in results if not r["success"]]
            if failed_actions:
                return {
                    "success": False, 
                    "error": f"部分操作失败: {len(failed_actions)}/{len(results)}",
                    "results": results
                }
            
            return {"success": True, "results": results}
            
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            return {"success": False, "error": str(e), "results": results}
            
    def close(self):
        """关闭连接"""
        try:
            self.session.close()
        except:
            pass
            
class MCPManager:
    """MCP 集群管理器"""
    
    def __init__(self, max_concurrent_per_instance: int = 1):
        self.instances: Dict[str, MCPInstance] = {}
        self.task_queue = Queue()
        self.completed_tasks: List[TestTask] = []
        self.max_concurrent_per_instance = max_concurrent_per_instance
        self.monitoring = False
        self.monitor_thread = None
        self.worker_threads: Dict[str, threading.Thread] = {}
        
    def add_instance(self, instance_id: str, url: str, port: int):
        """添加 MCP 实例"""
        self.instances[instance_id] = MCPInstance(id=instance_id, url=url, port=port)
        logger.info(f"添加实例: {instance_id} -> {url}")
        
    def start_monitoring(self):
        """启动监控"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        # 为每个实例启动工作线程
        for instance_id in self.instances:
            worker_thread = threading.Thread(target=self._worker_loop, args=(instance_id,), daemon=True)
            worker_thread.start()
            self.worker_threads[instance_id] = worker_thread
            
        logger.info("监控已启动")
        
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
        for worker_thread in self.worker_threads.values():
            worker_thread.join(timeout=5)
            
        logger.info("监控已停止")
        
    def _monitor_loop(self):
        """监控循环 - 改进的健康检查策略"""
        while self.monitoring:
            try:
                for instance_id, instance in self.instances.items():
                    # 计算检查间隔 - 根据实例状态调整
                    current_time = time.time()
                    time_since_last_check = current_time - instance.last_check
                    
                    # 根据实例状态调整检查频率
                    if instance.status == "healthy":
                        check_interval = 30  # 健康实例30秒检查一次
                    elif instance.status == "unhealthy":
                        check_interval = 15  # 不健康实例15秒检查一次
                    else:
                        check_interval = 10  # 未知状态10秒检查一次
                    
                    # 如果距离上次检查时间不够，跳过
                    if time_since_last_check < check_interval:
                        continue
                    
                    # 健康检查
                    client = SSEClient(instance.url)
                    
                    if instance.status == "unknown":
                        # 首次连接，尝试初始化
                        if client.initialize():
                            instance.status = "healthy"
                            instance.health_check_failures = 0
                            logger.info(f"实例 {instance_id} 初始化成功")
                        else:
                            instance.status = "unhealthy"
                            instance.health_check_failures += 1
                            logger.warning(f"实例 {instance_id} 初始化失败")
                    else:
                        # 定期健康检查
                        if client.health_check():
                            if instance.status != "healthy":
                                instance.status = "healthy"
                                instance.health_check_failures = 0
                                logger.info(f"实例 {instance_id} 恢复健康")
                        else:
                            instance.health_check_failures += 1
                            # 根据失败次数调整阈值
                            failure_threshold = 5 if instance.status == "healthy" else 3
                            if instance.health_check_failures >= failure_threshold:
                                instance.status = "unhealthy"
                                logger.warning(f"实例 {instance_id} 变为不健康 (失败次数: {instance.health_check_failures})")
                                
                    instance.last_check = current_time
                    client.close()
                    
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                
            time.sleep(5)  # 主循环5秒一次，但实际检查频率由各实例状态决定
            
    def _worker_loop(self, instance_id: str):
        """工作线程循环"""
        while self.monitoring:
            try:
                instance = self.instances[instance_id]
                
                # 检查实例是否健康且有可用容量
                if (instance.status == "healthy" and 
                    instance.active_tasks < self.max_concurrent_per_instance):
                    
                    try:
                        # 尝试获取任务
                        task = self.task_queue.get_nowait()
                        task.assigned_instance = instance_id
                        task.status = "running"
                        task.start_time = time.time()
                        instance.active_tasks += 1
                        
                        logger.info(f"实例 {instance_id} 开始执行任务: {task.name}")
                        
                        # 执行任务
                        client = SSEClient(instance.url)
                        if client.initialize():
                            result = client.execute_task(task)
                            
                            task.end_time = time.time()
                            task.result = result
                            
                            if result.get("success", False):
                                task.status = "completed"
                                instance.completed_tasks += 1
                                logger.info(f"任务 {task.name} 执行成功")
                            else:
                                task.status = "failed"
                                instance.failed_tasks += 1
                                logger.error(f"任务 {task.name} 执行失败: {result.get('error', '未知错误')}")
                                
                        else:
                            task.status = "failed"
                            task.result = {"error": "无法初始化连接"}
                            instance.failed_tasks += 1
                            logger.error(f"任务 {task.name} 初始化失败")
                            
                        client.close()
                        self.completed_tasks.append(task)
                        
                    except Empty:
                        # 队列为空，等待
                        time.sleep(1)
                        continue
                    finally:
                        instance.active_tasks = max(0, instance.active_tasks - 1)
                        
                else:
                    # 实例不健康或无可用容量，等待
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"工作线程 {instance_id} 错误: {e}")
                time.sleep(5)
                
    def submit_task(self, task: TestTask):
        """提交任务"""
        self.task_queue.put(task)
        logger.info(f"提交任务: {task.name}")
        
    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "instances": {
                inst_id: {
                    "status": inst.status,
                    "active_tasks": inst.active_tasks,
                    "completed_tasks": inst.completed_tasks,
                    "failed_tasks": inst.failed_tasks,
                    "last_check": inst.last_check
                }
                for inst_id, inst in self.instances.items()
            },
            "queue_size": self.task_queue.qsize(),
            "completed_tasks": len([t for t in self.completed_tasks if t.status == "completed"]),
            "failed_tasks": len([t for t in self.completed_tasks if t.status == "failed"])
        } 