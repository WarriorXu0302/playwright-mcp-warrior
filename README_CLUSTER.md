# Playwright MCP 集群管理详细文档

## 🎯 概述

本文档详细介绍 Playwright MCP 集群版的高级功能，包括集群管理、隔离模式、Docker部署和完整的测试套件。

## 🏗️ 架构设计

### 集群架构图
```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Client (LLM)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
      ┌───────────────┼───────────────┐
      │               │               │
┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
│ Instance 1│   │ Instance 2│   │ Instance 3│
│Port: 9001 │   │Port: 9002 │   │Port: 9003 │
│Profile: A │   │Profile: B │   │Profile: C │
└───────────┘   └───────────┘   └───────────┘
```

### 隔离模式原理
每个实例运行在独立的浏览器配置文件中：
- **本地模式**: 每个实例使用不同的 `USER_DATA_DIR`
- **Docker模式**: 每个容器使用独立的环境变量
- **内存隔离**: 会话数据完全分离，无相互干扰

## 📋 管理脚本详解

### start.sh - 集群启动脚本

#### 功能特性
- **智能模式检测**: 自动选择本地或Docker部署模式
- **隔离模式**: 默认启用，避免实例间配置冲突
- **端口管理**: 自动检测和释放占用端口
- **健康检查**: 多层验证确保实例正常启动
- **详细日志**: 完整的启动过程记录和错误诊断

#### 使用示例
```bash
# 基础启动（本地模式，隔离启用）
./start.sh

# Docker模式启动
./start.sh --docker

# 自定义配置文件
./start.sh --config my_cluster.json

# 禁用隔离模式（不推荐）
./start.sh --no-isolated

# 查看帮助
./start.sh --help
```

#### 启动流程
1. **参数解析** → 处理命令行选项
2. **配置验证** → 检查配置文件有效性
3. **环境准备** → 创建必要目录，清理旧进程
4. **实例启动** → 根据配置逐一启动实例
5. **健康检查** → 验证所有实例运行状态
6. **结果报告** → 输出启动统计和访问信息

### stop.sh - 智能停止脚本 🆕

#### 重大升级特性
- **🔍 混合环境检测**: 自动识别本地和Docker实例
- **🎯 选择性停止**: 支持按类型停止特定实例
- **🧹 智能清理**: 彻底清理隔离模式产生的资源
- **💪 强制模式**: 应急情况下的完全清理
- **📊 状态验证**: 确保停止操作的完整性

#### 使用示例
```bash
# 智能停止所有实例（推荐）
./stop.sh

# 仅停止本地实例
./stop.sh --local

# 仅停止Docker实例
./stop.sh --docker

# 强制停止并清理所有资源
./stop.sh --force

# 查看帮助
./stop.sh --help
```

#### 停止机制
**本地实例停止**:
1. **PID文件停止** → 通过保存的进程ID优雅停止
2. **进程名称清理** → 清理残留的相关进程
3. **端口释放** → 强制释放占用的端口
4. **临时文件清理** → 删除隔离模式产生的临时文件

**Docker实例停止**:
1. **容器发现** → 自动识别所有MCP相关容器
2. **优雅停止** → 使用docker stop命令停止容器
3. **容器清理** → 自动清理停止的容器
4. **强制清理** → 强制模式下删除所有相关容器

#### 实际使用场景
```bash
# 场景1: 开发过程中快速重启
./stop.sh && ./start.sh

# 场景2: 只重启Docker实例
./stop.sh --docker && ./start.sh --docker

# 场景3: 应急情况完全清理
./stop.sh --force

# 场景4: 维护模式（保留日志）
./stop.sh --local

# 场景5: 检查运行状态
./stop.sh  # 会显示当前运行的实例数量
```

## 🔧 配置文件详解

### cluster_config.json 完整配置

