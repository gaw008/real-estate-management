#!/usr/bin/env python3
"""
房地产管理系统 - 主启动文件
重新组织后的项目结构启动入口
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 导入核心应用
from core.real_estate_web import app

if __name__ == '__main__':
    print("🚀 启动房地产管理系统...")
    print("📁 项目结构已重新组织")
    print("🌐 访问地址: http://127.0.0.1:8888")
    print("👤 管理员账户: admin / admin123")
    print("-" * 50)
    
    app.run(host='127.0.0.1', port=8888, debug=True) 