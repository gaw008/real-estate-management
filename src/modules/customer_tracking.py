#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户追踪模块
管理客户信息、跟踪进度和记录
"""

import mysql.connector
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import json
from src.core.config_loader import DB_CONFIG

class CustomerTrackingManager:
    """客户追踪管理器"""
    
    def __init__(self):
        self.db_config = DB_CONFIG
    
    def get_db_connection(self):
        """获取数据库连接"""
        try:
            # 直接使用配置创建连接
            import mysql.connector
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return None
    
    def create_customer_tracking_tables(self):
        """创建客户追踪相关表"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            # 创建客户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    property_address TEXT,
                    rental_types JSON,
                    tracking_status VARCHAR(50) DEFAULT '初始接触',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    deleted_at TIMESTAMP NULL,
                    INDEX idx_deleted_at (deleted_at),
                    INDEX idx_tracking_status (tracking_status)
                )
            """)
            
            # 创建跟踪记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customer_tracking_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id INT NOT NULL,
                    record_date DATE NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    deleted_at TIMESTAMP NULL,
                    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                    INDEX idx_customer_id (customer_id),
                    INDEX idx_record_date (record_date),
                    INDEX idx_deleted_at (deleted_at)
                )
            """)
            
            conn.commit()
            print("✅ 客户追踪表创建成功")
            return True
            
        except Exception as e:
            print(f"❌ 创建客户追踪表失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def add_customer(self, customer_data: Dict[str, Any]) -> Optional[int]:
        """添加客户"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        try:
            # 处理租赁类别（多选）
            rental_types = customer_data.get('rental_types', [])
            if isinstance(rental_types, list):
                rental_types_json = json.dumps(rental_types, ensure_ascii=False)
            else:
                rental_types_json = json.dumps([], ensure_ascii=False)
            
            # 处理日期字段
            contract_date = customer_data.get('contract_date')
            termination_date = customer_data.get('termination_date')
            
            # 如果日期字段为空字符串，设为None
            if contract_date == '':
                contract_date = None
            if termination_date == '':
                termination_date = None
            
            query = """
                INSERT INTO customers (name, phone, email, property_address, rental_types, tracking_status, notes, contract_date, termination_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                customer_data['name'],
                customer_data.get('phone', ''),
                customer_data.get('email', ''),
                customer_data.get('property_address', ''),
                rental_types_json,
                customer_data.get('tracking_status', '初始接触'),
                customer_data.get('notes', ''),
                contract_date,
                termination_date
            )
            
            cursor.execute(query, values)
            customer_id = cursor.lastrowid
            conn.commit()
            
            print(f"✅ 客户 '{customer_data['name']}' 添加成功，ID: {customer_id}")
            return customer_id
            
        except Exception as e:
            print(f"❌ 添加客户失败: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()
    
    def update_customer(self, customer_id: int, customer_data: Dict[str, Any], user_id: Optional[int] = None, username: Optional[str] = None) -> bool:
        """更新客户信息"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 首先获取当前客户信息，用于比较状态变化
            cursor.execute("""
                SELECT tracking_status FROM customers 
                WHERE id = %s AND deleted_at IS NULL
            """, (customer_id,))
            current_customer = cursor.fetchone()
            
            if not current_customer:
                print(f"❌ 客户 ID {customer_id} 不存在或已被删除")
                return False
            
            old_status = current_customer['tracking_status']
            new_status = customer_data.get('tracking_status', '初始接触')
            
            # 处理租赁类别（多选）
            rental_types = customer_data.get('rental_types', [])
            if isinstance(rental_types, list):
                rental_types_json = json.dumps(rental_types, ensure_ascii=False)
            else:
                rental_types_json = json.dumps([], ensure_ascii=False)
            
            # 处理日期字段
            contract_date = customer_data.get('contract_date')
            termination_date = customer_data.get('termination_date')
            
            # 如果日期字段为空字符串，设为None
            if contract_date == '':
                contract_date = None
            if termination_date == '':
                termination_date = None
            
            # 更新客户信息
            update_query = """
                UPDATE customers 
                SET name = %s, phone = %s, email = %s, property_address = %s, 
                    rental_types = %s, tracking_status = %s, notes = %s,
                    contract_date = %s, termination_date = %s
                WHERE id = %s AND deleted_at IS NULL
            """
            update_values = (
                customer_data['name'],
                customer_data.get('phone', ''),
                customer_data.get('email', ''),
                customer_data.get('property_address', ''),
                rental_types_json,
                new_status,
                customer_data.get('notes', ''),
                contract_date,
                termination_date,
                customer_id
            )
            
            cursor.execute(update_query, update_values)
            
            # 如果状态发生变化，自动添加状态变更记录
            if old_status != new_status:
                status_change_content = f"跟踪状态变更：{old_status} → {new_status}"
                if username:
                    status_change_content += f" (操作人：{username})"
                
                # 添加状态变更记录
                record_query = """
                    INSERT INTO customer_tracking_records (customer_id, record_date, content)
                    VALUES (%s, %s, %s)
                """
                record_values = (
                    customer_id,
                    datetime.now().date(),
                    status_change_content
                )
                
                cursor.execute(record_query, record_values)
                print(f"✅ 状态变更记录已添加：{old_status} → {new_status}")
            
            conn.commit()
            print(f"✅ 客户 ID {customer_id} 更新成功")
            return True
                
        except Exception as e:
            print(f"❌ 更新客户失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def delete_customer(self, customer_id: int) -> bool:
        """删除客户（软删除）"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            query = "UPDATE customers SET deleted_at = CURRENT_TIMESTAMP WHERE id = %s AND deleted_at IS NULL"
            cursor.execute(query, (customer_id,))
            
            if cursor.rowcount == 0:
                print(f"❌ 客户 ID {customer_id} 不存在或已被删除")
                return False
                
            conn.commit()
            print(f"✅ 客户 ID {customer_id} 删除成功")
            return True
                
        except Exception as e:
            print(f"❌ 删除客户失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def get_all_customers(self, page: int = 1, per_page: int = 20, search: str = '', status: str = '') -> Dict[str, Any]:
        """获取所有客户（分页）"""
        conn = self.get_db_connection()
        if not conn:
            return {'customers': [], 'total': 0, 'pages': 0, 'current_page': page}
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 构建查询条件
            where_conditions = ["deleted_at IS NULL"]
            params = []
            
            if search:
                where_conditions.append("(name LIKE %s OR phone LIKE %s OR email LIKE %s OR property_address LIKE %s)")
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param, search_param])
            
            if status:
                where_conditions.append("tracking_status = %s")
                params.append(status)
            
            where_clause = " AND ".join(where_conditions)
            
            # 获取总数
            count_query = f"SELECT COUNT(*) as total FROM customers WHERE {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * per_page
            query = f"""
                SELECT id, name, phone, email, property_address, rental_types, 
                       tracking_status, notes, contract_date, termination_date,
                       created_at, updated_at
                FROM customers 
                WHERE {where_clause}
                ORDER BY updated_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, params + [per_page, offset])
            customers = cursor.fetchall()
            
            # 处理JSON字段
            for customer in customers:
                if customer['rental_types']:
                    try:
                        customer['rental_types'] = json.loads(customer['rental_types'])
                    except:
                        customer['rental_types'] = []
                else:
                    customer['rental_types'] = []
            
            pages = (total + per_page - 1) // per_page
            
            return {
                'customers': customers,
                'total': total,
                'pages': pages,
                'current_page': page
            }
            
        except Exception as e:
            print(f"❌ 获取客户列表失败: {e}")
            return {'customers': [], 'total': 0, 'pages': 0, 'current_page': page}
        finally:
            cursor.close()
            conn.close()
    
    def get_customer_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取客户详情"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            query = """
                SELECT id, name, phone, email, property_address, rental_types, 
                       tracking_status, notes, contract_date, termination_date, 
                       created_at, updated_at
                FROM customers 
                WHERE id = %s AND deleted_at IS NULL
            """
            cursor.execute(query, (customer_id,))
            customer = cursor.fetchone()
            
            if customer and customer['rental_types']:
                try:
                    customer['rental_types'] = json.loads(customer['rental_types'])
                except:
                    customer['rental_types'] = []
            elif customer:
                customer['rental_types'] = []
            
            return customer
            
        except Exception as e:
            print(f"❌ 获取客户详情失败: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def add_tracking_record(self, customer_id: int, record_data: Dict[str, Any]) -> Optional[int]:
        """添加跟踪记录"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        try:
            query = """
                INSERT INTO customer_tracking_records (customer_id, record_date, content)
                VALUES (%s, %s, %s)
            """
            values = (
                customer_id,
                record_data['record_date'],
                record_data['content']
            )
            
            cursor.execute(query, values)
            record_id = cursor.lastrowid
            conn.commit()
            
            print(f"✅ 跟踪记录添加成功，ID: {record_id}")
            return record_id
            
        except Exception as e:
            print(f"❌ 添加跟踪记录失败: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()
    
    def get_tracking_records(self, customer_id: int) -> List[Dict[str, Any]]:
        """获取客户的所有跟踪记录"""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            query = """
                SELECT id, record_date, content, created_at
                FROM customer_tracking_records 
                WHERE customer_id = %s AND deleted_at IS NULL
                ORDER BY record_date DESC, created_at DESC
            """
            cursor.execute(query, (customer_id,))
            records = cursor.fetchall()
            
            return records
            
        except Exception as e:
            print(f"❌ 获取跟踪记录失败: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def update_tracking_record(self, record_id: int, record_data: Dict[str, Any]) -> bool:
        """更新跟踪记录"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            query = """
                UPDATE customer_tracking_records 
                SET record_date = %s, content = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND deleted_at IS NULL
            """
            values = (
                record_data['record_date'],
                record_data['content'],
                record_id
            )
            
            cursor.execute(query, values)
            
            if cursor.rowcount == 0:
                print(f"❌ 跟踪记录 ID {record_id} 不存在或已被删除")
                return False
            
            conn.commit()
            print(f"✅ 跟踪记录 ID {record_id} 更新成功")
            return True
            
        except Exception as e:
            print(f"❌ 更新跟踪记录失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def delete_tracking_record(self, record_id: int) -> bool:
        """删除跟踪记录（软删除）"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            query = "UPDATE customer_tracking_records SET deleted_at = CURRENT_TIMESTAMP WHERE id = %s AND deleted_at IS NULL"
            cursor.execute(query, (record_id,))
            
            if cursor.rowcount == 0:
                print(f"❌ 跟踪记录 ID {record_id} 不存在或已被删除")
                return False
                
            conn.commit()
            print(f"✅ 跟踪记录 ID {record_id} 删除成功")
            return True
                
        except Exception as e:
            print(f"❌ 删除跟踪记录失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def get_tracking_status_options(self) -> List[str]:
        """获取跟踪状态选项"""
        return [
            '初始接触',
            '需求了解',
            '看房安排',
            '价格谈判',
            '合同准备',
            '签约完成',
            '跟进服务',
            '已流失'
        ]
    
    def get_rental_type_options(self) -> List[str]:
        """获取租赁类别选项"""
        return [
            '短租',
            '中租', 
            '长租',
            '买卖'
        ]

# 创建全局实例
customer_tracking_manager = CustomerTrackingManager() 