#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复Render服务器登录问题
Fix Render Server Login Issues
"""

import sys
import os
from auth_system import AuthSystem
from config_loader import DB_CONFIG

def diagnose_login_issue():
    """诊断登录问题"""
    print("🔍 开始诊断Render服务器登录问题...")
    print("="*60)
    
    auth_system = AuthSystem()
    
    # 1. 测试数据库连接
    print("\n1️⃣ 测试数据库连接...")
    conn = auth_system.get_db_connection()
    if not conn:
        print("❌ 数据库连接失败 - 这是主要问题！")
        print("📋 数据库配置:")
        if DB_CONFIG:
            print(f"   - 主机: {DB_CONFIG.get('host', 'unknown')}")
            print(f"   - 端口: {DB_CONFIG.get('port', 'unknown')}")
            print(f"   - 数据库: {DB_CONFIG.get('database', 'unknown')}")
            print(f"   - 用户: {DB_CONFIG.get('user', 'unknown')}")
            print(f"   - 密码设置: {'✅' if DB_CONFIG.get('password') else '❌'}")
        return False
    else:
        print("✅ 数据库连接成功")
        conn.close()
    
    # 2. 检查用户表状态
    print("\n2️⃣ 检查用户表状态...")
    auth_system.debug_users_table()
    
    # 3. 测试演示模式认证
    print("\n3️⃣ 测试演示模式认证...")
    demo_result = auth_system._demo_authenticate('admin', 'admin123')
    if demo_result:
        print("✅ 演示模式认证正常")
        print(f"   用户信息: {demo_result}")
    else:
        print("❌ 演示模式认证失败")
    
    # 4. 测试数据库认证
    print("\n4️⃣ 测试数据库认证...")
    db_result = auth_system.authenticate_user('admin', 'admin123')
    if db_result:
        print("✅ 数据库认证成功")
        print(f"   用户信息: {db_result}")
    else:
        print("❌ 数据库认证失败 - 这是问题所在！")
    
    return True

def fix_login_issue():
    """修复登录问题"""
    print("\n🔧 开始修复登录问题...")
    print("="*60)
    
    auth_system = AuthSystem()
    
    # 1. 创建用户表
    print("\n1️⃣ 创建/检查用户表...")
    if auth_system.create_users_table():
        print("✅ 用户表创建/检查成功")
    else:
        print("❌ 用户表创建失败")
        return False
    
    # 2. 创建默认管理员用户
    print("\n2️⃣ 创建默认管理员用户...")
    success = auth_system.create_admin_user(
        username='admin',
        email='admin@example.com', 
        password='admin123',
        full_name='系统管理员'
    )
    
    if success:
        print("✅ 管理员用户创建成功")
    else:
        print("⚠️ 管理员用户已存在或创建失败")
    
    # 3. 创建其他测试用户
    print("\n3️⃣ 创建其他测试用户...")
    test_users = [
        ('superadmin', 'super@example.com', 'super2025', '超级管理员'),
        ('manager', 'manager@example.com', 'manager123', '管理器'),
        ('pm01', 'pm01@example.com', '123456', '房产管理员')
    ]
    
    for username, email, password, full_name in test_users:
        success = auth_system.create_admin_user(username, email, password, full_name)
        if success:
            print(f"✅ 用户 {username} 创建成功")
        else:
            print(f"⚠️ 用户 {username} 已存在或创建失败")
    
    # 4. 验证修复结果
    print("\n4️⃣ 验证修复结果...")
    test_result = auth_system.authenticate_user('admin', 'admin123')
    if test_result:
        print("✅ 修复成功！admin用户现在可以正常登录")
        print(f"   用户信息: {test_result}")
        return True
    else:
        print("❌ 修复失败，admin用户仍无法登录")
        return False

def main():
    """主函数"""
    print("🏠 房地产管理系统 - Render登录问题修复工具")
    print("Real Estate Management System - Render Login Fix Tool")
    print("="*60)
    
    # 检查环境
    is_render = bool(os.environ.get('PORT'))
    print(f"🌍 运行环境: {'Render云服务器' if is_render else '本地开发环境'}")
    
    # 诊断问题
    if not diagnose_login_issue():
        print("\n❌ 诊断失败，无法继续修复")
        return False
    
    # 修复问题
    if fix_login_issue():
        print("\n✅ 修复完成！")
        print("\n📝 修复总结:")
        print("   - 数据库连接正常")
        print("   - 用户表已创建")
        print("   - 默认管理员用户已创建")
        print("   - 登录功能应该现在可以正常工作")
        print("\n🔑 可用的登录账户:")
        print("   - admin / admin123")
        print("   - superadmin / super2025") 
        print("   - manager / manager123")
        print("   - pm01 / 123456")
        print("\n🌐 请访问您的Render应用测试登录功能")
        return True
    else:
        print("\n❌ 修复失败，请检查错误信息")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 