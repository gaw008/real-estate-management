# -*- coding: utf-8 -*-
"""
注册申请管理器
处理用户注册申请、审核和账户创建
"""

import hashlib
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import mysql.connector
from src.core.config_loader import DB_CONFIG

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RegistrationManager:
    """注册申请管理器"""
    
    def __init__(self):
        """初始化注册管理器"""
        self.departments = [
            '销售部',
            '房产管理部', 
            '会计部',
            '市场部',
            '管理员'
        ]
    
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
            logger.error(f"❌ 数据库连接错误: {e}")
            return None
    
    def create_tables(self):
        """创建注册申请相关表"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # 创建注册申请表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS registration_applications (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    phone VARCHAR(20),
                    department VARCHAR(50) NOT NULL,
                    job_title VARCHAR(100),
                    notes TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP,
                    reviewed_by INTEGER,
                    review_notes TEXT,
                    initial_password VARCHAR(255)
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("✅ 注册申请相关表创建成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建注册申请表失败: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """密码哈希 - 与认证系统保持一致"""
        import secrets
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'), 
                                          salt.encode('utf-8'), 
                                          100000)
        return salt + password_hash.hex()
    
    def submit_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """提交注册申请"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {'success': False, 'message': '数据库连接失败'}
                
            cursor = conn.cursor()
            
            # 检查用户名和邮箱是否已存在
            cursor.execute("""
                SELECT id FROM registration_applications 
                WHERE username = %s OR email = %s
            """, (application_data['username'], application_data['email']))
            
            if cursor.fetchone():
                return {
                    'success': False,
                    'message': '用户名或邮箱已存在'
                }
            
            # 检查用户表中是否已存在
            cursor.execute("""
                SELECT id FROM users 
                WHERE username = %s OR email = %s
            """, (application_data['username'], application_data['email']))
            
            if cursor.fetchone():
                return {
                    'success': False,
                    'message': '用户名或邮箱已被注册'
                }
            
            # 插入申请记录
            cursor.execute("""
                INSERT INTO registration_applications 
                (username, email, full_name, phone, department, job_title, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                application_data['username'],
                application_data['email'],
                application_data['full_name'],
                application_data.get('phone', ''),
                application_data['department'],
                application_data.get('job_title', ''),
                application_data.get('notes', '')
            ))
            
            # 获取插入的ID
            application_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ 注册申请提交成功，ID: {application_id}")
            
            return {
                'success': True,
                'message': '注册申请提交成功，请等待管理员审核',
                'application_id': application_id
            }
            
        except Exception as e:
            logger.error(f"❌ 提交注册申请失败: {e}")
            return {
                'success': False,
                'message': f'提交申请失败: {str(e)}'
            }
    
    def get_applications(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取注册申请列表"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return []
                
            cursor = conn.cursor()
            
            query = """
                SELECT ra.*, u.username as reviewer_name
                FROM registration_applications ra
                LEFT JOIN users u ON ra.reviewed_by = u.id
            """
            params = []
            
            if status:
                query += " WHERE ra.status = %s"
                params.append(status)
            
            query += " ORDER BY ra.created_at DESC"
            
            cursor.execute(query, params)
            applications = []
            
            for row in cursor.fetchall():
                applications.append({
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'full_name': row[3],
                    'phone': row[4],
                    'department': row[5],
                    'job_title': row[6],
                    'notes': row[7],
                    'status': row[8],
                    'created_at': row[9],
                    'reviewed_at': row[10],
                    'reviewed_by': row[11],
                    'review_notes': row[12],
                    'initial_password': row[13],
                    'reviewer_name': row[14]
                })
            
            cursor.close()
            conn.close()
            
            return applications
            
        except Exception as e:
            logger.error(f"❌ 获取注册申请列表失败: {e}")
            return []
    
    def get_application_by_id(self, application_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取申请详情"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return None
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ra.*, u.username as reviewer_name
                FROM registration_applications ra
                LEFT JOIN users u ON ra.reviewed_by = u.id
                WHERE ra.id = %s
            """, (application_id,))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'full_name': row[3],
                    'phone': row[4],
                    'department': row[5],
                    'job_title': row[6],
                    'notes': row[7],
                    'status': row[8],
                    'created_at': row[9],
                    'reviewed_at': row[10],
                    'reviewed_by': row[11],
                    'review_notes': row[12],
                    'initial_password': row[13],
                    'reviewer_name': row[14]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取申请详情失败: {e}")
            return None
    
    def review_application(self, application_id: int, action: str, 
                          reviewer_id: int, review_notes: str = '', 
                          initial_password: str = '') -> Dict[str, Any]:
        """审核注册申请"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {'success': False, 'message': '数据库连接失败'}
                
            cursor = conn.cursor()
            
            # 获取申请信息
            application = self.get_application_by_id(application_id)
            if not application:
                return {
                    'success': False,
                    'message': '申请不存在'
                }
            
            if application['status'] != 'pending':
                return {
                    'success': False,
                    'message': '该申请已被审核'
                }
            
            if action == 'approve':
                # 批准申请
                if not initial_password:
                    return {
                        'success': False,
                        'message': '批准申请需要设置初始密码'
                    }
                
                # 创建用户账户
                user_created = self._create_user_account(application, initial_password)
                if not user_created['success']:
                    return user_created
                
                # 更新申请状态
                cursor.execute("""
                    UPDATE registration_applications 
                    SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP,
                        reviewed_by = %s, review_notes = %s, initial_password = %s
                    WHERE id = %s
                """, (reviewer_id, review_notes, initial_password, application_id))
                
                message = '申请已批准，用户账户已创建'
                
            elif action == 'reject':
                # 拒绝申请
                cursor.execute("""
                    UPDATE registration_applications 
                    SET status = 'rejected', reviewed_at = CURRENT_TIMESTAMP,
                        reviewed_by = %s, review_notes = %s
                    WHERE id = %s
                """, (reviewer_id, review_notes, application_id))
                
                message = '申请已拒绝'
                
            else:
                return {
                    'success': False,
                    'message': '无效的审核操作'
                }
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ 申请审核完成，ID: {application_id}, 操作: {action}")
            
            return {
                'success': True,
                'message': message
            }
            
        except Exception as e:
            logger.error(f"❌ 审核申请失败: {e}")
            return {
                'success': False,
                'message': f'审核失败: {str(e)}'
            }
    
    def _create_user_account(self, application: Dict[str, Any], 
                           initial_password: str) -> Dict[str, Any]:
        """创建用户账户"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {'success': False, 'message': '数据库连接失败'}
                
            cursor = conn.cursor()
            
            # 检查用户是否已存在
            cursor.execute("""
                SELECT id FROM users WHERE username = %s OR email = %s
            """, (application['username'], application['email']))
            
            if cursor.fetchone():
                return {
                    'success': False,
                    'message': '用户账户已存在'
                }
            
            # 确定用户类型
            if application['department'] == '管理员':
                user_type = 'admin'
            elif application['department'] == '销售部':
                user_type = 'sales'
            elif application['department'] == '会计部':
                user_type = 'accounting'
            elif application['department'] == '房产管理部':
                user_type = 'property_manager'
            else:
                user_type = 'sales'  # 默认为销售部门
            
            # 创建用户账户
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, 
                                 user_type, department, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (
                application['username'],
                application['email'],
                self.hash_password(initial_password),
                application['full_name'],
                user_type,
                application['department']
            ))
            
            # 获取插入的用户ID
            user_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ 用户账户创建成功，ID: {user_id}")
            
            return {
                'success': True,
                'message': '用户账户创建成功',
                'user_id': user_id
            }
            
        except Exception as e:
            logger.error(f"❌ 创建用户账户失败: {e}")
            return {
                'success': False,
                'message': f'创建用户账户失败: {str(e)}'
            }
    
    def get_statistics(self) -> Dict[str, int]:
        """获取申请统计信息"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {'total': 0, 'pending': 0, 'approved': 0, 'rejected': 0}
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected
                FROM registration_applications
            """)
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return {
                'total': row[0],
                'pending': row[1],
                'approved': row[2],
                'rejected': row[3]
            }
            
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {
                'total': 0,
                'pending': 0,
                'approved': 0,
                'rejected': 0
            }
    
    def delete_application(self, application_id: int) -> Dict[str, Any]:
        """删除注册申请"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {'success': False, 'message': '数据库连接失败'}
                
            cursor = conn.cursor()
            
            # 检查申请是否存在
            cursor.execute("""
                SELECT status FROM registration_applications WHERE id = %s
            """, (application_id,))
            
            row = cursor.fetchone()
            if not row:
                return {
                    'success': False,
                    'message': '申请不存在'
                }
            
            if row[0] == 'approved':
                return {
                    'success': False,
                    'message': '已批准的申请不能删除'
                }
            
            # 删除申请
            cursor.execute("""
                DELETE FROM registration_applications WHERE id = %s
            """, (application_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ 注册申请删除成功，ID: {application_id}")
            
            return {
                'success': True,
                'message': '申请删除成功'
            }
            
        except Exception as e:
            logger.error(f"❌ 删除申请失败: {e}")
            return {
                'success': False,
                'message': f'删除失败: {str(e)}'
            }

# 创建全局实例
registration_manager = RegistrationManager() 