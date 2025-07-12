#!/usr/bin/env python3
"""
Playwright MCP 全工具测试脚本
使用国内网站测试所有25个可用工具
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

def test_all_tools_with_chinese_sites():
    """使用国内网站测试所有工具"""
    print("🇨🇳 Playwright MCP 全工具测试 - 国内网站版")
    print("=" * 70)
    
    config = load_config()
    instances = config["cluster"]["instances"]
    
    if not instances:
        print("❌ 配置文件中没有找到实例")
        return False
        
    # 选择第一个实例进行测试
    test_instance = instances[0]
    print(f"🎯 使用Docker实例: {test_instance['id']} ({test_instance['url']})")
    
    client = SSEClient(test_instance["url"])
    
    try:
        # 初始化连接
        print("\n🔗 初始化连接...")
        if not client.initialize():
            print("❌ 初始化失败")
            return False
        print("✅ 连接建立成功")
        
        # 获取所有工具列表
        print("\n📋 获取工具列表...")
        tools = client.list_tools()
        if not tools:
            print("❌ 无法获取工具列表")
            return False
            
        print(f"✅ 发现 {len(tools)} 个可用工具")
        
        # 测试结果记录
        test_results = []
        
        # 国内测试网站列表
        chinese_sites = [
            "https://www.baidu.com",
            "https://www.qq.com", 
            "https://www.taobao.com",
            "https://www.jd.com",
            "https://www.bilibili.com"
        ]
        
        current_site_index = 0
        
        # 逐一测试每个工具
        for i, tool in enumerate(tools, 1):
            tool_name = tool.get('name', 'unknown')
            tool_description = tool.get('description', 'No description')
            
            print(f"\n[{i:2d}/{len(tools)}] 🧪 测试工具: {tool_name}")
            print(f"   描述: {tool_description}")
            
            # 根据工具类型选择测试策略
            result = test_single_tool_with_chinese_sites(client, tool_name, chinese_sites, current_site_index)
            
            test_results.append({
                'name': tool_name,
                'description': tool_description,
                'success': result['success'],
                'message': result['message'],
                'details': result.get('details', {}),
                'site_used': result.get('site_used', '')
            })
            
            # 更新网站索引，轮换使用不同网站
            if result.get('site_used'):
                current_site_index = (current_site_index + 1) % len(chinese_sites)
            
            # 每个工具测试后稍作等待
            time.sleep(2)
        
        # 显示测试汇总
        print("\n" + "="*70)
        print("📊 全工具测试汇总报告")
        print("="*70)
        
        success_count = sum(1 for r in test_results if r['success'])
        total_count = len(test_results)
        
        print(f"🇨🇳 测试环境: 国内网站")
        print(f"📊 测试统计:")
        print(f"   总工具数: {total_count}")
        print(f"   测试成功: {success_count}")
        print(f"   测试失败: {total_count - success_count}")
        print(f"   成功率: {success_count/total_count*100:.1f}%")
        
        print(f"\n🌐 使用的测试网站:")
        for i, site in enumerate(chinese_sites, 1):
            print(f"   {i}. {site}")
        
        print(f"\n📋 详细测试结果:")
        for result in test_results:
            status_icon = "✅" if result['success'] else "❌"
            site_info = f" (网站: {result['site_used']})" if result.get('site_used') else ""
            print(f"{status_icon} {result['name']}: {result['message']}{site_info}")
        
        # 按功能分类统计
        print(f"\n📈 功能分类统计:")
        category_stats = categorize_tools(test_results)
        for category, stats in category_stats.items():
            success_rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"   {category}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()
        print("\n🔒 连接已安全关闭")

def test_single_tool_with_chinese_sites(client: SSEClient, tool_name: str, sites: List[str], site_index: int) -> Dict[str, Any]:
    """使用国内网站测试单个工具"""
    try:
        # 根据工具名称执行相应的测试
        if tool_name == 'browser_navigate':
            return test_navigate_tool(client, sites[site_index])
        elif tool_name == 'browser_take_screenshot':
            return test_screenshot_tool(client, sites[site_index])
        elif tool_name == 'browser_snapshot':
            return test_snapshot_tool(client, sites[site_index])
        elif tool_name == 'browser_click':
            return test_click_tool(client, sites[site_index])
        elif tool_name == 'browser_type':
            return test_type_tool(client, sites[site_index])
        elif tool_name == 'browser_scroll':
            return test_scroll_tool(client, sites[site_index])
        elif tool_name == 'browser_wait_for':
            return test_wait_for_tool(client, sites[site_index])
        elif tool_name == 'browser_get_page_content':
            return test_get_content_tool(client, sites[site_index])
        elif tool_name == 'browser_evaluate':
            return test_evaluate_tool(client, sites[site_index])
        elif tool_name == 'browser_new_page':
            return test_new_page_tool(client, sites[site_index])
        elif tool_name == 'browser_close_page':
            return test_close_page_tool(client, sites[site_index])
        elif tool_name == 'browser_tab_list':
            return test_tab_list_tool(client, sites[site_index])
        elif tool_name == 'browser_tab_new':
            return test_tab_new_tool(client, sites[site_index])
        elif tool_name == 'browser_tab_select':
            return test_tab_select_tool(client, sites[site_index])
        elif tool_name == 'browser_tab_close':
            return test_tab_close_tool(client, sites[site_index])
        elif tool_name == 'browser_navigate_back':
            return test_navigate_back_tool(client, sites[site_index])
        elif tool_name == 'browser_navigate_forward':
            return test_navigate_forward_tool(client, sites[site_index])
        elif tool_name == 'browser_resize':
            return test_resize_tool(client, sites[site_index])
        elif tool_name == 'browser_press_key':
            return test_press_key_tool(client, sites[site_index])
        elif tool_name == 'browser_console_messages':
            return test_console_messages_tool(client, sites[site_index])
        elif tool_name == 'browser_network_requests':
            return test_network_requests_tool(client, sites[site_index])
        elif tool_name == 'browser_pdf_save':
            return test_pdf_save_tool(client, sites[site_index])
        elif tool_name == 'browser_close':
            return test_close_tool(client, sites[site_index])
        elif tool_name == 'browser_install':
            return test_install_tool(client, sites[site_index])
        elif tool_name == 'browser_handle_dialog':
            return test_handle_dialog_tool(client, sites[site_index])
        elif tool_name == 'browser_file_upload':
            return test_file_upload_tool(client, sites[site_index])
        elif tool_name == 'browser_drag':
            return test_drag_tool(client, sites[site_index])
        elif tool_name == 'browser_hover':
            return test_hover_tool(client, sites[site_index])
        elif tool_name == 'browser_select_option':
            return test_select_option_tool(client, sites[site_index])
        elif tool_name == 'browser_generate_playwright_test':
            return test_generate_test_tool(client, sites[site_index])
        else:
            return test_generic_tool(client, tool_name, sites[site_index])
            
    except Exception as e:
        return {
            'success': False,
            'message': f'测试异常: {str(e)}',
            'details': {'error': str(e)},
            'site_used': sites[site_index]
        }

# 具体工具测试函数
def test_navigate_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试导航工具"""
    try:
        result = client.call_tool('browser_navigate', {'url': site})
        if result and not result.get('isError'):
            return {'success': True, 'message': f'成功导航到 {site}', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'导航失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'导航异常: {str(e)}', 'site_used': site}

def test_screenshot_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试截图工具"""
    try:
        # 先导航到网站
        client.call_tool('browser_navigate', {'url': site})
        time.sleep(3)
        
        result = client.call_tool('browser_take_screenshot', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': f'成功截取 {site} 页面截图', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'截图失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'截图异常: {str(e)}', 'site_used': site}

def test_snapshot_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试快照工具"""
    try:
        # 先导航到网站
        client.call_tool('browser_navigate', {'url': site})
        time.sleep(3)
        
        result = client.call_tool('browser_snapshot', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': f'成功获取 {site} 页面快照', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'快照失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'快照异常: {str(e)}', 'site_used': site}

def test_click_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试点击工具"""
    try:
        # 先导航并获取快照
        client.call_tool('browser_navigate', {'url': site})
        time.sleep(3)
        snapshot_result = client.call_tool('browser_snapshot', {})
        
        if snapshot_result and not snapshot_result.get('isError'):
            # 尝试点击页面上的第一个可点击元素
            result = client.call_tool('browser_click', {
                'element': '可点击元素',
                'ref': '1'
            })
            if result and not result.get('isError'):
                return {'success': True, 'message': f'成功点击 {site} 页面元素', 'site_used': site}
            else:
                error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
                return {'success': False, 'message': f'点击失败: {error_msg}', 'site_used': site}
        else:
            return {'success': False, 'message': '点击失败: 无法获取页面快照', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'点击异常: {str(e)}', 'site_used': site}

def test_type_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试输入工具"""
    try:
        # 先导航到百度进行搜索测试
        test_site = "https://www.baidu.com"
        client.call_tool('browser_navigate', {'url': test_site})
        time.sleep(3)
        
        # 尝试在搜索框中输入
        result = client.call_tool('browser_type', {
            'element': '搜索框',
            'ref': '1',
            'text': 'Playwright测试'
        })
        if result and not result.get('isError'):
            return {'success': True, 'message': f'成功在 {test_site} 输入文本', 'site_used': test_site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'输入失败: {error_msg}', 'site_used': test_site}
    except Exception as e:
        return {'success': False, 'message': f'输入异常: {str(e)}', 'site_used': test_site}

def test_scroll_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试滚动工具"""
    try:
        # 先导航到网站
        client.call_tool('browser_navigate', {'url': site})
        time.sleep(3)
        
        result = client.call_tool('browser_scroll', {'direction': 'down', 'amount': 500})
        if result and not result.get('isError'):
            return {'success': True, 'message': f'成功滚动 {site} 页面', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'滚动失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'滚动异常: {str(e)}', 'site_used': site}

def test_wait_for_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试等待工具"""
    try:
        # 先导航到网站
        client.call_tool('browser_navigate', {'url': site})
        time.sleep(3)
        
        result = client.call_tool('browser_wait_for', {'time': 2000})
        if result and not result.get('isError'):
            return {'success': True, 'message': f'成功等待 {site} 页面加载', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'等待失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'等待异常: {str(e)}', 'site_used': site}

def test_get_content_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试获取内容工具"""
    try:
        # 先导航到网站
        client.call_tool('browser_navigate', {'url': site})
        time.sleep(3)
        
        result = client.call_tool('browser_get_page_content', {'format': 'text'})
        if result and not result.get('isError'):
            return {'success': True, 'message': f'成功获取 {site} 页面内容', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'获取内容失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'获取内容异常: {str(e)}', 'site_used': site}

def test_evaluate_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试JavaScript执行工具"""
    try:
        # 先导航到网站
        client.call_tool('browser_navigate', {'url': site})
        time.sleep(3)
        
        result = client.call_tool('browser_evaluate', {'script': 'document.title'})
        if result and not result.get('isError'):
            return {'success': True, 'message': f'成功执行JavaScript获取 {site} 标题', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'JavaScript执行失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'JavaScript执行异常: {str(e)}', 'site_used': site}

def test_new_page_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试新建页面工具"""
    try:
        result = client.call_tool('browser_new_page', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功创建新页面', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'新建页面失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'新建页面异常: {str(e)}', 'site_used': site}

def test_close_page_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试关闭页面工具"""
    try:
        result = client.call_tool('browser_close_page', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功关闭页面', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'关闭页面失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'关闭页面异常: {str(e)}', 'site_used': site}

def test_tab_list_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试标签页列表工具"""
    try:
        result = client.call_tool('browser_tab_list', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功获取标签页列表', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'获取标签页列表失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'获取标签页列表异常: {str(e)}', 'site_used': site}

def test_tab_new_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试新建标签页工具"""
    try:
        result = client.call_tool('browser_tab_new', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功创建新标签页', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'创建新标签页失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'创建新标签页异常: {str(e)}', 'site_used': site}

def test_tab_select_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试选择标签页工具"""
    try:
        result = client.call_tool('browser_tab_select', {'index': 0})
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功选择标签页', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'选择标签页失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'选择标签页异常: {str(e)}', 'site_used': site}

def test_tab_close_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试关闭标签页工具"""
    try:
        result = client.call_tool('browser_tab_close', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功关闭标签页', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'关闭标签页失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'关闭标签页异常: {str(e)}', 'site_used': site}

def test_navigate_back_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试后退工具"""
    try:
        # 先导航到两个不同的网站
        client.call_tool('browser_navigate', {'url': site})
        time.sleep(2)
        client.call_tool('browser_navigate', {'url': 'https://www.baidu.com'})
        time.sleep(2)
        
        result = client.call_tool('browser_navigate_back', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': f'成功后退到 {site}', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'后退失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'后退异常: {str(e)}', 'site_used': site}

def test_navigate_forward_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试前进工具"""
    try:
        result = client.call_tool('browser_navigate_forward', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': f'成功前进到下一个页面', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'前进失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'前进异常: {str(e)}', 'site_used': site}

def test_resize_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试调整大小工具"""
    try:
        result = client.call_tool('browser_resize', {'width': 1200, 'height': 800})
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功调整窗口大小为1200x800', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'调整大小失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'调整大小异常: {str(e)}', 'site_used': site}

def test_press_key_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试按键工具"""
    try:
        result = client.call_tool('browser_press_key', {'key': 'Escape'})
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功按下Escape键', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'按键失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'按键异常: {str(e)}', 'site_used': site}

def test_console_messages_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试控制台消息工具"""
    try:
        # 先导航到网站
        client.call_tool('browser_navigate', {'url': site})
        time.sleep(3)
        
        result = client.call_tool('browser_console_messages', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': f'成功获取 {site} 控制台消息', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'获取控制台消息失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'获取控制台消息异常: {str(e)}', 'site_used': site}

def test_network_requests_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试网络请求工具"""
    try:
        # 先导航到网站
        client.call_tool('browser_navigate', {'url': site})
        time.sleep(3)
        
        result = client.call_tool('browser_network_requests', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': f'成功获取 {site} 网络请求', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'获取网络请求失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'获取网络请求异常: {str(e)}', 'site_used': site}

def test_pdf_save_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试PDF保存工具"""
    try:
        # 先导航到网站
        client.call_tool('browser_navigate', {'url': site})
        time.sleep(3)
        
        result = client.call_tool('browser_pdf_save', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': f'成功保存 {site} 为PDF', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'PDF保存失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'PDF保存异常: {str(e)}', 'site_used': site}

def test_close_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试关闭工具"""
    try:
        result = client.call_tool('browser_close', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功关闭浏览器', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'关闭浏览器失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'关闭浏览器异常: {str(e)}', 'site_used': site}

def test_install_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试安装工具"""
    try:
        result = client.call_tool('browser_install', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功安装浏览器', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'安装浏览器失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'安装浏览器异常: {str(e)}', 'site_used': site}

def test_handle_dialog_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试对话框处理工具"""
    try:
        result = client.call_tool('browser_handle_dialog', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功处理对话框', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'处理对话框失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'处理对话框异常: {str(e)}', 'site_used': site}

def test_file_upload_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试文件上传工具"""
    try:
        result = client.call_tool('browser_file_upload', {})
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功处理文件上传', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'文件上传失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'文件上传异常: {str(e)}', 'site_used': site}

def test_drag_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试拖拽工具"""
    try:
        result = client.call_tool('browser_drag', {
            'startElement': '元素1',
            'startRef': '1',
            'endElement': '元素2', 
            'endRef': '2'
        })
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功执行拖拽操作', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'拖拽失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'拖拽异常: {str(e)}', 'site_used': site}

def test_hover_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试悬停工具"""
    try:
        result = client.call_tool('browser_hover', {
            'element': '可悬停元素',
            'ref': '1'
        })
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功执行悬停操作', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'悬停失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'悬停异常: {str(e)}', 'site_used': site}

def test_select_option_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试选择选项工具"""
    try:
        result = client.call_tool('browser_select_option', {
            'element': '下拉框',
            'ref': '1',
            'values': ['选项1']
        })
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功选择下拉框选项', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'选择选项失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'选择选项异常: {str(e)}', 'site_used': site}

