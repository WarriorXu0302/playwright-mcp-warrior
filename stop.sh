#!/bin/bash

# Playwright MCP 集群停止脚本
# 支持本地模式和Docker模式自动检测

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 默认配置
LOCAL_CONFIG="cluster_config.json"
DOCKER_CONFIG="docker_cluster_config.json"
LOGS_DIR="logs"
FORCE_MODE=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --local)
            STOP_MODE="local"
            shift
            ;;
        --docker)
            STOP_MODE="docker"
            shift
            ;;
        --all)
            STOP_MODE="all"
            shift
            ;;
        --force)
            FORCE_MODE=true
            shift
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --local         仅停止本地实例"
            echo "  --docker        仅停止Docker实例"
            echo "  --all           停止所有实例（默认）"
            echo "  --force         强制停止（跳过确认）"
            echo "  --help          显示帮助信息"
            exit 0
            ;;
        *)
            print_error "未知参数: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 默认停止所有实例
if [ -z "$STOP_MODE" ]; then
    STOP_MODE="all"
fi

print_info "🛑 停止 Playwright MCP 集群..."
print_info "   停止模式: $STOP_MODE"
print_info "   强制模式: $([ "$FORCE_MODE" = true ] && echo "启用" || echo "禁用")"

# 检测运行中的实例
detect_running_instances() {
    local local_instances=0
    local docker_instances=0
    
    # 检测本地实例
    if pgrep -f "npx.*@playwright/mcp.*--port" >/dev/null 2>&1; then
        local_instances=$(pgrep -f "npx.*@playwright/mcp.*--port" | wc -l)
    fi
    
    # 检测Docker实例
    if command -v docker >/dev/null 2>&1; then
        docker_instances=$(docker ps --filter name=mcp-instance --format "{{.Names}}" 2>/dev/null | wc -l)
    fi
    
    echo "local:$local_instances,docker:$docker_instances"
}

# 停止本地实例
stop_local_instances() {
    print_info "🔄 停止本地实例..."
    
    local stopped_count=0

# 方法1: 通过PID文件停止
if [ -d "$LOGS_DIR" ]; then
        print_info "📁 通过PID文件停止实例..."
    
    for pid_file in "$LOGS_DIR"/mcp-*.pid; do
        if [ -f "$pid_file" ]; then
            instance_name=$(basename "$pid_file" .pid)
            pid=$(cat "$pid_file")
            
            if kill -0 "$pid" 2>/dev/null; then
                    print_info "   停止实例 $instance_name (PID: $pid)..."
                
                    if kill "$pid" 2>/dev/null; then
                # 等待进程结束
                        sleep 3
                
                if kill -0 "$pid" 2>/dev/null; then
                            print_warning "   进程 $pid 未响应，强制终止..."
                    kill -9 "$pid" 2>/dev/null || true
                fi
                
                        print_success "   ✅ 实例 $instance_name 已停止"
                        stopped_count=$((stopped_count + 1))
                    else
                        print_warning "   ⚠️  无法停止进程 $pid"
                    fi
            else
                    print_warning "   ⚠️  PID $pid 进程不存在，清理PID文件"
            fi
            
            rm -f "$pid_file"
        fi
    done
fi

    # 方法2: 通过进程名称停止残留实例
    print_info "🔍 清理残留的本地实例..."
    local remaining_pids=$(pgrep -f "npx.*@playwright/mcp.*--port" 2>/dev/null || true)
    
    if [ -n "$remaining_pids" ]; then
        print_info "   发现残留进程，正在清理..."
        echo "$remaining_pids" | xargs kill -9 2>/dev/null || true
        stopped_count=$((stopped_count + $(echo "$remaining_pids" | wc -w)))
    fi

# 方法3: 通过端口停止
    if [ -f "$LOCAL_CONFIG" ]; then
        print_info "🌐 释放本地实例端口..."
    
        local ports=$(jq -r '.cluster.instances[].port' "$LOCAL_CONFIG" 2>/dev/null || true)
    
        if [ -n "$ports" ]; then
            for port in $ports; do
                if [ -n "$port" ] && [ "$port" != "null" ]; then
                    local pids=$(lsof -ti:$port 2>/dev/null || true)
                
                    if [ -n "$pids" ]; then
                        print_info "   释放端口 $port..."
                        echo "$pids" | xargs kill -9 2>/dev/null || true
                        print_success "   ✅ 端口 $port 已释放"
                fi
                fi
            done
        fi
    fi
    
    print_success "📊 本地实例停止完成 (停止数量: $stopped_count)"
}

