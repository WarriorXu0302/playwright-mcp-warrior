#!/bin/bash

# Playwright MCP 集群启动脚本
# 基于官方 Playwright MCP 项目
# 支持隔离模式避免浏览器配置冲突

set -e  # 出错时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查端口占用情况
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # 端口已被占用
    else
        return 1  # 端口可用
    fi
}

# Docker模式启动函数
start_docker_cluster() {
    print_info "🐳 使用Docker模式启动集群..."
    
    # 停止已运行的Docker容器
    print_info "🛑 停止已运行的Docker容器..."
    docker rm -f $(docker ps -aq --filter name=mcp-instance) 2>/dev/null || true
    
    # 从配置文件读取实例信息
    INSTANCES=$(jq -r '.cluster.instances[] | "\(.id) \(.port)"' "$CONFIG_FILE")
    
    print_info "📋 从配置文件读取实例信息："
    echo "$INSTANCES"
    
    # 启动每个Docker实例
    CONTAINER_COUNT=0
    while IFS=' ' read -r instance_id port; do
        if [ -z "$instance_id" ] || [ -z "$port" ]; then
            continue
        fi
        
        CONTAINER_COUNT=$((CONTAINER_COUNT + 1))
        
        print_info "🔄 启动Docker实例 $instance_id (端口: $port)..."
        
        # 构建Docker启动命令
        DOCKER_CMD="docker run -d --name mcp-instance-$CONTAINER_COUNT"
        DOCKER_CMD+=" -p $port:9000"
        
        # 添加隔离模式环境变量
        if [ "$ISOLATED_MODE" = true ]; then
            DOCKER_CMD+=" -e USER_DATA_DIR=/tmp/playwright-$CONTAINER_COUNT"
            DOCKER_CMD+=" -e BROWSER_PROFILE_DIR=/tmp/browser-profile-$CONTAINER_COUNT"
        fi
        
        DOCKER_CMD+=" playwright-mcp --port 9000"
        
        # 添加隔离模式参数
        if [ "$ISOLATED_MODE" = true ]; then
            DOCKER_CMD+=" --isolated"
        fi
        
        # 执行Docker启动命令
        if eval $DOCKER_CMD; then
            print_success "✅ Docker实例 $instance_id 已启动 (容器: mcp-instance-$CONTAINER_COUNT)"
        else
            print_error "❌ Docker实例 $instance_id 启动失败"
        fi
        
        # 短暂等待避免启动过快
        sleep 1
        
    done <<< "$INSTANCES"
    
    # 等待Docker容器完全启动
    print_info "⏳ 等待Docker容器完全启动..."
    sleep 15
    
    # 验证Docker实例状态
    verify_docker_instances
}

