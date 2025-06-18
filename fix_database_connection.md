# Aiven MySQL 数据库连接修复指南

## 🔍 问题诊断结果

根据测试结果，发现以下问题：

### ✅ 正常项目
- **网络连通性**: 可以正常访问 Aiven 服务器
- **主机地址**: `gng-4d77d5e-gngvacation-8888.f.aivencloud.com:21192`

### ❌ 需要修复的问题

#### 1. 关键问题：缺少数据库密码
**错误**: `Access denied for user 'avnadmin'`
**原因**: 环境变量 `DB_PASSWORD` 未设置

#### 2. SSL连接配置问题  
**错误**: `SSL: WRONG_VERSION_NUMBER`
**原因**: 可能端口配置或SSL协议版本不匹配

## 🔧 修复方案

### 方案1: 设置环境变量（推荐）

```bash
# 设置数据库密码（请替换为实际密码）
export DB_PASSWORD='你的实际数据库密码'

# 可选：设置其他环境变量
export DB_HOST='gng-4d77d5e-gngvacation-8888.f.aivencloud.com'
export DB_PORT='21192'
export DB_DATABASE='defaultdb'
export DB_USER='avnadmin'

# 验证设置
echo "密码已设置: $(if [ -n "$DB_PASSWORD" ]; then echo "是"; else echo "否"; fi)"
```

### 方案2: 直接修改 config.py 文件

```python
# 在 config.py 中直接设置密码（不推荐用于生产环境）
DB_CONFIG = {
    'host': 'gng-4d77d5e-gngvacation-8888.f.aivencloud.com',
    'port': 21192,
    'database': 'defaultdb',
    'user': 'avnadmin',
    'password': '你的实际数据库密码',  # 在这里填入实际密码
    'ssl_disabled': False,
    'ssl_verify_cert': False,
    'ssl_verify_identity': False
}
```

### 方案3: 创建 .env 文件

```bash
# 创建 .env 文件
cat > .env << EOF
DB_HOST=gng-4d77d5e-gngvacation-8888.f.aivencloud.com
DB_PORT=21192
DB_DATABASE=defaultdb
DB_USER=avnadmin
DB_PASSWORD=你的实际数据库密码
EOF

# 设置文件权限
chmod 600 .env
```

## 🔍 获取正确的数据库密码

### 如果您有 Aiven 控制台访问权限：

1. 登录 [Aiven 控制台](https://console.aiven.io/)
2. 找到您的 MySQL 服务实例
3. 在服务详情页面查看连接信息
4. 复制 `avnadmin` 用户的密码

### 如果忘记了密码：

1. 在 Aiven 控制台重置密码
2. 或联系 Aiven 支持团队
3. 或创建新的数据库用户

## 🧪 验证修复

修复后运行测试：

```bash
# 重新测试连接
python3 test_database_connection.py

# 或者快速测试
python3 -c "
import os
print('密码状态:', '已设置' if os.environ.get('DB_PASSWORD') else '未设置')
"
```

## 🚨 常见错误处理

### 错误1: `Access denied`
- **检查**: 密码是否正确
- **解决**: 重新获取或重置密码

### 错误2: `SSL connection error`
- **检查**: SSL配置和端口
- **解决**: 尝试不同的SSL设置

### 错误3: `Connection timeout`
- **检查**: 网络和防火墙
- **解决**: 检查IP白名单设置

## 📝 最佳实践

1. **安全性**: 使用环境变量存储密码，不要在代码中硬编码
2. **权限**: 设置适当的文件权限保护敏感信息
3. **备份**: 保存正确的连接参数以便恢复
4. **监控**: 定期检查数据库连接状态

## 🔄 重启应用

修复后重启房地产管理系统：

```bash
# 停止当前运行的服务
pkill -f "python3 real_estate_web.py"

# 重新启动
python3 real_estate_web.py
```

## 📞 如需帮助

如果问题仍然存在：

1. 检查 Aiven 服务状态
2. 验证网络连接
3. 确认 IP 地址是否在白名单中
4. 联系 Aiven 技术支持

---

**注意**: 请确保将 `你的实际数据库密码` 替换为从 Aiven 控制台获取的真实密码。 