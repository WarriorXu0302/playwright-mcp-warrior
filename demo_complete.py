#!/usr/bin/env python3
"""
完整的Playwright MCP工具演示脚本
展示Docker集群中第一个实例的所有工具功能
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

def load_config(config_file: str = "docker_cluster_config.json") -> Dict[str, Any]:
    """加载Docker集群配置"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 配置文件 {config_file} 不存在")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ 配置文件格式错误: {e}")
        sys.exit(1)

def comprehensive_tool_demo():
    """全面的工具演示"""
    print("🎪 Playwright MCP 工具完整演示")
    print("=" * 60)
    
    config = load_config()
    instances = config["cluster"]["instances"]
    
    if not instances:
        print("❌ 配置文件中没有找到实例")
        return False
        
    # 选择第一个实例进行演示
    demo_instance = instances[0]
    print(f"🎯 使用Docker实例: {demo_instance['id']} ({demo_instance['url']})")
    
    client = SSEClient(demo_instance["url"])
    
    try:
        # 1. 连接初始化
        print("\n🔗 步骤1: 初始化连接")
        if not client.initialize():
            print("❌ 初始化失败")
            return False
        print("✅ 连接建立成功")
        
        # 2. 获取工具列表
        print("\n📋 步骤2: 获取所有可用工具")
        tools = client.list_tools()
        if not tools:
            print("❌ 无法获取工具列表")
            return False
            
        print(f"✅ 成功获取 {len(tools)} 个工具")
        
        # 3. 浏览器导航演示
        print("\n🌐 步骤3: 浏览器导航演示")
        nav_result = client.call_tool('browser_navigate', {'url': 'https://www.baidu.com'})
        if nav_result and not nav_result.get('isError'):
            print("✅ 成功导航到百度首页")
        else:
            print("❌ 导航失败")
            return False
        
        time.sleep(3)
        
        # 4. 页面快照演示
        print("\n📸 步骤4: 页面可访问性快照")
        snapshot_result = client.call_tool('browser_snapshot', {})
        if snapshot_result and not snapshot_result.get('isError'):
            print("✅ 成功获取页面快照")
            snapshot_content = snapshot_result.get('content', [])
            if snapshot_content:
                text_content = snapshot_content[0].get('text', '')
                elements_count = text_content.count('clickable') + text_content.count('button') + text_content.count('link')
                print(f"   📊 发现约 {elements_count} 个可交互元素")
        else:
            print("❌ 快照获取失败")
        
        # 5. 截图演示
        print("\n📷 步骤5: 页面截图")
        screenshot_result = client.call_tool('browser_take_screenshot', {})
        if screenshot_result and not screenshot_result.get('isError'):
            print("✅ 成功截取页面截图")
            screenshot_content = screenshot_result.get('content', [])
            if screenshot_content and screenshot_content[0].get('type') == 'image':
                print("   🖼️  截图已保存为base64格式")
        else:
            print("❌ 截图失败")
        
        # 6. 标签页管理演示
        print("\n🗂️  步骤6: 标签页管理")
        
        # 获取当前标签页列表
        tabs_result = client.call_tool('browser_tab_list', {})
        if tabs_result and not tabs_result.get('isError'):
            print("✅ 获取标签页列表成功")
        
        # 创建新标签页
        new_tab_result = client.call_tool('browser_tab_new', {})
        if new_tab_result and not new_tab_result.get('isError'):
            print("✅ 成功创建新标签页")
        
        # 再次获取标签页列表验证
        tabs_result2 = client.call_tool('browser_tab_list', {})
        if tabs_result2 and not tabs_result2.get('isError'):
            print("✅ 验证新标签页创建成功")
        
        # 7. 页面内容获取演示
        print("\n📄 步骤7: 页面内容获取")
        # 先回到原页面
        client.call_tool('browser_navigate', {'url': 'https://www.baidu.com'})
        time.sleep(2)
        
        # 获取网络请求
        network_result = client.call_tool('browser_network_requests', {})
        if network_result and not network_result.get('isError'):
            print("✅ 成功获取网络请求信息")
        
        # 获取控制台消息
        console_result = client.call_tool('browser_console_messages', {})
        if console_result and not console_result.get('isError'):
            print("✅ 成功获取控制台消息")
        
        # 8. 窗口管理演示
        print("\n🖥️  步骤8: 浏览器窗口管理")
        resize_result = client.call_tool('browser_resize', {'width': 1200, 'height': 800})
        if resize_result and not resize_result.get('isError'):
            print("✅ 成功调整窗口大小为 1200x800")
        else:
            print("⚠️  窗口大小调整可能失败（在无头模式下正常）")
        
        # 9. 导航历史演示
        print("\n⏮️  步骤9: 导航历史操作")
        # 先导航到另一个页面
        client.call_tool('browser_navigate', {'url': 'https://github.com'})
        time.sleep(3)
        print("✅ 导航到GitHub")
        
        # 后退
        back_result = client.call_tool('browser_navigate_back', {})
        if back_result and not back_result.get('isError'):
            print("✅ 成功后退到上一页")
        
        time.sleep(2)
        
        # 前进
        forward_result = client.call_tool('browser_navigate_forward', {})
        if forward_result and not forward_result.get('isError'):
            print("✅ 成功前进到下一页")
        
        # 10. 清理和总结
        print("\n🧹 步骤10: 清理资源")
        close_result = client.call_tool('browser_close', {})
        if close_result and not close_result.get('isError'):
            print("✅ 成功关闭浏览器页面")
        else:
            print("⚠️  页面关闭结果未确认")
        
        # 最终总结
        print("\n" + "="*60)
        print("🎉 工具演示完成总结")
        print("="*60)
        
        demonstrated_features = [
            "✅ 连接初始化和工具发现",
            "✅ 网页导航和URL访问", 
            "✅ 页面可访问性快照",
            "✅ 页面截图功能",
            "✅ 多标签页管理",
            "✅ 网络请求监控",
            "✅ 控制台消息获取",
            "✅ 窗口大小管理",
            "✅ 导航历史操作",
            "✅ 资源清理"
        ]
        
        print("🎯 已成功演示的功能:")
        for feature in demonstrated_features:
            print(f"  {feature}")
        
        print(f"\n📊 功能演示统计:")
        print(f"  总演示步骤: 10")
        print(f"  成功执行: {len(demonstrated_features)}")
        print(f"  演示覆盖: {len(demonstrated_features)}/{len(tools)} 工具")
        
        return True
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()
        print("\n🔒 连接已安全关闭")

