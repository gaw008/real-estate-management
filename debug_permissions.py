#!/usr/bin/env python3
"""
调试权限检查过程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.modules.department_modules import has_module_access, get_user_accessible_modules
from src.modules.user_module_permissions import get_user_module_permissions, init_user_module_permissions
from src.core.config_loader import DB_CONFIG
import mysql.connector

def debug_permissions():
    """调试权限检查过程"""
    print("🔍 调试权限检查过程...")
    
    # 1. 检查权限系统是否初始化
    print("\n1. 检查权限系统初始化...")
    try:
        user_module_permissions = get_user_module_permissions()
        if user_module_permissions:
            print("✅ 用户模块权限系统已初始化")
        else:
            print("❌ 用户模块权限系统未初始化")
            print("尝试重新初始化...")
            init_user_module_permissions(DB_CONFIG)
            user_module_permissions = get_user_module_permissions()
            if user_module_permissions:
                print("✅ 重新初始化成功")
            else:
                print("❌ 重新初始化失败")
    except Exception as e:
        print(f"❌ 权限系统检查失败: {e}")
    
    # 2. 直接检查数据库中的权限
    print("\n2. 检查数据库中的权限...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 检查admin用户
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        
        if admin_user:
            print(f"✅ 找到admin用户: ID={admin_user['id']}")
            
            # 检查customer_tracking权限
            cursor.execute("""
                SELECT * FROM user_module_permissions 
                WHERE user_id = %s AND module_name = 'customer_tracking'
            """, (admin_user['id'],))
            
            permission = cursor.fetchone()
            if permission:
                print(f"✅ customer_tracking权限记录存在: {permission}")
            else:
                print("❌ customer_tracking权限记录不存在")
                
                # 检查所有权限记录
                cursor.execute("""
                    SELECT * FROM user_module_permissions 
                    WHERE user_id = %s
                """, (admin_user['id'],))
                
                all_permissions = cursor.fetchall()
                print(f"该用户的所有权限记录: {all_permissions}")
                
                # 如果没有权限记录，尝试初始化
                if not all_permissions:
                    print("尝试为admin用户初始化权限...")
                    if user_module_permissions:
                        success = user_module_permissions.initialize_user_modules(
                            admin_user['id'], 
                            admin_user['user_type'], 
                            admin_user.get('department')
                        )
                        print(f"权限初始化结果: {success}")
        else:
            print("❌ 未找到admin用户")
            
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    
    # 3. 测试权限检查函数
    print("\n3. 测试权限检查函数...")
    try:
        # 模拟session
        from flask import session
        import threading
        
        # 创建一个简单的session模拟
        session_data = {'user_id': 1, 'user_type': 'admin', 'username': 'admin'}
        
        # 测试has_module_access
        print("测试has_module_access('customer_tracking')...")
        result = has_module_access('customer_tracking')
        print(f"权限检查结果: {result}")
        
    except Exception as e:
        print(f"❌ 权限检查函数测试失败: {e}")

if __name__ == "__main__":
    debug_permissions() 