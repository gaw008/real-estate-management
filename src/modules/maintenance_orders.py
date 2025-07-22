# -*- coding: utf-8 -*-
"""
维修工单管理模块
提供维修工单的创建、查询、更新、删除等功能
"""

import mysql.connector
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.config import DB_CONFIG, CA_CERTIFICATE


class MaintenanceOrdersManager:
    """维修工单管理器"""
    
    def __init__(self):
        """初始化维修工单管理器"""
        self.db_config = DB_CONFIG
        self.ca_certificate = CA_CERTIFICATE
    
    def get_db_connection(self):
        """获取数据库连接"""
        try:
            # 使用系统统一的数据库连接方法
            from core.real_estate_web import get_db_connection
            return get_db_connection()
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return None
    
    def create_maintenance_orders_table(self):
        """创建维修工单表"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            # 创建维修工单表
            orders_sql = """
            CREATE TABLE IF NOT EXISTS maintenance_orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                property_id VARCHAR(20) NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT NOT NULL,
                assigned_to VARCHAR(100) NOT NULL,
                assigned_phone VARCHAR(20),
                tracked_by INT NOT NULL,
                priority ENUM('低', '中', '高', '紧急') DEFAULT '中',
                estimated_cost DECIMAL(10,2) DEFAULT 0.00,
                estimated_completion_date DATE,
                status ENUM('待处理', '进行中', '已完成', '已取消') DEFAULT '待处理',
                actual_cost DECIMAL(10,2) DEFAULT NULL,
                actual_completion_date DATE DEFAULT NULL,
                created_by INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                notes TEXT,
                
                INDEX idx_property_id (property_id),
                INDEX idx_assigned_to (assigned_to),
                INDEX idx_tracked_by (tracked_by),
                INDEX idx_status (status),
                INDEX idx_priority (priority),
                INDEX idx_created_at (created_at),
                INDEX idx_estimated_completion_date (estimated_completion_date),
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE RESTRICT,
                FOREIGN KEY (tracked_by) REFERENCES users(id) ON DELETE RESTRICT,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(orders_sql)
            conn.commit()
            print("✅ 维修工单表创建成功")
            return True
        except Exception as e:
            print(f"❌ 创建维修工单表失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def add_maintenance_order(self, order_data: Dict) -> Tuple[bool, str]:
        """添加维修工单"""
        conn = self.get_db_connection()
        if not conn:
            return False, "数据库连接失败"
        
        cursor = conn.cursor()
        
        try:
            sql = """
            INSERT INTO maintenance_orders (
                property_id, title, description, assigned_to, assigned_phone, tracked_by,
                priority, estimated_cost, estimated_completion_date,
                created_by, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                order_data['property_id'],
                order_data['title'],
                order_data['description'],
                order_data['assigned_to'],
                order_data.get('assigned_phone', ''),
                order_data['tracked_by'],
                order_data['priority'],
                order_data['estimated_cost'],
                order_data['estimated_completion_date'],
                order_data['created_by'],
                order_data.get('notes', '')
            )
            
            cursor.execute(sql, values)
            conn.commit()
            
            order_id = cursor.lastrowid
            print(f"✅ 维修工单创建成功，ID: {order_id}")
            return True, f"维修工单创建成功"
            
        except Exception as e:
            print(f"❌ 创建维修工单失败: {e}")
            conn.rollback()
            return False, f"创建维修工单失败: {e}"
        finally:
            cursor.close()
            conn.close()
    
    def get_all_orders(self, page: int = 1, per_page: int = 20, 
                      search: str = '', property_id: str = '', 
                      status: str = '', priority: str = '') -> Tuple[List[Dict], int]:
        """获取所有维修工单"""
        conn = self.get_db_connection()
        if not conn:
            return [], 0
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 构建查询条件
            where_conditions = []
            params = []
            
            if search:
                where_conditions.append("(mo.title LIKE %s OR mo.description LIKE %s)")
                params.extend([f'%{search}%', f'%{search}%'])
            
            if property_id:
                where_conditions.append("mo.property_id = %s")
                params.append(property_id)
            
            if status:
                where_conditions.append("mo.status = %s")
                params.append(status)
            
            if priority:
                where_conditions.append("mo.priority = %s")
                params.append(priority)
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # 获取总数
            count_sql = f"""
            SELECT COUNT(*) as total FROM maintenance_orders mo 
            WHERE {where_clause}
            """
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * per_page
            sql = f"""
            SELECT 
                mo.*,
                p.street_address as property_address,
                p.city as property_city,
                p.state as property_state,
                mo.assigned_to as assigned_name,
                tracked.full_name as tracked_name,
                creator.full_name as creator_name
            FROM maintenance_orders mo
            LEFT JOIN properties p ON mo.property_id = p.id
            LEFT JOIN users tracked ON mo.tracked_by = tracked.id
            LEFT JOIN users creator ON mo.created_by = creator.id
            WHERE {where_clause}
            ORDER BY mo.created_at DESC
            LIMIT %s OFFSET %s
            """
            
            cursor.execute(sql, params + [per_page, offset])
            orders = cursor.fetchall()
            
            return orders, total
            
        except Exception as e:
            print(f"❌ 获取维修工单失败: {e}")
            return [], 0
        finally:
            cursor.close()
            conn.close()
    
    def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        """根据ID获取维修工单详情"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            sql = """
            SELECT 
                mo.*,
                p.street_address as property_address,
                p.city as property_city,
                p.state as property_state,
                mo.assigned_to as assigned_name,
                tracked.full_name as tracked_name,
                creator.full_name as creator_name
            FROM maintenance_orders mo
            LEFT JOIN properties p ON mo.property_id = p.id
            LEFT JOIN users tracked ON mo.tracked_by = tracked.id
            LEFT JOIN users creator ON mo.created_by = creator.id
            WHERE mo.id = %s
            """
            
            cursor.execute(sql, (order_id,))
            order = cursor.fetchone()
            
            return order
            
        except Exception as e:
            print(f"❌ 获取维修工单详情失败: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def update_order(self, order_id: int, update_data: Dict) -> Tuple[bool, str]:
        """更新维修工单"""
        conn = self.get_db_connection()
        if not conn:
            return False, "数据库连接失败"
        
        cursor = conn.cursor()
        
        try:
            # 构建更新字段
            update_fields = []
            params = []
            
            for field, value in update_data.items():
                if field in ['title', 'description', 'assigned_to', 'assigned_phone', 'tracked_by', 
                           'priority', 'estimated_cost', 'estimated_completion_date', 
                           'status', 'actual_cost', 'actual_completion_date', 'notes']:
                    update_fields.append(f"{field} = %s")
                    params.append(value)
            
            if not update_fields:
                return False, "没有有效的更新字段"
            
            params.append(order_id)
            sql = f"""
            UPDATE maintenance_orders 
            SET {', '.join(update_fields)}
            WHERE id = %s
            """
            
            cursor.execute(sql, params)
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"✅ 维修工单更新成功，ID: {order_id}")
                return True, "维修工单更新成功"
            else:
                return False, "维修工单不存在或没有变化"
            
        except Exception as e:
            print(f"❌ 更新维修工单失败: {e}")
            conn.rollback()
            return False, f"更新维修工单失败: {e}"
        finally:
            cursor.close()
            conn.close()
    
    def delete_order(self, order_id: int, admin_id: int) -> Tuple[bool, str]:
        """删除维修工单"""
        conn = self.get_db_connection()
        if not conn:
            return False, "数据库连接失败"
        
        cursor = conn.cursor()
        
        try:
            # 检查工单是否存在
            check_sql = "SELECT title FROM maintenance_orders WHERE id = %s"
            cursor.execute(check_sql, (order_id,))
            result = cursor.fetchone()
            
            if not result:
                return False, "维修工单不存在"
            
            order_title = result[0]
            
            # 删除工单
            delete_sql = "DELETE FROM maintenance_orders WHERE id = %s"
            cursor.execute(delete_sql, (order_id,))
            conn.commit()
            
            print(f"✅ 维修工单删除成功: {order_title}")
            return True, f"维修工单 '{order_title}' 删除成功"
            
        except Exception as e:
            print(f"❌ 删除维修工单失败: {e}")
            conn.rollback()
            return False, f"删除维修工单失败: {e}"
        finally:
            cursor.close()
            conn.close()
    
    def get_order_stats(self) -> Dict:
        """获取维修工单统计信息"""
        conn = self.get_db_connection()
        if not conn:
            return {
                'total_orders': 0,
                'status_counts': {},
                'priority_counts': {},
                'this_month_orders': 0,
                'overdue_orders': 0
            }
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 总工单数
            cursor.execute("SELECT COUNT(*) as total FROM maintenance_orders")
            total_orders = cursor.fetchone()['total']
            
            # 各状态工单数
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM maintenance_orders 
                GROUP BY status
            """)
            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # 各优先级工单数
            cursor.execute("""
                SELECT priority, COUNT(*) as count 
                FROM maintenance_orders 
                GROUP BY priority
            """)
            priority_counts = {row['priority']: row['count'] for row in cursor.fetchall()}
            
            # 本月新增工单数
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM maintenance_orders 
                WHERE MONTH(created_at) = MONTH(NOW()) 
                AND YEAR(created_at) = YEAR(NOW())
            """)
            this_month_orders = cursor.fetchone()['count']
            
            # 逾期工单数（超过预计完成日期且未完成）
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM maintenance_orders 
                WHERE estimated_completion_date < CURDATE() 
                AND status NOT IN ('已完成', '已取消')
            """)
            overdue_orders = cursor.fetchone()['count']
            
            return {
                'total_orders': total_orders,
                'status_counts': status_counts,
                'priority_counts': priority_counts,
                'this_month_orders': this_month_orders,
                'overdue_orders': overdue_orders
            }
            
        except Exception as e:
            print(f"❌ 获取维修工单统计失败: {e}")
            return {
                'total_orders': 0,
                'status_counts': {},
                'priority_counts': {},
                'this_month_orders': 0,
                'overdue_orders': 0
            }
        finally:
            cursor.close()
            conn.close()
    
    def get_properties_for_select(self) -> List[Dict]:
        """获取房产列表用于下拉选择"""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            sql = """
            SELECT id, street_address as address, city, state 
            FROM properties 
            WHERE deleted_at IS NULL
            ORDER BY street_address
            """
            cursor.execute(sql)
            properties = cursor.fetchall()
            
            return properties
            
        except Exception as e:
            print(f"❌ 获取房产列表失败: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def get_users_for_select(self) -> List[Dict]:
        """获取用户列表用于下拉选择"""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            sql = """
            SELECT id, username, full_name, user_type 
            FROM users 
            WHERE is_active = 1
            ORDER BY full_name, username
            """
            cursor.execute(sql)
            users = cursor.fetchall()
            
            return users
            
        except Exception as e:
            print(f"❌ 获取用户列表失败: {e}")
            return []
        finally:
            cursor.close()
            conn.close()


# 创建全局实例
maintenance_orders_manager = MaintenanceOrdersManager() 