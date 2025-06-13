#!/bin/bash

# 房地产数据分析系统 - 局域网部署脚本
# 作者: AI Assistant
# 日期: 2024年

echo "🏠 房地产数据分析系统 - 局域网部署"
echo "=================================="

# 检查Python版本
echo "📋 检查系统环境..."
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 检查必要的包
echo "📦 检查依赖包..."
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "❌ Streamlit未安装，正在安装..."
    pip3 install streamlit
fi

if ! python3 -c "import psycopg2" 2>/dev/null; then
    echo "❌ psycopg2未安装，正在安装..."
    pip3 install psycopg2-binary
fi

# 获取本机IP地址
local_ip=$(hostname -I | awk '{print $1}' 2>/dev/null || ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
if [ -z "$local_ip" ]; then
    local_ip="localhost"
fi

echo "🌐 本机IP地址: $local_ip"

# 创建配置目录
mkdir -p ~/.streamlit

# 复制配置文件
if [ -f "streamlit_config.toml" ]; then
    cp streamlit_config.toml ~/.streamlit/config.toml
    echo "✅ 配置文件已复制"
else
    echo "⚠️  配置文件不存在，使用默认配置"
fi

# 检查数据库连接
echo "🔗 检查数据库连接..."
if [ -f ".env" ]; then
    echo "✅ 环境变量文件存在"
else
    echo "⚠️  .env文件不存在，请确保数据库配置正确"
fi

# 检查防火墙端口
echo "🔥 检查防火墙设置..."
if command -v ufw &> /dev/null; then
    echo "检测到UFW防火墙，建议运行: sudo ufw allow 8501"
elif command -v firewall-cmd &> /dev/null; then
    echo "检测到FirewallD，建议运行: sudo firewall-cmd --add-port=8501/tcp --permanent && sudo firewall-cmd --reload"
fi

echo ""
echo "🚀 准备启动服务..."
echo "📍 局域网访问地址: http://$local_ip:8501"
echo "📍 本地访问地址: http://localhost:8501"
echo ""
echo "📝 使用说明:"
echo "  • 确保所有设备在同一局域网内"
echo "  • 公司成员可以通过 http://$local_ip:8501 访问"
echo "  • 按 Ctrl+C 停止服务"
echo ""

# 启动服务
echo "🌟 启动房地产数据分析系统..."
streamlit run real_estate_dashboard.py --server.address 0.0.0.0 --server.port 8501 