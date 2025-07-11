#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复Render服务器登录问题
Fix Render Server Login Issues
"""

import sys
import os
import mysql.connector

# 从环境变量或配置文件获取数据库配置
def get_db_config():
    """获取数据库配置"""
    # 首先尝试从环境变量
    config = {
        'host': os.getenv('DB_HOST', 'gng-4d77d5e-gngvacation-8888.f.aivencloud.com'),
        'port': int(os.getenv('DB_PORT', '21192')),
        'database': os.getenv('DB_DATABASE', os.getenv('DB_NAME', 'defaultdb')),
        'user': os.getenv('DB_USER', 'avnadmin'),
        'password': os.getenv('DB_PASSWORD', ''),
        'charset': 'utf8mb4',
        'use_unicode': True,
        'autocommit': False,
        'ssl_disabled': False,
        'ssl_verify_cert': False,
        'ssl_verify_identity': False
    }
    
    # 如果环境变量中没有密码，尝试从config.py加载
    if not config['password']:
        try:
            from config import DB_CONFIG
            config.update(DB_CONFIG)
            print("✅ 从config.py文件加载数据库配置")
        except ImportError:
            print("⚠️ 未找到config.py文件")
    else:
        print("✅ 从环境变量加载数据库配置")
    
    return config

def get_db_connection():
    """获取数据库连接"""
    config = get_db_config()
    
    try:
        print(f"🔌 尝试连接数据库: {config['host']}:{config['port']}")
        connection = mysql.connector.connect(**config)
        print("✅ 数据库连接成功")
        return connection
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def hash_password(password):
    """密码哈希"""
    import hashlib
    import secrets
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', 
                                      password.encode('utf-8'), 
                                      salt.encode('utf-8'), 
                                      100000)
    return salt + password_hash.hex()

def create_users_table():
    """创建用户表"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        # 创建用户表
        users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            user_type ENUM('admin', 'property_manager', 'sales', 'accounting', 'owner') NOT NULL,
            department VARCHAR(100) NULL,
            owner_id VARCHAR(20) NULL,
            full_name VARCHAR(100) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            last_login TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            INDEX idx_username (username),
            INDEX idx_email (email),
            INDEX idx_user_type (user_type),
            INDEX idx_department (department),
            INDEX idx_owner_id (owner_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        cursor.execute(users_sql)
        
        # 创建会话表
        sessions_sql = """
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id VARCHAR(255) PRIMARY KEY,
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            ip_address VARCHAR(45),
            user_agent TEXT,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_expires (expires_at),
            INDEX idx_user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        cursor.execute(sessions_sql)
        
        conn.commit()
        print("✅ 用户认证表创建成功")
        return True
        
    except Exception as e:
        print(f"❌ 创建用户表失败: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def create_admin_user(username, email, password, full_name):
    """创建管理员用户"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        
        insert_sql = """
        INSERT INTO users (username, email, password_hash, user_type, full_name)
        VALUES (%s, %s, %s, 'admin', %s)
        """
        
        cursor.execute(insert_sql, (username, email, password_hash, full_name))
        conn.commit()
        
        print(f"✅ 管理员用户 {username} 创建成功")
        return True
        
    except mysql.connector.IntegrityError as e:
        print(f"⚠️ 用户 {username} 已存在")
        return False
    except Exception as e:
        print(f"❌ 创建用户时出错: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def diagnose_login_issue():
    """诊断登录问题"""
    print("🔍 开始诊断Render服务器登录问题...")
    print("="*60)
    
    # 1. 测试数据库连接
    print("\n1️⃣ 测试数据库连接...")
    conn = get_db_connection()
    if not conn:
        print("❌ 数据库连接失败 - 这是主要问题！")
        config = get_db_config()
        print("📋 数据库配置:")
        print(f"   - 主机: {config.get('host', 'unknown')}")
        print(f"   - 端口: {config.get('port', 'unknown')}")
        print(f"   - 数据库: {config.get('database', 'unknown')}")
        print(f"   - 用户: {config.get('user', 'unknown')}")
        print(f"   - 密码设置: {'✅' if config.get('password') else '❌'}")
        return False
    else:
        print("✅ 数据库连接成功")
        conn.close()
    
    # 2. 检查用户表状态
    print("\n2️⃣ 检查用户表状态...")
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # 检查用户表是否存在
            cursor.execute("SHOW TABLES LIKE 'users'")
            table_exists = cursor.fetchone()
            
            if table_exists:
                print("✅ users表存在")
                
                # 查看用户数量
                cursor.execute("SELECT COUNT(*) as count FROM users")
                user_count = cursor.fetchone()['count']
                print(f"📊 用户总数: {user_count}")
                
                # 查看管理员用户
                cursor.execute("SELECT username, user_type, is_active FROM users WHERE user_type = 'admin'")
                admin_users = cursor.fetchall()
                print(f"👑 管理员用户: {len(admin_users)}")
                for admin in admin_users:
                    print(f"   - {admin['username']} (活跃: {admin['is_active']})")
                
                # 查看业主用户数量
                cursor.execute("SELECT COUNT(*) as count FROM users WHERE user_type = 'owner'")
                owner_count = cursor.fetchone()['count']
                print(f"🏠 业主用户: {owner_count}")
                
            else:
                print("❌ users表不存在 - 这是主要问题！")
                
        except Exception as e:
            print(f"❌ 检查用户表失败: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return True

def fix_login_issue():
    """修复登录问题"""
    print("\n🔧 开始修复登录问题...")
    print("="*60)
    
    # 1. 创建用户表
    print("\n1️⃣ 创建/检查用户表...")
    if create_users_table():
        print("✅ 用户表创建/检查成功")
    else:
        print("❌ 用户表创建失败")
        return False
    
    # 2. 创建默认管理员用户
    print("\n2️⃣ 创建默认管理员用户...")
    success = create_admin_user(
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
        success = create_admin_user(username, email, password, full_name)
        if success:
            print(f"✅ 用户 {username} 创建成功")
        else:
            print(f"⚠️ 用户 {username} 已存在或创建失败")
    
    # 4. 验证修复结果
    print("\n4️⃣ 验证修复结果...")
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE username = 'admin'")
            admin_exists = cursor.fetchone()['count'] > 0
            
            if admin_exists:
                print("✅ 修复成功！admin用户已存在于数据库中")
                print("🌐 现在可以在Render应用中使用以下账户登录:")
                print("   - admin / admin123")
                print("   - superadmin / super2025")
                print("   - manager / manager123")
                print("   - pm01 / 123456")
                return True
            else:
                print("❌ 修复失败，admin用户仍不存在")
                return False
        finally:
            cursor.close()
            conn.close()
    
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
        print("\n🔑 现在您可以访问Render应用并使用以下账户登录:")
        print("   - admin / admin123 (默认管理员)")
        print("   - superadmin / super2025 (超级管理员)")
        print("   - manager / manager123 (管理器)")
        print("   - pm01 / 123456 (房产管理员)")
        print("\n🌐 Render应用地址:")
        print("   https://real-estate-management-p7p9.onrender.com/login")
        return True
    else:
        print("\n❌ 修复失败，请检查错误信息")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 