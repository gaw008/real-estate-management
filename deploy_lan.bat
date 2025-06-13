@echo off
chcp 65001 >nul
echo 🏠 房地产数据分析系统 - 局域网部署 (Windows)
echo ==================================================

echo 📋 检查系统环境...
python --version
if errorlevel 1 (
    echo ❌ Python未安装，请先安装Python 3.7+
    pause
    exit /b 1
)

echo 📦 检查依赖包...
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo ❌ Streamlit未安装，正在安装...
    pip install streamlit
)

python -c "import psycopg2" 2>nul
if errorlevel 1 (
    echo ❌ psycopg2未安装，正在安装...
    pip install psycopg2-binary
)

echo 🌐 获取本机IP地址...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set "local_ip=%%a"
    goto :found_ip
)
:found_ip
set local_ip=%local_ip: =%
echo 本机IP地址: %local_ip%

echo 📁 创建配置目录...
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"

echo 📄 复制配置文件...
if exist "streamlit_config.toml" (
    copy "streamlit_config.toml" "%USERPROFILE%\.streamlit\config.toml" >nul
    echo ✅ 配置文件已复制
) else (
    echo ⚠️  配置文件不存在，使用默认配置
)

echo 🔗 检查数据库配置...
if exist ".env" (
    echo ✅ 环境变量文件存在
) else (
    echo ⚠️  .env文件不存在，请确保数据库配置正确
)

echo 🔥 防火墙提示...
echo 请确保Windows防火墙允许端口8501的入站连接
echo 可以在Windows防火墙设置中添加例外规则

echo.
echo 🚀 准备启动服务...
echo 📍 局域网访问地址: http://%local_ip%:8501
echo 📍 本地访问地址: http://localhost:8501
echo.
echo 📝 使用说明:
echo   • 确保所有设备在同一局域网内
echo   • 公司成员可以通过 http://%local_ip%:8501 访问
echo   • 按 Ctrl+C 停止服务
echo.

echo 🌟 启动房地产数据分析系统...
streamlit run real_estate_dashboard.py --server.address 0.0.0.0 --server.port 8501

pause 