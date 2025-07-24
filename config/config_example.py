# -*- coding: utf-8 -*-
"""
数据库和应用配置文件示例
请复制此文件为 config.py 并填写您的数据库凭据。
不要将此文件提交到公共Git仓库。
"""

# ==================== 数据库配置 ====================
# AWS RDS MySQL 数据库配置示例
DB_CONFIG = {
    'host': 'your-db-host.region.rds.amazonaws.com',  # AWS RDS 主机地址
    'port': 3306,                        # MySQL 标准端口
    'database': 'your-database-name',    # 数据库名称
    'user': 'your-username',             # 用户名
    'password': 'your-password',         # 数据库密码
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': False
}

# ==================== CA证书 ====================
# 通常情况下，您不需要修改这里。加载器会自动使用内置证书。
# 如果您有特定的CA证书，可以在这里以字符串形式提供。
CA_CERTIFICATE = """-----BEGIN CERTIFICATE-----
MIIEUDCCArigAwIBAgIUEOQCAGPvYMDs8qbhoENfGVHljkswDQYJKoZIhvcNAQEM
BQAwQDE+MDwGA1UEAww1MDAzZTc1YTQtMmYzMi00NjhlLWI3YTEtYWZlMDJkN2Ew
NWVlIEdFTiAxIFByb2plY3QgQ0EwHhcNMjUwNjEyMTk1OTE2WhcNMzUwNjEwMTk1
OTE2WjBAMT4wPAYDVQQDDDUwMDNlNzVhNC0yZjMyLTQ2OGUtYjdhMS1hZmUwMmQ3
YTA1ZWUgR0VOIDEgUHJvamVjdCBDQTCCAaIwDQYJKoZIhvcNAQEBBQADggGPADCC
AYoCggGBAK1XltvgpRPQrP+kIFY+u1PW+OC0eFHTGLg9jG4FgWC77svwQuALRBjK
9IUiEPfzqwes18YysABPGvs0U+u1hKKjaEKNFuehY1kDEfhH8jAr3YWO3WkUR7qv
8dTDYRheJUHSlVGemmlrXKZZul4RZTS/ukekRb7kjUj2KlhaL7xJiPD0OWw9iO7e
ntRRtc0EUcmIcx4AvX/Qhjb/ORQZ+9AVhLdRXeg+tMu46dtFNffSiJJct777JgbiN
FUuKrTzqauZYMRpHLsix8mcoV3Xg/E+eQ7J15XcYO9STZQGv/np716sQyU8+rpbK
94tHP4y2l6AzWGHkWR6mWx8NR7+LHcUS5bYJhtfr9+7EodC0XxnxlVFmptLCipuF
7XtoPxm7/2oCIarNSk53MMP8Yye0TTey5782FOllbuCzs1wrTacr5QsGBYkl6HTws
1pKH0z8KTQtsQrNenyxrDcp/62ZqLiixBnIOcXhQEvkkSeaQliegFL13hqMTk01
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

# ==================== Flask应用配置 ====================
FLASK_CONFIG = {
    'debug': False,      # 生产环境设为False，开发环境可设为True
    'host': '0.0.0.0',
    'port': 8888
}

# ==================== 其他应用配置 ====================
APP_CONFIG = {
    'secret_key': 'your-secret-key-here',  # 请生成一个安全的密钥
    'per_page': 12
} 