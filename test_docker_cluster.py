#!/usr/bin/env python3
"""
Docker集群管理和测试脚本
启动多个Docker实例并测试集群功能
"""

import subprocess
import json
import time
import sys
import uuid
import os
from typing import List, Dict, Any

# 添加 python 目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))

from mcp_manager_sse import MCPManager, TestTask, SSEClient

class DockerClusterManager:
    """Docker集群管理器"""
    
    def __init__(self, image_name="playwright-mcp", num_instances=2):
        self.image_name = image_name
        self.num_instances = num_instances
        self.containers = []
        self.base_port = 9001
        
    def build_image(self):
        """构建Docker镜像"""
        print("🔨 构建Docker镜像...")
        try:
            result = subprocess.run([
                "docker", "build", "-t", self.image_name, "."
            ], check=True, capture_output=True, text=True)
            print("✅ Docker镜像构建成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Docker镜像构建失败: {e}")
            print(f"错误输出: {e.stderr}")
            return False
    
    def start_containers(self):
        """启动Docker容器"""
        print(f"🚀 启动 {self.num_instances} 个Docker实例...")
        
        for i in range(self.num_instances):
            container_name = f"mcp-instance-{i+1}"
            port = self.base_port + i
            
            try:
                # 停止并删除已存在的容器
                subprocess.run([
                    "docker", "rm", "-f", container_name
                ], capture_output=True)
                
                # 启动新容器
                result = subprocess.run([
                    "docker", "run", "-d",
                    "--name", container_name,
                    "-p", f"{port}:9000",
                    self.image_name
                ], check=True, capture_output=True, text=True)
                
                container_id = result.stdout.strip()
                self.containers.append({
                    "name": container_name,
                    "id": container_id,
                    "port": port,
                    "url": f"http://localhost:{port}/mcp"
                })
                
                print(f"✅ 启动实例 {container_name} (端口: {port})")
                
            except subprocess.CalledProcessError as e:
                print(f"❌ 启动容器 {container_name} 失败: {e}")
                return False
        
        return True
    
    def wait_for_containers(self, timeout=60):
        """等待容器启动完成"""
        print("⏳ 等待容器启动完成...")
        
        start_time = time.time()
        ready_containers = []
        
        while time.time() - start_time < timeout:
            for container in self.containers:
                if container["name"] in ready_containers:
                    continue
                    
                try:
                    # 检查容器健康状态
                    result = subprocess.run([
                        "curl", "-s", "-f", f"http://localhost:{container['port']}"
                    ], capture_output=True, timeout=5)
                    
                    if result.returncode == 0:
                        print(f"✅ 实例 {container['name']} 就绪")
                        ready_containers.append(container["name"])
                    
                except subprocess.TimeoutExpired:
                    pass
                except Exception:
                    pass
            
            if len(ready_containers) == len(self.containers):
                print("🎉 所有容器启动完成！")
                return True
                
            time.sleep(3)
        
        print(f"⚠️  超时等待，只有 {len(ready_containers)}/{len(self.containers)} 个容器就绪")
        return len(ready_containers) > 0
    
    def stop_containers(self):
        """停止Docker容器"""
        print("🛑 停止Docker容器...")
        
        for container in self.containers:
            try:
                subprocess.run([
                    "docker", "stop", container["name"]
                ], check=True, capture_output=True)
                
                subprocess.run([
                    "docker", "rm", container["name"]
                ], check=True, capture_output=True)
                
                print(f"✅ 停止并删除容器 {container['name']}")
                
            except subprocess.CalledProcessError as e:
                print(f"⚠️  停止容器 {container['name']} 时出错: {e}")
    
    def get_cluster_config(self):
        """生成集群配置"""
        return {
            "cluster": {
                "instances": [
                    {
                        "id": f"docker-mcp-{i+1}",
                        "port": container["port"],
                        "url": container["url"]
                    }
                    for i, container in enumerate(self.containers)
                ],
                "max_concurrent_per_instance": 1,
                "health_check_interval": 10,
                "max_retries": 3
            }
        }

def create_docker_test_tasks() -> List[TestTask]:
    """创建Docker测试任务"""
    tasks = []
    
    # 任务1: 连接测试
    task1 = TestTask(
        id=str(uuid.uuid4()),
        name="Docker实例连接测试",
        url="",
        actions=[
            {"type": "list_tools"},
            {"type": "health_check"},
            {"type": "wait", "time": 1}
        ]
    )
    tasks.append(task1)
    
    # 任务2: 稳定性测试
    task2 = TestTask(
        id=str(uuid.uuid4()),
        name="Docker实例稳定性测试",
        url="",
        actions=[
            {"type": "list_tools"},
            {"type": "wait", "time": 2},
            {"type": "health_check"},
            {"type": "list_tools"}
        ]
    )
    tasks.append(task2)
    
    # 任务3: 并发测试
    task3 = TestTask(
        id=str(uuid.uuid4()),
        name="Docker并发处理测试",
        url="",
        actions=[
            {"type": "health_check"},
            {"type": "list_tools"},
            {"type": "wait", "time": 1},
            {"type": "health_check"}
        ]
    )
    tasks.append(task3)
    
    # 任务4: 负载测试
    task4 = TestTask(
        id=str(uuid.uuid4()),
        name="Docker负载均衡测试",
        url="",
        actions=[
            {"type": "list_tools"},
            {"type": "health_check"},
            {"type": "wait", "time": 1.5},
            {"type": "list_tools"}
        ]
    )
    tasks.append(task4)
    
    return tasks

