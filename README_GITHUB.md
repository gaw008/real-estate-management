# 🏠 房地产管理系统 (Real Estate Management System)

一个基于Flask的现代化房地产管理Web应用，支持房产信息管理、业主管理、财务数据分析和智能查询功能。

## ✨ 主要功能

### 📊 数据管理
- **房产管理**: 完整的房产信息录入、查看、搜索和筛选
- **业主管理**: 业主信息管理，支持多房产关联
- **财务管理**: 清洁费、管理费率(Net/Gross)等财务数据管理
- **关系管理**: 房产-业主多对多关系管理

### 🌐 Web界面
- **响应式设计**: 支持桌面端和移动端访问
- **现代化UI**: 基于Bootstrap 5的美观界面
- **交互式图表**: 使用Chart.js的数据可视化
- **中文界面**: 完全本地化的用户体验

### 🔍 智能查询
- **自然语言查询**: 支持中英文自然语言数据查询
- **高级筛选**: 多条件组合搜索
- **实时统计**: 动态数据统计和分析
- **API接口**: RESTful API支持

### 📈 数据可视化
- **仪表板**: 实时数据概览
- **统计图表**: 城市分布、房产类型、管理费分布等
- **交互式报表**: 可视化数据分析工具

## 🚀 快速开始

### 环境要求
- Python 3.9+
- MySQL 8.0+
- 现代浏览器

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/real-estate-management.git
cd real-estate-management
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置数据库**
```python
# 在 real_estate_web.py 中修改数据库配置
DB_CONFIG = {
    'host': 'your-mysql-host',
    'port': 3306,
    'database': 'your-database',
    'user': 'your-username',
    'password': 'your-password',
    'ssl_disabled': False,  # 根据需要调整
}
```

4. **导入数据**
```bash
# 使用提供的CSV文件导入示例数据
python import_to_aiven_mysql.py
```

5. **启动应用**
```bash
python real_estate_web.py
```

6. **访问应用**
打开浏览器访问: `http://localhost:8888`

## 📁 项目结构

```
real-estate-management/
├── real_estate_web.py          # 主Web应用
├── templates/                  # HTML模板
│   ├── base.html              # 基础模板
│   ├── index_fixed.html       # 主页
│   ├── properties_fixed.html  # 房产列表
│   ├── property_detail_fixed.html # 房产详情
│   ├── owners_fixed.html      # 业主列表
│   └── owner_detail_fixed.html # 业主详情
├── static/                    # 静态资源
│   ├── css/style.css         # 样式文件
│   └── js/main.js            # JavaScript文件
├── import_to_aiven_mysql.py   # 数据导入脚本
├── natural_language_query.py  # 自然语言查询工具
├── requirements.txt           # Python依赖
├── Database - Properties.csv  # 示例房产数据
├── Database - Owners.csv      # 示例业主数据
├── Database - Finance.csv     # 示例财务数据
└── README.md                  # 项目说明
```

## 🎯 核心特性

### 管理费率显示
系统智能识别并显示管理费率类型：
- `20.00% of Net Income` - 基于净收入的管理费
- `15.00% of Gross Income` - 基于总收入的管理费

### 数据库架构
- **properties**: 房产主表
- **owners_master**: 业主主表  
- **property_owners**: 房产-业主关系表
- **finance**: 财务信息表

### 性能优化
- 复合索引优化查询性能
- 分页加载大数据集
- 缓存机制提升响应速度
- SSL安全连接

## 🛠️ 技术栈

### 后端
- **Flask**: Python Web框架
- **MySQL**: 关系型数据库
- **mysql-connector-python**: 数据库连接器

### 前端
- **Bootstrap 5**: CSS框架
- **Chart.js**: 图表库
- **Font Awesome**: 图标库
- **jQuery**: JavaScript库

### 部署
- **Aiven MySQL**: 云数据库服务
- **SSL/TLS**: 安全连接
- **Docker**: 容器化部署(可选)

## 📊 数据示例

项目包含真实的房地产数据示例：
- **92个房产**: 主要位于加州各城市
- **69个业主**: 包含完整联系信息
- **财务数据**: 清洁费、管理费率等

## 🔧 配置说明

### 数据库配置
```python
DB_CONFIG = {
    'host': 'your-host',
    'port': 21192,
    'database': 'defaultdb',
    'user': 'username',
    'password': 'password',
    'ssl_disabled': False,
    'ssl_ca': 'ca-certificate.crt'  # SSL证书路径
}
```

### 应用配置
```python
app.run(
    debug=True,          # 开发模式
    host='0.0.0.0',     # 监听所有接口
    port=8888           # 端口号
)
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- 项目链接: [https://github.com/yourusername/real-estate-management](https://github.com/yourusername/real-estate-management)
- 问题反馈: [Issues](https://github.com/yourusername/real-estate-management/issues)

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Web框架
- [Bootstrap](https://getbootstrap.com/) - CSS框架
- [Chart.js](https://www.chartjs.org/) - 图表库
- [Aiven](https://aiven.io/) - 云数据库服务

---

⭐ 如果这个项目对您有帮助，请给它一个星标！ 