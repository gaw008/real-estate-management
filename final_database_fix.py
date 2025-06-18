#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终数据库连接修复
确保Web应用能够正确连接数据库
"""

import mysql.connector
from config_loader import DB_CONFIG, CA_CERTIFICATE

def test_all_connection_methods():
    """测试所有可能的连接方法"""
    print("=" * 60)
    print("🔧 最终数据库连接修复测试")
    print("=" * 60)
    
    # 测试不同的SSL配置
    ssl_configs = [
        # 方式1：使用CA证书
        ("使用CA证书", {
            'ssl_disabled': False,
            'ssl_verify_cert': True,
            'ssl_verify_identity': False,
            'ssl_ca': CA_CERTIFICATE
        }),
        # 方式2：禁用证书验证
        ("禁用证书验证", {
            'ssl_disabled': False,
            'ssl_verify_cert': False,
            'ssl_verify_identity': False
        }),
        # 方式3：完全禁用SSL
        ("完全禁用SSL", {
            'ssl_disabled': True
        })
    ]
    
    working_config = None
    
    for name, ssl_config in ssl_configs:
        try:
            config = {**DB_CONFIG, **ssl_config}
            print(f"\n🔍 测试{name}...")
            print(f"   配置: {ssl_config}")
            
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            
            # 测试基本查询
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            # 测试用户表查询
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            print(f"✅ {name}连接成功！")
            print(f"   用户数量: {user_count}")
            
            if not working_config:
                working_config = (name, ssl_config)
                
        except Exception as e:
            print(f"❌ {name}连接失败: {e}")
    
    if working_config:
        print(f"\n🎯 推荐配置: {working_config[0]}")
        print(f"   配置详情: {working_config[1]}")
        return working_config[1]
    else:
        print("\n❌ 所有连接方式都失败")
        return None

def update_web_app_config(working_ssl_config):
    """更新Web应用配置"""
    if not working_ssl_config:
        print("❌ 没有可用的数据库配置")
        return
    
    print(f"\n🔧 更新Web应用数据库配置...")
    
    # 读取当前的real_estate_web.py
    with open('real_estate_web.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并替换数据库连接配置
    old_pattern = '''ssl_configs = [
            # 方式1：使用CA证书
            {
                'ssl_disabled': False,
                'ssl_verify_cert': True,
                'ssl_verify_identity': False,
                'ssl_ca': CA_CERTIFICATE
            },
            # 方式2：禁用证书验证
            {
                'ssl_disabled': False,
                'ssl_verify_cert': False,
                'ssl_verify_identity': False
            },
            # 方式3：完全禁用SSL（不推荐，但作为备用）
            {
                'ssl_disabled': True
            }
        ]'''
    
    new_pattern = f'''ssl_configs = [
            # 优先使用经过验证的配置
            {working_ssl_config},
            # 方式2：禁用证书验证（备用）
            {{
                'ssl_disabled': False,
                'ssl_verify_cert': False,
                'ssl_verify_identity': False
            }},
            # 方式3：完全禁用SSL（最后备用）
            {{
                'ssl_disabled': True
            }}
        ]'''
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        
        with open('real_estate_web.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Web应用配置已更新")
        return True
    else:
        print("❌ 未找到配置模式，手动更新失败")
        return False

if __name__ == "__main__":
    working_config = test_all_connection_methods()
    if working_config:
        update_web_app_config(working_config)
        print("\n🎉 数据库连接修复完成！")
        print("请重启Web应用以应用新配置：")
        print("   python3 real_estate_web.py")
    else:
        print("\n❌ 无法修复数据库连接问题") 