def test_docker_cluster():
    """测试Docker集群"""
    docker_manager = DockerClusterManager(num_instances=2)
    
    try:
        # 1. 构建镜像
        print("=" * 60)
        print("🐳 Docker集群管理和测试")
        print("=" * 60)
        
        if not docker_manager.build_image():
            return False
        
        # 2. 启动容器
        if not docker_manager.start_containers():
            return False
        
        # 3. 等待容器就绪
        if not docker_manager.wait_for_containers():
            print("❌ 容器启动超时，继续测试可用的实例")
        
        # 4. 创建集群管理器
        print(f"\n🏗️  创建集群管理器...")
        cluster_config = docker_manager.get_cluster_config()
        
        # 保存配置到文件（可选）
        with open("docker_cluster_config.json", "w") as f:
            json.dump(cluster_config, f, indent=2)
        
        manager = MCPManager(max_concurrent_per_instance=1)
        
        # 添加实例
        for instance in cluster_config["cluster"]["instances"]:
            manager.add_instance(
                instance_id=instance["id"],
                url=instance["url"],
                port=instance["port"]
            )
        
        print(f"✅ 添加了 {len(cluster_config['cluster']['instances'])} 个Docker实例")
        
        # 5. 启动监控
        print("🔄 启动集群监控...")
        manager.start_monitoring()
        
        # 等待实例初始化
        print("⏳ 等待实例初始化...")
        time.sleep(8)  # Docker实例可能需要更长时间
        
        # 6. 检查实例状态
        status = manager.get_status()
        healthy_count = sum(1 for inst in status["instances"].values() if inst["status"] == "healthy")
        total_count = len(status["instances"])
        
        print(f"📊 Docker实例状态: {healthy_count}/{total_count} 健康")
        
        if healthy_count == 0:
            print("❌ 没有健康的Docker实例")
            return False
        
        # 显示详细状态
        print("\n📋 Docker实例详细状态:")
        for inst_id, inst_status in status["instances"].items():
            container_info = next((c for c in docker_manager.containers if f"docker-mcp-{c['name'].split('-')[-1]}" == inst_id), None)
            status_icon = "✅" if inst_status['status'] == "healthy" else "❌"
            if container_info:
                print(f"  {status_icon} {inst_id} ({container_info['name']}): {inst_status['status']}")
            else:
                print(f"  {status_icon} {inst_id}: {inst_status['status']}")
        
        # 7. 创建和提交测试任务
        print(f"\n📝 创建Docker测试任务...")
        tasks = create_docker_test_tasks()
        
        print(f"✅ 创建了 {len(tasks)} 个测试任务:")
        for task in tasks:
            print(f"   - {task.name} ({len(task.actions)} 个操作)")
        
        # 提交任务
        print(f"\n🚀 提交任务到Docker集群...")
        start_time = time.time()
        
        for task in tasks:
            manager.submit_task(task)
        
        # 8. 等待任务完成
        print("⏳ 等待任务执行完成...")
        max_wait_time = 45
        wait_time = 0
        
        while wait_time < max_wait_time:
            status = manager.get_status()
            completed = status["completed_tasks"]
            failed = status["failed_tasks"]
            queue_size = status["queue_size"]
            
            print(f"📊 进度: 完成{completed}, 失败{failed}, 队列{queue_size}")
            
            if completed + failed >= len(tasks):
                break
                
            time.sleep(3)
            wait_time += 3
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 9. 显示测试结果
        final_status = manager.get_status()
        completed = final_status["completed_tasks"]
        failed = final_status["failed_tasks"]
        
        print(f"\n📊 Docker集群测试结果:")
        print(f"   总任务数: {len(tasks)}")
        print(f"   完成任务: {completed}")
        print(f"   失败任务: {failed}")
        print(f"   成功率: {completed/len(tasks)*100:.1f}%")
        print(f"   执行时间: {execution_time:.2f} 秒")
        
        # 详细任务结果
        print(f"\n📋 详细任务结果:")
        for task in manager.completed_tasks:
            status_icon = "✅" if task.status == "completed" else "❌"
            duration = task.end_time - task.start_time if task.end_time and task.start_time else 0
            print(f"   {status_icon} {task.name} - {duration:.2f}s (实例: {task.assigned_instance})")
            
            if task.status == "failed" and task.result:
                error = task.result.get("error", "未知错误")
                print(f"      错误: {error}")
        
        # Docker实例统计
        print(f"\n🐳 Docker实例工作统计:")
        for inst_id, inst_status in final_status["instances"].items():
            print(f"   {inst_id}:")
            print(f"     状态: {inst_status['status']}")
            print(f"     完成任务: {inst_status['completed_tasks']}")
            print(f"     失败任务: {inst_status['failed_tasks']}")
        
        # 停止监控
        print(f"\n🛑 停止集群监控...")
        manager.stop_monitoring()
        
        success = completed >= len(tasks) * 0.8
        
        if success:
            print(f"\n🎊 Docker集群测试成功！")
            print(f"✅ Docker容器集群工作正常")
            print(f"✅ 任务调度和负载均衡有效")
        else:
            print(f"\n😞 Docker集群测试部分失败")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Docker集群测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理Docker容器
        print(f"\n🧹 清理Docker容器...")
        docker_manager.stop_containers()

def main():
    """主函数"""
    try:
        success = test_docker_cluster()
        
        if success:
            print(f"\n🎉 Docker集群管理和调度功能测试成功！")
            sys.exit(0)
        else:
            print(f"\n😞 Docker集群测试未完全成功")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n\n⚠️  用户中断，正在清理...")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生未预期的错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 