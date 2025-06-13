#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版AI查询助手模块
支持更智能的自然语言转SQL查询功能
"""

import openai
import os
import re
from typing import Dict, List, Optional, Tuple
import pandas as pd
from openai import OpenAI

class EnhancedAIQueryAssistant:
    """增强版AI查询助手类"""
    
    def __init__(self):
        """初始化AI助手"""
        self.api_key = os.getenv('OPENAI_API_KEY', '')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.use_openai = bool(self.api_key and self.api_key != 'your_openai_api_key_here')
        
        if self.use_openai:
            openai.api_key = self.api_key
        
        # 数据库表结构信息
        self.schema_info = {
            'properties': {
                'description': '房产信息表',
                'columns': {
                    'id': '房产唯一标识',
                    'name': '房产名称',
                    'street_address': '详细地址',
                    'city': '城市',
                    'state': '州',
                    'layout': '房型布局',
                    'property_size': '房产面积(数字)',
                    'land_size': '土地面积',
                    'occupancy': '入住人数(数字)',
                    'beds': '床位配置',
                    'owner_id': '业主ID',
                    'front_door_code': '前门密码',
                    'storage_code': '储物密码',
                    'wifi_name': 'WiFi名称',
                    'wifi_password': 'WiFi密码',
                    'trash_day': '垃圾收集日'
                }
            },
            'owners': {
                'description': '业主信息表',
                'columns': {
                    'id': '记录ID',
                    'owner_id': '业主唯一标识',
                    'name': '业主姓名',
                    'phone': '联系电话',
                    'email': '邮箱地址',
                    'preferences_staragy': '偏好策略',
                    'hobbies': '兴趣爱好',
                    'residence': '居住地',
                    'lanaguage': '语言偏好'
                }
            },
            'finance': {
                'description': '财务信息表',
                'columns': {
                    'id': '房产ID',
                    'owner_clean': '业主信息',
                    'cleaning_fee': '清洁费',
                    'manegement_fee_pct': '管理费百分比',
                    'contract_signed_date': '合同签署日期',
                    'listing_date': '上市日期',
                    'first_booking_date': '首次预订日期'
                }
            }
        }
        
        # 增强的查询模式 - 支持更多变体和表达方式
        self.query_patterns = [
            # 具体房产属性查询类 - 新增！
            {
                'patterns': [
                    r'(?:what\s+is|查询|告诉我).{0,20}(?:trash\s+day|垃圾.{0,5}日|垃圾.{0,5}收集).{0,20}(?:property\s+id|房产id|房产编号|id).{0,10}["\']?([^"\'?\n]+?)["\']?(?:\?|$|\.)',
                    r'(?:property\s+id|房产id|房产编号|id).{0,10}["\']?([^"\'?\n]+?)["\']?.{0,20}(?:trash\s+day|垃圾.{0,5}日|垃圾.{0,5}收集)',
                    r'([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*).{0,10}(?:的|的房产|property).{0,10}(?:trash\s+day|垃圾.{0,5}日|垃圾.{0,5}收集)',
                ],
                'template': "SELECT name as 房产名称, trash_day as 垃圾收集日, city as 城市, state as 州 FROM properties WHERE name ILIKE '%{id}%' OR id::text = '{id}'",
                'description': '查询特定房产的垃圾收集日',
                'extract_id': True
            },
            {
                'patterns': [
                    r'(?:what\s+is|查询|告诉我).{0,20}(?:wifi|WiFi|无线网|网络).{0,20}(?:property\s+id|房产id|房产编号|id).{0,10}["\']?([^"\'?\n]+?)["\']?(?:\?|$|\.)',
                    r'(?:property\s+id|房产id|房产编号|id).{0,10}["\']?([^"\'?\n]+?)["\']?.{0,20}(?:wifi|WiFi|无线网|网络)',
                    r'([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*).{0,10}(?:的|的房产|property).{0,10}(?:wifi|WiFi|无线网|网络)',
                ],
                'template': "SELECT name as 房产名称, wifi_name as WiFi名称, wifi_password as WiFi密码, city as 城市 FROM properties WHERE name ILIKE '%{id}%' OR id::text = '{id}'",
                'description': '查询特定房产的WiFi信息',
                'extract_id': True
            },
            {
                'patterns': [
                    r'(?:what\s+is|查询|告诉我).{0,20}(?:layout|房型|户型|布局).{0,20}(?:property\s+id|房产id|房产编号|id).{0,10}["\']?([^"\'?\n]+?)["\']?(?:\?|$|\.)',
                    r'(?:property\s+id|房产id|房产编号|id).{0,10}["\']?([^"\'?\n]+?)["\']?.{0,20}(?:layout|房型|户型|布局)',
                    r'([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*).{0,10}(?:的|的房产|property).{0,10}(?:layout|房型|户型|布局)',
                ],
                'template': "SELECT name as 房产名称, layout as 房型布局, property_size as 面积, occupancy as 入住人数, city as 城市 FROM properties WHERE name ILIKE '%{id}%' OR id::text = '{id}'",
                'description': '查询特定房产的布局信息',
                'extract_id': True
            },
            {
                'patterns': [
                    r'(?:what\s+is|查询|告诉我).{0,20}(?:address|地址|位置).{0,20}(?:property\s+id|房产id|房产编号|id).{0,10}["\']?([^"\'?\n]+?)["\']?(?:\?|$|\.)',
                    r'(?:property\s+id|房产id|房产编号|id).{0,10}["\']?([^"\'?\n]+?)["\']?.{0,20}(?:address|地址|位置)',
                    r'([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*).{0,10}(?:的|的房产|property).{0,10}(?:address|地址|位置)',
                ],
                'template': "SELECT name as 房产名称, street_address as 详细地址, city as 城市, state as 州 FROM properties WHERE name ILIKE '%{id}%' OR id::text = '{id}'",
                'description': '查询特定房产的地址信息',
                'extract_id': True
            },
            {
                'patterns': [
                    r'(?:what\s+is|查询|告诉我).{0,20}(?:door\s+code|front\s+door|门禁|前门|密码|房门|门|房门密码).{0,20}(?:property\s+id|房产id|房产编号|id|房子|房产).{0,10}["\']?([^"\'?\n]+?)["\']?(?:\?|$|\.)',
                    r'(?:property\s+id|房产id|房产编号|id|房子|房产).{0,10}["\']?([^"\'?\n]+?)["\']?.{0,20}(?:door\s+code|front\s+door|门禁|前门|密码|房门|门|房门密码)',
                    r'([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*).{0,10}(?:的|的房产|property|房子).{0,10}(?:door\s+code|front\s+door|门禁|前门|密码|房门|门|房门密码)',
                ],
                'template': "SELECT name as 房产名称, front_door_code as 前门密码, storage_code as 储物密码, city as 城市, state as 州 FROM properties WHERE name ILIKE '%{id}%' OR id ILIKE '%{id}%' OR id = '{id}'",
                'description': '查询特定房产的门禁密码',
                'extract_id': True
            },
            {
                'patterns': [
                    r'(?:show\s+me|给我看|查询|tell\s+me).{0,20}(?:property\s+id|房产id|房产编号|id).{0,10}["\']?([^"\'?\n]+?)["\']?.{0,20}(?:information|info|信息|详情)',
                    r'(?:property\s+id|房产id|房产编号|id).{0,10}["\']?([^"\'?\n]+?)["\']?.{0,20}(?:details|信息|详情|全部)',
                    r'([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*).{0,10}(?:的|的房产|property).{0,10}(?:information|info|信息|详情|全部)',
                ],
                'template': "SELECT name as 房产名称, street_address as 详细地址, city as 城市, state as 州, layout as 房型, property_size as 面积, occupancy as 入住人数, wifi_name as WiFi名称, trash_day as 垃圾收集日, front_door_code as 前门密码 FROM properties WHERE name ILIKE '%{id}%' OR id::text = '{id}'",
                'description': '查询特定房产的完整信息',
                'extract_id': True
            },
            {
                'patterns': [
                    r'(?:what\s+is|查询|告诉我).{0,20}(?:management\s+fee|管理费|合约|合同|contract).{0,20}(?:property\s+id|房产id|房产编号|id|房子|房产).{0,10}["\']?([^"\'?\n]+?)["\']?(?:\?|$|\.)',
                    r'(?:property\s+id|房产id|房产编号|id|房子|房产).{0,10}["\']?([^"\'?\n]+?)["\']?.{0,20}(?:management\s+fee|管理费|合约|合同|contract)',
                    r'([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*).{0,10}(?:的|的房产|property|房子|签的).{0,10}(?:management\s+fee|管理费|合约|合同|contract|百分比)',
                    r'([A-Za-z0-9]+(?:\s*[A-Za-z0-9]*)*)\s*签的\s*合约.{0,15}(?:多少|是|百分比)',
                    r'([A-Za-z0-9]+(?:\s*[A-Za-z0-9]*)*).{0,5}(?:合约|合同).{0,15}(?:多少|百分比|费用)',
                    r'([A-Za-z0-9]+(?:\s*[A-Za-z0-9]*)*).{0,5}(?:百分比|管理费).{0,10}(?:多少|是什么)',
                ],
                'template': "SELECT p.name as 房产名称, f.manegement_fee_pct as 管理费百分比, f.contract_signed_date as 合同签署日期, f.cleaning_fee as 清洁费, p.city as 城市, p.state as 州 FROM properties p LEFT JOIN finance f ON p.id = f.id WHERE p.name ILIKE '%{id}%' OR p.id ILIKE '%{id}%' OR p.id = '{id}'",
                'description': '查询特定房产的合约管理费信息',
                'extract_id': True
            },
            {
                'patterns': [
                    r'(?:who\s+is|谁是|查询|告诉我).{0,20}(?:owner|业主|房东|房主).{0,20}(?:property\s+id|房产id|房产编号|id|房子|房产).{0,10}["\']?([^"\'?\n]+?)["\']?(?:\?|$|\.)',
                    r'(?:property\s+id|房产id|房产编号|id|房子|房产).{0,10}["\']?([^"\'?\n]+?)["\']?.{0,20}(?:owner|业主|房东|房主|的业主|的房东)',
                    r'([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*).{0,10}(?:的|这个|房子|房产).{0,10}(?:owner|业主|房东|房主|是谁)',
                ],
                'template': "SELECT p.name as 房产名称, o.name as 业主姓名, o.phone as 联系电话, o.email as 邮箱地址, p.city as 城市, p.state as 州 FROM properties p LEFT JOIN owners o ON p.id = o.id WHERE p.name ILIKE '%{id}%' OR p.id::text = '{id}'",
                'description': '查询特定房产的业主信息',
                'extract_id': True
            },
            
            # 基础统计类
            {
                'patterns': [
                    r'(?:有多少|数量|总数|统计|一共有).{0,10}(?:房产|房子|物业|房屋)',
                    r'房产.{0,5}(?:总数|数量|统计)',
                    r'(?:总共|一共).{0,5}(?:房产|房子|物业)'
                ],
                'template': 'SELECT COUNT(*) as 房产总数 FROM properties',
                'description': '统计房产总数'
            },
            {
                'patterns': [
                    r'(?:有多少|数量|总数|统计|一共有).{0,10}(?:业主|房东|房主|物业主)',
                    r'业主.{0,5}(?:总数|数量|统计)',
                    r'(?:总共|一共).{0,5}(?:业主|房东)'
                ],
                'template': 'SELECT COUNT(DISTINCT owner_id) as 业主总数 FROM owners',
                'description': '统计业主总数'
            },
            
            # 地理分布类
            {
                'patterns': [
                    r'(?:城市|地区|地方).{0,10}(?:分布|统计|房产)',
                    r'(?:各个|每个|不同).{0,5}城市.{0,10}(?:房产|房子|数量)',
                    r'房产.{0,10}(?:城市|地区).{0,5}分布',
                    r'(?:哪些|什么)城市.{0,5}(?:有|存在).{0,5}房产'
                ],
                'template': 'SELECT city as 城市, COUNT(*) as 房产数量 FROM properties WHERE city IS NOT NULL AND city != \'nan\' GROUP BY city ORDER BY COUNT(*) DESC',
                'description': '统计各城市房产分布'
            },
            {
                'patterns': [
                    r'(?:州|state).{0,10}(?:分布|统计|房产)',
                    r'(?:各个|每个|不同).{0,5}州.{0,10}(?:房产|房子|数量)',
                    r'房产.{0,10}(?:州|state).{0,5}分布'
                ],
                'template': 'SELECT state as 州, COUNT(*) as 房产数量 FROM properties WHERE state IS NOT NULL AND state != \'nan\' GROUP BY state ORDER BY COUNT(*) DESC',
                'description': '统计各州房产分布'
            },
            
            # 房型分析类
            {
                'patterns': [
                    r'(?:房型|户型|layout|布局).{0,10}(?:分布|统计|种类)',
                    r'(?:各种|不同).{0,5}(?:房型|户型).{0,10}(?:数量|统计)',
                    r'房产.{0,5}(?:房型|户型|布局).{0,5}(?:分布|统计)'
                ],
                'template': 'SELECT layout as 房型, COUNT(*) as 数量 FROM properties WHERE layout IS NOT NULL AND layout != \'nan\' GROUP BY layout ORDER BY COUNT(*) DESC',
                'description': '统计房型分布'
            },
            
            # 加州专项查询
            {
                'patterns': [
                    r'(?:加州|California|加利福尼亚).{0,10}(?:房产|房子|物业)',
                    r'(?:加州|California).{0,5}(?:有多少|数量|统计)',
                    r'(?:在|位于).{0,5}(?:加州|California).{0,5}(?:房产|房子)'
                ],
                'template': "SELECT city as 城市, COUNT(*) as 房产数量 FROM properties WHERE state = 'California' GROUP BY city ORDER BY COUNT(*) DESC",
                'description': '统计加州各城市房产分布'
            },
            
            # WiFi覆盖类
            {
                'patterns': [
                    r'(?:wifi|WiFi|无线网|网络).{0,10}(?:覆盖|统计|情况)',
                    r'(?:有多少|多少比例).{0,5}房产.{0,5}(?:有|配备).{0,5}(?:wifi|WiFi|无线网)',
                    r'(?:wifi|WiFi|无线网).{0,5}覆盖率'
                ],
                'template': 'SELECT COUNT(CASE WHEN wifi_name IS NOT NULL AND wifi_name != \'nan\' THEN 1 END) as 有WiFi房产, COUNT(*) as 总房产数, ROUND(COUNT(CASE WHEN wifi_name IS NOT NULL AND wifi_name != \'nan\' THEN 1 END) * 100.0 / COUNT(*), 1) as WiFi覆盖率 FROM properties',
                'description': '统计WiFi覆盖情况'
            },
            
            # 面积分析类
            {
                'patterns': [
                    r'(?:平均|平均面积|平均大小).{0,10}(?:房产|房子|物业)',
                    r'房产.{0,5}(?:平均|平均面积|平均大小)',
                    r'(?:房产|房子).{0,5}(?:面积|大小).{0,5}平均'
                ],
                'template': 'SELECT ROUND(AVG(CAST(property_size AS NUMERIC)), 1) as 平均面积, COUNT(*) as 房产数量 FROM properties WHERE property_size IS NOT NULL AND property_size != \'nan\' AND CAST(property_size AS NUMERIC) > 0',
                'description': '计算房产平均面积'
            },
            
            # 入住人数分析
            {
                'patterns': [
                    r'(?:入住|住宿|容纳).{0,10}(?:人数|人员|容量)',
                    r'(?:平均|最大|最小).{0,5}(?:入住|住宿).{0,5}人数',
                    r'房产.{0,5}(?:入住|住宿|容纳).{0,5}(?:人数|能力)'
                ],
                'template': 'SELECT AVG(CAST(occupancy AS NUMERIC)) as 平均入住人数, MAX(CAST(occupancy AS NUMERIC)) as 最大入住人数, MIN(CAST(occupancy AS NUMERIC)) as 最小入住人数 FROM properties WHERE occupancy IS NOT NULL AND occupancy != \'nan\' AND CAST(occupancy AS NUMERIC) > 0',
                'description': '统计入住人数情况'
            },
            
            # 财务相关
            {
                'patterns': [
                    r'(?:合同|签约|签署).{0,10}(?:统计|数量|情况)',
                    r'(?:有多少|多少).{0,5}(?:合同|签约)',
                    r'签约.{0,5}(?:情况|统计|比例)'
                ],
                'template': 'SELECT COUNT(*) as 总记录数, COUNT(CASE WHEN contract_signed_date IS NOT NULL AND contract_signed_date != \'nan\' THEN 1 END) as 已签约数, ROUND(COUNT(CASE WHEN contract_signed_date IS NOT NULL AND contract_signed_date != \'nan\' THEN 1 END) * 100.0 / COUNT(*), 1) as 签约率 FROM finance',
                'description': '统计合同签约情况'
            },
            
            # 业主联系方式
            {
                'patterns': [
                    r'(?:联系方式|联系信息|邮箱|电话).{0,10}(?:统计|完整|情况)',
                    r'(?:有多少|多少).{0,5}业主.{0,5}(?:有|提供).{0,5}(?:联系方式|邮箱|电话)',
                    r'业主.{0,5}(?:联系方式|联系信息).{0,5}(?:完整|统计)'
                ],
                'template': 'SELECT COUNT(*) as 业主总数, COUNT(CASE WHEN email IS NOT NULL AND email != \'nan\' THEN 1 END) as 有邮箱, COUNT(CASE WHEN phone IS NOT NULL AND phone != \'nan\' THEN 1 END) as 有电话 FROM owners',
                'description': '统计业主联系方式完整度'
            },
            
            # 排行榜类查询
            {
                'patterns': [
                    r'(?:哪个|哪些|什么).{0,5}城市.{0,5}房产.{0,5}(?:最多|排名|前|top)',
                    r'房产.{0,5}(?:最多|排名前).{0,5}城市',
                    r'城市.{0,5}房产.{0,5}排行'
                ],
                'template': 'SELECT city as 城市, COUNT(*) as 房产数量 FROM properties WHERE city IS NOT NULL AND city != \'nan\' GROUP BY city ORDER BY COUNT(*) DESC LIMIT 10',
                'description': '房产数量最多的城市排行榜'
            }
        ]
    
    def enhanced_pattern_match(self, question: str) -> Optional[Tuple[str, str]]:
        """增强的模式匹配"""
        question_lower = question.lower()
        
        for pattern_group in self.query_patterns:
            for pattern in pattern_group['patterns']:
                match = re.search(pattern, question_lower, re.IGNORECASE)
                if match:
                    template = pattern_group['template']
                    description = pattern_group['description']
                    
                    # 如果需要提取ID
                    if pattern_group.get('extract_id', False) and match.groups():
                        property_id = match.group(1).strip()
                        # 清理ID中的引号和多余字符
                        property_id = re.sub(r'["\'\?\.]', '', property_id).strip()
                        # 确保ID不为空且合理
                        if len(property_id) >= 1:  # 改为更宽松的条件
                            template = template.format(id=property_id)
                        else:
                            continue  # 跳过无效的ID
                    
                    return template, f"智能匹配 - {description}"
        
        return None
    
    def advanced_keyword_analysis(self, question: str) -> Optional[Tuple[str, str]]:
        """高级关键词分析"""
        question_lower = question.lower()
        
        # 改进的房产ID提取逻辑
        property_id = None
        
        # 方法1: 匹配 "property id xxxx" 格式
        match1 = re.search(r'(?:property\s+id|房产id|id)["\s]*[\'"]?([A-Za-z0-9\s]+?)[\'"]?(?:\?|$|\.|\s)', question_lower)
        if match1:
            property_id = match1.group(1).strip()
        
        # 方法2: 匹配具体的房产ID模式
        if not property_id:
            # 匹配类似 1101BMP, 10654, 1203Glendora 等格式
            match2 = re.search(r'\b([0-9]+[A-Za-z]*[0-9]*[A-Za-z]*)\b', question)
            if match2:
                candidate = match2.group(1)
                # 确保不是单纯的数字，且长度合理
                if len(candidate) >= 3 and not candidate.isdigit() or len(candidate) >= 4:
                    property_id = candidate
        
        # 方法3: 匹配中文上下文中的ID
        if not property_id:
            match3 = re.search(r'(?:房产|查询|告诉我)([A-Za-z0-9]+)', question)
            if match3:
                property_id = match3.group(1)
        
        if property_id:
            property_id = property_id.strip()
            
            # 根据问题内容确定查询字段
            if any(word in question_lower for word in ['trash', '垃圾', '收集']):
                return f"SELECT name as 房产名称, trash_day as 垃圾收集日, city as 城市, state as 州 FROM properties WHERE name ILIKE '%{property_id}%' OR id::text = '{property_id}'", f"高级分析 - 查询房产{property_id}的垃圾收集日"
            
            elif any(word in question_lower for word in ['wifi', '无线网', '网络', 'password']):
                return f"SELECT name as 房产名称, wifi_name as WiFi名称, wifi_password as WiFi密码, city as 城市 FROM properties WHERE name ILIKE '%{property_id}%' OR id::text = '{property_id}'", f"高级分析 - 查询房产{property_id}的WiFi信息"
            
            elif any(word in question_lower for word in ['layout', '房型', '户型', '布局']):
                return f"SELECT name as 房产名称, layout as 房型布局, property_size as 面积, occupancy as 入住人数, city as 城市 FROM properties WHERE name ILIKE '%{property_id}%' OR id::text = '{property_id}'", f"高级分析 - 查询房产{property_id}的布局信息"
            
            elif any(word in question_lower for word in ['address', '地址', '位置']):
                return f"SELECT name as 房产名称, street_address as 详细地址, city as 城市, state as 州 FROM properties WHERE name ILIKE '%{property_id}%' OR id::text = '{property_id}'", f"高级分析 - 查询房产{property_id}的地址信息"
            
            elif any(word in question_lower for word in ['door', 'code', '门禁', '密码', '前门']):
                return f"SELECT name as 房产名称, front_door_code as 前门密码, storage_code as 储物密码, city as 城市 FROM properties WHERE name ILIKE '%{property_id}%' OR id::text = '{property_id}'", f"高级分析 - 查询房产{property_id}的门禁信息"
            
            elif any(word in question_lower for word in ['management', 'fee', '管理费', 'percentage']):
                return f"SELECT p.name as 房产名称, f.manegement_fee_pct as 管理费百分比, p.city as 城市, p.state as 州 FROM properties p JOIN finance f ON p.id = f.id WHERE p.name ILIKE '%{property_id}%' OR p.id::text = '{property_id}'", f"高级分析 - 查询房产{property_id}的管理费信息"
            
            elif any(word in question_lower for word in ['owner', 'who', '业主', '房东', '房主', '谁', '是谁']):
                return f"SELECT p.name as 房产名称, o.name as 业主姓名, o.phone as 联系电话, o.email as 邮箱地址, p.city as 城市, p.state as 州 FROM properties p LEFT JOIN owners o ON p.id = o.id WHERE p.name ILIKE '%{property_id}%' OR p.id::text = '{property_id}'", f"高级分析 - 查询房产{property_id}的业主信息"
            
            elif any(word in question_lower for word in ['information', 'info', '信息', '详情', '全部']):
                return f"SELECT name as 房产名称, street_address as 详细地址, city as 城市, state as 州, layout as 房型, property_size as 面积, occupancy as 入住人数, wifi_name as WiFi名称, trash_day as 垃圾收集日, front_door_code as 前门密码 FROM properties WHERE name ILIKE '%{property_id}%' OR id::text = '{property_id}'", f"高级分析 - 查询房产{property_id}的完整信息"
        
        # 数量词检测
        quantity_words = ['多少', '数量', '总数', '统计', '一共', '总共', '几个', '几套']
        has_quantity = any(word in question_lower for word in quantity_words)
        
        # 实体词检测
        property_words = ['房产', '房子', '物业', '房屋', '住宅']
        owner_words = ['业主', '房东', '房主', '物业主']
        city_words = ['城市', '地区', '地方']
        layout_words = ['房型', '户型', '布局', 'layout']
        
        # 动作词检测
        distribution_words = ['分布', '分配', '分散']
        comparison_words = ['最多', '最少', '排名', '排行', '前几', 'top']
        
        # 组合逻辑判断
        if has_quantity:
            if any(word in question_lower for word in property_words):
                if any(word in question_lower for word in city_words):
                    return "SELECT city as 城市, COUNT(*) as 房产数量 FROM properties WHERE city IS NOT NULL GROUP BY city ORDER BY COUNT(*) DESC", "高级分析 - 城市房产统计"
                else:
                    return "SELECT COUNT(*) as 房产总数 FROM properties", "高级分析 - 房产总数统计"
            
            elif any(word in question_lower for word in owner_words):
                return "SELECT COUNT(DISTINCT owner_id) as 业主总数 FROM owners", "高级分析 - 业主总数统计"
        
        # 特殊地区查询
        if any(region in question_lower for region in ['加州', 'california', '加利福尼亚', '洛杉矶', 'los angeles']):
            return "SELECT city as 城市, COUNT(*) as 房产数量 FROM properties WHERE state = 'California' GROUP BY city ORDER BY COUNT(*) DESC", "高级分析 - 加州房产分布"
        
        # WiFi相关查询
        if any(wifi_word in question_lower for wifi_word in ['wifi', '无线网', '网络', '上网']):
            return "SELECT COUNT(CASE WHEN wifi_name IS NOT NULL AND wifi_name != 'nan' THEN 1 END) as 有WiFi房产, COUNT(*) as 总房产数 FROM properties", "高级分析 - WiFi覆盖统计"
        
        return None
    
    def generate_sql_with_openai(self, question: str) -> Tuple[str, str]:
        """使用OpenAI生成SQL查询"""
        try:
            client = OpenAI(api_key=self.api_key)
            
            schema_prompt = self.generate_schema_prompt()
            
            system_prompt = f"""你是一个专业的SQL查询助手，擅长理解中文自然语言并生成PostgreSQL查询。

