"""
Aiven MySQL 数据库连接配置
此配置已通过连接测试验证
"""

import os
import ssl

# Aiven MySQL 连接配置
AIVEN_DB_CONFIG = {
    'host': 'gng-4d77d5e-gngvacation-8888.f.aivencloud.com',
    'port': 21192,
    'database': 'defaultdb',
    'user': 'avnadmin',
    'password': os.environ.get('DB_PASSWORD', ''),
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': True,
    'ssl_disabled': False,
    'ssl_verify_cert': False,
    'ssl_verify_identity': False,
}

def get_aiven_connection():
    """获取Aiven数据库连接"""
    import mysql.connector
    try:
        connection = mysql.connector.connect(**AIVEN_DB_CONFIG)
        return connection
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None
