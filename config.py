import os

# 数据库配置 - 使用环境变量存储敏感信息
# 设置环境变量示例:
# export DB_HOST="your-host"
# export DB_PASSWORD="your-password"

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'gng-4d77d5e-gngvacation-8888.f.aivencloud.com'),
    'port': int(os.environ.get('DB_PORT', '28888')),
    'database': os.environ.get('DB_NAME', 'defaultdb'),
    'user': os.environ.get('DB_USER', 'avnadmin'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'ssl_disabled': False,
    'ssl_verify_cert': False,
    'ssl_verify_identity': False
}

# Flask应用配置
FLASK_CONFIG = {
    'debug': os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
    'host': os.environ.get('FLASK_HOST', '0.0.0.0'),
    'port': int(os.environ.get('FLASK_PORT', '8888'))
}

# 其他配置
APP_CONFIG = {
    'secret_key': os.environ.get('APP_SECRET_KEY', 'dev-secret-key-change-in-production'),
    'per_page': int(os.environ.get('APP_PER_PAGE', '12')),
    'max_search_results': int(os.environ.get('APP_MAX_SEARCH_RESULTS', '1000'))
} 