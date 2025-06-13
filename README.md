# 🏡 房地产管理系统 Real Estate Management System

一个基于Python和MySQL的房地产管理系统，支持数据导入、查询分析和Web界面管理。

## 🚀 功能特性

- **数据导入**: 从CSV文件导入房产、业主和财务数据到Aiven MySQL云数据库
- **智能查询**: 支持自然语言查询和SQL查询
- **Web界面**: 基于Flask的现代化Web管理界面
- **性能优化**: 针对检索效率优化的数据库架构
- **安全配置**: 支持环境变量和配置文件的安全配置方式

## 📁 项目结构

```
sqldatabase/
├── 📊 数据文件
│   ├── Database - Properties.csv      # 房产数据
│   ├── Database - Owners.csv          # 业主数据
│   └── Database - Finance.csv         # 财务数据
├── 🐍 Python脚本
│   ├── import_to_aiven_mysql.py       # 数据导入脚本
│   ├── natural_language_query.py      # 自然语言查询工具
│   ├── query_aiven_database.py        # 数据库查询脚本
│   └── real_estate_web.py             # Web应用
├── ⚙️ 配置文件
│   ├── config_loader.py               # 安全配置加载器
│   ├── config_example.py              # 配置文件模板
│   └── .gitignore                     # Git忽略文件
├── 🎨 前端文件
│   └── templates/                     # HTML模板
└── 📋 文档
    ├── database_visualization.html    # 数据库架构可视化
    └── README.md                      # 项目说明
```

## 🔧 安装和配置

### 1. 安装依赖

```bash
pip install mysql-connector-python pandas python-dateutil flask
```

### 2. 数据库配置

**方式一：环境变量（推荐）**

```bash
export DB_HOST='your-mysql-host.com'
export DB_PORT='3306'
export DB_DATABASE='your-database-name'
export DB_USER='your-username'
export DB_PASSWORD='your-password'
export DB_CA_CERTIFICATE='-----BEGIN CERTIFICATE-----
...your-ca-certificate...
-----END CERTIFICATE-----'
```

**方式二：配置文件**

1. 复制配置模板：
```bash
cp config_example.py config.py
```

2. 编辑 `config.py` 文件，填入您的数据库信息：
```python
DB_CONFIG = {
    'host': 'your-mysql-host.com',
    'port': 3306,
    'database': 'your-database-name',
    'user': 'your-username',
    'password': 'your-password',
    # ... 其他配置
}
```

⚠️ **安全提醒**: `config.py` 文件包含敏感信息，已添加到 `.gitignore` 中，不会被提交到版本控制系统。

## 🚀 使用方法

### 1. 数据导入

```bash
python import_to_aiven_mysql.py
```

这将：
- 连接到Aiven MySQL数据库
- 创建优化的表结构
- 导入CSV数据
- 验证数据完整性

### 2. 自然语言查询

```bash
python natural_language_query.py
```

支持中文查询，例如：
- "有多少个房产？"
- "加州有多少房产？"
- "显示管理费率分布"

### 3. Web界面

```bash
python real_estate_web.py
```

访问 http://localhost:8888 查看Web界面，包括：
- 房产列表和详情
- 业主信息管理
- 数据统计分析
- 搜索和筛选功能

### 4. 数据库查询

```bash
python query_aiven_database.py
```

执行预定义的查询和性能测试。

## 🏗️ 数据库架构

系统采用4表架构，针对检索效率优化：

1. **Properties** (房产主表)
   - 房产基本信息
   - 地理位置索引
   - 容量和面积索引

2. **Owners_Master** (业主主表)
   - 去重的业主信息
   - 姓名和邮箱索引

3. **Property_Owners** (关系表)
   - 房产-业主多对多关系
   - 支持共同所有权

4. **Finance** (财务表)
   - 管理费和合同信息
   - 日期和费率索引

## 📊 性能目标

- 地理位置查询: < 50ms
- 业主查询: < 5ms  
- 统计分析查询: < 100ms

