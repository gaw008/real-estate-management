#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证系统初始化脚本
Initialize Authentication System
"""

from auth_system import auth_system

def setup_authentication_system():
    """设置认证系统"""
    print("🔧 开始设置用户认证系统...")
    
    # 1. 创建用户表
    print("\n1. 创建用户表和会话表...")
    if auth_system.create_users_table():
        print("✅ 用户表创建成功")
    else:
        print("❌ 用户表创建失败")
        return False
    
    # 2. 创建默认管理员账户
    print("\n2. 创建默认管理员账户...")
    admin_created = auth_system.create_admin_user(
        username="admin",
        email="admin@company.com",
        password="admin123",
        full_name="系统管理员"
    )
    
    if admin_created:
        print("✅ 默认管理员账户创建成功")
        print("   用户名: admin")
        print("   密码: admin123")
        print("   ⚠️  请登录后立即修改密码！")
    else:
        print("⚠️  管理员账户可能已存在")
    
    # 3. 为现有业主创建用户账户
    print("\n3. 为现有业主创建用户账户...")
    if auth_system.create_owner_users_from_existing():
        print("✅ 业主用户账户创建完成")
        print("   业主用户名格式: owner_[业主ID]")
        print("   默认密码: 手机号后4位或123456")
    else:
        print("❌ 业主用户账户创建失败")
    
    print("\n🎉 用户认证系统设置完成！")
    print("\n📋 登录信息:")
    print("管理员登录:")
    print("  - 用户名: admin")
    print("  - 密码: admin123")
    print("\n业主登录:")
    print("  - 用户名: owner_[业主ID]")
    print("  - 密码: 手机号后4位或123456")
    
    return True

if __name__ == "__main__":
    setup_authentication_system() 