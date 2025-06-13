#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户注册和审核系统
User Registration and Approval System
"""

import hashlib
import secrets
from datetime import datetime
from config_loader import DB_CONFIG
import mysql.connector

class UserRegistrationSystem:
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
    
    def create_registration_tables(self):
        """创建用户注册相关表"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            # 创建用户注册申请表
            registration_sql = """
            CREATE TABLE IF NOT EXISTS user_registrations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                user_type ENUM('admin', 'owner') NOT NULL,
                
                -- 员工信息
                job_title VARCHAR(100) NULL,
                department VARCHAR(100) NULL,
                
                -- 业主信息
                property_address TEXT NULL,
                phone VARCHAR(50) NULL,
                
                -- 审核状态
                status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                admin_notes TEXT NULL,
                reviewed_by INT NULL,
                reviewed_at TIMESTAMP NULL,
                
                -- 时间戳
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_status (status),
                INDEX idx_user_type (user_type),
                INDEX idx_email (email),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(registration_sql)
            
            # 创建审核日志表
            audit_log_sql = """
            CREATE TABLE IF NOT EXISTS registration_audit_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                registration_id INT NOT NULL,
                admin_id INT NOT NULL,
                action ENUM('approve', 'reject', 'request_info') NOT NULL,
                notes TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_registration_id (registration_id),
                INDEX idx_admin_id (admin_id),
                INDEX idx_action (action)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(audit_log_sql)
            
            conn.commit()
            print("✅ 用户注册表创建成功")
            return True
            
        except Exception as e:
            print(f"❌ 创建注册表失败: {e}")
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
    
    def submit_registration(self, registration_data):
        """提交用户注册申请"""
        conn = self.get_db_connection()
        if not conn:
            return False, "数据库连接失败"
        
        cursor = conn.cursor()
        
        try:
            # 检查用户名和邮箱是否已存在
            cursor.execute("""
                SELECT COUNT(*) as count FROM user_registrations 
                WHERE username = %s OR email = %s
            """, (registration_data['username'], registration_data['email']))
            
            if cursor.fetchone()[0] > 0:
                return False, "用户名或邮箱已存在"
            
            # 检查已有用户表中是否存在
            cursor.execute("""
                SELECT COUNT(*) as count FROM users 
                WHERE username = %s OR email = %s
            """, (registration_data['username'], registration_data['email']))
            
            if cursor.fetchone()[0] > 0:
                return False, "用户名或邮箱已被使用"
            
            # 哈希密码
            password_hash = self.hash_password(registration_data['password'])
            
            # 插入注册申请
            if registration_data['user_type'] == 'admin':
                insert_sql = """
                INSERT INTO user_registrations 
                (username, email, password_hash, full_name, user_type, job_title, department)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    registration_data['username'],
                    registration_data['email'],
                    password_hash,
                    registration_data['full_name'],
                    registration_data['user_type'],
                    registration_data.get('job_title'),
                    registration_data.get('department')
                )
            else:  # owner
                insert_sql = """
                INSERT INTO user_registrations 
                (username, email, password_hash, full_name, user_type, property_address, phone)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    registration_data['username'],
                    registration_data['email'],
                    password_hash,
                    registration_data['full_name'],
                    registration_data['user_type'],
                    registration_data.get('property_address'),
                    registration_data.get('phone')
                )
            
            cursor.execute(insert_sql, values)
            registration_id = cursor.lastrowid
            
            conn.commit()
            
            print(f"✅ 用户注册申请提交成功: {registration_data['username']}")
            return True, f"注册申请已提交，申请ID: {registration_id}"
            
        except mysql.connector.IntegrityError as e:
            print(f"❌ 注册申请失败 - 数据冲突: {e}")
            return False, "用户名或邮箱已存在"
        except Exception as e:
            print(f"❌ 注册申请失败: {e}")
            return False, "注册申请提交失败，请重试"
        finally:
            cursor.close()
            conn.close()
    
    def get_pending_registrations(self, page=1, per_page=10):
        """获取待审核的注册申请"""
        conn = self.get_db_connection()
        if not conn:
            return [], 0
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 获取总数
            cursor.execute("SELECT COUNT(*) as count FROM user_registrations WHERE status = 'pending'")
            total_count = cursor.fetchone()['count']
            
            # 获取分页数据
            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT * FROM user_registrations 
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT %s OFFSET %s
            """, (per_page, offset))
            
            registrations = cursor.fetchall()
            
            return registrations, total_count
            
        except Exception as e:
            print(f"❌ 获取待审核申请失败: {e}")
            return [], 0
        finally:
            cursor.close()
            conn.close()
    
    def get_all_registrations(self, status=None, page=1, per_page=20):
        """获取所有注册申请"""
        conn = self.get_db_connection()
        if not conn:
            return [], 0
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 构建查询条件
            where_clause = ""
            params = []
            
            if status:
                where_clause = "WHERE status = %s"
                params.append(status)
            
            # 获取总数
            count_sql = f"SELECT COUNT(*) as count FROM user_registrations {where_clause}"
            cursor.execute(count_sql, params)
            total_count = cursor.fetchone()['count']
            
            # 获取分页数据
            offset = (page - 1) * per_page
            query_sql = f"""
                SELECT ur.*, u.username as reviewed_by_username
                FROM user_registrations ur
                LEFT JOIN users u ON ur.reviewed_by = u.id
                {where_clause}
                ORDER BY ur.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query_sql, params + [per_page, offset])
            
            registrations = cursor.fetchall()
            
            return registrations, total_count
            
        except Exception as e:
            print(f"❌ 获取注册申请失败: {e}")
            return [], 0
        finally:
            cursor.close()
            conn.close()
    
    def approve_registration(self, registration_id, admin_id, notes=None):
        """审核通过注册申请"""
        conn = self.get_db_connection()
        if not conn:
            return False, "数据库连接失败"
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 获取注册申请信息
            cursor.execute("""
                SELECT * FROM user_registrations WHERE id = %s AND status = 'pending'
            """, (registration_id,))
            
            registration = cursor.fetchone()
            if not registration:
                return False, "注册申请不存在或已处理"
            
            # 创建用户账户
            user_insert_sql = """
            INSERT INTO users (username, email, password_hash, user_type, full_name)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(user_insert_sql, (
                registration['username'],
                registration['email'],
                registration['password_hash'],
                registration['user_type'],
                registration['full_name']
            ))
            
            # 更新注册申请状态
            cursor.execute("""
                UPDATE user_registrations 
                SET status = 'approved', reviewed_by = %s, reviewed_at = NOW(), admin_notes = %s
                WHERE id = %s
            """, (admin_id, notes, registration_id))
            
            # 记录审核日志
            cursor.execute("""
                INSERT INTO registration_audit_log (registration_id, admin_id, action, notes)
                VALUES (%s, %s, 'approve', %s)
            """, (registration_id, admin_id, notes))
            
            conn.commit()
            
            print(f"✅ 注册申请审核通过: {registration['username']}")
            return True, "用户账户创建成功"
            
        except mysql.connector.IntegrityError as e:
            print(f"❌ 审核失败 - 用户已存在: {e}")
            conn.rollback()
            return False, "用户名或邮箱已被使用"
        except Exception as e:
            print(f"❌ 审核失败: {e}")
            conn.rollback()
            return False, "审核处理失败"
        finally:
            cursor.close()
            conn.close()
    
    def reject_registration(self, registration_id, admin_id, notes):
        """拒绝注册申请"""
        conn = self.get_db_connection()
        if not conn:
            return False, "数据库连接失败"
        
        cursor = conn.cursor()
        
        try:
            # 更新注册申请状态
            cursor.execute("""
                UPDATE user_registrations 
                SET status = 'rejected', reviewed_by = %s, reviewed_at = NOW(), admin_notes = %s
                WHERE id = %s AND status = 'pending'
            """, (admin_id, notes, registration_id))
            
            if cursor.rowcount == 0:
                return False, "注册申请不存在或已处理"
            
            # 记录审核日志
            cursor.execute("""
                INSERT INTO registration_audit_log (registration_id, admin_id, action, notes)
                VALUES (%s, %s, 'reject', %s)
            """, (registration_id, admin_id, notes))
            
            conn.commit()
            
            print(f"✅ 注册申请已拒绝: ID {registration_id}")
            return True, "注册申请已拒绝"
            
        except Exception as e:
            print(f"❌ 拒绝申请失败: {e}")
            conn.rollback()
            return False, "处理失败"
        finally:
            cursor.close()
            conn.close()
    
    def get_registration_stats(self):
        """获取注册申请统计"""
        conn = self.get_db_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            stats = {}
            
            # 总申请数
            cursor.execute("SELECT COUNT(*) as count FROM user_registrations")
            stats['total'] = cursor.fetchone()['count']
            
            # 待审核数
            cursor.execute("SELECT COUNT(*) as count FROM user_registrations WHERE status = 'pending'")
            stats['pending'] = cursor.fetchone()['count']
            
            # 已通过数
            cursor.execute("SELECT COUNT(*) as count FROM user_registrations WHERE status = 'approved'")
            stats['approved'] = cursor.fetchone()['count']
            
            # 已拒绝数
            cursor.execute("SELECT COUNT(*) as count FROM user_registrations WHERE status = 'rejected'")
            stats['rejected'] = cursor.fetchone()['count']
            
            # 按用户类型统计
            cursor.execute("""
                SELECT user_type, COUNT(*) as count 
                FROM user_registrations 
                GROUP BY user_type
            """)
            type_stats = cursor.fetchall()
            stats['by_type'] = {item['user_type']: item['count'] for item in type_stats}
            
            return stats
            
        except Exception as e:
            print(f"❌ 获取统计失败: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()

# 全局注册系统实例
registration_system = UserRegistrationSystem() 