```json
{
  "cluster": {
    "instances": [
      {
        "id": "mcp-1",                    // 实例唯一标识
        "port": 9001,                     // 监听端口
        "url": "http://localhost:9001/sse" // 访问URL
      },
      {
        "id": "mcp-2",
        "port": 9002,
        "url": "http://localhost:9002/sse"
      },
      {
        "id": "mcp-3",
        "port": 9003,
        "url": "http://localhost:9003/sse"
      },
      {
        "id": "mcp-4",
        "port": 9004,
        "url": "http://localhost:9004/sse"
      },
      {
        "id": "mcp-5",
        "port": 9005,
        "url": "http://localhost:9005/sse"
      }
    ],
    "max_concurrent_per_instance": 1,    // 每实例最大并发数
    "health_check_interval": 10,         // 健康检查间隔(秒)  
    "max_retries": 3                     // 最大重试次数
  },
  "browser": {
    "headless": true,                    // 无头模式
    "timeout": 30000,                    // 超时时间(毫秒)
    "viewport": {                        // 视窗大小
      "width": 1280,
      "height": 720
    }
  },
  "network": {
    "timeout": 30,                       // 网络超时
    "retry_attempts": 3,                 // 重试次数
    "retry_delay": 1                     // 重试延迟(秒)
  },
  "logging": {
    "level": "INFO",                     // 日志级别
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

### docker_cluster_config.json 配置

```json
{
  "cluster": {
    "instances": [
      {
        "id": "docker-mcp-1",
        "port": 9001,
        "url": "http://localhost:9001/mcp"  // Docker使用/mcp端点
      },
      {
        "id": "docker-mcp-2", 
        "port": 9002,
        "url": "http://localhost:9002/mcp"
      },
      {
        "id": "docker-mcp-3",
        "port": 9003,
        "url": "http://localhost:9003/mcp"
      },
      {
        "id": "docker-mcp-4",
        "port": 9004,
        "url": "http://localhost:9004/mcp"
      },
      {
        "id": "docker-mcp-5",
        "port": 9005,
        "url": "http://localhost:9005/mcp"
      }
    ],
    "max_concurrent_per_instance": 1,
    "health_check_interval": 10,
    "max_retries": 3
  }
}
```

## 🔒 隔离模式深入解析

### 隔离模式的优势
1. **并发安全**: 避免多实例间的资源竞争
2. **数据隔离**: 每个实例的会话数据完全独立
3. **故障隔离**: 单个实例崩溃不影响其他实例
4. **配置分离**: 浏览器设置和插件不会冲突

### 隔离实现机制

#### 本地模式隔离
```bash
# 每个实例使用独立的环境变量
export PLAYWRIGHT_BROWSERS_PATH="/home/user/.cache/ms-playwright-1"
export USER_DATA_DIR="/tmp/playwright-profile-1"

# 启动命令包含隔离参数
npx @playwright/mcp@latest --port 9001 --isolated
```

#### Docker模式隔离
```bash
# 每个容器使用独立的环境变量和挂载目录
docker run -d \
  --name mcp-instance-1 \
  -p 9001:9000 \
  -e USER_DATA_DIR="/tmp/playwright-1" \
  -e BROWSER_PROFILE_DIR="/tmp/browser-profile-1" \
  playwright-mcp --port 9000 --isolated
```

## 🧪 测试套件详解

### 1. test_all_tools_chinese.py - 全工具测试

**功能**: 使用国内网站测试所有25个工具
**特色**: 
- 支持5个主流国内网站轮换测试
- 按功能分类统计成功率
- 详细的错误报告和调试信息

**测试网站**:
- 百度 (https://www.baidu.com) - 搜索引擎
- 腾讯 (https://www.qq.com) - 门户网站
- 淘宝 (https://www.taobao.com) - 电商平台
- 京东 (https://www.jd.com) - 电商平台
- 哔哩哔哩 (https://www.bilibili.com) - 视频网站

**测试分类**:
```
导航控制: browser_navigate, browser_navigate_back, browser_navigate_forward
页面操作: browser_click, browser_type, browser_scroll, browser_hover, browser_drag
页面管理: browser_new_page, browser_close_page, browser_close
标签页管理: browser_tab_list, browser_tab_new, browser_tab_select, browser_tab_close
内容获取: browser_snapshot, browser_take_screenshot, browser_get_page_content, browser_pdf_save
网络监控: browser_network_requests, browser_console_messages
窗口控制: browser_resize, browser_press_key
高级功能: browser_evaluate, browser_wait_for, browser_select_option
系统功能: browser_install, browser_handle_dialog, browser_file_upload, browser_generate_playwright_test
```

### 2. test_cluster_management.py - 集群管理测试

**功能**: 测试集群的管理和调度功能
**包含**:
- 连接测试和工具发现
- 集群健康检查
- 任务调度和负载均衡
- 实例故障恢复

### 3. test_docker_tools.py - Docker工具测试

**功能**: 专门测试Docker环境下的工具功能
**特色**:
- Docker容器健康检查
- 隔离模式验证
- 网络连接测试

### 4. test_stress.py - 压力测试

**功能**: 测试集群在高负载下的性能表现
**测试项**:
- 并发任务处理能力
- 资源使用情况监控
- 故障恢复时间测试

## 🎭 演示脚本说明

### demo_complete.py - 完整功能演示

展示所有主要功能的完整工作流程：

1. **连接初始化**: 建立与集群的连接
2. **工具发现**: 获取所有可用工具列表
3. **网页导航**: 访问多个网站
4. **页面操作**: 截图、快照、内容获取
5. **标签页管理**: 创建、切换、关闭标签页
6. **网络监控**: 获取请求和控制台信息
7. **窗口控制**: 调整大小、导航历史
8. **资源清理**: 安全关闭连接

### demo_simple.py - 简单演示

基础功能快速演示，适合入门用户。

## 🐳 Docker集成

### Dockerfile 解析

```dockerfile
# 多阶段构建，优化镜像大小
FROM node:22-bookworm-slim AS base

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    curl wget ca-certificates

