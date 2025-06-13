#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码管理系统
Password Management System
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from config_loader import DB_CONFIG
import mysql.connector

class PasswordManager:
    def __init__(self):
        pass
    
    def get_db_connection(self):
        """获取数据库连接"""
        try:
            ssl_config = {
                'ssl_disabled': False,
                'ssl_verify_cert': False,
                'ssl_verify_identity': False
            }
            config = {**DB_CONFIG, **ssl_config}
            connection = mysql.connector.connect(**config)
            return connection
        except Exception as e:
            print(f"数据库连接错误: {e}")
            return None
    
    def create_password_tables(self):
        """创建密码管理相关表"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            # 创建密码重置令牌表
            reset_tokens_sql = """
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_at TIMESTAMP NULL,
                
                INDEX idx_token (token),
                INDEX idx_user_id (user_id),
                INDEX idx_expires_at (expires_at),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(reset_tokens_sql)
            
            # 创建密码修改日志表
            password_log_sql = """
            CREATE TABLE IF NOT EXISTS password_change_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                changed_by INT NOT NULL,
                change_type ENUM('self_change', 'admin_reset', 'token_reset') NOT NULL,
                ip_address VARCHAR(45) NULL,
                user_agent TEXT NULL,
                notes TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_user_id (user_id),
                INDEX idx_changed_by (changed_by),
                INDEX idx_change_type (change_type),
                INDEX idx_created_at (created_at),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(password_log_sql)
            
            conn.commit()
            print("✅ 密码管理表创建成功")
            return True
            
        except Exception as e:
            print(f"❌ 创建密码管理表失败: {e}")
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
        if not stored_hash or len(stored_hash) < 32:
            return False
        
        salt = stored_hash[:32]
        stored_password_hash = stored_hash[32:]
        
        password_hash = hashlib.pbkdf2_hmac('sha256',
                                          password.encode('utf-8'),
                                          salt.encode('utf-8'),
                                          100000)
        
        return password_hash.hex() == stored_password_hash
    
    def change_password(self, user_id, old_password, new_password, changed_by=None, ip_address=None, user_agent=None):
        """用户修改密码"""
        conn = self.get_db_connection()
        if not conn:
            return False, "数据库连接失败"
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 获取用户当前密码
            cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return False, "用户不存在"
            
            # 验证旧密码
            if not self.verify_password(old_password, user['password_hash']):
                return False, "当前密码错误"
            
            # 检查新密码强度
            if len(new_password) < 8:
                return False, "新密码长度至少8位"
            
            # 哈希新密码
            new_password_hash = self.hash_password(new_password)
            
            # 更新密码
            cursor.execute("""
                UPDATE users SET password_hash = %s, updated_at = NOW()
                WHERE id = %s
            """, (new_password_hash, user_id))
            
            # 记录密码修改日志
            cursor.execute("""
                INSERT INTO password_change_log 
                (user_id, changed_by, change_type, ip_address, user_agent, notes)
                VALUES (%s, %s, 'self_change', %s, %s, '用户自主修改密码')
            """, (user_id, changed_by or user_id, ip_address, user_agent))
            
            conn.commit()
            
            print(f"✅ 用户 {user_id} 密码修改成功")
            return True, "密码修改成功"
            
        except Exception as e:
            print(f"❌ 密码修改失败: {e}")
            conn.rollback()
            return False, "密码修改失败"
        finally:
            cursor.close()
            conn.close()
    
    def admin_reset_password(self, admin_id, target_user_id, new_password, notes=None, ip_address=None, user_agent=None):
        """管理员重置用户密码"""
        conn = self.get_db_connection()
        if not conn:
            return False, "数据库连接失败"
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 验证管理员权限
            cursor.execute("SELECT user_type FROM users WHERE id = %s", (admin_id,))
            admin = cursor.fetchone()
            
            if not admin or admin['user_type'] != 'admin':
                return False, "权限不足"
            
            # 验证目标用户存在
            cursor.execute("SELECT username FROM users WHERE id = %s", (target_user_id,))
            target_user = cursor.fetchone()
            
            if not target_user:
                return False, "目标用户不存在"
            
            # 检查新密码强度
            if len(new_password) < 8:
                return False, "新密码长度至少8位"
            
            # 哈希新密码
            new_password_hash = self.hash_password(new_password)
            
            # 更新密码
            cursor.execute("""
                UPDATE users SET password_hash = %s, updated_at = NOW()
                WHERE id = %s
            """, (new_password_hash, target_user_id))
            
            # 记录密码修改日志
            cursor.execute("""
                INSERT INTO password_change_log 
                (user_id, changed_by, change_type, ip_address, user_agent, notes)
                VALUES (%s, %s, 'admin_reset', %s, %s, %s)
            """, (target_user_id, admin_id, ip_address, user_agent, notes or '管理员重置密码'))
            
            conn.commit()
            
            print(f"✅ 管理员 {admin_id} 重置用户 {target_user_id} 密码成功")
            return True, "密码重置成功"
            
        except Exception as e:
            print(f"❌ 密码重置失败: {e}")
            conn.rollback()
            return False, "密码重置失败"
        finally:
            cursor.close()
            conn.close()
    
    def generate_reset_token(self, user_id, expires_hours=24):
        """生成密码重置令牌"""
        conn = self.get_db_connection()
        if not conn:
            return None, "数据库连接失败"
        
        cursor = conn.cursor()
        
        try:
            # 验证用户存在
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                return None, "用户不存在"
            
            # 生成令牌
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            # 清理该用户的旧令牌
            cursor.execute("DELETE FROM password_reset_tokens WHERE user_id = %s", (user_id,))
            
            # 插入新令牌
            cursor.execute("""
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES (%s, %s, %s)
            """, (user_id, token, expires_at))
            
            conn.commit()
            
            print(f"✅ 为用户 {user_id} 生成密码重置令牌")
            return token, "重置令牌生成成功"
            
        except Exception as e:
            print(f"❌ 生成重置令牌失败: {e}")
            conn.rollback()
            return None, "生成重置令牌失败"
        finally:
            cursor.close()
            conn.close()
    
    def verify_reset_token(self, token):
        """验证密码重置令牌"""
        conn = self.get_db_connection()
        if not conn:
            return None, "数据库连接失败"
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT prt.*, u.username, u.email
                FROM password_reset_tokens prt
                JOIN users u ON prt.user_id = u.id
                WHERE prt.token = %s AND prt.used = FALSE AND prt.expires_at > NOW()
            """, (token,))
            
            token_data = cursor.fetchone()
            
            if not token_data:
                return None, "令牌无效或已过期"
            
            return token_data, "令牌验证成功"
            
        except Exception as e:
            print(f"❌ 验证重置令牌失败: {e}")
            return None, "验证重置令牌失败"
        finally:
            cursor.close()
            conn.close()
    
    def reset_password_with_token(self, token, new_password, ip_address=None, user_agent=None):
        """使用令牌重置密码"""
        conn = self.get_db_connection()
        if not conn:
            return False, "数据库连接失败"
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 验证令牌
            cursor.execute("""
                SELECT user_id FROM password_reset_tokens
                WHERE token = %s AND used = FALSE AND expires_at > NOW()
            """, (token,))
            
            token_data = cursor.fetchone()
            
            if not token_data:
                return False, "令牌无效或已过期"
            
            user_id = token_data['user_id']
            
            # 检查新密码强度
            if len(new_password) < 8:
                return False, "新密码长度至少8位"
            
            # 哈希新密码
            new_password_hash = self.hash_password(new_password)
            
            # 更新密码
            cursor.execute("""
                UPDATE users SET password_hash = %s, updated_at = NOW()
                WHERE id = %s
            """, (new_password_hash, user_id))
            
            # 标记令牌为已使用
            cursor.execute("""
                UPDATE password_reset_tokens 
                SET used = TRUE, used_at = NOW()
                WHERE token = %s
            """, (token,))
            
            # 记录密码修改日志
            cursor.execute("""
                INSERT INTO password_change_log 
                (user_id, changed_by, change_type, ip_address, user_agent, notes)
                VALUES (%s, %s, 'token_reset', %s, %s, '通过重置令牌修改密码')
            """, (user_id, user_id, ip_address, user_agent))
            
            conn.commit()
            
            print(f"✅ 用户 {user_id} 通过令牌重置密码成功")
            return True, "密码重置成功"
            
        except Exception as e:
            print(f"❌ 令牌重置密码失败: {e}")
            conn.rollback()
            return False, "密码重置失败"
        finally:
            cursor.close()
            conn.close()
    
    def get_password_change_history(self, user_id, limit=10):
        """获取密码修改历史"""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT pcl.*, u.username as changed_by_username
                FROM password_change_log pcl
                LEFT JOIN users u ON pcl.changed_by = u.id
                WHERE pcl.user_id = %s
                ORDER BY pcl.created_at DESC
                LIMIT %s
            """, (user_id, limit))
            
            history = cursor.fetchall()
            return history
            
        except Exception as e:
            print(f"❌ 获取密码修改历史失败: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def cleanup_expired_tokens(self):
        """清理过期的重置令牌"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM password_reset_tokens WHERE expires_at < NOW()")
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"✅ 清理了 {deleted_count} 个过期的重置令牌")
            return True
            
        except Exception as e:
            print(f"❌ 清理过期令牌失败: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

# 全局密码管理器实例
password_manager = PasswordManager() 