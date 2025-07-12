# Playwright MCP MinIO 截图存储功能

本模块为 Playwright MCP 集群提供了将截图保存到 MinIO 对象存储服务的功能。即使在没有 MinIO 服务的环境中，该模块也会通过本地备份确保截图不会丢失。

## 功能特点

1. **MinIO 对象存储集成**：将截图和快照数据直接保存到 MinIO 对象存储服务
2. **本地备份**：即使 MinIO 服务不可用，也能将数据保存到本地目录
3. **灵活配置**：支持通过配置文件定制 MinIO 连接参数和存储策略
4. **无缝集成**：与现有的 Playwright MCP 截图和快照功能无缝集成
5. **容错设计**：即使未安装 MinIO 客户端库，仍可使用本地存储功能
6. **多种数据格式支持**：支持存储图片、HTML、JSON、文本等多种格式
7. **视觉数据支持**：支持保存页面快照、Accessibility结构和视觉信息

## 安装要求

1. **MinIO 服务**：一个可访问的 MinIO 服务器
2. **Python 依赖**：
   - `minio` 客户端库 (可选，无则使用本地存储)
   - `Pillow` 库 (用于测试脚本中创建测试图片)

## 快速开始

### 1. 安装 MinIO 客户端库

```bash
pip install minio
```

### 2. 配置 MinIO 连接

创建或修改 `minio_config.json` 文件：

```json
{
    "endpoint": "127.0.0.1:9000",
    "access_key": "minioadmin",
    "secret_key": "minioadmin",
    "secure": false,
    "bucket_name": "playwright-screenshots",
    "region": "cn-north-1",
    "use_minio": true,
    "local_backup": true,
    "local_backup_dir": "/tmp/playwright-screenshots"
}
```

### 3. 测试存储功能

运行演示脚本测试 MinIO 存储功能：

```bash
python demo_minio.py
```

### 4. 与 Playwright MCP 集成

1. 启动 Playwright MCP 集群：

```bash
./start.sh
```

2. 运行演示脚本：

```bash
python demo.py
```

## 配置选项

`minio_config.json` 文件支持以下配置选项：

| 配置项 | 说明 | 默认值 |
|-------|------|-------|
| endpoint | MinIO 服务器端点 | 127.0.0.1:9000 |
| access_key | 访问密钥 | minioadmin |
| secret_key | 密码密钥 | minioadmin |
| secure | 是否使用 HTTPS | false |
| bucket_name | 存储桶名称 | playwright-screenshots |
| region | 区域名称 | cn-north-1 |
| use_minio | 是否启用 MinIO 存储 | true |
| local_backup | 是否本地备份截图 | true |
| local_backup_dir | 本地备份目录 | /tmp/playwright-screenshots |

## 使用示例

### 基本使用

```python
from python.minio_storage import get_minio_storage

# 获取 MinIO 存储实例
storage = get_minio_storage()

# 保存 Base64 格式的截图
result = storage.save_screenshot(base64_data, "screenshot.png")

# 保存本地文件
result = storage.save_screenshot_file("/path/to/screenshot.png", "screenshot.png")

# 保存HTML内容
result = storage.save_text_content("<html><body>Hello World</body></html>", "page.html", "text/html")

# 保存JSON数据
result = storage.save_text_content('{"key": "value"}', "data.json", "application/json") 
```

### 集成到 Playwright MCP

MinIO 存储功能已经集成到 Playwright MCP 的截图和快照功能中。当执行这些操作时，会自动保存到 MinIO：

```python
# 示例代码: 执行截图操作
client = SSEClient("http://localhost:9001/sse")
client.initialize()

# 调用截图工具
result = client.call_tool('browser_take_screenshot', {
    'filename': 'my_screenshot.png'
})

# 截图会自动保存到 MinIO，并在结果中包含 MinIO URL
if result and 'minio_url' in result:
    print(f"MinIO URL: {result['minio_url']}")

# 调用快照工具
result = client.call_tool('browser_snapshot', {})

# 快照会自动保存到 MinIO，并在结果中包含 MinIO URLs
if result and 'minio_urls' in result:
    urls = result['minio_urls']
    if 'html' in urls:
        print(f"HTML内容: {urls['html']}")
    if 'json' in urls:
        print(f"JSON数据: {urls['json']}")
    if 'snapshot' in urls:
        print(f"快照数据: {urls['snapshot']}")
```

### 使用演示脚本

项目提供了以下演示脚本：

1. **demo_minio.py**: 基础MinIO存储功能演示
2. **demo_vision_minio.py**: 将页面快照(Vision数据)保存到MinIO的演示

运行演示脚本：

```bash
# 启动服务
./start.sh

# 测试截图存储
python demo_minio.py

# 测试视觉数据存储
python demo_vision_minio.py
```

## 故障排除

### 1. MinIO 客户端库未安装

**症状**：出现 `未安装 minio 客户端库` 的警告

**解决方案**：安装 MinIO 客户端库

```bash
pip install minio
```

### 2. 无法连接到 MinIO 服务器

**症状**：出现 `MinIO 客户端初始化失败` 的错误

**解决方案**：
- 确认 MinIO 服务器是否运行
- 验证 endpoint, access_key, secret_key 等配置是否正确
- 检查网络连接和防火墙设置

### 3. 本地备份路径不存在或无写入权限

**症状**：出现 `保存截图到本地失败` 的警告

**解决方案**：
- 确认本地备份路径是否存在
- 确认当前用户是否有权限写入该路径
- 修改配置文件中的 `local_backup_dir` 为有权限的路径

## 开发说明

### 文件结构

- `python/minio_storage.py`: MinIO 存储功能实现
- `minio_config.json`: MinIO 配置文件
- `demo_minio.py`: MinIO 基础存储功能演示脚本
- `demo_vision_minio.py`: MinIO 视觉数据存储演示脚本
- `README_MINIO.md`: MinIO 功能文档

### 存储类型

MinIO存储功能支持以下类型的数据：

1. **图片**:
   - 截图 (.png)
   - 视觉快照

2. **页面数据**:
   - HTML内容 (.html)
   - 结构化JSON数据 (.json)
   - 可访问性数据 (Accessibility)
   - 快照元数据

### 扩展功能

要扩展存储功能，可以修改 `minio_storage.py` 文件，添加新的存储方法或支持其他存储服务。 