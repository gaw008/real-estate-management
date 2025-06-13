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