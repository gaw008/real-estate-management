#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户表部门字段升级脚本
为users表添加department字段，支持员工部门管理功能
"""

import mysql.connector
from core.config_loader import DB_CONFIG

def get_db_connection():
    """获取数据库连接"""
    try:
        # 为Aiven MySQL配置SSL连接
        ssl_config = {
            'ssl_disabled': False,
            'ssl_verify_cert': False,  # 禁用证书验证以解决自签名证书问题
            'ssl_verify_identity': False
        }
        
        # 合并配置
        config = {**DB_CONFIG, **ssl_config}
        
        print(f"尝试连接数据库: {config['host']}:{config['port']}")
        connection = mysql.connector.connect(**config)
        print("✅ 数据库连接成功")
        return connection
    except Exception as e:
        print(f"❌ 数据库连接错误: {e}")
        return None

def update_users_table():
    """更新users表，添加department字段"""
    conn = get_db_connection()
    if not conn:
        print("❌ 数据库连接失败，无法执行升级")
        return False
    
    cursor = conn.cursor()
    
    try:
        print("🔍 检查users表结构...")
        
        # 检查department字段是否存在
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]
        
        if 'department' in column_names:
            print("✅ department字段已存在，无需更新")
            return True
        
        print("📝 添加department字段...")
        
        # 添加department字段
        alter_sql = """
        ALTER TABLE users 
        ADD COLUMN department VARCHAR(100) NULL 
        AFTER user_type
        """
        
        cursor.execute(alter_sql)
        
        # 添加索引
        index_sql = """
        ALTER TABLE users 
        ADD INDEX idx_department (department)
        """
        
        cursor.execute(index_sql)
        
        conn.commit()
        print("✅ users表升级成功！")
        print("📊 添加的字段:")
        print("   - department VARCHAR(100) NULL - 员工部门")
        print("   - idx_department - 部门索引")
        
        # 显示更新后的表结构
        print("\n📋 当前users表结构:")
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"   {col[0]:20} {col[1]:20} {col[2]:10} {col[3]:10}")
        
        return True
        
    except Exception as e:
        print(f"❌ 升级失败: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def verify_upgrade():
    """验证升级结果"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        print("\n🔍 验证升级结果...")
        
        # 检查表结构
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        
        has_department = False
        for col in columns:
            if col['Field'] == 'department':
                has_department = True
                print(f"✅ department字段: {col['Type']} {col['Null']} {col['Default']}")
                break
        
        if not has_department:
            print("❌ department字段未找到")
            return False
        
        # 检查索引
        cursor.execute("SHOW INDEX FROM users WHERE Key_name = 'idx_department'")
        index_info = cursor.fetchall()
        
        if index_info:
            print("✅ department索引已创建")
        else:
            print("⚠️  department索引未找到")
        
        # 检查现有用户数据
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE user_type != 'owner'")
        employee_count = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as assigned FROM users WHERE user_type != 'owner' AND department IS NOT NULL")
        assigned_count = cursor.fetchone()['assigned']
        
        print(f"📊 员工用户统计:")
        print(f"   总员工数: {employee_count}")
        print(f"   已分配部门: {assigned_count}")
        print(f"   未分配部门: {employee_count - assigned_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """主函数"""
    print("🏢 房地产管理系统 - 用户表部门字段升级")
    print("=" * 50)
    
    # 执行升级
    if update_users_table():
        print("\n" + "=" * 50)
        verify_upgrade()
        print("\n✅ 升级完成！")
        print("📌 提示：")
        print("   1. 现在可以通过 /admin/employee_departments 页面管理员工部门")
        print("   2. 所有现有员工的部门字段初始为NULL，需要管理员手动分配")
        print("   3. 系统支持以下预定义部门：")
        departments = ['人事部', '财务部', '销售部', '市场部', '技术部', '客服部', '法务部', '运营部', '管理部', '其他']
        for dept in departments:
            print(f"      - {dept}")
    else:
        print("\n❌ 升级失败！")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 