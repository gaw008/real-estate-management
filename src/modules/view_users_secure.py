#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户数据查看工具 - 安全版本
User Data Viewer - Secure Version
"""

import sys
import os
import tempfile
import mysql.connector
from datetime import datetime

def get_database_connection():
    """获取数据库连接 - 使用环境变量或配置文件"""
    
    # 首先尝试从环境变量获取配置
    config = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'database': os.getenv('DB_DATABASE'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'ssl_disabled': False,
        'ssl_verify_cert': True,
        'charset': 'utf8mb4',
        'use_unicode': True
    }
    
    # 如果环境变量不完整，尝试从配置加载器获取
    if not all([config['host'], config['database'], config['user'], config['password']]):
        try:
            from core.config_loader import DB_CONFIG, CA_CERTIFICATE
            if DB_CONFIG:
                config.update(DB_CONFIG)
                print("✅ 使用config_loader中的数据库配置")
            else:
                print("❌ 错误：无法加载数据库配置")
                print("\n请选择以下方式之一配置数据库连接：")
                print("1. 设置环境变量：")
                print("   export DB_HOST='your-host'")
                print("   export DB_DATABASE='your-database'")
                print("   export DB_USER='your-username'")
                print("   export DB_PASSWORD='your-password'")
                print("\n2. 确保config_loader.py中有正确的配置")
                return None
        except ImportError:
            print("❌ 错误：无法导入配置加载器")
            return None
    
    # 获取CA证书
    ca_cert = None
    try:
        from core.config_loader import CA_CERTIFICATE
        ca_cert = CA_CERTIFICATE
    except ImportError:
        # 使用默认的Aiven CA证书
        ca_cert = """-----BEGIN CERTIFICATE-----
