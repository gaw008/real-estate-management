"""
房地产管理系统 - 用户模块权限管理
支持为每个用户单独设置可访问的模块权限
"""

import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 系统模块定义
SYSTEM_MODULES = {
    'property_info': {
        'name': '房产信息管理',
        'description': '查看和管理房产基本信息',
        'icon': 'fas fa-home',
        'color': '#007bff'
    },
    'customer_management': {
        'name': '客户管理',
        'description': '管理客户信息和进度跟踪',
        'icon': 'fas fa-users',
        'color': '#28a745'
    },
    'customer_tracking': {
        'name': '客户跟踪',
        'description': '跟踪客户看房进度',
        'icon': 'fas fa-chart-line',
        'color': '#17a2b8'
    },
    'maintenance_records': {
        'name': '维修记录',
        'description': '管理房屋维修记录',
        'icon': 'fas fa-tools',
        'color': '#ffc107'
    },

    'financial_records': {
        'name': '财务记录',
        'description': '查看和管理财务数据',
        'icon': 'fas fa-dollar-sign',
        'color': '#dc3545'
    },
    'financial_records_view': {
        'name': '财务查看',
        'description': '仅查看财务数据',
        'icon': 'fas fa-eye',
        'color': '#6c757d'
    },
    'owner_info': {
        'name': '业主信息',
        'description': '管理业主信息',
        'icon': 'fas fa-user-tie',
        'color': '#fd7e14'
    },
    'user_management': {
        'name': '用户管理',
        'description': '管理系统用户和权限',
        'icon': 'fas fa-user-cog',
        'color': '#e83e8c'
    },
    'employee_departments': {
        'name': '员工部门',
        'description': '管理员工部门信息',
        'icon': 'fas fa-building',
        'color': '#20c997'
    },
    'system_settings': {
        'name': '系统设置',
        'description': '管理系统配置',
        'icon': 'fas fa-cogs',
        'color': '#6c757d'
    },
    'registration_management': {
        'name': '注册管理',
        'description': '管理用户注册申请',
        'icon': 'fas fa-user-plus',
        'color': '#28a745'
    }
}

