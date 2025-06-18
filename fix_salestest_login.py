#!/usr/bin/env python3
"""
修复salestest用户登录问题
主要解决密码哈希算法不一致的问题
"""

from auth_system import auth_system
import bcrypt

def fix_salestest_user():
    """修复salestest用户的登录问题"""
    print("🔧 修复salestest用户登录问题")
    print("=" * 50)
    
    conn = auth_system.get_db_connection()
    if not conn:
        print("❌ 数据库连接失败")
        print("请先解决数据库连接问题，然后重新运行此脚本")
        return False
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. 检查用户是否存在
        cursor.execute("""
            SELECT id, username, user_type, is_active, password_hash 
            FROM users WHERE username = %s
        """, ('salestest',))
        
        user = cursor.fetchone()
        if not user:
            print("❌ 用户salestest不存在")
            return False
        
        print(f"✅ 找到用户: {user['username']}")
        print(f"用户ID: {user['id']}")
        print(f"用户类型: {user['user_type']}")
        print(f"激活状态: {user['is_active']}")
        
        # 2. 检查密码哈希格式
        current_hash = user['password_hash']
        print(f"当前密码哈希长度: {len(current_hash)}")
        print(f"当前密码哈希前20位: {current_hash[:20]}...")
        
        # 3. 生成新的bcrypt密码哈希
        new_password = 'sales123456'
        salt = bcrypt.gensalt()
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt)
        new_hash_str = new_hash.decode('utf-8')
        
        print(f"新的bcrypt哈希长度: {len(new_hash_str)}")
        print(f"新的bcrypt哈希前20位: {new_hash_str[:20]}...")
        
        # 4. 更新用户密码和激活状态
        cursor.execute("""
            UPDATE users 
            SET password_hash = %s, is_active = 1 
            WHERE username = %s
        """, (new_hash_str, 'salestest'))
        
        conn.commit()
        print("✅ 密码哈希已更新为bcrypt格式")
        print("✅ 用户已激活")
        
        # 5. 验证修复结果
        print("\n🧪 验证修复结果...")
        
        # 测试密码验证
        test_result = bcrypt.checkpw(new_password.encode('utf-8'), new_hash_str.encode('utf-8'))
        print(f"密码验证测试: {'✅ 通过' if test_result else '❌ 失败'}")
        
        # 测试认证系统
        auth_user = auth_system.authenticate_user('salestest', 'sales123456')
        if auth_user:
            print("✅ 认证系统测试通过")
            print(f"认证返回: {auth_user['username']}, 类型: {auth_user['user_type']}")
        else:
            print("❌ 认证系统测试失败")
        
        print("\n🎉 修复完成！")
        print("现在可以使用以下信息登录：")
        print("用户名: salestest")
        print("密码: sales123456")
        print("用户类型: admin")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def check_all_users_password_format():
    """检查所有用户的密码格式"""
    print("\n🔍 检查所有用户的密码格式")
    print("=" * 30)
    
    conn = auth_system.get_db_connection()
    if not conn:
        print("❌ 数据库连接失败")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT username, user_type, password_hash, is_active
            FROM users 
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        for user in users:
            hash_format = "bcrypt" if user['password_hash'].startswith('$2b$') else "其他格式"
            status = "激活" if user['is_active'] else "未激活"
            print(f"{user['username']:12} | {user['user_type']:8} | {hash_format:8} | {status}")
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # 修复salestest用户
    success = fix_salestest_user()
    
    if success:
        # 检查所有用户状态
        check_all_users_password_format()
    else:
        print("\n💡 如果数据库连接问题，请：")
        print("1. 检查Aiven数据库服务状态")
        print("2. 验证连接信息是否正确")
        print("3. 数据库连接恢复后重新运行此脚本") 