MIIEUDCCArigAwIBAgIUEOQCAGPvYMDs8qbhoENfGVHljkswDQYJKoZIhvcNAQEM
BQAwQDE+MDwGA1UEAww1MDAzZTc1YTQtMmYzMi00NjhlLWI3YTEtYWZlMDJkN2Ew
NWVlIEdFTiAxIFByb2plY3QgQ0EwHhcNMjUwNjEyMTk1OTE2WhcNMzUwNjEwMTk1
OTE2WjBAMT4wPAYDVQQDDDUwMDNlNzVhNC0yZjMyLTQ2OGUtYjdhMS1hZmUwMmQ3
YTA1ZWUgR0VOIDEgUHJvamVjdCBDQTCCAaIwDQYJKoZIhvcNAQEBBQADggGPADCC
AYoCggGBAK1XltvgpRPQrP+kIFY+u1PW+OC0eFHTGLg9jG4FgWC77svwQuALRBjK
9IUiEPfzqwes18YysABPGvs0U+u1hKKjaEKNFuehY1kDEfhH8jAr3YWO3WkUR7qv
8dTDYRheJUHSlVGemmlrXKZZul4RZTS/ukekRb7kjUj2KlhaL7xJiPD0OWw9iO7e
tRRtc0EUcmIcx4AvX/Qhjb/ORQZ+9AVhLdRXeg+tMu46dtFNffSiJJct777JgbiN
FUuKrTzqauZYMRpHLsix8mcoV3Xg/E+eQ7J15XcYO9STZQGv/np716sQyU8+rpbK
94tHP4y2l6AzWGHkWR6mWx8NR7+LHcUS5bYJhtfr9+7EodC0XxnxlVFmptLCipuF
7XtoPxm7/2oCIarNSk53MMP8Yye0TTey5782FOllbuCzs1wrTacr5QsGBYkl6HTw
s1pKH0z8KTQtsQrNenyxrDcp/62ZqLiixBnIOcXhQEvkkSeaQliegFL13hqMTk01
Y6O6hAcj/wIDAQABo0IwQDAdBgNVHQ4EFgQUJABbJ4em80Y6ONdnSXsGy2ZAsCcw
EgYDVR0TAQH/BAgwBgEB/wIBADALBgNVHQ8EBAMCAQYwDQYJKoZIhvcNAQEMBQAD
ggGBAJWTOdb3hMg9QFtzU4GoZp7RutOZHtczpj/HlnpMWXp8QHfKpXcTQoLWyBM7
klJlX84s3RxvBu3C7VFIDbpEvGTlyZeXCNyXDsiXznsPLK48HcVL17Pv+VcwlVRc
lmFSUv92vIlHX7rudfdF4UbY+5Q2kUdAW/ajb/t0HIFBTKxGcAbgzmAS7aNR2N7t
fQ9hNL0ZLQf/qO+g3JXPIvcIkjuZ3oevWMHQSqZFcVJoBelENgiyr9OOO2PmvOxD
T/FTNzakBdDEuclx2y7mN9AqFgwQT6bmVoHgi6C6LucDneMZ5ENI1734FBNiqHaO
ywDLidkGeYq8sBPVd57S5cXGjj92qsr4ZcokZMm/HYzGvJUxZZV0sq1yYmk4P3qW
3+9F/IBv3SMPsSQmCsP5SzEgWquI++D/TICe9c7hnGCIW6gg3Gk/7D6Tt+zpSmWo
MDZS8Z9MMljZdJFjlNDtc10Fb2sleLB+yOr8emwzb0nhgFL6EGX9MmJzJVlsJOIq
Xtdm+g==
-----END CERTIFICATE-----"""
    
    try:
        # 设置SSL证书
        if ca_cert:
            ca_cert_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem')
            ca_cert_file.write(ca_cert)
            ca_cert_file.close()
            config['ssl_ca'] = ca_cert_file.name
        
        # 连接数据库
        connection = mysql.connector.connect(**config)
        return connection
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def view_all_users():
    """查看所有用户数据"""
    print("👥 查看所有用户数据")
    print("=" * 60)
    
    conn = get_database_connection()
    if not conn:
        return
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 首先检查users表是否存在
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            print("❌ 用户表(users)不存在")
            print("📋 可用的表:")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            for table in tables:
                print(f"   - {table[0]}")
            return
        
        # 查询所有用户
        query_sql = """
            SELECT u.id, u.username, u.email, u.user_type, u.owner_id, 
                   u.full_name, u.is_active, u.last_login, u.created_at,
                   om.name as owner_master_name, om.phone as owner_phone
            FROM users u
            LEFT JOIN owners om ON u.owner_id = om.owner_id
            ORDER BY u.user_type, u.username
        """
        
        cursor.execute(query_sql)
        users = cursor.fetchall()
        
        if not users:
            print("📭 没有找到任何用户")
            return
        
        print(f"📊 总共找到 {len(users)} 个用户\n")
        
        # 按用户类型分组显示
        admin_users = [u for u in users if u['user_type'] == 'admin']
        owner_users = [u for u in users if u['user_type'] == 'owner']
        
        # 显示管理员用户
        if admin_users:
            print("👑 管理员用户:")
            print("-" * 40)
            for user in admin_users:
                status = "✅ 活跃" if user['is_active'] else "❌ 禁用"
                last_login = user['last_login'].strftime('%Y-%m-%d %H:%M') if user['last_login'] else '从未登录'
                
                print(f"ID: {user['id']}")
                print(f"用户名: {user['username']}")
                print(f"姓名: {user['full_name']}")
                print(f"邮箱: {user['email']}")
                print(f"状态: {status}")
                print(f"最后登录: {last_login}")
                print(f"创建时间: {user['created_at'].strftime('%Y-%m-%d %H:%M')}")
                print("-" * 40)
        
        # 显示业主用户（只显示前10个，避免输出过长）
        if owner_users:
            print(f"\n🏠 业主用户 ({len(owner_users)}个，显示前10个):")
            print("-" * 40)
            for user in owner_users[:10]:
                status = "✅ 活跃" if user['is_active'] else "❌ 禁用"
                last_login = user['last_login'].strftime('%Y-%m-%d %H:%M') if user['last_login'] else '从未登录'
                
                print(f"ID: {user['id']}")
                print(f"用户名: {user['username']}")
                print(f"姓名: {user['full_name']}")
                print(f"业主ID: {user['owner_id']}")
                if user['owner_master_name']:
                    print(f"业主资料姓名: {user['owner_master_name']}")
                print(f"邮箱: {user['email']}")
                print(f"状态: {status}")
                print(f"最后登录: {last_login}")
                print("-" * 40)
            
            if len(owner_users) > 10:
                print(f"... 还有 {len(owner_users) - 10} 个业主用户")
        
        # 统计信息
        print(f"\n📈 统计信息:")
        print(f"管理员用户: {len(admin_users)}")
        print(f"业主用户: {len(owner_users)}")
        active_users = len([u for u in users if u['is_active']])
        print(f"活跃用户: {active_users}")
        print(f"禁用用户: {len(users) - active_users}")
        
        # 最近登录用户
        recent_logins = [u for u in users if u['last_login']]
        if recent_logins:
            recent_logins.sort(key=lambda x: x['last_login'], reverse=True)
            print(f"\n🕐 最近登录的5个用户:")
            for user in recent_logins[:5]:
                print(f"  {user['username']} ({user['full_name']}) - {user['last_login'].strftime('%Y-%m-%d %H:%M')}")
        
    except Exception as e:
        print(f"❌ 查询用户数据失败: {e}")
    finally:
        cursor.close()
        conn.close()

def view_database_tables():
    """查看数据库中的所有表"""
    print("\n📋 数据库表结构")
    print("=" * 60)
    
    conn = get_database_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        # 获取所有表
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 数据库中共有 {len(tables)} 个表:\n")
        
        for table in tables:
            # 获取表的记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"📋 表名: {table} ({count} 条记录)")
        
    except Exception as e:
        print(f"❌ 查询表结构失败: {e}")
    finally:
        cursor.close()
        conn.close()

def search_user(search_term):
    """搜索特定用户"""
    print(f"🔍 搜索用户: {search_term}")
    print("=" * 60)
    
    conn = get_database_connection()
    if not conn:
        return
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 检查users表是否存在
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            print("❌ 用户表(users)不存在")
            return
        
        # 搜索用户
        query_sql = """
            SELECT u.*, om.name as owner_master_name, om.phone as owner_phone
            FROM users u
            LEFT JOIN owners om ON u.owner_id = om.owner_id
            WHERE u.username LIKE %s OR u.email LIKE %s OR u.full_name LIKE %s
            ORDER BY u.username
        """
        
        search_pattern = f'%{search_term}%'
        cursor.execute(query_sql, (search_pattern, search_pattern, search_pattern))
        users = cursor.fetchall()
        
        if not users:
            print(f"📭 没有找到匹配 '{search_term}' 的用户")
            return
        
        print(f"📊 找到 {len(users)} 个匹配的用户\n")
        
        for user in users:
            status = "✅ 活跃" if user['is_active'] else "❌ 禁用"
            last_login = user['last_login'].strftime('%Y-%m-%d %H:%M') if user['last_login'] else '从未登录'
            
            print(f"ID: {user['id']}")
            print(f"用户名: {user['username']}")
            print(f"姓名: {user['full_name']}")
            print(f"类型: {user['user_type']}")
            if user['owner_id']:
                print(f"业主ID: {user['owner_id']}")
            print(f"邮箱: {user['email']}")
            print(f"状态: {status}")
            print(f"最后登录: {last_login}")
            print("-" * 40)
        
    except Exception as e:
        print(f"❌ 搜索用户失败: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🚀 用户数据查看工具 (安全版本)")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'tables':
            # 查看数据库表结构
            view_database_tables()
        else:
            # 搜索用户
            search_user(sys.argv[1])
    else:
        # 显示所有用户
        view_all_users()
    
    print("\n💡 使用说明:")
    print("python3 view_users_secure.py           # 查看所有用户")
    print("python3 view_users_secure.py tables    # 查看数据库表结构")
    print("python3 view_users_secure.py 张三      # 搜索特定用户")
    print("python3 view_users_secure.py admin     # 搜索管理员")
    print("\n🔒 安全提示:")
    print("请设置环境变量或确保config_loader.py中有正确的数据库配置") 