class UserModulePermissions:
    """用户模块权限管理类"""
    
    def __init__(self, db_config):
        """初始化数据库连接配置"""
        self.db_config = db_config
        self.create_user_module_permissions_table()
    
    def get_db_connection(self):
        """获取数据库连接"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            if connection.is_connected():
                return connection
        except Error as e:
            logger.error(f"数据库连接失败: {e}")
            return None
    
    def create_user_module_permissions_table(self):
        """创建用户模块权限表"""
        try:
            connection = self.get_db_connection()
            if not connection:
                return False
            
            cursor = connection.cursor()
            
            # 创建用户模块权限表
            create_table_query = """
            CREATE TABLE IF NOT EXISTS user_module_permissions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                module_name VARCHAR(50) NOT NULL,
                can_access BOOLEAN DEFAULT TRUE,
                can_edit BOOLEAN DEFAULT FALSE,
                can_delete BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_user_module (user_id, module_name),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_table_query)
            connection.commit()
            
            logger.info("✅ 用户模块权限表创建成功")
            return True
            
        except Error as e:
            logger.error(f"❌ 创建用户模块权限表失败: {e}")
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_user_modules(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的可访问模块列表"""
        try:
            connection = self.get_db_connection()
            if not connection:
                return []
            
            cursor = connection.cursor(dictionary=True)
            
            query = """
            SELECT module_name, can_access, can_edit, can_delete
            FROM user_module_permissions
            WHERE user_id = %s AND can_access = TRUE
            """
            
            cursor.execute(query, (user_id,))
            user_modules = cursor.fetchall()
            
            # 转换为模块信息格式
            result = []
            for module in user_modules:
                module_info = SYSTEM_MODULES.get(module['module_name'], {})
                result.append({
                    'module_name': module['module_name'],
                    'name': module_info.get('name', module['module_name']),
                    'description': module_info.get('description', ''),
                    'icon': module_info.get('icon', 'fas fa-cube'),
                    'color': module_info.get('color', '#6c757d'),
                    'can_access': module['can_access'],
                    'can_edit': module['can_edit'],
                    'can_delete': module['can_delete']
                })
            
            return result
            
        except Error as e:
            logger.error(f"❌ 获取用户模块失败: {e}")
            return []
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def has_module_access(self, user_id: int, module_name: str) -> bool:
        """检查用户是否有访问指定模块的权限"""
        try:
            connection = self.get_db_connection()
            if not connection:
                return False
            
            cursor = connection.cursor()
            
            query = """
            SELECT can_access FROM user_module_permissions
            WHERE user_id = %s AND module_name = %s AND can_access = TRUE
            """
            
            cursor.execute(query, (user_id, module_name))
            result = cursor.fetchone()
            
            return result is not None
            
        except Error as e:
            logger.error(f"❌ 检查模块权限失败: {e}")
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def set_user_modules(self, user_id: int, modules: List[Dict[str, Any]]) -> bool:
        """设置用户的模块权限"""
        try:
            connection = self.get_db_connection()
            if not connection:
                return False
            
            cursor = connection.cursor()
            
            # 先删除用户的所有模块权限
            delete_query = "DELETE FROM user_module_permissions WHERE user_id = %s"
            cursor.execute(delete_query, (user_id,))
            
            # 插入新的模块权限
            insert_query = """
            INSERT INTO user_module_permissions 
            (user_id, module_name, can_access, can_edit, can_delete)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            for module in modules:
                cursor.execute(insert_query, (
                    user_id,
                    module['module_name'],
                    module.get('can_access', True),
                    module.get('can_edit', False),
                    module.get('can_delete', False)
                ))
            
            connection.commit()
            logger.info(f"✅ 用户 {user_id} 的模块权限设置成功")
            return True
            
        except Error as e:
            logger.error(f"❌ 设置用户模块权限失败: {e}")
            if connection:
                connection.rollback()
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_all_modules(self) -> List[Dict[str, Any]]:
        """获取所有系统模块列表"""
        return [
            {
                'module_name': name,
                'name': info['name'],
                'description': info['description'],
                'icon': info['icon'],
                'color': info['color']
            }
            for name, info in SYSTEM_MODULES.items()
        ]
    
    def get_user_modules_summary(self, user_id: int) -> Dict[str, Any]:
        """获取用户模块权限摘要"""
        try:
            connection = self.get_db_connection()
            if not connection:
                return {}
            
            cursor = connection.cursor(dictionary=True)
            
            # 获取用户基本信息
            user_query = "SELECT username, full_name, user_type, department FROM users WHERE id = %s"
            cursor.execute(user_query, (user_id,))
            user_info = cursor.fetchone()
            
            if not user_info:
                return {}
            
            # 获取用户模块权限
            modules = self.get_user_modules(user_id)
            
            return {
                'user_info': user_info,
                'modules': modules,
                'total_modules': len(modules),
                'all_modules': self.get_all_modules()
            }
            
        except Error as e:
            logger.error(f"❌ 获取用户模块摘要失败: {e}")
            return {}
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def initialize_user_modules(self, user_id: int, user_type: str, department: str = None) -> bool:
        """根据用户类型和部门初始化用户模块权限"""
        try:
            # 基于部门权限的默认模块分配
            department_modules = {
                'admin': ['property_info', 'customer_management', 'customer_tracking', 
                         'maintenance_records', 'financial_records', 
                         'owner_info', 'user_management', 'employee_departments', 
                         'system_settings', 'registration_management'],
                'property_manager': ['property_info', 'customer_management', 'customer_tracking', 
                                   'maintenance_records', 'financial_records_view', 
                                   'owner_info', 'employee_departments'],
                'sales': ['property_info', 'customer_management', 'customer_tracking', 'owner_info'],
                'accounting': ['financial_records', 'owner_info', 'financial_records_view'],
                'marketing': ['property_info', 'customer_management', 'customer_tracking'],
                'owner': ['property_info', 'financial_records_view', 'owner_info']
            }
            
            # 获取默认模块
            default_modules = department_modules.get(user_type, [])
            
            # 转换为权限格式
            modules = []
            for module_name in default_modules:
                modules.append({
                    'module_name': module_name,
                    'can_access': True,
                    'can_edit': user_type == 'admin',  # 只有管理员可以编辑
                    'can_delete': user_type == 'admin'  # 只有管理员可以删除
                })
            
            # 设置用户模块权限
            return self.set_user_modules(user_id, modules)
            
        except Exception as e:
            logger.error(f"❌ 初始化用户模块权限失败: {e}")
            return False

# 全局实例
user_module_permissions = None

def init_user_module_permissions(db_config):
    """初始化用户模块权限管理器"""
    global user_module_permissions
    user_module_permissions = UserModulePermissions(db_config)
    return user_module_permissions

def get_user_module_permissions():
    """获取用户模块权限管理器实例"""
    return user_module_permissions 