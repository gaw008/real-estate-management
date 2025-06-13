#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加载器 - 从环境变量或配置文件中安全加载配置
Configuration Loader - Safely load configuration from environment variables or config file
"""

import os
import sys
from typing import Dict, Any

def load_database_config() -> Dict[str, Any]:
    """
    加载数据库配置
    优先级：环境变量 > config.py文件 > 默认值
    """
    config = {}
    
    # 尝试从环境变量加载
    config['host'] = os.getenv('DB_HOST', 'localhost')
    config['port'] = int(os.getenv('DB_PORT', '3306'))
    config['database'] = os.getenv('DB_DATABASE', 'defaultdb')
    config['user'] = os.getenv('DB_USER', 'root')
    config['password'] = os.getenv('DB_PASSWORD', '')
    config['ssl_disabled'] = os.getenv('DB_SSL_DISABLED', 'False').lower() == 'true'
    config['ssl_verify_cert'] = os.getenv('DB_SSL_VERIFY_CERT', 'True').lower() == 'true'
    config['charset'] = os.getenv('DB_CHARSET', 'utf8mb4')
    config['use_unicode'] = os.getenv('DB_USE_UNICODE', 'True').lower() == 'true'
    config['autocommit'] = os.getenv('DB_AUTOCOMMIT', 'False').lower() == 'true'
    
    # 如果环境变量中没有密码，尝试从config.py加载
    if not config['password']:
        try:
            from config import DB_CONFIG
            config.update(DB_CONFIG)
            print("✅ 从config.py文件加载数据库配置")
        except ImportError:
            print("⚠️  警告：未找到config.py文件，且环境变量中未设置数据库密码")
            print("请创建config.py文件或设置环境变量DB_PASSWORD")
            return None
    else:
        print("✅ 从环境变量加载数据库配置")
    
    return config

def load_ca_certificate() -> str:
    """
    加载CA证书
    优先级：环境变量 > config.py文件 > 文件路径
    """
    # 尝试从环境变量加载
    ca_cert = os.getenv('DB_CA_CERTIFICATE')
    if ca_cert:
        print("✅ 从环境变量加载CA证书")
        return ca_cert
    
    # 尝试从config.py加载
    try:
        from config import CA_CERTIFICATE
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
    
    print("⚠️  警告：未找到CA证书")
    return None

def load_flask_config() -> Dict[str, Any]:
    """加载Flask配置"""
    config = {
        'debug': os.getenv('FLASK_DEBUG', 'True').lower() == 'true',
        'host': os.getenv('FLASK_HOST', '0.0.0.0'),
        'port': int(os.getenv('FLASK_PORT', '8888'))
    }
    
    # 尝试从config.py加载
    try:
        from config import FLASK_CONFIG
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
        from config import APP_CONFIG
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