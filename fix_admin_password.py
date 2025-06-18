#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复admin用户密码
"""

import hashlib
import secrets
from config_loader import DB_CONFIG, CA_CERTIFICATE
import mysql.connector

def get_db_connection():
    """获取数据库连接"""
    try:
        # 使用方式2：禁用证书验证（根据之前的测试结果）
        ssl_config = {
            'ssl_disabled': False,
            'ssl_verify_cert': False,
            'ssl_verify_identity': False
        }
        
        config = {**DB_CONFIG, **ssl_config}
        print(f"连接数据库: {config['host']}:{config['port']}")
        connection = mysql.connector.connect(**config)
        print("✅ 数据库连接成功")
        return connection
        
    except Exception as e:
        print(f"❌ 数据库连接错误: {e}")
        return None

def hash_password(password):
    """使用与auth_system.py相同的密码哈希方法"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', 
                                      password.encode('utf-8'), 
                                      salt.encode('utf-8'), 
                                      100000)
    return salt + password_hash.hex()

def fix_admin_password():
    """修复admin用户密码"""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        # 生成正确的密码哈希
        new_password = "admin123"
        password_hash = hash_password(new_password)
        
        print(f"新密码哈希: {password_hash}")
        
        # 更新admin用户密码
        cursor.execute("""
            UPDATE users 
            SET password_hash = %s, updated_at = NOW()
            WHERE username = 'admin'
        """, (password_hash,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print("✅ admin用户密码更新成功")
            
            # 验证更新
            cursor.execute("SELECT username, password_hash FROM users WHERE username = 'admin'")
            result = cursor.fetchone()
            if result:
                print(f"✅ 验证：admin用户密码哈希已更新")
                print(f"   新哈希: {result[1][:50]}...")
        else:
            print("❌ 未找到admin用户")
        
    except Exception as e:
        print(f"❌ 更新密码失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 修复admin用户密码")
    print("=" * 60)
    fix_admin_password() 