#!/usr/bin/env python3
"""
Playwright MCP 集群管理和调度功能测试
专门测试管理和调度系统，不依赖具体的浏览器工具
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

def test_connection_and_tools():
    """测试连接和工具列表获取"""
    print("🔍 测试连接和工具列表获取...")
    
    config = load_config()
    instances = config["cluster"]["instances"]
    
    results = {}
    
    for instance in instances:
        instance_id = instance["id"]
        instance_url = instance["url"]
        
        print(f"\n📡 测试实例 {instance_id} ({instance_url})")
        
        client = SSEClient(instance_url)
        
        try:
            # 初始化连接
            if client.initialize():
                print(f"  ✅ 初始化成功")
                
                # 获取工具列表
                tools = client.list_tools()
                if tools:
                    print(f"  ✅ 获取到 {len(tools)} 个工具")
                    results[instance_id] = {
                        "status": "healthy",
                        "tools_count": len(tools),
                        "tools": [tool.get('name') for tool in tools[:10]]  # 前10个工具名
                    }
                else:
                    print(f"  ⚠️  未获取到工具列表")
                    results[instance_id] = {
                        "status": "partial",
                        "tools_count": 0,
                        "error": "无法获取工具列表"
                    }
            else:
                print(f"  ❌ 初始化失败")
                results[instance_id] = {
                    "status": "unhealthy",
                    "error": "初始化失败"
                }
                
        except Exception as e:
            print(f"  ❌ 连接异常: {e}")
            results[instance_id] = {
                "status": "error",
                "error": str(e)
            }
        finally:
            client.close()
    
    return results

def create_lightweight_tasks() -> List[TestTask]:
    """创建轻量级测试任务（不依赖浏览器具体操作）"""
    tasks = []
    
    # 任务1: 工具列表获取
    task1 = TestTask(
        id=str(uuid.uuid4()),
        name="工具列表获取测试",
        url="",
        actions=[
            {"type": "list_tools"},
            {"type": "wait", "time": 1}
        ]
    )
    tasks.append(task1)
    
    # 任务2: 健康检查
    task2 = TestTask(
        id=str(uuid.uuid4()),
        name="健康检查测试",
        url="",
        actions=[
            {"type": "health_check"},
            {"type": "wait", "time": 1}
        ]
    )
    tasks.append(task2)
    
    # 任务3: 连接测试
    task3 = TestTask(
        id=str(uuid.uuid4()),
        name="连接稳定性测试",
        url="",
        actions=[
            {"type": "list_tools"},
            {"type": "wait", "time": 2},
            {"type": "list_tools"}
        ]
    )
    tasks.append(task3)
    
    # 任务4: 并发测试
    task4 = TestTask(
        id=str(uuid.uuid4()),
        name="并发处理测试",
        url="",
        actions=[
            {"type": "list_tools"},
            {"type": "health_check"},
            {"type": "wait", "time": 1}
        ]
    )
    tasks.append(task4)
    
    return tasks

def test_cluster_management():
    """测试集群管理功能"""
    print("\n🏗️  测试集群管理功能...")
    
    config = load_config()
    cluster_config = config["cluster"]
    
    # 创建集群管理器
    manager = MCPManager(max_concurrent_per_instance=cluster_config["max_concurrent_per_instance"])
    
    # 添加实例
    for instance in cluster_config["instances"]:
        manager.add_instance(
            instance_id=instance["id"],
            url=instance["url"], 
            port=instance["port"]
        )
    
    print(f"✅ 添加了 {len(cluster_config['instances'])} 个实例")
    
    # 启动监控
    print("🔄 启动集群监控...")
    manager.start_monitoring()
    
    # 等待实例初始化
    print("⏳ 等待实例初始化...")
    for i in range(10):
        time.sleep(1)
        status = manager.get_status()
        healthy_count = sum(1 for inst in status["instances"].values() if inst["status"] == "healthy")
        print(f"  检查中... {healthy_count}/{len(cluster_config['instances'])} 健康")
        if healthy_count > 0:
            break
    
    # 检查最终状态
    final_status = manager.get_status()
    healthy_count = sum(1 for inst in final_status["instances"].values() if inst["status"] == "healthy")
    total_count = len(final_status["instances"])
    
    print(f"📊 最终状态: {healthy_count}/{total_count} 健康")
    
    # 显示详细状态
    print("\n📋 实例详细状态:")
    for inst_id, inst_status in final_status["instances"].items():
        status_icon = "✅" if inst_status['status'] == "healthy" else "❌"
        print(f"  {status_icon} {inst_id}: {inst_status['status']}")
    
    return manager, healthy_count > 0

def test_task_scheduling(manager: MCPManager):
    """测试任务调度功能"""
    print("\n📝 测试任务调度功能...")
    
    # 创建轻量级任务
    tasks = create_lightweight_tasks()
    
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
    max_wait_time = 30  # 最多等待30秒
    wait_time = 0
    
    while wait_time < max_wait_time:
        status = manager.get_status()
        completed = status["completed_tasks"]
        failed = status["failed_tasks"]
        queue_size = status["queue_size"]
        
        print(f"📊 进度: 完成{completed}, 失败{failed}, 队列{queue_size}")
        
        if completed + failed >= len(tasks):
            break
            
        time.sleep(2)
        wait_time += 2
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # 显示结果
    final_status = manager.get_status()
    print(f"\n📊 执行结果:")
    print(f"   总任务数: {len(tasks)}")
    print(f"   完成任务: {final_status['completed_tasks']}")
    print(f"   失败任务: {final_status['failed_tasks']}")
    print(f"   执行时间: {execution_time:.2f} 秒")
    
    # 详细任务结果
    print("\n📋 详细任务结果:")
    for task in manager.completed_tasks:
        status_icon = "✅" if task.status == "completed" else "❌"
        duration = task.end_time - task.start_time if task.end_time and task.start_time else 0
        print(f"   {status_icon} {task.name} - {duration:.2f}s (实例: {task.assigned_instance})")
        
        if task.status == "failed" and task.result:
            error = task.result.get("error", "未知错误")
            print(f"      错误: {error}")
    
    # 实例统计
    print("\n🏭 实例工作统计:")
    for inst_id, inst_status in final_status["instances"].items():
        print(f"   {inst_id}:")
        print(f"     状态: {inst_status['status']}")
        print(f"     完成任务: {inst_status['completed_tasks']}")
        print(f"     失败任务: {inst_status['failed_tasks']}")
        print(f"     当前活跃: {inst_status['active_tasks']}")
    
    return final_status['completed_tasks'] > 0

def main():
    """主函数"""
    print("🚀 Playwright MCP 集群管理和调度功能测试")
    print("=" * 60)
    
    try:
        # 第一步：测试连接和工具获取
        connection_results = test_connection_and_tools()
        
        healthy_instances = sum(1 for result in connection_results.values() if result.get("status") == "healthy")
        
        print(f"\n📊 连接测试结果: {healthy_instances}/{len(connection_results)} 实例健康")
        
        if healthy_instances == 0:
            print("❌ 所有实例都不健康，无法继续测试")
            return False
        
        # 第二步：测试集群管理
        manager, cluster_healthy = test_cluster_management()
        
        if not cluster_healthy:
            print("❌ 集群管理测试失败")
            return False
        
        # 第三步：测试任务调度
        scheduling_success = test_task_scheduling(manager)
        
        # 停止监控
        print("\n🛑 停止集群监控...")
        manager.stop_monitoring()
        
        # 总结
        print(f"\n🎉 测试完成！")
        print(f"✅ 连接测试: {healthy_instances}/{len(connection_results)} 实例健康")
        print(f"✅ 集群管理: {'成功' if cluster_healthy else '失败'}")
        print(f"✅ 任务调度: {'成功' if scheduling_success else '失败'}")
        
        return scheduling_success
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎊 所有测试通过！集群管理和调度功能正常工作！")
        sys.exit(0)
    else:
        print("\n😞 部分测试失败，请检查配置和服务状态")
        sys.exit(1) 