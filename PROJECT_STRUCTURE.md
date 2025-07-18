# 房地产管理系统 - 项目结构说明

## 📁 目录结构

```
sqldatabase/
├── app.py                          # 🚀 主启动文件
├── requirements.txt                # 📦 Python依赖包
├── runtime.txt                     # ⚙️ 运行时配置
├── LICENSE                         # 📄 许可证文件
├── .gitignore                      # 🚫 Git忽略文件
├── .env                           # 🔐 环境变量
├── .env.backup                    # 💾 环境变量备份
│
├── src/                           # 📂 源代码目录
│   ├── core/                      # 🔧 核心模块
│   │   ├── real_estate_web.py     # 🌐 Flask主应用
│   │   ├── auth_system.py         # 🔐 用户认证系统
│   │   └── config_loader.py       # ⚙️ 配置加载器
│   │
│   ├── modules/                   # 🏢 业务模块
│   │   ├── department_modules.py  # 👥 部门管理
│   │   ├── financial_reports.py   # 💰 财务报表
│   │   ├── password_manager.py    # 🔑 密码管理
│   │   ├── user_registration.py   # 📝 用户注册
│   │   ├── language_manager.py    # 🌍 多语言管理
│   │   ├── view_users_secure.py   # 👤 用户查看
│   │   ├── update_users_table_department.py  # 🔄 用户表更新
│   │   ├── real_estate_dashboard.py  # 📊 仪表板
│   │   ├── ai_query_assistant.py  # 🤖 AI查询助手
│   │   └── natural_language_query.py  # 💬 自然语言查询
│   │
│   └── utils/                     # 🛠️ 工具模块
│       ├── mock_data_manager.py   # 📋 模拟数据管理
│       └── automated_test_suite.py # 🧪 自动化测试
│
├── data/                          # 📊 数据目录
│   ├── csv/                       # 📄 CSV数据文件
│   │   ├── Database - Finance.csv
│   │   ├── Database - Owners.csv
│   │   └── Database - Properties.csv
│   └── exports/                   # 📤 导出文件
│       └── import_log.txt         # 📝 导入日志
│
├── scripts/                       # 📜 脚本目录
│   ├── database/                  # 🗄️ 数据库脚本
│   │   ├── import_to_aiven_mysql.py  # 📥 数据导入
│   │   └── query_aiven_database.py   # 🔍 数据库查询
│   └── deployment/                # 🚀 部署脚本
│       ├── deploy_to_github.sh    # 📤 GitHub部署
│       ├── deploy_to_github.bat   # 📤 GitHub部署(Windows)
│       ├── start_render.py        # 🌐 Render部署启动
│       └── setup_auth.py          # 🔐 认证设置
│
├── config/                        # ⚙️ 配置目录
│   ├── config.py                  # 🔧 主配置文件
│   └── streamlit_config.toml      # 📊 Streamlit配置
│
├── docs/                          # 📚 文档目录
│   ├── user_guides/               # 👥 用户指南
│   ├── technical/                 # 🔧 技术文档
│   └── deployment/                # 🚀 部署文档
│
├── static/                        # 🎨 静态资源
│   ├── css/                       # 🎨 样式文件
│   └── js/                        # ⚡ JavaScript文件
│
├── templates/                     # 📄 模板目录
│   └── new_ui/                    # 🆕 新版UI模板
│
├── tests/                         # 🧪 测试目录
│
└── UI Design/                     # 🎨 UI设计文件
```

## 🎯 各目录用途说明

### `src/` - 源代码目录
- **core/**: 核心功能模块，包含Flask应用、认证系统和配置管理
- **modules/**: 业务逻辑模块，包含各个功能模块的实现
- **utils/**: 工具和辅助功能，包含测试和数据处理工具

### `data/` - 数据目录
- **csv/**: 原始CSV数据文件
- **exports/**: 系统生成的导出文件和日志

### `scripts/` - 脚本目录
- **database/**: 数据库相关的脚本，如数据导入和查询
- **deployment/**: 部署相关的脚本，支持多种部署方式

### `config/` - 配置目录
- 包含各种配置文件，支持不同环境的配置

### `docs/` - 文档目录
- 包含用户指南、技术文档和部署说明

### `static/` 和 `templates/` - 前端资源
- 包含CSS、JavaScript和HTML模板文件

## 🚀 启动方式

### 本地开发
```bash
python app.py
```

### 生产部署
```bash
python scripts/deployment/start_render.py
```

## 📋 主要功能模块

1. **用户认证系统** (`src/core/auth_system.py`)
   - 用户登录/登出
   - 密码管理
   - 会话管理
   - 权限控制

2. **房产管理** (`src/modules/`)
   - 房产信息管理
   - 业主信息管理
   - 财务记录管理

3. **部门管理** (`src/modules/department_modules.py`)
   - 员工部门分配
   - 权限模块管理
   - 部门仪表板

4. **多语言支持** (`src/modules/language_manager.py`)
   - 中英文切换
   - 界面本地化

5. **AI功能** (`src/modules/ai_query_assistant.py`)
   - 智能查询助手
   - 自然语言处理

## 🔧 配置说明

- **数据库配置**: `config/config.py`
- **环境变量**: `.env`
- **依赖包**: `requirements.txt`

## 📝 注意事项

1. 首次运行前需要配置数据库连接信息
2. 确保所有依赖包已安装
3. 数据库初始化脚本位于 `scripts/database/`
4. 部署脚本支持GitHub和Render平台 