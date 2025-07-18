#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
房地产管理系统 - 自然语言数据库查询工具
Real Estate Management System - Natural Language Database Query Tool
"""

import mysql.connector
import tempfile
import os
import re
import json
from datetime import datetime
from core.config_loader import DB_CONFIG, CA_CERTIFICATE

class NaturalLanguageQuery:
    def __init__(self):
        # 从配置加载器导入数据库连接配置
        self.config = DB_CONFIG.copy() if DB_CONFIG else {}
        
        # 从配置加载器获取CA证书
        self.ca_cert = CA_CERTIFICATE
        
        self.connection = None
        self.ca_cert_file = None
        
        # 数据库架构信息
        self.schema_info = {
            'properties': {
                'description': '房产信息表',
                'columns': {
                    'id': '房产ID',
                    'name': '房产名称',
                    'street_address': '街道地址',
                    'city': '城市',
                    'state': '州/省',
                    'layout': '房型布局(如3b2b表示3卧2浴)',
                    'property_size': '房产面积(平方英尺)',
                    'land_size': '土地面积(平方英尺)',
                    'occupancy': '最大入住人数',
                    'beds': '床位配置',
                    'front_door_code': '前门密码',
                    'storage_code': '储物间密码',
                    'wifi_name': 'WiFi名称',
                    'wifi_password': 'WiFi密码',
                    'trash_day': '垃圾收集日',
                    'is_active': '是否活跃'
                }
            },
            'owners_master': {
                'description': '业主信息表',
                'columns': {
                    'owner_id': '业主ID',
                    'name': '业主姓名',
                    'phone': '电话号码',
                    'email': '邮箱地址',
                    'preferences_strategy': '偏好策略',
                    'hobbies': '爱好',
                    'residence': '居住地',
                    'language': '语言',
                    'total_properties': '拥有房产总数'
                }
            },
            'property_owners': {
                'description': '房产-业主关系表',
                'columns': {
                    'property_id': '房产ID',
                    'owner_id': '业主ID',
                    'is_primary': '是否主要业主'
                }
            },
            'finance': {
                'description': '财务信息表',
                'columns': {
                    'property_id': '房产ID',
                    'owner_clean': '业主清洁信息',
                    'cleaning_fee': '清洁费',
                    'management_fee_rate': '管理费率(%)',
                    'management_fee_type': '管理费类型(Net/Gross)',
                    'contract_signed_date': '合同签署日期',
                    'listing_date': '上市日期',
                    'first_booking_date': '首次预订日期'
                }
            }
        }
        
        # 预定义查询模板
        self.query_patterns = [
            {
                'pattern': r'(有多少|多少个|总共|数量).*(房产|房子|物业)',
                'sql': 'SELECT COUNT(*) as total_properties FROM properties',
                'description': '查询房产总数'
            },
            {
                'pattern': r'(有多少|多少个|总共|数量).*(业主|房东)',
                'sql': 'SELECT COUNT(*) as total_owners FROM owners_master',
                'description': '查询业主总数'
            },
            {
                'pattern': r'(.*)(加州|California|加利福尼亚).*(房产|房子|物业)',
                'sql': "SELECT COUNT(*) as california_properties FROM properties WHERE state = 'California'",
                'description': '查询加州房产数量'
            },
            {
                'pattern': r'(.*)(洛杉矶|Los Angeles).*(房产|房子|物业)',
                'sql': "SELECT COUNT(*) as la_properties FROM properties WHERE city = 'Los Angeles'",
                'description': '查询洛杉矶房产数量'
            },
            {
                'pattern': r'(最大|最高).*(管理费|费率)',
                'sql': 'SELECT MAX(management_fee_rate) as max_fee_rate FROM finance WHERE management_fee_rate IS NOT NULL',
                'description': '查询最高管理费率'
            },
            {
                'pattern': r'(平均|平均值).*(管理费|费率)',
                'sql': 'SELECT AVG(management_fee_rate) as avg_fee_rate FROM finance WHERE management_fee_rate IS NOT NULL',
                'description': '查询平均管理费率'
            },
            {
                'pattern': r'(.*)(3.*卧|3b|三卧).*(房产|房子|物业)',
                'sql': "SELECT COUNT(*) as three_bedroom_properties FROM properties WHERE layout LIKE '3b%'",
                'description': '查询3卧室房产数量'
            },
            {
                'pattern': r'(.*)(4.*卧|4b|四卧).*(房产|房子|物业)',
                'sql': "SELECT COUNT(*) as four_bedroom_properties FROM properties WHERE layout LIKE '4b%'",
                'description': '查询4卧室房产数量'
            },
            {
                'pattern': r'(最大|最多).*(入住|容量|人数)',
                'sql': 'SELECT MAX(occupancy) as max_occupancy FROM properties WHERE occupancy IS NOT NULL',
                'description': '查询最大入住人数'
            },
            {
                'pattern': r'(.*)(城市|地区).*(分布|统计)',
                'sql': 'SELECT city, COUNT(*) as property_count FROM properties WHERE city IS NOT NULL AND city != "" GROUP BY city ORDER BY property_count DESC LIMIT 10',
                'description': '查询城市房产分布'
            },
            {
                'pattern': r'(.*)(州|省).*(分布|统计)',
                'sql': 'SELECT state, COUNT(*) as property_count FROM properties WHERE state IS NOT NULL AND state != "" GROUP BY state ORDER BY property_count DESC',
                'description': '查询州/省房产分布'
            },
            {
                'pattern': r'(.*)(房型|布局).*(分布|统计)',
                'sql': 'SELECT layout, COUNT(*) as property_count FROM properties WHERE layout IS NOT NULL AND layout != "" GROUP BY layout ORDER BY property_count DESC LIMIT 10',
                'description': '查询房型分布'
            }
        ]

    def setup_ssl_cert(self):
        """设置SSL证书文件"""
        self.ca_cert_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem')
        self.ca_cert_file.write(self.ca_cert)
        self.ca_cert_file.close()
        self.config['ssl_ca'] = self.ca_cert_file.name

    def connect(self):
        """连接到数据库"""
        self.setup_ssl_cert()
        self.connection = mysql.connector.connect(**self.config)

    def parse_natural_language(self, question):
        """解析自然语言问题"""
        question = question.lower().strip()
        
        # 尝试匹配预定义模式
        for pattern_info in self.query_patterns:
            if re.search(pattern_info['pattern'], question):
                return {
                    'sql': pattern_info['sql'],
                    'description': pattern_info['description'],
                    'confidence': 0.9
                }
        
        # 如果没有匹配到预定义模式，尝试基于关键词生成查询
        return self.generate_query_from_keywords(question)

    def generate_query_from_keywords(self, question):
        """基于关键词生成查询"""
        keywords = question.split()
        
        # 检查是否询问特定房产
        if any(word in question for word in ['房产', '房子', '物业', 'property']):
            if any(word in question for word in ['列表', '显示', '查看', 'show', 'list']):
                return {
                    'sql': 'SELECT id, name, city, state, layout, occupancy FROM properties LIMIT 10',
                    'description': '显示房产列表',
                    'confidence': 0.7
                }
        
        # 检查是否询问业主信息
        if any(word in question for word in ['业主', '房东', 'owner']):
            if any(word in question for word in ['列表', '显示', '查看', 'show', 'list']):
                return {
                    'sql': 'SELECT owner_id, name, total_properties FROM owners_master LIMIT 10',
                    'description': '显示业主列表',
                    'confidence': 0.7
                }
        
        # 检查是否询问财务信息
        if any(word in question for word in ['财务', '费用', '管理费', 'finance', 'fee']):
            return {
                'sql': 'SELECT property_id, cleaning_fee, management_fee_rate, management_fee_type FROM finance WHERE management_fee_rate IS NOT NULL LIMIT 10',
                'description': '显示财务信息',
                'confidence': 0.7
            }
        
        # 默认查询
        return {
            'sql': 'SELECT COUNT(*) as total_records FROM properties',
            'description': '显示房产总数（默认查询）',
            'confidence': 0.3
        }

    def execute_query(self, sql_query):
        """执行SQL查询"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql_query)
            
            # 获取列名
            columns = [desc[0] for desc in cursor.description]
            
            # 获取结果
            results = cursor.fetchall()
            cursor.close()
            
            return {
                'success': True,
                'columns': columns,
                'data': results,
                'row_count': len(results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def format_results(self, query_result, description):
        """格式化查询结果"""
        if not query_result['success']:
            return f"❌ 查询出错: {query_result['error']}"
        
        output = [f"📊 {description}"]
        output.append("=" * 60)
        
        if query_result['row_count'] == 0:
            output.append("📭 没有找到匹配的记录")
            return "\n".join(output)
        
        # 如果只有一行一列的结果（通常是统计查询）
        if query_result['row_count'] == 1 and len(query_result['columns']) == 1:
            value = query_result['data'][0][0]
            output.append(f"🔢 结果: {value}")
            return "\n".join(output)
        
        # 表格形式显示结果
        columns = query_result['columns']
        data = query_result['data']
        
        # 计算列宽
        col_widths = []
        for i, col in enumerate(columns):
            max_width = len(str(col))
            for row in data:
                max_width = max(max_width, len(str(row[i])))
            col_widths.append(min(max_width, 20))  # 限制最大宽度
        
        # 表头
        header = " | ".join(str(col).ljust(col_widths[i]) for i, col in enumerate(columns))
        output.append(header)
        output.append("-" * len(header))
        
        # 数据行
        for row in data[:20]:  # 限制显示前20行
            formatted_row = []
            for i, value in enumerate(row):
                if value is None:
                    formatted_value = "NULL"
                else:
                    formatted_value = str(value)
                    if len(formatted_value) > col_widths[i]:
                        formatted_value = formatted_value[:col_widths[i]-3] + "..."
                formatted_row.append(formatted_value.ljust(col_widths[i]))
            output.append(" | ".join(formatted_row))
        
        if query_result['row_count'] > 20:
            output.append(f"... 还有 {query_result['row_count'] - 20} 行记录")
        
        output.append(f"\n📈 总计: {query_result['row_count']} 条记录")
        
        return "\n".join(output)

    def show_help(self):
        """显示帮助信息"""
        help_text = """
🤖 房地产数据库自然语言查询助手

📋 支持的查询类型:

📊 统计查询:
  • "有多少个房产？"
  • "总共有多少业主？"
  • "加州有多少房产？"
  • "洛杉矶有多少房子？"

💰 财务查询:
  • "最高管理费率是多少？"
  • "平均管理费率是多少？"
  • "显示财务信息"

🏠 房产查询:
  • "显示房产列表"
  • "3卧室房产有多少个？"
  • "4卧室房子有多少？"
  • "最大入住人数是多少？"

📍 地理分布:
  • "城市分布统计"
  • "州分布统计"
  • "房型分布统计"

👥 业主查询:
  • "显示业主列表"
  • "业主信息"

💡 使用提示:
  • 支持中英文查询
  • 可以使用自然语言描述
  • 输入 'help' 显示此帮助
  • 输入 'quit' 或 'exit' 退出

🔍 示例查询:
  • "洛杉矶有几个房产？"
  • "显示所有3卧室的房子"
  • "管理费最高的是多少？"
  • "按城市统计房产分布"
        """
        print(help_text)

    def run_interactive(self):
        """运行交互式查询"""
        try:
            self.connect()
            print("🎉 成功连接到房地产数据库！")
            print("💬 您可以用自然语言查询数据库，输入 'help' 查看帮助")
            print("=" * 60)
            
            while True:
                try:
                    question = input("\n🤔 请输入您的问题: ").strip()
                    
                    if not question:
                        continue
                    
                    if question.lower() in ['quit', 'exit', '退出', '结束']:
                        print("👋 再见！")
                        break
                    
                    if question.lower() in ['help', '帮助']:
                        self.show_help()
                        continue
                    
                    print(f"\n🔍 正在分析问题: {question}")
                    
                    # 解析自然语言
                    query_info = self.parse_natural_language(question)
                    
                    print(f"💡 理解为: {query_info['description']}")
                    print(f"🔧 SQL查询: {query_info['sql']}")
                    print(f"🎯 置信度: {query_info['confidence']:.1%}")
                    
                    # 执行查询
                    result = self.execute_query(query_info['sql'])
                    
                    # 显示结果
                    formatted_result = self.format_results(result, query_info['description'])
                    print(f"\n{formatted_result}")
                    
                except KeyboardInterrupt:
                    print("\n👋 再见！")
                    break
                except Exception as e:
                    print(f"❌ 处理问题时出错: {str(e)}")
                    
        except Exception as e:
            print(f"❌ 连接数据库失败: {str(e)}")
        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        if self.connection:
            self.connection.close()
        if self.ca_cert_file and os.path.exists(self.ca_cert_file.name):
            os.unlink(self.ca_cert_file.name)

if __name__ == "__main__":
    query_tool = NaturalLanguageQuery()
    query_tool.run_interactive() 