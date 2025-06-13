# 房地产管理系统 - 员工权限管理

## 🏢 系统概述

本系统实现了基于角色的员工权限管理，支持4种员工角色和6个功能模块，确保不同职位的员工只能访问相应的功能。

## 👥 员工角色

### 1. 系统管理员 (Admin)
- **权限**: 全权限访问所有功能
- **账号**: `admin` / `admin123`
- **功能**: 
  - 房产信息管理
  - 新客户进度管理
  - 房屋维修记录
  - 房屋清洁记录
  - 财务记录管理
  - 屋主信息管理
  - 用户管理

### 2. 房产经理 (Property Manager)
- **权限**: 房产维护相关功能
- **账号**: `property_manager` / `pm123`
- **功能**:
  - 房产信息管理
  - 房屋维修记录
  - 房屋清洁记录

### 3. 销售专员 (Sales)
- **权限**: 客户关系管理
- **账号**: `sales` / `sales123`
- **功能**:
  - 房产信息管理
  - 新客户进度管理
  - 屋主信息管理

### 4. 财务会计 (Accounting)
- **权限**: 财务数据管理
- **账号**: `accounting` / `acc123`
- **功能**:
  - 房产信息管理
  - 财务记录管理
  - 屋主信息管理

## 🏗️ 功能模块

### 1. 房产信息管理 (Property Information)
- **访问权限**: 所有员工
- **功能**: 查看和管理房产基本信息
- **路由**: `/property_information`

### 2. 新客户进度管理 (Customer Progress)
- **访问权限**: Admin, Sales
- **功能**: 跟踪客户看房进度，管理客户信息
- **路由**: `/customer_progress`
- **数据表**: `customer_progress`

### 3. 房屋维修记录 (Maintenance Records)
- **访问权限**: Admin, Property Manager
- **功能**: 记录房屋维修情况，管理维修成本
- **路由**: `/maintenance_records`
- **数据表**: `maintenance_records`

### 4. 房屋清洁记录 (Cleaning Records)
- **访问权限**: Admin, Property Manager
- **功能**: 管理房屋清洁安排，记录清洁费用
- **路由**: `/cleaning_records`
- **数据表**: `cleaning_records`

### 5. 财务记录管理 (Financial Records)
- **访问权限**: Admin, Accounting
- **功能**: 管理财务报表，查看收入支出
- **路由**: `/financial_records`

### 6. 屋主信息管理 (Owner Information)
- **访问权限**: Admin, Sales, Accounting
- **功能**: 查看和管理业主信息
- **路由**: `/owner_information`

## 🔐 权限控制

### 权限装饰器
- `@admin_required`: 仅管理员可访问
- `@property_manager_required`: 管理员和房产经理可访问
- `@sales_required`: 管理员和销售专员可访问
- `@accounting_required`: 管理员和财务会计可访问
- `@staff_required`: 所有员工可访问
- `@owner_required`: 仅业主可访问

### 权限检查函数
```python
has_module_access(module_name)
```
动态检查用户是否有访问指定模块的权限。

## 🗄️ 数据库表结构

### 用户表 (users)
```sql
user_type ENUM('admin', 'property_manager', 'sales', 'accounting', 'owner')
```

### 客户进度表 (customer_progress)
```sql
CREATE TABLE customer_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    contact_info VARCHAR(200) NOT NULL,
    property_interest TEXT,
    status ENUM('initial_contact', 'viewing_scheduled', 'viewed', 'interested', 'negotiating', 'closed', 'lost'),
    notes TEXT,
    sales_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 维修记录表 (maintenance_records)
```sql
CREATE TABLE maintenance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id VARCHAR(20) NOT NULL,
    issue_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    cost DECIMAL(10,2) DEFAULT 0.00,
    status ENUM('pending', 'in_progress', 'completed', 'cancelled'),
    contractor VARCHAR(100),
    manager_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL
);
```

### 清洁记录表 (cleaning_records)
```sql
CREATE TABLE cleaning_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id VARCHAR(20) NOT NULL,
    cleaning_type ENUM('regular', 'deep', 'move_out', 'move_in'),
    cleaning_date DATE NOT NULL,
    cost DECIMAL(10,2) DEFAULT 0.00,
    cleaner_name VARCHAR(100),
    notes TEXT,
    manager_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 使用方法

### 1. 启动系统
```bash
python3 real_estate_web.py
```

### 2. 访问员工登录页面
- 主登录页面: `http://localhost:8888/login`
- 员工登录页面: `http://localhost:8888/staff_login`

### 3. 使用示例账户登录
选择对应的角色并使用相应的账号密码登录。

### 4. 访问功能模块
登录后会自动跳转到员工仪表板，根据角色显示可访问的功能模块。

## 🎨 用户界面特性

### 员工仪表板
- 现代化卡片式布局
- 根据角色动态显示功能模块
- 无权限模块显示锁定状态
- 响应式设计，支持移动设备

### 角色选择登录
- 可视化角色选择界面
- 实时显示角色权限说明
- 美观的渐变色设计

### 权限提示
- 清晰的权限错误提示
- 友好的用户体验
- 自动重定向到合适页面

## 🔧 技术实现

### 后端技术
- Flask Web框架
- MySQL数据库
- 基于装饰器的权限控制
- 会话管理和用户认证

### 前端技术
- Bootstrap 5响应式框架
- Font Awesome图标库
- 现代CSS3动画效果
- JavaScript交互功能

### 安全特性
- 密码哈希存储
- 会话超时管理
- SQL注入防护
- 权限验证机制

## 📝 开发说明

### 添加新角色
1. 修改`auth_system.py`中的用户类型枚举
2. 创建对应的权限装饰器
3. 更新`has_module_access`函数的权限映射

### 添加新功能模块
1. 创建路由和视图函数
2. 添加相应的权限装饰器
3. 更新员工仪表板模板
4. 创建对应的数据库表（如需要）

### 自定义权限
可以通过修改`module_permissions`字典来调整各角色的模块访问权限。

## 🎯 系统优势

1. **模块化设计**: 功能模块独立，易于维护和扩展
2. **灵活权限**: 基于角色的权限控制，支持细粒度权限管理
3. **用户友好**: 直观的界面设计，清晰的权限提示
4. **安全可靠**: 完善的认证和授权机制
5. **响应式**: 支持各种设备访问
6. **可扩展**: 易于添加新角色和功能模块 