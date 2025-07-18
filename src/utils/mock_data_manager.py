#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟数据管理器
在数据库连接失败时提供测试数据
"""

from datetime import datetime, date

class MockDataManager:
    """模拟数据管理器 - 提供测试数据"""
    
    def __init__(self):
        self.mock_properties = [
            {
                'id': 'PROP001',
                'name': '海景公寓',
                'address': '123 Ocean View Dr',
                'city': 'Miami',
                'state': 'FL',
                'assigned_owners_count': 1
            },
            {
                'id': 'PROP002', 
                'name': '市中心豪华公寓',
                'address': '456 Downtown Ave',
                'city': 'New York',
                'state': 'NY',
                'assigned_owners_count': 2
            },
            {
                'id': 'PROP003',
                'name': '湖边别墅',
                'address': '789 Lake Shore Blvd',
                'city': 'Orlando',
                'state': 'FL',
                'assigned_owners_count': 0
            },
            {
                'id': 'PROP004',
                'name': '商务公寓',
                'address': '321 Business District',
                'city': 'Atlanta',
                'state': 'GA',
                'assigned_owners_count': 1
            },
            {
                'id': 'PROP005',
                'name': '度假屋',
                'address': '654 Vacation Way',
                'city': 'Key West',
                'state': 'FL',
                'assigned_owners_count': 3
            }
        ]
        
        self.mock_owners = [
            {
                'owner_id': 'OWN001',
                'name': '张三',
                'phone': '123-456-7890',
                'email': 'zhang@example.com',
                'assigned_properties_count': 2
            },
            {
                'owner_id': 'OWN002',
                'name': '李四',
                'phone': '234-567-8901', 
                'email': 'li@example.com',
                'assigned_properties_count': 1
            },
            {
                'owner_id': 'OWN003',
                'name': '王五',
                'phone': '345-678-9012',
                'email': 'wang@example.com',
                'assigned_properties_count': 3
            }
        ]
        
        self.mock_reports = [
            {
                'id': 1,
                'property_id': 'PROP001',
                'property_name': '海景公寓',
                'report_year': 2024,
                'report_month': 11,
                'report_title': '2024年11月财务报表',
                'onedrive_link': 'https://example.com/report1',
                'upload_date': datetime(2024, 12, 1, 10, 0, 0),
                'uploaded_by': 1,
                'uploaded_by_name': '管理员',
                'is_active': True
            },
            {
                'id': 2,
                'property_id': 'PROP002',
                'property_name': '市中心豪华公寓',
                'report_year': 2024,
                'report_month': 11,
                'report_title': '2024年11月财务报表',
                'onedrive_link': 'https://example.com/report2',
                'upload_date': datetime(2024, 12, 2, 14, 30, 0),
                'uploaded_by': 1,
                'uploaded_by_name': '管理员',
                'is_active': True
            }
        ]
        
    def get_properties_list(self):
        """获取模拟房产列表"""
        print("🧪 使用模拟房产数据（数据库连接失败时的备用数据）")
        return self.mock_properties.copy()
    
    def get_owners_list(self):
        """获取模拟业主列表"""
        print("🧪 使用模拟业主数据（数据库连接失败时的备用数据）")
        return self.mock_owners.copy()
    
    def get_all_reports(self, year=None, month=None, property_id=None, page=1, per_page=20):
        """获取模拟财务报表列表"""
        print("🧪 使用模拟财务报表数据（数据库连接失败时的备用数据）")
        
        reports = self.mock_reports.copy()
        
        # 过滤数据
        if year:
            reports = [r for r in reports if r['report_year'] == year]
        if month:
            reports = [r for r in reports if r['report_month'] == month]
        if property_id:
            reports = [r for r in reports if r['property_id'] == property_id]
        
        # 分页
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # 格式化日期
        for report in reports:
            report['upload_date_str'] = report['upload_date'].strftime('%Y-%m-%d %H:%M')
            report['report_date_str'] = f"{report['report_year']}年{report['report_month']}月"
        
        return {
            'reports': reports[start_idx:end_idx],
            'total_count': len(reports),
            'current_page': page,
            'per_page': per_page,
            'total_pages': (len(reports) + per_page - 1) // per_page
        }
    
    def get_property_assignments(self, property_id=None, owner_id=None):
        """获取模拟房产分配记录"""
        print("🧪 使用模拟分配数据（数据库连接失败时的备用数据）")
        
        # 模拟分配记录
        assignments = [
            {
                'id': 1,
                'property_id': 'PROP001',
                'property_name': '海景公寓',
                'property_address': '123 Ocean View Dr',
                'owner_id': 'OWN001',
                'owner_name': '张三',
                'owner_phone': '123-456-7890',
                'owner_email': 'zhang@example.com',
                'assigned_date': datetime(2024, 11, 1, 9, 0, 0),
                'assigned_date_str': '2024-11-01 09:00',
                'assigned_by_name': '管理员',
                'is_active': True
            },
            {
                'id': 2, 
                'property_id': 'PROP002',
                'property_name': '市中心豪华公寓',
                'property_address': '456 Downtown Ave',
                'owner_id': 'OWN002',
                'owner_name': '李四',
                'owner_phone': '234-567-8901',
                'owner_email': 'li@example.com',
                'assigned_date': datetime(2024, 11, 5, 14, 0, 0),
                'assigned_date_str': '2024-11-05 14:00',
                'assigned_by_name': '管理员',
                'is_active': True
            }
        ]
        
        # 过滤
        if property_id:
            assignments = [a for a in assignments if a['property_id'] == property_id]
        if owner_id:
            assignments = [a for a in assignments if a['owner_id'] == owner_id]
            
        return assignments
    
    def get_report_stats(self):
        """获取模拟报表统计"""
        print("🧪 使用模拟统计数据（数据库连接失败时的备用数据）")
        return {
            'total_reports': len(self.mock_reports),
            'current_month_reports': 2,
            'properties_with_reports': 2,
            'total_assignments': 2,
            'latest_upload': '2024-12-02 14:30'
        }
    
    def add_financial_report(self, property_id, report_year, report_month, report_title, onedrive_link, uploaded_by, notes=None):
        """模拟添加财务报表"""
        print("🧪 模拟添加财务报表（数据库连接失败时的演示功能）")
        return True, f"模拟添加成功: 房产 {property_id} 的 {report_year}年{report_month}月财务报表"
    
    def assign_property_to_owner(self, property_id, owner_id, assigned_by, notes=None):
        """模拟分配房产给业主"""
        print("🧪 模拟分配房产（数据库连接失败时的演示功能）")
        return True, f"模拟分配成功: 房产 {property_id} 已分配给业主 {owner_id}"

# 全局模拟数据管理器实例
mock_data_manager = MockDataManager() 