## 🔒 安全特性

- 敏感信息不硬编码在代码中
- 支持环境变量配置
- SSL/TLS加密连接
- 配置文件自动忽略提交

## 📈 数据统计

- 房产数量: 113条记录
- 业主数量: 91条记录（去重后）
- 财务记录: 93条记录
- 支持的州: 加州、德州等多个州

## 🛠️ 开发说明

### 添加新功能

1. 数据库相关功能请参考现有脚本的连接和查询模式
2. Web功能请在 `real_estate_web.py` 中添加新路由
3. 查询功能请在 `natural_language_query.py` 中添加新模式

### 配置管理

系统使用 `config_loader.py` 统一管理配置，支持：
- 环境变量优先级最高
- 配置文件作为备选
- 默认值保证系统可运行

## 📝 许可证

本项目仅供学习和内部使用。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目。

---

**注意**: 请确保在生产环境中使用强密码和适当的安全配置。

# 房地产管理系统

一个功能完整的房地产管理系统，支持用户注册、密码管理、房产管理等功能。

## 🚀 功能特性

### 用户管理
- ✅ 用户注册申请系统（支持员工和业主注册）
- ✅ 管理员审核注册申请
- ✅ 基于角色的访问控制（管理员/业主）
- ✅ 用户认证和会话管理

### 密码管理
- ✅ 用户自主修改密码
- ✅ 管理员重置用户密码
- ✅ 密码重置令牌系统
- ✅ 密码修改历史记录和审计日志
- ✅ 密码强度检查

### 房产管理
- ✅ 房产信息管理
- ✅ 业主信息管理
- ✅ 财务数据管理
- ✅ 数据统计和报表

## 🛠️ 技术栈

- **后端**: Python Flask
- **数据库**: MySQL (支持Aiven云数据库)
- **前端**: HTML5, CSS3, JavaScript, Bootstrap
- **安全**: PBKDF2-HMAC-SHA256密码哈希

## 📦 安装和配置

### 1. 克隆项目
```bash
git clone https://github.com/gaw008/real-estate-management.git
cd real-estate-management
```

### 2. 安装依赖
```bash
pip install flask mysql-connector-python
```

### 3. 配置环境变量

复制环境变量示例文件：
```bash
cp env.example .env
```

编辑 `.env` 文件，填入您的数据库配置：
```bash
# 数据库配置
DB_HOST=your-database-host
DB_PORT=3306
DB_NAME=your-database-name
DB_USER=your-database-user
DB_PASSWORD=your-database-password

# Flask应用配置
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=8888

# 应用配置
APP_SECRET_KEY=your-secret-key-for-session-encryption
```

### 4. 加载环境变量
```bash
source .env
```

### 5. 启动应用
```bash
python3 real_estate_web.py
```

应用将在 http://localhost:8888 启动

## 🔐 默认账户

系统启动时会自动创建默认管理员账户：
- **用户名**: admin
- **密码**: admin123
- **类型**: 管理员

## 📱 主要页面

- **登录页面**: `/login`
- **用户注册**: `/register`
- **仪表板**: `/dashboard`
- **修改密码**: `/change_password`
- **管理员功能**:
  - 注册审核: `/admin/registrations`
  - 重置密码: `/admin/reset_password`
  - 房产管理: `/properties`
  - 业主管理: `/owners`

## 🗄️ 数据库结构

系统会自动创建以下数据表：
- `users` - 用户账户表
- `user_sessions` - 用户会话表
- `user_registrations` - 注册申请表
- `registration_audit_log` - 注册审核日志
- `password_reset_tokens` - 密码重置令牌表
- `password_change_log` - 密码修改日志表

## 🔒 安全特性

- 密码使用PBKDF2-HMAC-SHA256算法加密
- 基于角色的访问控制
- 会话管理和超时控制
- 操作审计日志
- 密码重置令牌安全机制
- SQL注入防护

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目。

## 📄 许可证

本项目采用MIT许可证。 