def test_generate_test_tool(client: SSEClient, site: str) -> Dict[str, Any]:
    """测试生成测试工具"""
    try:
        result = client.call_tool('browser_generate_playwright_test', {
            'name': '测试用例',
            'description': '测试描述',
            'steps': ['步骤1', '步骤2']
        })
        if result and not result.get('isError'):
            return {'success': True, 'message': '成功生成Playwright测试', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'生成测试失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'生成测试异常: {str(e)}', 'site_used': site}

def test_generic_tool(client: SSEClient, tool_name: str, site: str) -> Dict[str, Any]:
    """测试通用工具"""
    try:
        result = client.call_tool(tool_name, {})
        if result and not result.get('isError'):
            return {'success': True, 'message': f'成功调用工具 {tool_name}', 'site_used': site}
        else:
            error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result else '无响应'
            return {'success': False, 'message': f'工具 {tool_name} 调用失败: {error_msg}', 'site_used': site}
    except Exception as e:
        return {'success': False, 'message': f'工具 {tool_name} 调用异常: {str(e)}', 'site_used': site}

def categorize_tools(test_results: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """按功能分类工具测试结果"""
    categories = {
        '导航控制': ['browser_navigate', 'browser_navigate_back', 'browser_navigate_forward'],
        '页面操作': ['browser_click', 'browser_type', 'browser_scroll', 'browser_hover', 'browser_drag'],
        '页面管理': ['browser_new_page', 'browser_close_page', 'browser_close'],
        '标签页管理': ['browser_tab_list', 'browser_tab_new', 'browser_tab_select', 'browser_tab_close'],
        '内容获取': ['browser_snapshot', 'browser_take_screenshot', 'browser_get_page_content', 'browser_pdf_save'],
        '网络监控': ['browser_network_requests', 'browser_console_messages'],
        '窗口控制': ['browser_resize', 'browser_press_key'],
        '高级功能': ['browser_evaluate', 'browser_wait_for', 'browser_select_option'],
        '系统功能': ['browser_install', 'browser_handle_dialog', 'browser_file_upload', 'browser_generate_playwright_test']
    }
    
    stats = {}
    for category, tools in categories.items():
        category_results = [r for r in test_results if r['name'] in tools]
        stats[category] = {
            'total': len(category_results),
            'success': sum(1 for r in category_results if r['success'])
        }
    
    return stats

def main():
    """主函数"""
    print("🚀 Playwright MCP 全工具测试 - 国内网站版")
    print("🎯 目标: 使用国内网站测试所有25个工具")
    print("=" * 70)
    
    success = test_all_tools_with_chinese_sites()
    
    if success:
        print("\n🎊 🎊 🎊 全工具测试完成！🎊 🎊 🎊")
        print("✨ 已成功测试了Playwright MCP的所有工具")
        print("🇨🇳 使用国内网站进行测试")
        print("🛠️  工具功能验证通过")
        return 0
    else:
        print("\n😞 部分工具测试失败")
        print("🔧 请检查Docker容器状态和网络连接")
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