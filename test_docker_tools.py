#!/usr/bin/env python3
"""
Docker版本的Playwright MCP 工具测试脚本
选择一个Docker实例测试所有可用的工具功能
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

def test_docker_instance_tools():
    """测试Docker实例的所有工具"""
    print("🛠️  开始测试Docker实例的所有Playwright MCP工具")
    print("=" * 60)
    
    config = load_config()
    instances = config["cluster"]["instances"]
    
    if not instances:
        print("❌ 配置文件中没有找到实例")
        return False
        
    # 选择第一个实例进行测试
    test_instance = instances[0]
    print(f"🎯 选择Docker实例: {test_instance['id']} ({test_instance['url']})")
    
    # 等待Docker实例完全启动
    print("⏳ 等待Docker实例完全启动...")
    time.sleep(10)
    
    client = SSEClient(test_instance["url"])
    
    try:
        # 初始化连接
        print("\n🔗 初始化连接...")
        if not client.initialize():
            print("❌ 初始化失败")
            return False
        print("✅ 连接初始化成功")
        
        # 获取所有工具列表
        print("\n📋 获取工具列表...")
        tools = client.list_tools()
        if not tools:
            print("❌ 无法获取工具列表")
            return False
            
        print(f"✅ 发现 {len(tools)} 个可用工具:")
        for i, tool in enumerate(tools, 1):
            name = tool.get('name', 'unknown')
            description = tool.get('description', 'No description')
            print(f"   {i:2d}. {name}")
            print(f"       {description[:80]}{'...' if len(description) > 80 else ''}")
        
        # 测试关键工具
        print(f"\n🧪 开始测试关键工具...")
        test_results = []
        
        # 重点测试的工具列表
        key_tools = [
            'browser_navigate',
            'browser_take_screenshot', 
            'browser_snapshot',
            'browser_click',
            'browser_type',
            'browser_tab_new',
            'browser_tab_list'
        ]
        
        for tool_name in key_tools:
            tool = next((t for t in tools if t.get('name') == tool_name), None)
            if tool:
                print(f"\n测试工具: {tool_name}")
                result = test_key_tool(client, tool_name)
                test_results.append({
                    'name': tool_name,
                    'success': result['success'],
                    'message': result['message'],
                    'details': result.get('details', {})
                })
                time.sleep(2)  # 等待更长时间
            else:
                print(f"\n⚠️  工具 {tool_name} 不可用")
        
        # 显示测试汇总
        print("\n" + "="*60)
        print("📊 Docker实例工具测试汇总报告")
        print("="*60)
        
        success_count = sum(1 for r in test_results if r['success'])
        total_count = len(test_results)
        
        print(f"测试工具数: {total_count}")
        print(f"测试成功: {success_count}")
        print(f"测试失败: {total_count - success_count}")
        print(f"成功率: {success_count/total_count*100:.1f}%" if total_count > 0 else "0%")
        
        print("\n📋 详细结果:")
        for result in test_results:
            status_icon = "✅" if result['success'] else "❌"
            print(f"{status_icon} {result['name']}: {result['message']}")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

def test_key_tool(client: SSEClient, tool_name: str) -> Dict[str, Any]:
    """测试关键工具"""
    try:
        if tool_name == 'browser_navigate':
            return test_navigate_with_params(client)
        elif tool_name == 'browser_take_screenshot':
            return test_screenshot_simple(client)
        elif tool_name == 'browser_snapshot':
            return test_snapshot_simple(client)
        elif tool_name == 'browser_click':
            return test_click_with_params(client)
        elif tool_name == 'browser_type':
            return test_type_with_params(client)
        elif tool_name == 'browser_tab_new':
            return test_new_tab(client)
        elif tool_name == 'browser_tab_list':
            return test_tab_list(client)
        else:
            return test_generic_with_error_handling(client, tool_name)
            
    except Exception as e:
        return {
            'success': False,
            'message': f'测试异常: {str(e)}',
            'details': {'error': str(e)}
        }

def test_navigate_with_params(client: SSEClient) -> Dict[str, Any]:
    """测试导航工具（带参数）"""
    try:
        result = client.call_tool('browser_navigate', {'url': 'https://www.baidu.com'})
        if result and not result.get('isError'):
            return {'success': True, 'message': '导航成功', 'details': result}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'导航失败: {error_msg}'}
    except Exception as e:
        return {'success': False, 'message': f'导航异常: {str(e)}'}

def test_screenshot_simple(client: SSEClient) -> Dict[str, Any]:
    """测试截图工具"""
    try:
        # 先导航到页面
        client.call_tool('browser_navigate', {'url': 'https://www.baidu.com'})
        time.sleep(3)
        
        result = client.call_tool('browser_take_screenshot', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': '截图成功', 'details': result}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'截图失败: {error_msg}'}
    except Exception as e:
        return {'success': False, 'message': f'截图异常: {str(e)}'}

def test_snapshot_simple(client: SSEClient) -> Dict[str, Any]:
    """测试快照工具"""
    try:
        result = client.call_tool('browser_snapshot', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': '快照成功', 'details': result}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'快照失败: {error_msg}'}
    except Exception as e:
        return {'success': False, 'message': f'快照异常: {str(e)}'}

def test_click_with_params(client: SSEClient) -> Dict[str, Any]:
    """测试点击工具（带参数）"""
    try:
        # 先导航并获取快照
        client.call_tool('browser_navigate', {'url': 'https://www.baidu.com'})
        time.sleep(3)
        snapshot_result = client.call_tool('browser_snapshot', {})
        
        if snapshot_result and not snapshot_result.get('isError'):
            # 使用快照中的元素引用
            result = client.call_tool('browser_click', {
                'element': '搜索框',
                'ref': '1'  # 假设的引用ID
            })
            if result and not result.get('isError'):
                return {'success': True, 'message': '点击成功', 'details': result}
            else:
                error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
                return {'success': False, 'message': f'点击失败: {error_msg}'}
        else:
            return {'success': False, 'message': '点击失败: 无法获取页面快照'}
    except Exception as e:
        return {'success': False, 'message': f'点击异常: {str(e)}'}

def test_type_with_params(client: SSEClient) -> Dict[str, Any]:
    """测试输入工具（带参数）"""
    try:
        result = client.call_tool('browser_type', {
            'element': '搜索框',
            'ref': '1',
            'text': 'Playwright测试'
        })
        if result and not result.get('isError'):
            return {'success': True, 'message': '输入成功', 'details': result}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'输入失败: {error_msg}'}
    except Exception as e:
        return {'success': False, 'message': f'输入异常: {str(e)}'}

def test_new_tab(client: SSEClient) -> Dict[str, Any]:
    """测试新建标签页"""
    try:
        result = client.call_tool('browser_tab_new', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': '新建标签页成功', 'details': result}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'新建标签页失败: {error_msg}'}
    except Exception as e:
        return {'success': False, 'message': f'新建标签页异常: {str(e)}'}

def test_tab_list(client: SSEClient) -> Dict[str, Any]:
    """测试标签页列表"""
    try:
        result = client.call_tool('browser_tab_list', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': '获取标签页列表成功', 'details': result}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'获取标签页列表失败: {error_msg}'}
    except Exception as e:
        return {'success': False, 'message': f'获取标签页列表异常: {str(e)}'}

def test_generic_with_error_handling(client: SSEClient, tool_name: str) -> Dict[str, Any]:
    """测试通用工具（带错误处理）"""
    try:
        result = client.call_tool(tool_name, {})
        if result and not result.get('isError'):
            return {'success': True, 'message': '工具调用成功', 'details': result}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'工具调用失败: {error_msg}'}
    except Exception as e:
        return {'success': False, 'message': f'工具调用异常: {str(e)}'}

def main():
    """主函数"""
    print("🚀 Docker版Playwright MCP 工具测试")
    print(f"选择第一个Docker实例进行关键工具测试")
    
    success = test_docker_instance_tools()
    
    if success:
        print("\n🎉 Docker实例工具测试完成！至少有部分工具正常工作。")
        return 0
    else:
        print("\n😞 Docker实例工具测试失败，请检查容器状态。")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生未处理的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 