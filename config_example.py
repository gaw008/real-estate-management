# 数据库配置示例
# 复制此文件为 config.py 并填入您的实际数据库信息

DB_CONFIG = {
    'host': 'your-mysql-host.com',
    'port': 3306,  # 或您的MySQL端口
    'database': 'your-database-name',
    'user': 'your-username',
    'password': 'your-password',
    'ssl_disabled': False,  # 如果需要SSL连接
    'ssl_ca': 'path/to/ca-certificate.crt'  # SSL证书路径(如果需要)
}

# Flask应用配置
FLASK_CONFIG = {
    'debug': True,  # 生产环境请设置为False
    'host': '0.0.0.0',
    'port': 8888
}

# 其他配置
APP_CONFIG = {
    'secret_key': 'your-secret-key-here',  # 用于session加密
    'per_page': 12,  # 每页显示的记录数
    'max_search_results': 1000  # 最大搜索结果数
} 