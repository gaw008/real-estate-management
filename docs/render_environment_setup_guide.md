# Render环境变量设置完整指南

## 🚀 在Render控制台设置环境变量

### 1. 登录Render控制台
访问：https://dashboard.render.com

### 2. 找到您的应用
点击您的房地产管理系统应用（real-estate-management-p7p9）

### 3. 进入环境变量设置
- 点击左侧菜单的 **Environment**
- 或点击 **Settings** → **Environment**

### 4. 添加以下环境变量

#### 必需的数据库环境变量：
```
DB_HOST = gng-4d77d5e-gngvacation-8888.f.aivencloud.com
DB_PORT = 21192
DB_NAME = defaultdb
DB_USER = avnadmin
DB_PASSWORD = [从Aiven控制台复制实际密码]
```

#### 必需的应用环境变量：
```
SECRET_KEY = your-super-secret-key-here-12345
FLASK_ENV = production
```

#### 可选的环境变量：
```
DEBUG = False
PORT = 10000
```

## 🔄 设置步骤

### 步骤1：添加环境变量
1. 点击 **Add Environment Variable**
2. 输入变量名（如：`DB_HOST`）
3. 输入变量值（如：`gng-4d77d5e-gngvacation-8888.f.aivencloud.com`）
4. 点击 **Save**

### 步骤2：重复添加所有变量
对每个环境变量重复步骤1

### 步骤3：重新部署
1. 所有环境变量添加完成后
2. 点击 **Manual Deploy** → **Deploy Latest Commit**
3. 等待部署完成（约2-5分钟）

## 🧪 验证部署

### 方法1：检查应用日志
1. 在Render控制台点击 **Logs**
2. 查看启动日志，应该看到：
   ```
   ✅ 从环境变量加载数据库配置
   ✅ 使用内置CA证书
   ✅ 启动时数据库连接测试成功
   ```

### 方法2：访问测试页面
- 员工部门管理：https://real-estate-management-p7p9.onrender.com/demo/employee_departments
- 演示首页：https://real-estate-management-p7p9.onrender.com/demo

### 方法3：运行测试脚本
本地运行：`python3 test_render_database.py`

## ❌ 常见问题排查

### 问题1：仍然显示演示模式
**解决方案：**
- 检查DB_PASSWORD是否正确设置
- 确认所有环境变量都已保存
- 重新部署应用

### 问题2：应用无法启动
**解决方案：**
- 检查应用日志
- 确认SECRET_KEY已设置
- 检查所有环境变量格式是否正确

### 问题3：数据库连接失败
**解决方案：**
- 验证Aiven数据库服务是否正常
- 检查网络连接
- 确认数据库密码没有被修改

## 📞 测试URL
部署完成后，访问这些URL验证功能：

1. **主页**：https://real-estate-management-p7p9.onrender.com
2. **员工管理**：https://real-estate-management-p7p9.onrender.com/demo/employee_departments
3. **房产管理**：https://real-estate-management-p7p9.onrender.com/properties
4. **业主管理**：https://real-estate-management-p7p9.onrender.com/owners

## 🎯 成功标志
当环境变量正确设置后，您应该看到：
- ✅ 所有四个部门都显示：管理员、销售、财务、房屋管理
- ✅ 员工数据来自真实数据库而非演示数据
- ✅ 页面加载速度正常
- ✅ 没有"演示模式"相关提示 