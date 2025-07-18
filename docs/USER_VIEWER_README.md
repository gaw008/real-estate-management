# 用户数据查看工具

## 功能说明

`view_users_secure.py` - 安全的用户数据查看工具

### 主要功能
- 查看所有用户数据（管理员 + 业主）
- 搜索特定用户
- 查看数据库表结构
- 用户统计信息

### 使用方法

```bash
# 查看所有用户
python3 view_users_secure.py

# 查看数据库表结构
python3 view_users_secure.py tables

# 搜索特定用户
python3 view_users_secure.py admin
python3 view_users_secure.py 张三
```

### 配置要求

工具会自动从以下来源获取数据库配置：
1. 环境变量（推荐）
2. config_loader.py 配置文件

### 当前系统数据

- 总用户数：73个
- 管理员用户：4个
- 业主用户：69个
- 数据库表：11个

### 安全特性

- 不包含硬编码密码
- 使用SSL连接
- 支持环境变量配置
- CA证书验证 