# 停止Docker实例
stop_docker_instances() {
    print_info "🐳 停止Docker实例..."
    
    if ! command -v docker >/dev/null 2>&1; then
        print_warning "⚠️  Docker未安装，跳过Docker实例停止"
        return
    fi
    
    local stopped_count=0
    
    # 获取所有MCP Docker容器
    local containers=$(docker ps --filter name=mcp-instance --format "{{.Names}}" 2>/dev/null || true)
    
    if [ -n "$containers" ]; then
        print_info "📋 发现Docker容器: $(echo "$containers" | wc -l) 个"
        
        for container in $containers; do
            print_info "   停止容器: $container"
            
            if docker stop "$container" >/dev/null 2>&1; then
                print_success "   ✅ 容器 $container 已停止"
                stopped_count=$((stopped_count + 1))
            else
                print_warning "   ⚠️  容器 $container 停止失败"
            fi
        done
        
        # 清理停止的容器
        print_info "🧹 清理停止的容器..."
        if docker container prune -f >/dev/null 2>&1; then
            print_success "   ✅ 容器清理完成"
        fi
    else
        print_info "📋 未发现运行中的Docker容器"
fi

    # 额外清理：强制删除所有MCP相关容器
    if [ "$FORCE_MODE" = true ]; then
        print_info "💪 强制模式：清理所有MCP相关容器..."
        local all_containers=$(docker ps -a --filter name=mcp-instance --format "{{.Names}}" 2>/dev/null || true)
        
        if [ -n "$all_containers" ]; then
            echo "$all_containers" | xargs docker rm -f >/dev/null 2>&1 || true
            print_success "   ✅ 强制清理完成"
        fi
    fi
    
    print_success "📊 Docker实例停止完成 (停止数量: $stopped_count)"
}

# 清理资源
cleanup_resources() {
    print_info "🧹 清理系统资源..."

# 清理PID文件
    if [ -d "$LOGS_DIR" ]; then
rm -f "$LOGS_DIR"/mcp-*.pid 2>/dev/null || true
        print_success "   ✅ PID文件已清理"
    fi
    
    # 清理临时文件（如果存在）
    local temp_dirs=$(find /tmp -maxdepth 1 -name "playwright-profile-*" -o -name "playwright-*" -o -name "browser-profile-*" 2>/dev/null || true)
    if [ -n "$temp_dirs" ]; then
        echo "$temp_dirs" | while read -r temp_dir; do
            if [ -d "$temp_dir" ]; then
                rm -rf "$temp_dir" 2>/dev/null || true
            fi
        done
    fi
    
    # 可选：清理日志文件（仅在强制模式下）
    if [ "$FORCE_MODE" = true ] && [ -d "$LOGS_DIR" ]; then
        print_warning "💪 强制模式：清理日志文件..."
        rm -f "$LOGS_DIR"/mcp-*.log 2>/dev/null || true
        print_success "   ✅ 日志文件已清理"
    fi
    
    print_success "✅ 资源清理完成"
}

