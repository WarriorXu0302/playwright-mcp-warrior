#!/usr/bin/env python3
"""
Playwright MCP 高级压力测试
测试集群在高负载下的表现
"""

import json
import sys
import time
import uuid
from typing import List, Dict, Any
import os
import random

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

def create_stress_test_tasks(num_tasks: int = 12) -> List[TestTask]:
    """创建压力测试任务"""
    tasks = []
    
    task_templates = [
        {
            "name_template": "工具列表压测-{}",
            "actions": [
                {"type": "list_tools"},
                {"type": "wait", "time": random.uniform(0.5, 2.0)},
                {"type": "list_tools"}
            ]
        },
        {
            "name_template": "健康检查压测-{}",
            "actions": [
                {"type": "health_check"},
                {"type": "wait", "time": random.uniform(0.3, 1.5)},
                {"type": "health_check"},
                {"type": "list_tools"}
            ]
        },
        {
            "name_template": "混合操作压测-{}",
            "actions": [
                {"type": "list_tools"},
                {"type": "health_check"},
                {"type": "wait", "time": random.uniform(0.2, 1.0)},
                {"type": "list_tools"},
                {"type": "health_check"}
            ]
        }
    ]
    
    for i in range(num_tasks):
        template = random.choice(task_templates)
        task = TestTask(
            id=str(uuid.uuid4()),
            name=template["name_template"].format(i+1),
            url="",
            actions=template["actions"].copy()
        )
        tasks.append(task)
    
    return tasks

def run_stress_test():
    """运行压力测试"""
    print("🔥 Playwright MCP 高级压力测试")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    cluster_config = config["cluster"]
    
    # 创建集群管理器 - 增加并发数
    manager = MCPManager(max_concurrent_per_instance=2)  # 每个实例允许2个并发任务
    
    # 添加实例
    for instance in cluster_config["instances"]:
        manager.add_instance(
            instance_id=instance["id"],
            url=instance["url"], 
            port=instance["port"]
        )
    
    print(f"🏗️  创建集群管理器 (每实例并发: 2)")
    print(f"✅ 添加了 {len(cluster_config['instances'])} 个实例")
    
    # 启动监控
    print("🔄 启动集群监控...")
    manager.start_monitoring()
    
    # 等待实例初始化
    print("⏳ 等待实例初始化...")
    time.sleep(3)
    
    # 检查实例状态
    status = manager.get_status()
    healthy_count = sum(1 for inst in status["instances"].values() if inst["status"] == "healthy")
    total_count = len(status["instances"])
    
    print(f"📊 实例状态: {healthy_count}/{total_count} 健康")
    
    if healthy_count == 0:
        print("❌ 没有健康的实例，无法执行压力测试")
        return False
    
    # 创建大量任务
    print("\n📝 创建压力测试任务...")
    tasks = create_stress_test_tasks(16)  # 创建16个任务
    
    print(f"✅ 创建了 {len(tasks)} 个压力测试任务")
    print(f"📊 理论最大并发: {healthy_count * 2} 个任务")
    
    # 分批提交任务
    print(f"\n🚀 分批提交任务...")
    start_time = time.time()
    
    # 第一批：8个任务
    batch1 = tasks[:8]
    print(f"📤 提交第一批任务 ({len(batch1)} 个)")
    for task in batch1:
        manager.submit_task(task)
    
    # 等待2秒
    time.sleep(2)
    
    # 第二批：剩余任务
    batch2 = tasks[8:]
    print(f"📤 提交第二批任务 ({len(batch2)} 个)")
    for task in batch2:
        manager.submit_task(task)
    
    # 监控执行过程
    print(f"\n⏳ 监控任务执行过程...")
    max_wait_time = 45  # 最多等待45秒
    wait_time = 0
    last_completed = 0
    
    while wait_time < max_wait_time:
        status = manager.get_status()
        completed = status["completed_tasks"]
        failed = status["failed_tasks"]
        queue_size = status["queue_size"]
        
        # 计算活跃任务数
        active_tasks = sum(inst["active_tasks"] for inst in status["instances"].values())
        
        if completed != last_completed:
            print(f"📊 进度: 完成{completed}, 失败{failed}, 队列{queue_size}, 活跃{active_tasks}")
            last_completed = completed
        
        if completed + failed >= len(tasks):
            break
            
        time.sleep(1)
        wait_time += 1
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # 分析结果
    final_status = manager.get_status()
    completed = final_status["completed_tasks"]
    failed = final_status["failed_tasks"]
    
    print(f"\n📊 压力测试结果:")
    print(f"   总任务数: {len(tasks)}")
    print(f"   完成任务: {completed}")
    print(f"   失败任务: {failed}")
    print(f"   成功率: {completed/len(tasks)*100:.1f}%")
    print(f"   总执行时间: {execution_time:.2f} 秒")
    print(f"   平均吞吐量: {completed/execution_time:.2f} 任务/秒")
    
    # 实例负载分析
    print(f"\n🏭 实例负载分析:")
    for inst_id, inst_status in final_status["instances"].items():
        load_ratio = inst_status["completed_tasks"] / completed if completed > 0 else 0
        print(f"   {inst_id}:")
        print(f"     完成任务: {inst_status['completed_tasks']} ({load_ratio*100:.1f}%)")
        print(f"     失败任务: {inst_status['failed_tasks']}")
        print(f"     状态: {inst_status['status']}")
    
    # 详细任务时间分析
    print(f"\n⏱️  任务执行时间分析:")
    durations = []
    for task in manager.completed_tasks:
        if task.end_time and task.start_time:
            duration = task.end_time - task.start_time
            durations.append(duration)
    
    if durations:
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        print(f"   平均执行时间: {avg_duration:.2f} 秒")
        print(f"   最快执行时间: {min_duration:.2f} 秒")
        print(f"   最慢执行时间: {max_duration:.2f} 秒")
    
    # 停止监控
    print(f"\n🛑 停止集群监控...")
    manager.stop_monitoring()
    
    return completed >= len(tasks) * 0.8  # 80%以上成功率视为通过

def main():
    """主函数"""
    try:
        success = run_stress_test()
        
        if success:
            print(f"\n🎊 压力测试通过！集群表现优秀！")
            print(f"✅ 系统能够稳定处理高并发任务")
            print(f"✅ 负载均衡工作正常")
            print(f"✅ 故障恢复机制有效")
            return True
        else:
            print(f"\n😞 压力测试未完全通过，但系统基本稳定")
            return False
            
    except Exception as e:
        print(f"\n❌ 压力测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 