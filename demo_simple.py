#!/usr/bin/env python3
"""
简化的 Playwright MCP 演示
测试单个实例连接
"""

import json
import sys
import time
import os

# 添加 python 目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))

from mcp_manager_sse import SSEClient

def test_simple_connection():
    """测试简单连接"""
    print("🔍 测试连接到 MCP 实例...")
    
    # 连接到单个实例
    client = SSEClient("http://localhost:9001/mcp")
    
    try:
        # 初始化连接
        print("🔄 初始化连接...")
        if client.initialize():
            print("✅ 初始化成功")
            
            # 获取工具列表
            print("📋 获取工具列表...")
            tools = client.list_tools()
            if tools:
                print(f"✅ 获取到 {len(tools)} 个工具")
                print("🛠️  前5个工具:")
                for i, tool in enumerate(tools[:5]):
                    print(f"   {i+1}. {tool.get('name', 'unknown')}")
            else:
                print("⚠️  未获取到工具列表")
                return False
                
            # 测试基本导航
            print("\n📝 测试导航到百度...")
            result = client.call_tool('browser_navigate', {'url': 'https://www.baidu.com'})
            if result:
                print("✅ 导航成功")
                print(f"   结果: {str(result)[:100]}...")
            else:
                print("❌ 导航失败")
                return False
                
            # 等待页面加载
            print("⏳ 等待页面加载...")
            time.sleep(3)
            
            # 测试截图
            print("📸 测试截图...")
            screenshot_result = client.call_tool('browser_take_screenshot', {})
            if screenshot_result:
                print("✅ 截图成功")
                print(f"   结果类型: {type(screenshot_result)}")
            else:
                print("❌ 截图失败")
                
            # 测试快照
            print("📊 测试页面快照...")
            snapshot_result = client.call_tool('browser_snapshot', {})
            if snapshot_result:
                print("✅ 快照成功")
                print(f"   结果类型: {type(snapshot_result)}")
            else:
                print("❌ 快照失败")
                
            print("\n🎉 所有测试完成！")
            return True
            
        else:
            print("❌ 初始化失败")
            return False
            
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        client.close()

if __name__ == "__main__":
    success = test_simple_connection()
    if success:
        print("✅ 测试成功！")
        sys.exit(0)
    else:
        print("❌ 测试失败！")
        sys.exit(1) 