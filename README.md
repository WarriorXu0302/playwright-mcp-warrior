# Playwright MCP 集群版

一个基于Model Context Protocol (MCP)的浏览器自动化服务器，使用[Playwright](https://playwright.dev)提供强大的Web自动化能力。此项目在原版基础上增加了**集群管理**、**隔离模式**和**完整的工具测试功能**。

## 🌟 核心特性

- **🚀 快速轻量**：基于Playwright的可访问性树，无需基于像素的输入
- **🤖 LLM友好**：无需视觉模型，纯结构化数据操作
- **🎯 确定性工具**：避免基于截图方法的模糊性
- **🐳 集群支持**：支持多实例并发，提高处理能力
- **🔒 隔离模式**：每个实例独立运行，避免配置冲突
- **🇨🇳 中文优化**：支持国内网站测试和中文界面
- **🛠️ 智能管理**：自动检测和管理本地/Docker混合环境

## 🛠️ 环境要求

- Node.js 18 或更新版本
- Docker (可选，用于容器化部署)
- Python 3.8+ (用于集群管理脚本)
- VS Code, Cursor, Windsurf, Claude Desktop, Goose 或其他MCP客户端

## 🚀 快速开始

### 单实例模式

```js
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest"
      ]
    }
  }
}
```

### 集群模式（推荐）

1. **本地集群启动**：
```bash
# 启动5个实例集群，默认启用隔离模式
./start.sh

# 指定配置文件
./start.sh --config cluster_config.json

# 禁用隔离模式
./start.sh --no-isolated
```

2. **Docker集群启动**：
```bash
# 构建Docker镜像
docker build -t playwright-mcp .

# 启动Docker集群（自动隔离模式）
./start.sh --docker
```

3. **集群管理**：
```bash
# 停止所有实例（智能检测）
./stop.sh

# 仅停止本地实例
./stop.sh --local

# 仅停止Docker实例
./stop.sh --docker

# 强制停止并清理所有资源
./stop.sh --force

# 查看日志
tail -f logs/mcp-*.log
```

## 🔧 集群配置

### 集群配置文件 (cluster_config.json)

```json
{
  "cluster": {
    "instances": [
      {
        "id": "mcp-1",
        "port": 9001,
        "url": "http://localhost:9001/sse"
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
    "max_concurrent_per_instance": 1,
    "health_check_interval": 10,
    "max_retries": 3
  },
  "browser": {
    "headless": true,
    "timeout": 30000,
    "viewport": {
      "width": 1280,
      "height": 720
    }
  }
}
```

### Docker集群配置 (docker_cluster_config.json)

```json
{
  "cluster": {
    "instances": [
      {
        "id": "docker-mcp-1",
        "port": 9001,
        "url": "http://localhost:9001/mcp"
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
    ]
  }
}
```

## 📋 管理脚本

### 启动脚本 (start.sh)

**功能**：智能启动集群，支持本地和Docker模式
```bash
./start.sh [选项]

选项:
  --config FILE       指定配置文件 (默认: cluster_config.json)
  --no-isolated       禁用隔离模式
  --docker           使用Docker模式启动
  --help             显示帮助信息
```

**特性**：
- ✅ 自动检测端口占用
- ✅ 隔离模式配置（默认启用）
- ✅ 健康检查和状态验证
- ✅ 详细的启动日志和错误处理

### 停止脚本 (stop.sh) - 🆕 全新升级

**功能**：智能停止集群，支持混合环境管理
```bash
./stop.sh [选项]

选项:
  --local         仅停止本地实例
  --docker        仅停止Docker实例
  --all           停止所有实例（默认）
  --force         强制停止并清理所有资源
  --help          显示帮助信息
```

**特性**：
- 🔍 **智能检测**：自动识别本地和Docker实例
- 🎯 **精确控制**：支持选择性停止
- 🧹 **彻底清理**：清理PID文件、临时文件、日志文件
- 💪 **强制模式**：应急情况下的彻底清理
- 📊 **状态验证**：确保停止操作完整性

## 🔒 隔离模式

隔离模式是本项目的重要特性，可以避免多实例间的浏览器配置冲突：

### 特性
- **独立配置文件**：每个实例使用单独的浏览器配置文件
- **内存隔离**：会话数据不会相互干扰
- **并发安全**：支持真正的并发操作
- **自动清理**：停止时自动清理隔离产生的临时文件

### 启用方式
```bash
# 本地模式（默认启用）
./start.sh

# Docker模式（自动启用）
./start.sh --docker

# 禁用隔离模式
./start.sh --no-isolated
```

## 🧪 测试套件

### 全工具测试（推荐）

使用国内网站测试所有25个工具：

```bash
# 测试所有工具（使用百度、腾讯、淘宝等国内网站）
python3 test_all_tools_chinese.py
```

**测试统计示例**：
```
🇨🇳 Playwright MCP 全工具测试 - 国内网站版
======================================================================
📊 测试统计:
   总工具数: 25
   测试成功: 16 (64.0%)
   测试失败: 9

📈 功能分类统计:
   导航控制: 3/3 (100.0%)
   页面管理: 1/1 (100.0%) 
   标签页管理: 3/4 (75.0%)
   内容获取: 3/3 (100.0%)
   网络监控: 2/2 (100.0%)
```

### 集群功能测试

```bash
# 集群管理测试
python3 test_cluster_management.py

# Docker工具测试
python3 test_docker_tools.py

# 压力测试
python3 test_stress.py
```

### 完整演示

```bash
# 完整功能演示
python3 demo_complete.py

# 简单演示
python3 demo_simple.py
```

## 🌐 支持的测试网站

项目针对国内网络环境优化，测试网站包括：
- 🔍 **百度** (https://www.baidu.com)
- 💬 **腾讯** (https://www.qq.com)
- 🛒 **淘宝** (https://www.taobao.com)
- 📦 **京东** (https://www.jd.com)
- 🎬 **哔哩哔哩** (https://www.bilibili.com)

## 🛠️ 工具列表

### 核心功能
- **browser_navigate** - 网页导航
- **browser_snapshot** - 页面可访问性快照  
- **browser_take_screenshot** - 页面截图
- **browser_click** - 元素点击
- **browser_type** - 文本输入

### 页面管理  
- **browser_new_page** - 新建页面
- **browser_close_page** - 关闭页面
- **browser_close** - 关闭浏览器

### 标签页管理
- **browser_tab_list** - 标签页列表
- **browser_tab_new** - 新建标签页
- **browser_tab_select** - 选择标签页
- **browser_tab_close** - 关闭标签页

### 导航控制
- **browser_navigate_back** - 后退
- **browser_navigate_forward** - 前进

### 内容获取
- **browser_get_page_content** - 获取页面内容
- **browser_pdf_save** - 保存PDF
- **browser_network_requests** - 网络请求
- **browser_console_messages** - 控制台消息

### 交互操作
- **browser_hover** - 鼠标悬停
- **browser_drag** - 拖拽操作
- **browser_scroll** - 页面滚动
- **browser_select_option** - 选择下拉框

### 高级功能
- **browser_evaluate** - JavaScript执行
- **browser_wait_for** - 等待操作
- **browser_resize** - 窗口调整
- **browser_press_key** - 按键操作
- **browser_generate_playwright_test** - 生成测试代码

## 📁 项目结构

```
playwright-mcp/
├── 🚀 启动脚本
│   ├── start.sh              # 集群启动脚本（支持隔离模式）
│   └── stop.sh               # 智能停止脚本（🆕 全新升级）
├── ⚙️ 配置文件
│   ├── cluster_config.json   # 本地集群配置
│   └── docker_cluster_config.json # Docker集群配置
├── 🧪 测试套件
│   ├── test_all_tools_chinese.py   # 全工具中文网站测试
│   ├── test_docker_tools.py        # Docker工具测试
│   ├── test_cluster_management.py  # 集群管理测试
│   └── test_stress.py              # 压力测试
├── 🎭 演示脚本
│   ├── demo_complete.py      # 完整功能演示
│   └── demo_simple.py        # 简单演示
├── 🐳 容器化
│   └── Dockerfile           # Docker镜像构建
└── 📚 文档
    ├── README.md            # 主要文档（本文件）
    └── README_CLUSTER.md    # 集群详细文档
```

## 🎯 使用场景

### 1. 自动化测试
```bash
# 并发测试多个网站
python3 test_stress.py
```

### 2. 数据采集
```bash
# 使用集群进行大规模数据采集
python3 demo_complete.py
```

### 3. 监控检查
```bash
# 网站健康检查
python3 test_cluster_management.py
```

### 4. 开发调试
```bash
# 启动单个实例进行调试
./start.sh --config cluster_config.json

# 完成后清理资源
./stop.sh --force
```

## 🚨 故障排除

### 常见问题

1. **端口冲突**
```bash
# 查看端口占用
lsof -i :9001-9005

# 停止占用进程
./stop.sh --force
```

2. **Docker权限问题**
```bash
# 确保Docker正在运行
docker version

# 检查镜像
docker images playwright-mcp

# 重建镜像
docker build -t playwright-mcp .
```

3. **实例启动失败**
```bash
# 查看启动日志
tail -f logs/mcp-*.log

# 检查配置文件
cat cluster_config.json

# 清理并重启
./stop.sh --force && ./start.sh
```

### 日志管理
```bash
# 实时查看所有日志
tail -f logs/mcp-*.log

# 查看特定实例日志  
tail -f logs/mcp-mcp-1.log

# Docker容器日志
docker logs mcp-instance-1

# 清理日志文件（强制模式）
./stop.sh --force
```

## 🔄 版本更新记录

### v2.1.0 - 🆕 最新版本
- ✅ **智能停止脚本**：全新的stop.sh，支持混合环境管理
- ✅ **自动检测功能**：智能识别本地和Docker实例
- ✅ **选择性停止**：支持按模式停止实例
- ✅ **资源清理优化**：彻底清理隔离模式产生的临时文件
- ✅ **错误处理增强**：更好的错误信息和故障排除提示

### v2.0.0 - 集群版本
- ✅ **集群管理**：支持多实例并发
- ✅ **隔离模式**：避免配置冲突  
- ✅ **Docker支持**：容器化部署
- ✅ **中文优化**：国内网站测试
- ✅ **完整测试**：覆盖所有25个工具
- ✅ **智能启动**：自动检测和配置

### 兼容性
- 完全兼容原版MCP协议
- 支持所有原版功能
- 新增功能向后兼容

## 📊 性能特性

### 并发处理能力
- **多实例**: 支持最多5个并发实例
- **负载均衡**: 智能任务分配
- **故障隔离**: 单实例故障不影响整体服务
- **资源优化**: 独立的资源管理和清理

### 监控和管理
- **实时状态**: 智能检测运行状态
- **健康检查**: 多层验证实例健康
- **自动恢复**: 失败实例自动重试
- **日志管理**: 详细的操作日志

## 📄 许可证

本项目基于 [Apache License 2.0](LICENSE) 开源。

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发指南
1. Fork本项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 📞 支持

- 📖 **文档**：查看 [README_CLUSTER.md](README_CLUSTER.md) 了解集群详情
- 🐛 **Bug报告**：提交GitHub Issue
- 💡 **功能建议**：欢迎在Issue中讨论

## 🎊 快速命令参考

```bash
# 🚀 启动相关
./start.sh                    # 启动本地集群（隔离模式）
./start.sh --docker          # 启动Docker集群
./start.sh --no-isolated     # 启动本地集群（非隔离）

# 🛑 停止相关（🆕 智能升级）
./stop.sh                    # 停止所有实例（智能检测）
./stop.sh --local           # 仅停止本地实例
./stop.sh --docker          # 仅停止Docker实例
./stop.sh --force           # 强制停止并清理所有资源

# 🧪 测试相关
python3 test_all_tools_chinese.py    # 全工具测试
python3 demo_complete.py            # 完整演示
python3 test_cluster_management.py  # 集群管理测试

# 📊 监控相关
tail -f logs/mcp-*.log       # 查看实时日志
docker ps --filter name=mcp  # 查看Docker实例
lsof -i :9001-9005           # 查看端口占用
```

---

**⭐ 如果这个项目对您有帮助，请给个Star支持！**
