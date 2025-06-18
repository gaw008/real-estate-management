#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接测试和诊断工具
Database Connection Test and Diagnostic Tool
"""

import mysql.connector
import os
import tempfile
import ssl
import socket
from datetime import datetime

def test_network_connectivity():
    """测试网络连通性"""
    print("🔍 测试网络连通性...")
    
    host = "gng-4d77d5e-gngvacation-8888.f.aivencloud.com"
    port = 21192
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ 网络连接正常：{host}:{port}")
            return True
        else:
            print(f"❌ 网络连接失败：{host}:{port} (错误码: {result})")
            return False
    except Exception as e:
        print(f"❌ 网络测试异常：{e}")
        return False

def test_ssl_connectivity():
    """测试SSL连接"""
    print("\n🔍 测试SSL连接...")
    
    host = "gng-4d77d5e-gngvacation-8888.f.aivencloud.com"
    port = 21192
    
    try:
        # 创建SSL上下文
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # 测试SSL连接
        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                print(f"✅ SSL连接成功")
                print(f"   协议版本: {ssock.version()}")
                print(f"   加密套件: {ssock.cipher()}")
                return True
                
    except Exception as e:
        print(f"❌ SSL连接失败：{e}")
        return False

def get_ca_certificate():
    """获取内置CA证书"""
    return """-----BEGIN CERTIFICATE-----
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

def test_database_connection():
    """测试数据库连接"""
    print("\n🔍 测试数据库连接...")
    
    # 获取配置
    config = {
        'host': 'gng-4d77d5e-gngvacation-8888.f.aivencloud.com',
        'port': 21192,
        'database': 'defaultdb',
        'user': 'avnadmin',
        'password': os.environ.get('DB_PASSWORD', ''),  # 从环境变量获取密码
        'ssl_disabled': False,
        'ssl_verify_cert': False,
        'ssl_verify_identity': False
    }
    
    print(f"📋 连接参数：")
    print(f"   主机: {config['host']}")
    print(f"   端口: {config['port']}")
    print(f"   数据库: {config['database']}")
    print(f"   用户: {config['user']}")
    print(f"   密码: {'已设置' if config['password'] else '❌ 未设置'}")
    
    if not config['password']:
        print("\n❌ 错误：未设置数据库密码")
        print("请设置环境变量 DB_PASSWORD：")
        print("export DB_PASSWORD='your-actual-password'")
        return False
    
    # 测试连接
    try:
        print(f"\n🔄 尝试连接数据库...")
        connection = mysql.connector.connect(**config)
        
        print("✅ 数据库连接成功！")
        
        # 获取数据库信息
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"   MySQL版本: {version[0]}")
        
        cursor.execute("SELECT DATABASE()")
        db = cursor.fetchone()
        print(f"   当前数据库: {db[0]}")
        
        cursor.execute("SELECT USER()")
        user = cursor.fetchone()
        print(f"   当前用户: {user[0]}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ 数据库连接失败：{e}")
        
        # 分析错误类型
        if "Access denied" in str(e):
            print("\n🔍 错误分析：认证失败")
            print("可能原因：")
            print("1. 密码错误或已过期")
            print("2. 用户名错误")
            print("3. 数据库用户权限被撤销")
            print("4. IP地址未在白名单中")
            
        elif "Can't connect" in str(e):
            print("\n🔍 错误分析：无法连接")
            print("可能原因：")
            print("1. 网络连接问题")
            print("2. 防火墙阻止")
            print("3. 服务器不可用")
            
        elif "SSL" in str(e):
            print("\n🔍 错误分析：SSL连接问题")
            print("可能原因：")
            print("1. SSL证书问题")
            print("2. SSL配置错误")
        
        return False
    
    except Exception as e:
        print(f"❌ 其他错误：{e}")
        return False

def test_with_ca_certificate():
    """使用CA证书测试连接"""
    print("\n🔍 使用CA证书测试连接...")
    
    # 创建临时CA证书文件
    ca_cert = get_ca_certificate()
    ca_cert_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem')
    ca_cert_file.write(ca_cert)
    ca_cert_file.close()
    
    config = {
        'host': 'gng-4d77d5e-gngvacation-8888.f.aivencloud.com',
        'port': 21192,
        'database': 'defaultdb',
        'user': 'avnadmin',
        'password': os.environ.get('DB_PASSWORD', ''),
        'ssl_ca': ca_cert_file.name,
        'ssl_disabled': False,
        'ssl_verify_cert': True,
        'ssl_verify_identity': False
    }
    
    if not config['password']:
        print("❌ 跳过：未设置密码")
        os.unlink(ca_cert_file.name)
        return False
    
    try:
        connection = mysql.connector.connect(**config)
        print("✅ 使用CA证书连接成功！")
        connection.close()
        result = True
    except Exception as e:
        print(f"❌ 使用CA证书连接失败：{e}")
        result = False
    
    # 清理临时文件
    os.unlink(ca_cert_file.name)
    return result

def main():
    """主函数"""
    print("=" * 60)
    print("🔧 Aiven MySQL 数据库连接诊断工具")
    print("=" * 60)
    print(f"⏰ 测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试网络连通性
    network_ok = test_network_connectivity()
    
    # 测试SSL连接
    ssl_ok = test_ssl_connectivity()
    
    # 测试数据库连接
    db_ok = test_database_connection()
    
    # 测试CA证书连接
    ca_ok = test_with_ca_certificate()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 诊断结果总结：")
    print("=" * 60)
    print(f"网络连通性: {'✅ 正常' if network_ok else '❌ 失败'}")
    print(f"SSL连接:   {'✅ 正常' if ssl_ok else '❌ 失败'}")
    print(f"数据库连接: {'✅ 正常' if db_ok else '❌ 失败'}")
    print(f"CA证书连接: {'✅ 正常' if ca_ok else '❌ 失败'}")
    
    if not any([network_ok, ssl_ok, db_ok]):
        print("\n🚨 严重问题：所有连接测试都失败")
        print("建议检查：")
        print("1. 网络连接是否正常")
        print("2. Aiven服务是否可用")
        print("3. 防火墙设置")
    elif network_ok and ssl_ok and not db_ok:
        print("\n⚠️ 认证问题：网络和SSL正常，但数据库认证失败")
        print("建议检查：")
        print("1. 数据库密码是否正确")
        print("2. 用户权限是否有效")
        print("3. IP白名单设置")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 