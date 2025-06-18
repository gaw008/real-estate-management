#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render数据库功能测试工具
专门测试Render上部署的房地产管理系统的数据库功能
"""

import requests
import json
import time
from datetime import datetime

RENDER_URL = "https://real-estate-management-p7p9.onrender.com"

def test_database_functions():
    """测试数据库相关功能"""
    print("=" * 60)
    print("🗄️  Render数据库功能测试")
    print("=" * 60)
    print(f"⏰ 测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 应用URL：{RENDER_URL}")
    print()
    
    # 测试数据库相关页面
    test_pages = [
        ("/demo/employee_departments", "员工部门管理"),
        ("/demo", "演示系统"),
        ("/properties", "房产管理"),
        ("/owners", "业主管理"),
        ("/", "主页"),
    ]
    
    for endpoint, name in test_pages:
        print(f"🔍 测试 {name} 页面...")
        try:
            url = f"{RENDER_URL}{endpoint}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ {name} 页面正常")
                print(f"   状态码: {response.status_code}")
                print(f"   响应时间: {response.elapsed.total_seconds():.2f}秒")
                
                # 检查页面内容
                content = response.text
                if "员工" in content or "房产" in content or "业主" in content or "管理" in content:
                    print("✅ 页面内容包含预期关键词")
                
                # 检查是否有数据库错误信息
                error_keywords = ["数据库连接失败", "连接错误", "Access denied", "演示模式"]
                found_errors = [kw for kw in error_keywords if kw in content]
                if found_errors:
                    if "演示模式" in found_errors:
                        print("⚠️  检测到演示模式，数据库可能未连接")
                    else:
                        print(f"⚠️  检测到错误信息: {', '.join(found_errors)}")
                else:
                    print("✅ 未检测到数据库错误信息")
                    
            elif response.status_code == 302:
                print(f"⚠️  {name} 页面重定向 (可能需要登录)")
            else:
                print(f"❌ {name} 页面返回状态码: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {name} 页面访问失败: {e}")
        
        print()
    
    # 测试员工部门功能的详细检查
    print("🔍 详细测试员工部门管理功能...")
    try:
        url = f"{RENDER_URL}/demo/employee_departments"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            content = response.text
            
            # 检查四个部门是否都存在
            departments = ["管理员", "销售", "财务", "房屋管理"]
            found_departments = [dept for dept in departments if dept in content]
            
            print(f"✅ 找到部门: {', '.join(found_departments)}")
            if len(found_departments) == 4:
                print("✅ 所有四个部门都存在")
            else:
                missing = [dept for dept in departments if dept not in found_departments]
                print(f"⚠️  缺少部门: {', '.join(missing)}")
            
            # 检查员工信息
            if "员工列表" in content or "员工信息" in content:
                print("✅ 员工列表功能正常")
            
            # 检查是否是演示数据
            if "演示数据" in content or "Demo" in content:
                print("ℹ️  使用演示数据模式")
            else:
                print("ℹ️  可能使用真实数据库数据")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ 员工部门功能测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("📊 数据库功能测试完成")
    print("=" * 60)

def check_environment_variables():
    """检查Render环境变量配置提示"""
    print("\n" + "=" * 60)
    print("🔧 Render环境变量配置检查提示")
    print("=" * 60)
    
    required_vars = [
        "DB_HOST",
        "DB_PORT", 
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "SECRET_KEY"
    ]
    
    print("请确认以下环境变量在Render中已正确设置：")
    for var in required_vars:
        if var == "DB_PASSWORD":
            print(f"✓ {var} = [从Aiven控制台复制实际密码]")
        elif var == "DB_HOST":
            print(f"✓ {var} = gng-4d77d5e-gngvacation-8888.f.aivencloud.com")
        elif var == "DB_PORT":
            print(f"✓ {var} = 21192")
        elif var == "DB_NAME":
            print(f"✓ {var} = defaultdb")
        elif var == "DB_USER":
            print(f"✓ {var} = avnadmin")
        elif var == "SECRET_KEY":
            print(f"✓ {var} = your-secret-key")
    
    print("\n💡 如果数据库仍然无法连接，请检查Render控制台的环境变量设置")

if __name__ == "__main__":
    test_database_functions()
    check_environment_variables() 