# 安装Playwright浏览器
FROM base AS browser
RUN npx -y playwright-core install chromium && \
    npx -y playwright-core install chrome

# 生产镜像
FROM base
# 复制浏览器文件和应用代码
COPY --from=browser ${PLAYWRIGHT_BROWSERS_PATH} ${PLAYWRIGHT_BROWSERS_PATH}
COPY --from=builder /app/lib /app/lib

# 支持隔离模式启动
ENTRYPOINT ["node", "cli.js", "--headless", "--browser", "chromium", "--isolated"]
```

### Docker集群启动过程

1. **镜像构建**: 创建包含所有依赖的Docker镜像
2. **容器启动**: 为每个实例启动独立容器
3. **网络配置**: 映射端口到主机
4. **环境隔离**: 设置独立的环境变量
5. **健康检查**: 验证容器运行状态

## 📊 监控和日志

### 日志系统
```
logs/
├── mcp-mcp-1.log      # 实例1日志
├── mcp-mcp-2.log      # 实例2日志
├── mcp-mcp-3.log      # 实例3日志
├── mcp-mcp-4.log      # 实例4日志
└── mcp-mcp-5.log      # 实例5日志
```

### 监控指标
- **实例状态**: 健康、不健康、错误
- **任务统计**: 完成数、失败数、队列大小
- **性能指标**: 响应时间、资源使用率
- **错误追踪**: 详细的错误日志和堆栈跟踪

## 🚨 故障排除指南

### 常见问题及解决方案

#### 1. 端口冲突
```bash
# 检查端口占用
lsof -i :9001-9005

# 解决方案
./stop.sh  # 停止所有实例
```

#### 2. Docker权限问题
```bash
# 检查Docker状态
docker version
sudo systemctl status docker

# 解决方案
sudo systemctl start docker
sudo usermod -aG docker $USER
```

#### 3. 浏览器安装失败
```bash
# 检查浏览器安装
npx playwright install --dry-run

# 解决方案
npx playwright install chrome
```

#### 4. 内存不足
```bash
# 检查内存使用
free -h
docker stats

# 解决方案
# 1. 减少实例数量
# 2. 增加系统内存
# 3. 优化浏览器参数
```

### 调试模式

#### 启用详细日志
```bash
# 本地模式调试
DEBUG=1 ./start.sh

# Docker模式调试
docker logs -f mcp-instance-1
```

#### 性能分析
```bash
# 查看实例性能
python3 -c "
import psutil
for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
    if 'playwright' in proc.info['name'].lower():
        print(f'PID: {proc.info[\"pid\"]}, Memory: {proc.info[\"memory_percent\"]:.1f}%')
"
```

## 🔄 版本升级指南

### 从单实例迁移到集群

1. **备份现有配置**
```bash
cp ~/.cache/ms-playwright ~/.cache/ms-playwright.backup
```

2. **安装集群版本**
```bash
git clone <repository>
cd playwright-mcp
```

3. **配置集群**
```bash
# 编辑配置文件
vim cluster_config.json