# 验证停止结果
verify_stop_result() {
print_info "🔍 验证停止结果..."
    
    local local_remaining=0
    local docker_remaining=0
    
    # 检查本地实例
    if pgrep -f "npx.*@playwright/mcp.*--port" >/dev/null 2>&1; then
        local_remaining=$(pgrep -f "npx.*@playwright/mcp.*--port" | wc -l)
    fi
    
    # 检查Docker实例
    if command -v docker >/dev/null 2>&1; then
        docker_remaining=$(docker ps --filter name=mcp-instance --format "{{.Names}}" 2>/dev/null | wc -l || echo "0")
    fi
    
    print_info "📊 验证结果:"
    print_info "   本地实例残留: $local_remaining"
    print_info "   Docker实例残留: $docker_remaining"
    
    if [ "$local_remaining" -eq "0" ] && [ "$docker_remaining" -eq "0" ]; then
        print_success "🎉 所有MCP实例已完全停止！"
        return 0
else
        print_warning "⚠️  仍有实例在运行"
        
        if [ "$local_remaining" -gt "0" ]; then
            print_warning "残留本地进程:"
    pgrep -f "npx.*@playwright/mcp.*--port" -l 2>/dev/null || true
fi 
        
        if [ "$docker_remaining" -gt "0" ]; then
            print_warning "残留Docker容器:"
            docker ps --filter name=mcp-instance --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || true
        fi
        
        return 1
    fi
}

# 主执行逻辑
main() {
    # 检测当前运行状态
    local status=$(detect_running_instances)
    local local_count=$(echo "$status" | cut -d',' -f1 | cut -d':' -f2)
    local docker_count=$(echo "$status" | cut -d',' -f2 | cut -d':' -f2)
    
    print_info "📊 当前运行状态:"
    print_info "   本地实例: $local_count"
    print_info "   Docker实例: $docker_count"
    
    if [ "$local_count" -eq "0" ] && [ "$docker_count" -eq "0" ]; then
        print_success "🎉 没有发现运行中的实例"
        return 0
    fi
    
    # 根据模式停止实例
    case "$STOP_MODE" in
        "local")
            if [ "$local_count" -gt "0" ]; then
                stop_local_instances
            else
                print_info "📋 没有运行中的本地实例"
            fi
            ;;
        "docker")
            if [ "$docker_count" -gt "0" ]; then
                stop_docker_instances
            else
                print_info "📋 没有运行中的Docker实例"
            fi
            ;;
        "all")
            if [ "$local_count" -gt "0" ]; then
                stop_local_instances
            fi
            if [ "$docker_count" -gt "0" ]; then
                stop_docker_instances
            fi
            ;;
    esac
    
    # 清理资源
    cleanup_resources
    
    # 验证结果
    verify_stop_result
}

# 显示帮助信息（如果没有参数且没有运行实例）
check_help_display() {
    if [ $# -eq 0 ]; then
        local status=$(detect_running_instances)
        local local_count=$(echo "$status" | cut -d',' -f1 | cut -d':' -f2)
        local docker_count=$(echo "$status" | cut -d',' -f2 | cut -d':' -f2)
        
        if [ "$local_count" -eq "0" ] && [ "$docker_count" -eq "0" ]; then
            echo "Playwright MCP 集群停止脚本"
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --local         仅停止本地实例"
            echo "  --docker        仅停止Docker实例"  
            echo "  --all           停止所有实例（默认）"
            echo "  --force         强制停止（清理所有相关资源）"
            echo "  --help          显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0              # 停止所有实例"
            echo "  $0 --local      # 仅停止本地实例"
            echo "  $0 --docker     # 仅停止Docker实例"
            echo "  $0 --force      # 强制停止并清理所有资源"
            echo ""
            echo "当前没有发现运行中的实例。"
            exit 0
        fi
    fi
}

# 检查是否需要显示帮助
# check_help_display "$@"

# 执行主函数
main

exit_code=$?
if [ $exit_code -eq 0 ]; then
    print_success "🎊 停止操作完成！"
else
    print_warning "⚠️  停止操作完成，但可能有残留实例"
    print_info "💡 提示: 使用 --force 参数进行强制清理"
fi

exit $exit_code 