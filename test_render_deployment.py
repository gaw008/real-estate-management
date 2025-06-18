#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render部署测试工具
测试Render上部署的房地产管理系统是否正常工作
"""

import requests
import json
import time
from datetime import datetime

# Render应用URL（请替换为您的实际URL）
RENDER_URL = "https://your-app-name.onrender.com"  # 请替换为您的实际Render URL

def test_render_deployment():
    """测试Render部署的应用"""
    print("=" * 60)
    print("🌐 Render部署测试工具")
    print("=" * 60)
    print(f"⏰ 测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 测试URL：{RENDER_URL}")
    print()
    
    # 测试1：检查应用是否启动
    print("🔍 测试1：检查应用是否可访问...")
    try:
        response = requests.get(RENDER_URL, timeout=30)
        if response.status_code == 200:
            print("✅ 应用可访问")
            print(f"   响应状态码：{response.status_code}")
            print(f"   响应时间：{response.elapsed.total_seconds():.2f}秒")
        else:
            print(f"⚠️  应用返回状态码：{response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 应用无法访问：{e}")
        return False
    
    # 测试2：检查员工部门管理页面
    print("\n🔍 测试2：检查员工部门管理页面...")
    try:
        demo_url = f"{RENDER_URL}/demo/employee_departments"
        response = requests.get(demo_url, timeout=30)
        if response.status_code == 200:
            print("✅ 员工部门管理页面可访问")
            if "员工部门管理" in response.text:
                print("✅ 页面内容正确")
            else:
                print("⚠️  页面内容可能有问题")
        else:
            print(f"❌ 员工部门管理页面返回状态码：{response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 员工部门管理页面无法访问：{e}")
    
    # 测试3：检查演示页面
    print("\n🔍 测试3：检查演示入口页面...")
    try:
        demo_home_url = f"{RENDER_URL}/demo"
        response = requests.get(demo_home_url, timeout=30)
        if response.status_code == 200:
            print("✅ 演示入口页面可访问")
            if "演示系统" in response.text or "房地产管理系统" in response.text:
                print("✅ 演示页面内容正确")
        else:
            print(f"❌ 演示入口页面返回状态码：{response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 演示入口页面无法访问：{e}")
    
    # 测试4：检查数据库连接状态（通过API）
    print("\n🔍 测试4：检查应用数据库连接状态...")
    try:
        # 尝试访问需要数据库的页面来间接测试数据库连接
        properties_url = f"{RENDER_URL}/properties"
        response = requests.get(properties_url, timeout=30)
        if response.status_code == 200:
            print("✅ 数据库相关页面可访问")
        elif response.status_code == 302:
            print("⚠️  页面重定向（可能需要登录）")
        else:
            print(f"⚠️  数据库页面返回状态码：{response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 数据库页面无法访问：{e}")
    
    print("\n" + "=" * 60)
    print("📊 测试完成")
    print("=" * 60)
    
    print("\n💡 如果需要更详细的测试，请提供您的实际Render URL")
    return True

def test_specific_url(url):
    """测试特定URL"""
    print(f"🔍 测试特定URL：{url}")
    try:
        response = requests.get(url, timeout=30)
        print(f"✅ 响应状态码：{response.status_code}")
        print(f"✅ 响应时间：{response.elapsed.total_seconds():.2f}秒")
        print(f"✅ 响应大小：{len(response.content)} bytes")
        
        # 检查是否包含关键词
        keywords = ["房地产", "员工", "部门", "管理", "演示"]
        found_keywords = [kw for kw in keywords if kw in response.text]
        if found_keywords:
            print(f"✅ 找到关键词：{', '.join(found_keywords)}")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ 访问失败：{e}")
        return False

if __name__ == "__main__":
    print("请选择测试模式：")
    print("1. 使用默认URL测试（请先修改脚本中的RENDER_URL）")
    print("2. 输入您的Render URL进行测试")
    
    choice = input("请输入选择（1或2）：").strip()
    
    if choice == "2":
        url = input("请输入您的Render应用URL：").strip()
        if url:
            RENDER_URL = url.rstrip('/')
            test_render_deployment()
        else:
            print("❌ URL不能为空")
    else:
        if "your-app-name" in RENDER_URL:
            print("⚠️  请先修改脚本中的RENDER_URL为您的实际Render URL")
            url = input("或者现在直接输入您的Render URL：").strip()
            if url:
                RENDER_URL = url.rstrip('/')
                test_render_deployment()
        else:
            test_render_deployment() 