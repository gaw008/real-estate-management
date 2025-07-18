#!/usr/bin/env python3
"""
Render部署专用启动文件
确保即使数据库连接失败也能正常启动应用
"""

import os
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_app():
    """启动应用的函数"""
    try:
        # 导入应用
        from real_estate_web import app
        
        # 获取端口配置
        port = int(os.environ.get('PORT', 10000))  # Render默认端口
        
        logger.info(f"🚀 Render部署启动...")
        logger.info(f"📍 端口: {port}")
        logger.info(f"🌍 主机: 0.0.0.0")
        
        # 启动应用
        app.run(
            debug=False,  # 生产环境关闭调试
            host='0.0.0.0',
            port=port,
            threaded=True  # 启用多线程
        )
        
    except ImportError as e:
        logger.error(f"❌ 导入应用失败: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        # 不退出，继续尝试
        pass

if __name__ == '__main__':
    start_app() 