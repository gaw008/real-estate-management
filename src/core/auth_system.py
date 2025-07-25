#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证系统
User Authentication System
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import session, request, redirect, url_for, flash
from .config_loader import DB_CONFIG
import mysql.connector

class AuthSystem:
    def __init__(self):
        self.session_timeout = 3600  # 1小时超时
    
    def get_db_connection(self):
        """获取数据库连接"""
        try:
            from .config_loader import DB_CONFIG, CA_CERTIFICATE
            
            # 尝试多种SSL配置方式（已测试成功的顺序）
            ssl_configs = [
                # 方式1：禁用证书验证（已测试成功）
                {
                    'ssl_disabled': False,
                    'ssl_verify_cert': False,
                    'ssl_verify_identity': False
                },
                # 方式2：使用CA证书
                {
                    'ssl_disabled': False,
                    'ssl_verify_cert': True,
                    'ssl_verify_identity': False,
                    'ssl_ca': CA_CERTIFICATE
                },
                # 方式3：完全禁用SSL（不推荐，但作为备用）
                {
                    'ssl_disabled': True
                }
            ]
            
            for i, ssl_config in enumerate(ssl_configs, 1):
                try:
                    config = {**DB_CONFIG, **ssl_config}
                    connection = mysql.connector.connect(**config)
                    return connection
                except Exception as ssl_e:
                    if i == len(ssl_configs):  # 最后一次尝试失败
                        print(f"数据库连接错误: {ssl_e}")
                    continue
            
            return None
        except Exception as e:
            print(f"数据库连接错误: {e}")
            return None
    
    def create_users_table(self):
        """创建用户表"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            # 先删除旧表（如果存在），以确保结构最新
            # 必须先删除有外键依赖的表
            cursor.execute("DROP TABLE IF EXISTS password_reset_tokens;")
            cursor.execute("DROP TABLE IF EXISTS password_change_log;")
            cursor.execute("DROP TABLE IF EXISTS property_assignments;")
            cursor.execute("DROP TABLE IF EXISTS user_sessions;")
            cursor.execute("DROP TABLE IF EXISTS users;")
            print("🗑️ 已移除旧的密码管理, 房产分配, 用户和会话表 (如果存在)")

            # 创建用户表（暂时不使用外键约束）
            users_sql = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                user_type ENUM('admin', 'property_manager', 'sales', 'accounting', 'owner') NOT NULL,
                department VARCHAR(100) NULL,
                owner_id VARCHAR(20) NULL,
                full_name VARCHAR(100) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                last_login TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_username (username),
                INDEX idx_email (email),
                INDEX idx_user_type (user_type),
                INDEX idx_department (department),
                INDEX idx_owner_id (owner_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(users_sql)
            
            # 创建会话表
            sessions_sql = """
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_expires (expires_at),
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(sessions_sql)
            
            conn.commit()
            print("✅ 用户认证表创建成功")
            return True
            
        except Exception as e:
            print(f"❌ 创建用户表失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def hash_password(self, password):
        """密码哈希"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'), 
                                          salt.encode('utf-8'), 
                                          100000)
        return salt + password_hash.hex()
    
    def verify_password(self, password, stored_hash):
        """验证密码"""
        salt = stored_hash[:32]
        stored_password_hash = stored_hash[32:]
        password_hash = hashlib.pbkdf2_hmac('sha256',
                                          password.encode('utf-8'),
                                          salt.encode('utf-8'),
                                          100000)
        return password_hash.hex() == stored_password_hash
    
    def create_admin_user(self, username, email, password, full_name):
        """创建管理员用户"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            
            insert_sql = """
            INSERT INTO users (username, email, password_hash, user_type, full_name)
            VALUES (%s, %s, %s, 'admin', %s)
            """
            
            cursor.execute(insert_sql, (username, email, password_hash, full_name))
            conn.commit()
            
            print(f"✅ 管理员用户 {username} 创建成功")
            return True
            
        except mysql.connector.IntegrityError as e:
            print(f"❌ 用户创建失败: {e}")
            return False
        except Exception as e:
            print(f"❌ 创建用户时出错: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def create_owner_users_from_existing(self):
        """从现有业主数据创建业主用户账户"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 获取所有业主信息
            cursor.execute("""
                SELECT owner_id, name, email, phone 
                FROM owners 
                WHERE email IS NOT NULL AND email != ''
            """)
            owners = cursor.fetchall()
            
            created_count = 0
            
            for owner in owners:
                # 生成用户名（使用owner_id）
                username = f"owner_{owner['owner_id']}"
                
                # 生成默认密码（使用手机号后4位或默认密码）
                if owner['phone'] and len(owner['phone']) >= 4:
                    default_password = owner['phone'][-4:]
                else:
                    default_password = "123456"
                
                password_hash = self.hash_password(default_password)
                
                try:
                    insert_sql = """
                    INSERT INTO users (username, email, password_hash, user_type, owner_id, full_name)
                    VALUES (%s, %s, %s, 'owner', %s, %s)
                    """
                    
                    cursor.execute(insert_sql, (
                        username,
                        owner['email'],
                        password_hash,
                        owner['owner_id'],
                        owner['name']
                    ))
                    
                    created_count += 1
                    print(f"✅ 为业主 {owner['name']} 创建用户账户: {username}")
                    
                except mysql.connector.IntegrityError:
                    print(f"⚠️  业主 {owner['name']} 的用户账户已存在")
                    continue
            
            conn.commit()
            print(f"✅ 成功创建 {created_count} 个业主用户账户")
            return True
            
        except Exception as e:
            print(f"❌ 创建业主用户失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def authenticate_user(self, username, password):
        """用户认证"""
        conn = self.get_db_connection()
        if not conn:
            print("❌ 认证时数据库连接失败")
            # 如果数据库连接失败，使用演示模式认证
            return self._demo_authenticate(username, password)
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            print(f"🔍 尝试认证用户: {username}")
            cursor.execute("""
                SELECT id, username, email, password_hash, user_type, department, owner_id, full_name, is_active
                FROM users 
                WHERE username = %s AND is_active = TRUE
            """, (username,))
            
            user = cursor.fetchone()
            
            if user:
                print(f"✅ 找到用户: {user['username']}, 类型: {user['user_type']}")
                if self.verify_password(password, user['password_hash']):
                    print("✅ 密码验证成功")
                    # 更新最后登录时间
                    cursor.execute("""
                        UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s
                    """, (user['id'],))
                    conn.commit()
                    
                    return {
                        'id': user['id'],
                        'username': user['username'],
                        'email': user['email'],
                        'user_type': user['user_type'],
                        'department': user['department'],
                        'owner_id': user['owner_id'],
                        'full_name': user['full_name']
                    }
                else:
                    print("❌ 密码验证失败")
            else:
                print(f"❌ 未找到用户: {username}")
            
            return None
            
        except Exception as e:
            print(f"❌ 用户认证失败: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def get_dashboard_stats(self):
        """获取仪表盘统计数据"""
        connection = self.get_db_connection()
        if not connection:
            return {'total_properties': 0, 'total_owners': 0, 'total_cities': 0}
        
        stats = {}
        try:
            cursor = connection.cursor()
            
            # 获取仪表盘统计数据
            cursor.execute("SELECT COUNT(*) FROM properties")
            stats['total_properties'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM owners")
            stats['total_owners'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT city) FROM properties")
            stats['total_cities'] = cursor.fetchone()[0]
            
            cursor.close()
        except Exception as e:
            print(f"Error fetching dashboard data: {e}")
            return {'total_properties': 0, 'total_owners': 0, 'total_cities': 0}
        finally:
            connection.close()
        return stats

    def _demo_authenticate(self, username, password):
        """演示模式认证 - 数据库连接失败时使用"""
        print("🔄 使用演示模式认证")
        print(f"🔍 认证参数: username='{username}', password='{password}' (长度: {len(password) if password else 0})")
        
        # 演示用户数据 - 使用更严格的数据类型
        demo_users = {
            'admin': {
                'password': 'admin123',
                'user_type': 'admin',
                'department': 'Admin',
                'full_name': '系统管理员',
                'email': 'admin@example.com',
                'id': 1,
                'owner_id': None
            },
            'superadmin': {
                'password': 'super2025',
                'user_type': 'admin',
                'department': 'Admin',
                'full_name': '超级管理员',
                'email': 'superadmin@example.com',
                'id': 10,
                'owner_id': None
            },
            'manager': {
                'password': 'manager123',
                'user_type': 'admin',
                'department': 'Admin',
                'full_name': '管理器账户',
                'email': 'manager@example.com',
                'id': 11,
                'owner_id': None
            },
            'pm01': {
                'password': '123456',
                'user_type': 'admin',
                'department': 'Property Management Department',
                'full_name': '房产管理员',
                'email': 'pm01@example.com',
                'id': 2,
                'owner_id': None
            },
            'owner1': {
                'password': '123456',
                'user_type': 'owner',
                'department': None,
                'full_name': '业主张三',
                'email': 'owner1@example.com',
                'id': 3,
                'owner_id': 1
            }
        }
        
        # 增强的认证逻辑 - 修复间歇性失败问题
        try:
            # 第一步：参数验证
            if not username or not password:
                print(f"❌ 演示模式认证失败: 参数为空 (username: {bool(username)}, password: {bool(password)})")
                return None
            
            # 第二步：参数清理和标准化
            try:
                username_clean = str(username).strip().lower()
                password_clean = str(password).strip()
            except Exception as e:
                print(f"❌ 演示模式认证失败: 参数处理错误 - {e}")
                return None
            
            # 第三步：验证清理后的参数
            if len(username_clean) == 0 or len(password_clean) == 0:
                print(f"❌ 演示模式认证失败: 清理后参数为空")
                return None
            
            print(f"🔍 清理后参数: username='{username_clean}', password='{password_clean}'")
            print(f"🔍 可用用户: {list(demo_users.keys())}")
            
            # 第四步：用户存在性检查 - 使用更健壮的比较方式
            matched_user = None
            for demo_username in demo_users.keys():
                if demo_username == username_clean:
                    matched_user = demo_username
                    break
            
            if not matched_user:
                print(f"❌ 演示模式认证失败: 用户不存在 '{username_clean}'")
                print(f"🔍 用户名精确比较结果:")
                for demo_username in demo_users.keys():
                    print(f"   - '{demo_username}' == '{username_clean}': {demo_username == username_clean}")
                return None
            
            # 第五步：获取用户数据
            user_data = demo_users[matched_user]
            expected_password = user_data['password']
            
            print(f"✅ 找到匹配用户: {matched_user}")
            print(f"🔍 密码验证: 输入长度={len(password_clean)}, 期望长度={len(expected_password)}")
            
            # 第六步：密码验证 - 使用更严格的比较
            password_match = False
            try:
                password_match = (password_clean == expected_password)
            except Exception as e:
                print(f"❌ 密码比较异常: {e}")
                return None
            
            if not password_match:
                print(f"❌ 演示模式认证失败: 密码错误")
                print(f"🔍 密码详细比较:")
                print(f"   - 输入: '{password_clean}' (类型: {type(password_clean)})")
                print(f"   - 期望: '{expected_password}' (类型: {type(expected_password)})")
                print(f"   - 匹配: {password_match}")
                # 字符级比较
                if len(password_clean) == len(expected_password):
                    for i, (c1, c2) in enumerate(zip(password_clean, expected_password)):
                        if c1 != c2:
                            print(f"   - 字符差异位置 {i}: '{c1}' != '{c2}'")
                return None
            
            print(f"✅ 演示模式认证成功: {username_clean}")
            
            # 第七步：构建返回数据 - 确保数据完整性
            try:
                auth_result = {
                    'id': int(user_data['id']),
                    'username': str(matched_user),  # 使用匹配的原始用户名
                    'email': str(user_data['email']),
                    'user_type': str(user_data['user_type']),
                    'department': str(user_data['department']) if user_data['department'] else None,
                    'owner_id': int(user_data['owner_id']) if user_data['owner_id'] else None,
                    'full_name': str(user_data['full_name'])
                }
                
                print(f"✅ 构建认证结果: {auth_result}")
                
                # 验证结果完整性
                required_fields = ['id', 'username', 'email', 'user_type', 'full_name']
                for field in required_fields:
                    if auth_result.get(field) is None:
                        print(f"❌ 认证结果字段缺失: {field}")
                        return None
                
                return auth_result
                
            except Exception as e:
                print(f"❌ 构建认证结果失败: {e}")
                return None
            
        except Exception as e:
            print(f"❌ 演示模式认证异常: {e}")
            print(f"🔍 异常类型: {type(e).__name__}")
            import traceback
            print(f"🔍 异常堆栈: {traceback.format_exc()}")
            return None
    
    def create_session(self, user_id, ip_address=None, user_agent=None):
        """创建用户会话"""
        conn = self.get_db_connection()
        if not conn:
            # 演示模式：返回演示会话ID
            print("🔄 数据库连接失败，创建演示模式会话")
            return f"demo_session_{user_id}_{secrets.token_hex(8)}"
        
        cursor = conn.cursor()
        
        try:
            session_id = secrets.token_urlsafe(32)
            # 使用UTC时间，然后转换为数据库时区
            from datetime import timezone
            now_utc = datetime.now(timezone.utc)
            expires_at_utc = now_utc + timedelta(seconds=self.session_timeout)
            
            print(f"🕒 创建会话时间: {now_utc}, 过期时间: {expires_at_utc}")
            
            cursor.execute("""
                INSERT INTO user_sessions (session_id, user_id, expires_at, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            """, (session_id, user_id, expires_at_utc, ip_address, user_agent))
            
            conn.commit()
            print(f"✅ 会话创建成功: {session_id}")
            return session_id
            
        except Exception as e:
            print(f"❌ 创建会话失败: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def validate_session(self, session_id):
        """验证会话"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 使用UTC时间进行比较
            from datetime import timezone
            now_utc = datetime.now(timezone.utc)
            
            cursor.execute("""
                SELECT us.user_id, us.expires_at, u.username, u.user_type, u.owner_id, u.full_name
                FROM user_sessions us
                JOIN users u ON us.user_id = u.id
                WHERE us.session_id = %s AND us.expires_at > %s AND u.is_active = TRUE
            """, (session_id, now_utc))
            
            session_data = cursor.fetchone()
            
            print(f"🔍 验证会话: {session_id[:20]}..., 当前UTC时间: {now_utc}")
            if session_data:
                print(f"✅ 找到有效会话，过期时间: {session_data['expires_at']}")
                # 延长会话时间
                new_expires_at_utc = now_utc + timedelta(seconds=self.session_timeout)
                cursor.execute("""
                    UPDATE user_sessions SET expires_at = %s WHERE session_id = %s
                """, (new_expires_at_utc, session_id))
                conn.commit()
                
                return {
                    'user_id': session_data['user_id'],
                    'username': session_data['username'],
                    'user_type': session_data['user_type'],
                    'owner_id': session_data['owner_id'],
                    'full_name': session_data['full_name']
                }
            else:
                print("❌ 未找到有效会话或会话已过期")
            
            return None
            
        except Exception as e:
            print(f"❌ 会话验证失败: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def logout_user(self, session_id):
        """用户登出"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM user_sessions WHERE session_id = %s", (session_id,))
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ 登出失败: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def debug_users_table(self):
        """调试用户表状态"""
        conn = self.get_db_connection()
        if not conn:
            print("❌ 调试时数据库连接失败")
            return
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 检查用户表是否存在
            cursor.execute("SHOW TABLES LIKE 'users'")
            table_exists = cursor.fetchone()
            
            if table_exists:
                print("✅ users表存在")
                
                # 查看用户数量
                cursor.execute("SELECT COUNT(*) as count FROM users")
                user_count = cursor.fetchone()['count']
                print(f"📊 用户总数: {user_count}")
                
                # 查看管理员用户
                cursor.execute("SELECT username, user_type, is_active FROM users WHERE user_type = 'admin'")
                admin_users = cursor.fetchall()
                print(f"👑 管理员用户: {len(admin_users)}")
                for admin in admin_users:
                    print(f"   - {admin['username']} (活跃: {admin['is_active']})")
                
                # 查看业主用户数量
                cursor.execute("SELECT COUNT(*) as count FROM users WHERE user_type = 'owner'")
                owner_count = cursor.fetchone()['count']
                print(f"🏠 业主用户: {owner_count}")
                
            else:
                print("❌ users表不存在")
                
        except Exception as e:
            print(f"❌ 调试失败: {e}")
        finally:
            cursor.close()
            conn.close()

# 装饰器函数
def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        
        if session.get('user_type') != 'admin':
            flash('需要管理员权限', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def owner_required(f):
    """业主权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        
        if session.get('user_type') != 'owner':
            flash('需要业主权限', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    """超级管理员权限验证装饰器 - 只允许username='admin'的用户访问"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        
        if session.get('user_type') != 'admin':
            flash('需要管理员权限', 'error')
            return redirect(url_for('dashboard'))
        
        # 检查是否为超级管理员（username='admin'）
        if session.get('username') != 'admin':
            flash('此功能仅限超级管理员访问', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

# 新增的员工角色权限装饰器
def property_manager_required(f):
    """需要房产经理权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'error')
            return redirect(url_for('login'))
        
        allowed_roles = ['admin', 'property_manager']
        if session.get('user_type') not in allowed_roles:
            flash('需要房产经理权限', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def sales_required(f):
    """需要销售权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'error')
            return redirect(url_for('login'))
        
        allowed_roles = ['admin', 'sales']
        if session.get('user_type') not in allowed_roles:
            flash('需要销售权限', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def accounting_required(f):
    """需要会计权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'error')
            return redirect(url_for('login'))
        
        allowed_roles = ['admin', 'accounting']
        if session.get('user_type') not in allowed_roles:
            flash('需要会计权限', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    """需要员工权限（任何内部员工角色）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'error')
            return redirect(url_for('login'))
        
        staff_roles = ['admin', 'property_manager', 'sales', 'accounting']
        if session.get('user_type') not in staff_roles:
            flash('需要员工权限', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

# 注意：has_module_access函数现在在department_modules.py中定义
# 请使用 from department_modules import has_module_access

# 全局认证系统实例
auth_system = AuthSystem() 