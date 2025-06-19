"""
房地产管理系统 - 部门模块管理
基于部门权限的功能模块分配和访问控制
"""

from functools import wraps
from flask import session, flash, redirect, url_for

# ==================== 部门权限配置 ====================

# 部门权限映射表
DEPARTMENT_PERMISSIONS = {
    'Admin': {
        'modules': ['property_info', 'customer_management', 'maintenance_records', 
                   'cleaning_records', 'financial_records', 'owner_info', 
                   'user_management', 'employee_departments', 'system_settings'],
        'description': '系统管理员 - 拥有全部权限'
    },
    'Property Management Department': {
        'modules': ['property_info', 'customer_management', 'maintenance_records', 
                   'cleaning_records', 'financial_records_view'],
        'description': '房产管理部 - 房产运营核心'
    },
    'Sales Department': {
        'modules': ['property_info', 'customer_management', 'owner_info'],
        'description': '销售部 - 客户关系管理'
    },
    'Accounting Department': {
        'modules': ['financial_records', 'owner_info', 'financial_reports'],
        'description': '财务部 - 财务管理专精'
    }
}

# 模块描述配置
MODULE_DESCRIPTIONS = {
    'property_info': {
        'name': '房产信息管理',
        'description': '房产基础信息、状态管理、房产展示',
        'icon': '🏠',
        'color': 'success'
    },
    'customer_management': {
        'name': '客户建档管理',
        'description': '客户信息、租户管理、客户关系维护',
        'icon': '👥',
        'color': 'primary'
    },
    'maintenance_records': {
        'name': '维修记录管理',
        'description': '房产维护、维修工单、设备管理',
        'icon': '🔧',
        'color': 'warning'
    },
    'cleaning_records': {
        'name': '清洁记录管理',
        'description': '清洁服务、保洁工单、环境维护',
        'icon': '🧹',
        'color': 'info'
    },
    'financial_records': {
        'name': '财务记录管理',
        'description': '收支管理、账目记录、财务分析',
        'icon': '💰',
        'color': 'danger'
    },
    'financial_records_view': {
        'name': '财务记录查看',
        'description': '查看相关财务数据（只读权限）',
        'icon': '📊',
        'color': 'secondary'
    },
    'owner_info': {
        'name': '业主信息管理',
        'description': '业主档案、联系方式、业主关系',
        'icon': '👤',
        'color': 'dark'
    },
    'user_management': {
        'name': '用户管理',
        'description': '用户账户、权限分配、系统用户',
        'icon': '⚙️',
        'color': 'danger'
    },
    'employee_departments': {
        'name': '员工部门管理',
        'description': '员工分组、部门设置、组织架构',
        'icon': '🏢',
        'color': 'primary'
    },
    'financial_reports': {
        'name': '财务报表',
        'description': '财务分析、报表生成、数据统计',
        'icon': '📈',
        'color': 'success'
    }
}

# ==================== 权限检查函数 ====================

def get_user_department():
    """获取当前用户部门"""
    return session.get('department', '')

def get_user_accessible_modules():
    """获取当前用户可访问的模块列表"""
    user_type = session.get('user_type', '')
    user_department = get_user_department()
    
    # 如果是管理员，返回所有模块
    if user_type == 'admin':
        return DEPARTMENT_PERMISSIONS['Admin']['modules']
    
    # 根据部门返回对应模块
    return DEPARTMENT_PERMISSIONS.get(user_department, {}).get('modules', [])

def has_module_access(module_name):
    """检查用户是否有访问指定模块的权限"""
    accessible_modules = get_user_accessible_modules()
    return module_name in accessible_modules

def get_department_info(department_name):
    """获取部门信息"""
    return DEPARTMENT_PERMISSIONS.get(department_name, {})

def get_module_info(module_name):
    """获取模块信息"""
    return MODULE_DESCRIPTIONS.get(module_name, {})

# ==================== 权限装饰器 ====================

def module_required(module_name):
    """模块权限验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('请先登录', 'warning')
                return redirect(url_for('login'))
            
            if not has_module_access(module_name):
                module_info = get_module_info(module_name)
                flash(f'您没有访问"{module_info.get("name", module_name)}"模块的权限', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def department_required(allowed_departments):
    """部门权限验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('请先登录', 'warning')
                return redirect(url_for('login'))
            
            user_type = session.get('user_type', '')
            user_department = get_user_department()
            
            # 管理员总是有权限
            if user_type == 'admin':
                return f(*args, **kwargs)
            
            # 检查部门权限
            if user_department not in allowed_departments:
                flash(f'此功能需要以下部门权限之一：{", ".join(allowed_departments)}', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== 部门仪表板数据生成 ====================

def generate_department_dashboard_data():
    """生成部门专属仪表板数据"""
    user_type = session.get('user_type', '')
    user_department = get_user_department()
    
    # 获取用户可访问的模块
    accessible_modules = get_user_accessible_modules()
    
    # 生成模块卡片数据
    modules_data = []
    for module in accessible_modules:
        module_info = get_module_info(module)
        if module_info:
            modules_data.append({
                'name': module,
                'display_name': module_info.get('name', module),
                'description': module_info.get('description', ''),
                'icon': module_info.get('icon', '📋'),
                'color': module_info.get('color', 'primary'),
                'url': f'/{module.replace("_", "-")}'
            })
    
    # 部门信息
    department_info = get_department_info(user_department) if user_department else {}
    
    return {
        'user_type': user_type,
        'user_department': user_department,
        'department_description': department_info.get('description', ''),
        'accessible_modules': accessible_modules,
        'modules_data': modules_data,
        'total_modules': len(modules_data)
    }

# ==================== 模块路由映射 ====================

MODULE_ROUTES = {
    'property_info': '/properties',
    'customer_management': '/customers',
    'maintenance_records': '/maintenance',
    'cleaning_records': '/cleaning',
    'financial_records': '/admin/financial_reports',
    'financial_records_view': '/financial-view',
    'owner_info': '/owners',
    'user_management': '/admin/user_management',
    'employee_departments': '/admin/employee_departments',
    'financial_reports': '/admin/financial_reports'
}

def get_module_url(module_name):
    """获取模块的URL路径"""
    return MODULE_ROUTES.get(module_name, f'/{module_name.replace("_", "-")}') 