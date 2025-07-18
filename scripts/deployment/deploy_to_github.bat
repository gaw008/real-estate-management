@echo off
chcp 65001 >nul

REM 房地产管理系统 - GitHub部署脚本 (Windows版本)
REM 使用方法: deploy_to_github.bat YOUR_GITHUB_USERNAME

echo 🏠 房地产管理系统 - GitHub部署脚本
echo ==================================

REM 检查是否提供了GitHub用户名
if "%1"=="" (
    echo ❌ 错误: 请提供您的GitHub用户名
    echo 使用方法: deploy_to_github.bat YOUR_GITHUB_USERNAME
    pause
    exit /b 1
)

set GITHUB_USERNAME=%1
set REPO_NAME=real-estate-management

echo 📋 部署信息:
echo    GitHub用户名: %GITHUB_USERNAME%
echo    仓库名称: %REPO_NAME%
echo    远程地址: https://github.com/%GITHUB_USERNAME%/%REPO_NAME%.git
echo.

REM 检查是否已经添加了远程仓库
git remote get-url origin >nul 2>&1
if %errorlevel% equ 0 (
    echo 🔄 更新远程仓库地址...
    git remote set-url origin https://github.com/%GITHUB_USERNAME%/%REPO_NAME%.git
) else (
    echo ➕ 添加远程仓库...
    git remote add origin https://github.com/%GITHUB_USERNAME%/%REPO_NAME%.git
)

REM 确保分支名称为main
echo 🌿 设置主分支为main...
git branch -M main

REM 推送到GitHub
echo 🚀 推送代码到GitHub...
echo 注意: 如果这是第一次推送，您可能需要输入GitHub用户名和密码(或Personal Access Token)
echo.

git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ✅ 成功! 项目已上传到GitHub
    echo 🌐 访问您的仓库: https://github.com/%GITHUB_USERNAME%/%REPO_NAME%
    echo.
    echo 📝 下一步:
    echo 1. 访问GitHub仓库页面
    echo 2. 检查README.md是否正确显示
    echo 3. 在Settings中配置GitHub Pages(如果需要)
    echo 4. 添加Collaborators(如果需要)
    echo.
    echo 🔧 本地开发:
    echo 1. 复制config_example.py为config.py
    echo 2. 填入您的数据库配置信息
    echo 3. 运行: python real_estate_web.py
) else (
    echo.
    echo ❌ 推送失败! 请检查:
    echo 1. GitHub仓库是否已创建
    echo 2. 网络连接是否正常
    echo 3. GitHub认证信息是否正确
    echo.
    echo 💡 如果需要使用Personal Access Token:
    echo 1. 访问 GitHub Settings ^> Developer settings ^> Personal access tokens
    echo 2. 生成新的token并选择repo权限
    echo 3. 使用token作为密码进行认证
)

pause 