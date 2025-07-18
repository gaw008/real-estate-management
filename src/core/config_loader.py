#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加载器 - 从环境变量或配置文件中安全加载配置
Configuration Loader - Safely load configuration from environment variables or config file
"""

import os
import sys
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def load_database_config() -> Dict[str, Any]:
    """
    加载数据库配置
    优先级：config.py文件 > 环境变量 > 默认值
    """
    config = {}
    
    # 优先尝试从config.py加载
    try:
        import sys
        import os
        # 添加项目根目录到路径
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from config.config import DB_CONFIG
        config.update(DB_CONFIG)
        print("✅ 从config.py文件加载数据库配置")
        # 如果密码有效，直接返回配置
        if config.get('password') and config.get('password') != 'YOUR_AIVEN_PASSWORD':
            return config
    except ImportError:
        print("ℹ️ 未找到config.py文件，将尝试从环境变量加载。")

    # 如果config.py中信息不完整或文件不存在，再尝试从环境变量加载
    print(" pokušavam učitati iz varijabli okruženja...")
    config['host'] = os.getenv('DB_HOST', config.get('host', 'localhost'))
    config['port'] = int(os.getenv('DB_PORT', config.get('port', 3306)))
    config['database'] = os.getenv('DB_DATABASE', config.get('database', 'defaultdb'))
    config['user'] = os.getenv('DB_USER', config.get('user', 'root'))
    config['password'] = os.getenv('DB_PASSWORD', config.get('password', ''))
    
    if os.getenv('DB_PASSWORD'):
        print("✅ 从环境变量加载数据库配置")
    
    # 最终检查
    if not config.get('password') or config.get('password') == 'YOUR_AIVEN_PASSWORD':
        print("❌ 错误：数据库密码未在config.py或环境变量中有效设置。")
        return None
        
    return config

def load_ca_certificate() -> str:
    """
    加载CA证书
    优先级：环境变量 > config.py文件 > 内置证书
    """
    # 尝试从环境变量加载
    ca_cert = os.getenv('DB_CA_CERTIFICATE')
    if ca_cert:
        print("✅ 从环境变量加载CA证书")
        return ca_cert
    
    # 尝试从config.py加载
    try:
        import sys
        # 添加项目根目录到路径
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from config.config import CA_CERTIFICATE
        print("✅ 从config.py文件加载CA证书")
        return CA_CERTIFICATE
    except ImportError:
        pass
    
    # 尝试从文件加载
    ca_cert_file = os.getenv('DB_CA_CERT_FILE', 'ca-certificate.crt')
    if os.path.exists(ca_cert_file):
        with open(ca_cert_file, 'r') as f:
            print(f"✅ 从文件{ca_cert_file}加载CA证书")
            return f.read()
    
    # 使用内置的Aiven CA证书（用于演示）
    builtin_cert = """-----BEGIN CERTIFICATE-----
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
    print("✅ 使用内置CA证书")
    return builtin_cert

def load_flask_config() -> Dict[str, Any]:
    """加载Flask配置"""
    config = {
        'debug': os.getenv('FLASK_DEBUG', 'True').lower() == 'true',
        'host': os.getenv('FLASK_HOST', '0.0.0.0'),
        'port': int(os.getenv('FLASK_PORT', '8888'))
    }
    
    # 尝试从config.py加载
    try:
        import sys
        # 添加项目根目录到路径
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from config.config import FLASK_CONFIG
        config.update(FLASK_CONFIG)
    except ImportError:
        pass
    
    return config

def load_app_config() -> Dict[str, Any]:
    """加载应用配置"""
    config = {
        'secret_key': os.getenv('APP_SECRET_KEY', 'default-secret-key-change-in-production'),
        'per_page': int(os.getenv('APP_PER_PAGE', '12')),
        'max_search_results': int(os.getenv('APP_MAX_SEARCH_RESULTS', '1000'))
    }
    
    # 尝试从config.py加载
    try:
        import sys
        # 添加项目根目录到路径
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from config.config import APP_CONFIG
        config.update(APP_CONFIG)
    except ImportError:
        pass
    
    return config

# 导出配置
DB_CONFIG = load_database_config()
CA_CERTIFICATE = load_ca_certificate()
FLASK_CONFIG = load_flask_config()
APP_CONFIG = load_app_config()

# 验证必要配置
if DB_CONFIG is None:
    print("❌ 错误：无法加载数据库配置")
    print("\n请选择以下方式之一配置数据库连接：")
    print("1. 设置环境变量：")
    print("   export DB_HOST='your-host'")
    print("   export DB_PORT='your-port'")
    print("   export DB_DATABASE='your-database'")
    print("   export DB_USER='your-username'")
    print("   export DB_PASSWORD='your-password'")
    print("\n2. 创建config.py文件（参考config_example.py）")
    sys.exit(1)

if CA_CERTIFICATE is None:
    print("⚠️  警告：未找到CA证书，SSL连接可能失败") 