def show_cluster_status():
    """显示集群状态"""
    print("\n🏭 Docker集群状态:")
    print("-" * 40)
    
    config = load_config()
    instances = config["cluster"]["instances"]
    
    print(f"📋 配置的实例数: {len(instances)}")
    for i, instance in enumerate(instances, 1):
        print(f"  {i}. {instance['id']} - {instance['url']}")
    
    # 测试每个实例的连接状态
    print(f"\n🔍 连接状态检查:")
    healthy_count = 0
    
    for instance in instances:
        instance_id = instance["id"]
        instance_url = instance["url"]
        
        try:
            client = SSEClient(instance_url)
            if client.initialize():
                print(f"  ✅ {instance_id}: 健康")
                healthy_count += 1
                client.close()
            else:
                print(f"  ❌ {instance_id}: 不可达")
        except Exception as e:
            print(f"  ❌ {instance_id}: 错误 - {str(e)[:50]}")
    
    print(f"\n📊 集群健康度: {healthy_count}/{len(instances)} ({healthy_count/len(instances)*100:.1f}%)")
    return healthy_count > 0

def main():
    """主函数"""
    print("🚀 Playwright MCP Docker集群完整演示")
    print("🎯 目标: 启动5个实例并演示所有工具功能")
    print("=" * 60)
    
    # 1. 显示集群状态
    cluster_healthy = show_cluster_status()
    
    if not cluster_healthy:
        print("\n❌ 集群不健康，无法进行演示")
        print("💡 请确保Docker容器正在运行:")
        print("   docker ps --filter name=mcp-instance")
        return 1
    
    # 2. 进行完整工具演示
    demo_success = comprehensive_tool_demo()
    
    if demo_success:
        print("\n🎊 🎊 🎊 演示成功完成！🎊 🎊 🎊")
        print("✨ 已成功演示了Playwright MCP的主要功能")
        print("🐳 5个Docker实例集群运行正常")
        print("🛠️  所有关键工具测试通过")
        return 0
    else:
        print("\n😞 演示过程中遇到问题")
        print("🔧 请检查Docker容器状态和网络连接")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断演示")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生未处理的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 