{schema_prompt}

重要规则：
1. 只生成SELECT查询，禁止增删改操作
2. 使用中文别名让结果更易懂
3. 合理使用聚合函数、分组、排序
4. 数字字段请用CAST转换类型
5. 注意NULL值处理，排除'nan'字符串
6. 自动添加LIMIT限制结果数量
7. 优先理解用户的真实意图

常见查询模式：
- 统计类：COUNT(*), COUNT(DISTINCT)
- 分布类：GROUP BY + ORDER BY
- 平均值：AVG(CAST(字段 AS NUMERIC))
- 排行榜：ORDER BY ... DESC LIMIT N

请根据问题生成SQL，只返回SQL语句。"""

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"用户问题：{question}"}
                ],
                max_tokens=600,
                temperature=0.2
            )
            
            sql_query = response.choices[0].message.content.strip()
            sql_query = self.clean_sql_query(sql_query)
            
            return sql_query, "OpenAI智能生成"
            
        except Exception as e:
            return "", f"OpenAI调用失败: {str(e)}"
    
    def clean_sql_query(self, sql: str) -> str:
        """清理和验证SQL查询"""
        # 移除代码块标记
        sql = re.sub(r'```(?:sql)?\s*', '', sql)
        sql = sql.strip()
        
        # 验证是SELECT查询
        if not sql.upper().startswith('SELECT'):
            return ""
        
        # 安全检查：禁止危险操作
        dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in sql.upper() for keyword in dangerous_keywords):
            return ""
        
        # 添加LIMIT
        if 'LIMIT' not in sql.upper():
            sql += ' LIMIT 100'
        
        return sql
    
    def generate_schema_prompt(self) -> str:
        """生成数据库结构说明"""
        schema_text = "=== 数据库表结构 ===\n\n"
        
        for table_name, table_info in self.schema_info.items():
            schema_text += f"表名: {table_name} - {table_info['description']}\n"
            schema_text += "字段说明:\n"
            for col, desc in table_info['columns'].items():
                schema_text += f"  • {col}: {desc}\n"
            schema_text += "\n"
        
        return schema_text
    
    def generate_sql_query(self, question: str) -> Tuple[str, str]:
        """主要的SQL生成入口"""
        if not question.strip():
            return "", "❌ 请输入您的问题"
        
        # 第一步：增强模式匹配
        result = self.enhanced_pattern_match(question)
        if result:
            return result
        
        # 第二步：高级关键词分析
        result = self.advanced_keyword_analysis(question)
        if result:
            return result
        
        # 第三步：OpenAI生成（如果可用）
        if self.use_openai:
            sql, method = self.generate_sql_with_openai(question)
            if sql:
                return sql, method
        
        # 第四步：基础兜底匹配
        return self.fallback_suggestions(question)
    
    def fallback_suggestions(self, question: str) -> Tuple[str, str]:
        """兜底建议"""
        # 检查是否包含一些基本概念
        if any(word in question.lower() for word in ['房产', '房子', '物业']):
            return "SELECT name as 房产名称, city as 城市, state as 州, layout as 房型 FROM properties LIMIT 20", "基础查询 - 房产基本信息"
        
        elif any(word in question.lower() for word in ['业主', '房东']):
            return "SELECT name as 业主姓名, phone as 电话, email as 邮箱 FROM owners LIMIT 20", "基础查询 - 业主基本信息"
        
        else:
            return "", "❌ 无法理解您的问题。请尝试：\n• 有多少房产？\n• 各个城市房产分布如何？\n• 加州有多少房产？\n• WiFi覆盖情况如何？"
    
    def explain_query(self, sql: str, question: str) -> str:
        """查询解释"""
        explanations = []
        
        if 'COUNT(*)' in sql.upper():
            explanations.append("📊 统计总数")
        if 'COUNT(DISTINCT' in sql.upper():
            explanations.append("🔢 统计唯一值")
        if 'GROUP BY' in sql.upper():
            explanations.append("📑 分组汇总")
        if 'ORDER BY' in sql.upper():
            explanations.append("📈 结果排序")
        if 'WHERE' in sql.upper():
            explanations.append("🔍 条件筛选")
        if 'AVG(' in sql.upper():
            explanations.append("📐 计算平均值")
        if 'MAX(' in sql.upper() or 'MIN(' in sql.upper():
            explanations.append("🎯 找极值")
        
        if explanations:
            return "🔍 查询说明: " + " | ".join(explanations)
        return "📝 执行基础查询"
    
    def format_results(self, df: pd.DataFrame, question: str) -> str:
        """结果格式化"""
        if df.empty:
            return "📭 查询未返回结果，请尝试调整问题描述"
        
        result_summary = f"✅ 查询成功! 共找到 **{len(df)}** 条记录\n\n"
        
        # 单值结果
        if len(df) == 1 and len(df.columns) == 1:
            value = df.iloc[0, 0]
            if isinstance(value, (int, float)):
                result_summary += f"**📊 答案: {value:,}**"
            else:
                result_summary += f"**📊 答案: {value}**"
            return result_summary
        
        # 统计结果显示
        if len(df) <= 15:
            result_summary += "**📈 详细结果:**\n"
            for idx, row in df.iterrows():
                if len(df.columns) == 2:
                    col1, col2 = df.columns
                    val1, val2 = row.iloc[0], row.iloc[1]
                    if isinstance(val2, (int, float)):
                        result_summary += f"• **{val1}**: {val2:,}\n"
                    else:
                        result_summary += f"• **{val1}**: {val2}\n"
                else:
                    # 多列显示
                    row_text = " | ".join([f"{col}: {val}" for col, val in row.items()])
                    result_summary += f"• {row_text}\n"
        else:
            result_summary += f"**📋 前10条结果预览** (共{len(df)}条):\n"
            for idx, row in df.head(10).iterrows():
                if len(df.columns) >= 2:
                    val1, val2 = row.iloc[0], row.iloc[1]
                    if isinstance(val2, (int, float)):
                        result_summary += f"• **{val1}**: {val2:,}\n"
                    else:
                        result_summary += f"• **{val1}**: {val2}\n"
        
        return result_summary

# 创建全局增强实例
ai_assistant = EnhancedAIQueryAssistant() 