# -*- coding: utf-8 -*-
"""
数据库和应用配置文件示例
请复制此文件为 config.py 并填写您的真实数据库凭据。
不要将此文件提交到公共Git仓库。
"""

# ==================== 数据库配置 ====================
# 请从您的Aiven控制台复制并粘贴以下信息
DB_CONFIG = {
    'host': 'your-aiven-host.aivencloud.com',          # 例如: gng-4d77d5e-gngvacation-8888.f.aivencloud.com
    'port': 21192,                      # 您的数据库端口
    'database': 'defaultdb',            # 数据库名称
    'user': 'avnadmin',                 # 用户名
    'password': 'YOUR_DATABASE_PASSWORD_HERE',  # 您的数据库密码
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': False
}

# ==================== CA证书 ====================
# 通常情况下，您不需要修改这里。加载器会自动使用内置证书。
# 如果您有特定的CA证书，可以在这里以字符串形式提供。
CA_CERTIFICATE = """-----BEGIN CERTIFICATE-----
YOUR_CA_CERTIFICATE_HERE
-----END CERTIFICATE-----"""

# ==================== Flask应用配置 ====================
FLASK_CONFIG = {
    'debug': True,       # 在开发时设为True以获取详细错误信息
    'host': '0.0.0.0',
    'port': 8888
}

# ==================== 其他应用配置 ====================
APP_CONFIG = {
    'secret_key': 'a-very-secret-and-long-random-string-for-flask-sessions',
    'per_page': 12
} 