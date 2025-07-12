#!/usr/bin/env python3
"""
Playwright MCP 集成演示
基于官方 Playwright MCP 项目的集群管理功能演示
"""

import json
import sys
import time
import uuid
from typing import List, Dict, Any
import os

# 添加 python 目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))

from mcp_manager_sse import MCPManager, TestTask, SSEClient

def load_config(config_file: str = "cluster_config.json") -> Dict[str, Any]:
    """加载集群配置"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 配置文件 {config_file} 不存在")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ 配置文件格式错误: {e}")
        sys.exit(1)

def create_test_tasks() -> List[TestTask]:
    """创建测试任务"""
    tasks = []
    
    # 任务1: 百度搜索演示
    task1 = TestTask(
        id=str(uuid.uuid4()),
        name="百度搜索演示",
        url="https://www.baidu.com",
        actions=[
            {"type": "navigate", "url": "https://www.baidu.com"},
            {"type": "wait", "time": 2},
            {"type": "screenshot"},
            {"type": "snapshot"},
            {"type": "close"}
        ]
    )
    tasks.append(task1)
    
    # 任务2: GitHub访问演示  
    task2 = TestTask(
        id=str(uuid.uuid4()),
        name="GitHub访问演示",
        url="https://github.com",
        actions=[
            {"type": "navigate", "url": "https://github.com"},
            {"type": "wait", "time": 2},
            {"type": "screenshot"},
            {"type": "snapshot"},
            {"type": "close"}
        ]
    )
    tasks.append(task2)
    
    # 任务3: Google访问演示
    task3 = TestTask(
        id=str(uuid.uuid4()),
        name="Google访问演示", 
        url="https://www.google.com",
        actions=[
            {"type": "navigate", "url": "https://www.google.com"},
            {"type": "wait", "time": 2},
            {"type": "screenshot"},
            {"type": "snapshot"},
            {"type": "close"}
        ]
    )
    tasks.append(task3)
    
    # 任务4: MDN Web Docs演示
    task4 = TestTask(
        id=str(uuid.uuid4()),
        name="MDN Web Docs演示",
        url="https://developer.mozilla.org",
        actions=[
            {"type": "navigate", "url": "https://developer.mozilla.org"},
            {"type": "wait", "time": 2},
            {"type": "screenshot"},
            {"type": "close"}
        ]
    )
    tasks.append(task4)
    
    return tasks

def test_single_instance():
    """测试单个实例连接"""
    print("\n🔍 测试单个实例连接...")
    
    config = load_config()
    instances = config["cluster"]["instances"]
    
    if not instances:
        print("❌ 配置文件中没有找到实例")
        return False
        
    # 测试第一个实例
    first_instance = instances[0]
    client = SSEClient(first_instance["url"])
    
    print(f"🔗 连接到实例: {first_instance['id']} ({first_instance['url']})")
    
    # 初始化连接
    if client.initialize():
        print("✅ 初始化成功")
        
        # 获取工具列表
        tools = client.list_tools()
        if tools:
            print(f"✅ 获取到 {len(tools)} 个工具")
            print("🛠️  可用工具:")
            for tool in tools[:5]:  # 只显示前5个
                print(f"   - {tool.get('name', 'unknown')}: {tool.get('description', 'No description')[:50]}...")
        else:
            print("⚠️  未获取到工具列表")
            
        # 简单测试导航
        print("\n📝 测试基本导航...")
        result = client.call_tool('browser_navigate', {'url': 'https://www.baidu.com'})
        if result:
            print("✅ 导航测试成功")
        else:
            print("❌ 导航测试失败")
            
        client.close()
        return True
    else:
        print("❌ 初始化失败")
        client.close()
        return False

def main():
    """主函数"""
    print("🚀 Playwright MCP 集成演示")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    cluster_config = config["cluster"]
    
    print(f"📋 集群配置:")
    print(f"   实例数量: {len(cluster_config['instances'])}")
    print(f"   并发限制: {cluster_config['max_concurrent_per_instance']}")
    
    # 测试单个实例
    if not test_single_instance():
        print("❌ 单实例测试失败，请检查服务是否启动")
        print("💡 提示: 运行 ./start.sh 启动集群")
        sys.exit(1)
    
    # 创建集群管理器
    print("\n🏗️  创建集群管理器...")
    manager = MCPManager(max_concurrent_per_instance=cluster_config["max_concurrent_per_instance"])
    
    # 添加实例
    for instance in cluster_config["instances"]:
        manager.add_instance(
            instance_id=instance["id"],
            url=instance["url"], 
            port=instance["port"]
        )
    
    # 启动监控
    print("🔄 启动集群监控...")
    manager.start_monitoring()
    
    # 等待实例初始化
    print("⏳ 等待实例初始化...")
    time.sleep(5)
    
    # 检查实例状态
    status = manager.get_status()
    healthy_count = sum(1 for inst in status["instances"].values() if inst["status"] == "healthy")
    total_count = len(status["instances"])
    
    print(f"📊 实例状态: {healthy_count}/{total_count} 健康")
    
    if healthy_count == 0:
        print("❌ 没有健康的实例，退出演示")
        manager.stop_monitoring()
        sys.exit(1)
    
    # 创建测试任务
    print("\n📝 创建测试任务...")
    tasks = create_test_tasks()
    
    print(f"✅ 创建了 {len(tasks)} 个测试任务:")
    for task in tasks:
        print(f"   - {task.name} ({len(task.actions)} 个操作)")
    
    # 提交任务
    print("\n🚀 提交任务到集群...")
    start_time = time.time()
    
    for task in tasks:
        manager.submit_task(task)
    
    # 等待任务完成
    print("⏳ 等待任务执行完成...")
    
    while True:
        status = manager.get_status()
        completed = status["completed_tasks"]
        queue_size = status["queue_size"]
        
        if completed >= len(tasks):
            break
            
        print(f"📊 进度: {completed}/{len(tasks)} 已完成, 队列: {queue_size}")
        time.sleep(2)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # 显示结果
    print("\n📊 执行结果:")
    print(f"   总任务数: {len(tasks)}")
    print(f"   执行时间: {execution_time:.2f} 秒")
    print(f"   平均耗时: {execution_time/len(tasks):.2f} 秒/任务")
    
    # 详细结果
    print("\n📋 详细结果:")
    success_count = 0
    for task in manager.completed_tasks:
        if task.result and task.result.get("success"):
            status_icon = "✅"
            success_count += 1
        else:
            status_icon = "❌"
            
        duration = task.end_time - task.start_time if task.end_time and task.start_time else 0
        print(f"   {status_icon} {task.name} - {duration:.2f}s (实例: {task.assigned_instance})")
        
        if task.result and not task.result.get("success"):
            error = task.result.get("error", "未知错误")
            print(f"      错误: {error}")
        
                                # 显示MinIO存储信息 (如果有)
                        if task.result and task.result.get("success"):
                            results = task.result.get("results", [])
                            for action_result in results:
                                # 处理截图
                                if action_result.get("action") == "screenshot" and action_result.get("success"):
                                    data = action_result.get("data", {})
                                    if isinstance(data, dict):
                                        # 检查是否有MinIO URL
                                        if "minio_url" in data:
                                            print(f"      📸 MinIO截图: {data['minio_url']}")
                                        elif "url" in data:
                                            print(f"      📸 截图URL: {data['url']}")
                                        elif "stored_in_minio" in data and data["stored_in_minio"]:
                                            print(f"      📸 已保存到MinIO")
                                        elif "local_path" in data:
                                            print(f"      📸 本地截图: {data['local_path']}")
                                        # 兼容旧版API
                                        elif "path" in data:
                                            print(f"      📸 截图路径: {data['path']}")
                                
                                # 处理快照
                                if action_result.get("action") == "snapshot" and action_result.get("success"):
                                    data = action_result.get("data", {})
                                    if isinstance(data, dict) and "minio_urls" in data:
                                        print(f"      📊 快照已保存到MinIO:")
                                        urls = data["minio_urls"]
                                        if "html" in urls:
                                            print(f"         - HTML内容: {urls['html']}")
                                        if "json" in urls:
                                            print(f"         - JSON数据: {urls['json']}")
                                        if "snapshot" in urls:
                                            print(f"         - 快照数据: {urls['snapshot']}")
    
    print(f"\n📈 成功率: {success_count}/{len(tasks)} ({success_count/len(tasks)*100:.1f}%)")
    
    # 实例统计
    print("\n🏭 实例统计:")
    final_status = manager.get_status()
    for inst_id, inst_status in final_status["instances"].items():
        print(f"   {inst_id}: {inst_status['status']}")
        print(f"     完成任务: {inst_status['completed_tasks']}")
        print(f"     失败任务: {inst_status['failed_tasks']}")
    
    # 停止监控
    print("\n🛑 停止集群监控...")
    manager.stop_monitoring()
    
    print("🎉 演示完成！")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断，正在清理...")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 