# 本地模式启动函数
start_local_cluster() {
    print_info "💻 使用本地进程模式启动集群..."
    
    # 创建输出目录
    OUTPUT_DIR="output"
    LOGS_DIR="logs"
    mkdir -p "$OUTPUT_DIR"
    mkdir -p "$LOGS_DIR"
    
    # 清理旧的日志文件
    rm -f "$LOGS_DIR"/*.log

# 停止已运行的实例
print_info "🛑 停止已运行的实例..."
pkill -f "npx.*@playwright/mcp.*--port" || true
sleep 2

# 启动 MCP 实例
INSTANCES=$(jq -r '.cluster.instances[] | "\(.id) \(.port)"' "$CONFIG_FILE")

print_info "📋 从配置文件读取实例信息："
echo "$INSTANCES"

# 启动每个实例
    INSTANCE_COUNT=0
while IFS=' ' read -r instance_id port; do
    if [ -z "$instance_id" ] || [ -z "$port" ]; then
        continue
    fi
        
        INSTANCE_COUNT=$((INSTANCE_COUNT + 1))
    
    print_info "🔄 启动实例 $instance_id (端口: $port)..."
    
    # 检查端口是否已被占用
    if check_port $port; then
        print_warning "端口 $port 已被占用，尝试停止占用进程..."
        lsof -ti:$port | xargs kill -9 || true
        sleep 1
    fi
    
    # 启动实例
    LOG_FILE="$LOGS_DIR/mcp-$instance_id.log"
        
        # 构建启动命令
        START_CMD="npx @playwright/mcp@latest"
        START_CMD+=" --port $port"
        START_CMD+=" --headless"
        START_CMD+=" --output-dir $OUTPUT_DIR"
        START_CMD+=" --host 0.0.0.0"
        
        # 添加隔离模式参数
        if [ "$ISOLATED_MODE" = true ]; then
            START_CMD+=" --isolated"
            # 设置独立的用户数据目录
            export PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright-$INSTANCE_COUNT"
            export USER_DATA_DIR="/tmp/playwright-profile-$INSTANCE_COUNT"
        fi
    
    # 使用 nohup 启动实例，确保后台运行
        if [ "$ISOLATED_MODE" = true ]; then
            nohup env PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright-$INSTANCE_COUNT" \
                  USER_DATA_DIR="/tmp/playwright-profile-$INSTANCE_COUNT" \
                  $START_CMD > "$LOG_FILE" 2>&1 &
        else
            nohup $START_CMD > "$LOG_FILE" 2>&1 &
        fi
    
    # 记录进程ID
    echo $! > "$LOGS_DIR/mcp-$instance_id.pid"
    
    print_success "✅ 实例 $instance_id 已启动 (PID: $!, 日志: $LOG_FILE)"
    
    # 等待实例启动
    sleep 3
    
done <<< "$INSTANCES"

print_info "⏳ 等待所有实例完全启动..."
sleep 10

    # 验证本地实例状态
    verify_local_instances
}

# 验证Docker实例状态
verify_docker_instances() {
    print_info "🔍 验证Docker实例状态..."
    
    # 显示Docker容器状态
    echo ""
    print_info "🐳 Docker容器状态:"
    docker ps --filter name=mcp-instance --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    # 测试连接
    INSTANCES=$(jq -r '.cluster.instances[] | "\(.id) \(.port)"' "$CONFIG_FILE")
SUCCESS_COUNT=0
TOTAL_COUNT=0

while IFS=' ' read -r instance_id port; do
    if [ -z "$instance_id" ] || [ -z "$port" ]; then
        continue
    fi
    
    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    
        # 测试端口连接 - 修复连接验证逻辑
        if curl -s --max-time 3 --connect-timeout 2 "http://localhost:$port/sse" | head -n 1 | grep -q "event:" 2>/dev/null; then
            print_success "✅ 实例 $instance_id (端口 $port) 连接正常"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            print_error "❌ 实例 $instance_id (端口 $port) 连接失败"
        fi
        
    done <<< "$INSTANCES"
    
    show_final_summary $SUCCESS_COUNT $TOTAL_COUNT
}

# 验证本地实例状态
verify_local_instances() {
    print_info "🔍 验证本地实例状态..."
    SUCCESS_COUNT=0
    TOTAL_COUNT=0
    
    INSTANCES=$(jq -r '.cluster.instances[] | "\(.id) \(.port)"' "$CONFIG_FILE")

    while IFS=' ' read -r instance_id port; do
        if [ -z "$instance_id" ] || [ -z "$port" ]; then
            continue
        fi
        
        TOTAL_COUNT=$((TOTAL_COUNT + 1))
        
        # 首先检查端口是否在监听
        if check_port $port; then
            # 进一步验证SSE连接是否正常
            if curl -s --max-time 3 --connect-timeout 2 "http://localhost:$port/sse" | head -n 1 | grep -q "event:" 2>/dev/null; then
                print_success "✅ 实例 $instance_id (端口 $port) 运行正常"
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
                print_error "❌ 实例 $instance_id (端口 $port) 端口监听但SSE连接失败"
        fi
    else
        print_error "❌ 实例 $instance_id (端口 $port) 启动失败"
        
        # 显示日志的最后几行
        LOG_FILE="$LOGS_DIR/mcp-$instance_id.log"
        if [ -f "$LOG_FILE" ]; then
            print_error "最后10行日志:"
            tail -10 "$LOG_FILE"
        fi
    fi
    
done <<< "$INSTANCES"
    
    show_final_summary $SUCCESS_COUNT $TOTAL_COUNT
}

# 显示最终总结
show_final_summary() {
    local success_count=$1
    local total_count=$2

print_info "📊 启动结果统计:"
    print_info "   总实例数: $total_count"
    print_info "   成功启动: $success_count"
    print_info "   失败数量: $((total_count - success_count))"
    print_info "   隔离模式: $([ "$ISOLATED_MODE" = true ] && echo "✅ 启用" || echo "❌ 禁用")"

    if [ $success_count -eq $total_count ] && [ $total_count -gt 0 ]; then
    print_success "🎉 所有实例启动成功！"
    
    print_info "📋 集群信息:"
    echo "   配置文件: $CONFIG_FILE"
        if [ "$USE_DOCKER" = false ]; then
    echo "   输出目录: $OUTPUT_DIR"
    echo "   日志目录: $LOGS_DIR"
        fi
    echo ""
    print_info "🌐 实例访问地址:"
        
        INSTANCES=$(jq -r '.cluster.instances[] | "\(.id) \(.port)"' "$CONFIG_FILE")
    while IFS=' ' read -r instance_id port; do
        if [ -n "$instance_id" ] && [ -n "$port" ]; then
                echo "   $instance_id: http://localhost:$port/sse"
        fi
    done <<< "$INSTANCES"
    
    echo ""
    print_info "📝 管理命令:"
        if [ "$USE_DOCKER" = true ]; then
            echo "   查看容器: docker ps --filter name=mcp-instance"
            echo "   停止集群: docker rm -f \$(docker ps -aq --filter name=mcp-instance)"
            echo "   查看日志: docker logs mcp-instance-1"
        else
    echo "   查看状态: ./status.sh"
    echo "   停止集群: ./stop.sh"
    echo "   查看日志: tail -f $LOGS_DIR/mcp-*.log"
        fi
        
        print_info "🛠️  测试命令:"
        echo "   测试工具: python3 $([ "$USE_DOCKER" = true ] && echo "test_docker_tools.py" || echo "test_all_tools.py")"
        echo "   完整演示: python3 $([ "$USE_DOCKER" = true ] && echo "demo_complete.py" || echo "demo.py")"
    
    exit 0
else
        print_error "❌ 部分或全部实例启动失败"
        if [ "$USE_DOCKER" = true ]; then
            print_info "💡 Docker故障排除:"
            echo "   1. 检查Docker是否运行: docker version"
            echo "   2. 检查镜像是否存在: docker images playwright-mcp"
            echo "   3. 查看容器日志: docker logs mcp-instance-1"
        else
            print_info "💡 本地模式故障排除:"
            echo "   1. 检查端口占用: lsof -i :9001-9005"
            echo "   2. 检查Playwright安装: npx @playwright/mcp@latest --help"
            echo "   3. 查看实例日志: tail -f logs/mcp-*.log"
        fi
        exit 1
    fi
}

# ==================== 主程序开始 ====================

# 默认配置
CONFIG_FILE="cluster_config.json"
ISOLATED_MODE=true  # 默认启用隔离模式
USE_DOCKER=false    # 默认使用本地模式

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --no-isolated)
            ISOLATED_MODE=false
            shift
            ;;
        --docker)
            USE_DOCKER=true
            CONFIG_FILE="docker_cluster_config.json"
            shift
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --config FILE       指定配置文件 (默认: cluster_config.json)"
            echo "  --no-isolated       禁用隔离模式"
            echo "  --docker           使用Docker模式启动"
            echo "  --help             显示帮助信息"
            exit 0
            ;;
        *)
            print_error "未知参数: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 检查配置文件
if [ ! -f "$CONFIG_FILE" ]; then
    print_error "配置文件 $CONFIG_FILE 不存在"
    exit 1
fi

print_info "🚀 启动 Playwright MCP 集群..."
print_info "   配置文件: $CONFIG_FILE"
print_info "   隔离模式: $([ "$ISOLATED_MODE" = true ] && echo "启用" || echo "禁用")"
print_info "   运行模式: $([ "$USE_DOCKER" = true ] && echo "Docker容器" || echo "本地进程")"

# 根据模式启动集群
if [ "$USE_DOCKER" = true ]; then
    start_docker_cluster
else
    start_local_cluster
fi 