# 启动集群
./start.sh
```

4. **验证迁移**
```bash
python3 test_cluster_management.py
```

### 升级检查清单
- [ ] 配置文件兼容性
- [ ] 端口可用性
- [ ] Docker环境准备
- [ ] 浏览器依赖安装
- [ ] 网络连接测试

## 📈 性能优化建议

### 1. 硬件配置
- **CPU**: 每个实例建议1核心，推荐4核心以上
- **内存**: 每个实例约500MB，推荐8GB以上
- **存储**: SSD推荐，至少10GB可用空间

### 2. 网络优化
- 使用稳定的网络连接
- 配置代理服务器（如需要）
- 调整超时参数

### 3. 浏览器优化
```bash
# 启动参数优化
--no-sandbox
--disable-dev-shm-usage
--disable-gpu
--disable-extensions
```

### 4. 集群调优
- 根据硬件资源调整实例数量
- 合理设置并发限制
- 优化健康检查间隔

## 🎯 最佳实践

### 1. 集群规划
- 根据业务需求确定实例数量
- 预留20%的资源余量
- 制定扩容和缩容策略

### 2. 监控告警
```bash
# 设置监控脚本
#!/bin/bash
UNHEALTHY=$(python3 -c "
from mcp_manager_sse import MCPManager
manager = MCPManager()
status = manager.get_status()
print(sum(1 for inst in status['instances'].values() if inst['status'] != 'healthy'))
")

if [ $UNHEALTHY -gt 0 ]; then
    echo "Warning: $UNHEALTHY instances unhealthy"
    # 发送告警通知
fi
```

### 3. 定期维护
- 每日检查日志文件大小
- 每周清理临时文件
- 每月更新浏览器版本

### 4. 安全考虑
- 限制网络访问范围
- 定期更新依赖版本
- 监控异常访问行为

## 📚 扩展开发

### 自定义工具开发
```python
def custom_tool(client: SSEClient, params: dict):
    """自定义工具示例"""
    try:
        result = client.call_tool('browser_evaluate', {
            'script': f'custom_function({params})'
        })
        return {'success': True, 'data': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

### 集群管理扩展
```python
class CustomMCPManager(MCPManager):
    """扩展的集群管理器"""
    
    def add_custom_monitoring(self):
        """添加自定义监控功能"""
        pass
    
    def implement_load_balancing(self):
        """实现负载均衡算法"""
        pass
```

## 🤝 贡献指南

### 开发环境设置
```bash
# 克隆项目
git clone <repository>
cd playwright-mcp

# 安装依赖
npm install
pip3 install -r python/requirements.txt

# 运行测试
python3 test_cluster_management.py
```

### 提交规范
- 功能开发：`feat: 添加新功能`
- 错误修复：`fix: 修复某个问题`
- 文档更新：`docs: 更新文档`
- 测试相关：`test: 添加测试用例`

---

**📞 如需更多帮助，请查看主文档或提交Issue！** 

## 🔄 工作流程优化

### 开发工作流
```bash
# 1. 启动开发环境
./start.sh --docker

# 2. 运行测试
python3 test_all_tools_chinese.py

# 3. 查看日志（如有问题）
tail -f logs/mcp-*.log

# 4. 停止并清理
./stop.sh --force
```

### 生产部署工作流
```bash
# 1. 构建生产镜像
docker build -t playwright-mcp:prod .

# 2. 启动生产集群
./start.sh --docker --config production_config.json

# 3. 验证集群状态
python3 test_cluster_management.py

# 4. 监控日志
tail -f logs/mcp-*.log
```

### 维护工作流
```bash
# 1. 检查当前状态
./stop.sh  # 仅显示状态，不停止

# 2. 选择性重启
./stop.sh --local && ./start.sh --config cluster_config.json

# 3. 完整系统重启
./stop.sh --force && ./start.sh --docker

# 4. 清理历史数据
./stop.sh --force  # 包含日志清理
```

### 故障排除工作流
```bash
# 1. 快速诊断
./stop.sh  # 查看当前实例状态
docker ps --filter name=mcp-instance  # 检查Docker容器
lsof -i :9001-9005  # 检查端口占用

# 2. 日志分析
tail -f logs/mcp-*.log  # 查看实时日志
docker logs mcp-instance-1  # 查看容器日志

# 3. 强制重置
./stop.sh --force  # 彻底清理
./start.sh --docker  # 重新启动

# 4. 验证修复
python3 test_all_tools_chinese.py  # 运行测试
``` 