#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多语言管理系统
Language Management System
"""

from flask import session, request
import json
import os

class LanguageManager:
    def __init__(self):
        self.default_language = 'zh'
        self.supported_languages = ['zh', 'en']
        self.translations = {}
        self.load_translations()
    
    def load_translations(self):
        """加载翻译文件"""
        # 中文翻译
        self.translations['zh'] = {
            # 通用
            'welcome': '欢迎',
            'login': '登录',
            'logout': '退出登录',
            'register': '注册',
            'dashboard': '仪表板',
            'settings': '设置',
            'profile': '个人资料',
            'change_password': '修改密码',
            'save': '保存',
            'cancel': '取消',
            'submit': '提交',
            'edit': '编辑',
            'delete': '删除',
            'view': '查看',
            'search': '搜索',
            'filter': '筛选',
            'export': '导出',
            'import': '导入',
            'refresh': '刷新',
            'back': '返回',
            'next': '下一步',
            'previous': '上一步',
            'confirm': '确认',
            'yes': '是',
            'no': '否',
            'loading': '加载中...',
            'success': '成功',
            'error': '错误',
            'warning': '警告',
            'info': '信息',
            
            # 用户管理
            'username': '用户名',
            'password': '密码',
            'email': '邮箱',
            'full_name': '姓名',
            'user_type': '用户类型',
            'admin': '管理员',
            'owner': '业主',
            'employee': '员工',
            'current_password': '当前密码',
            'new_password': '新密码',
            'confirm_password': '确认密码',
            'password_strength': '密码强度',
            'password_requirements': '密码要求',
            'login_required': '请先登录',
            'admin_required': '需要管理员权限',
            'super_admin_required': '此功能仅限超级管理员访问',
            
            # 注册相关
            
            'approved': '已批准',
            'rejected': '已拒绝',
            'pending': '待审核',
            'approve': '批准',
            'reject': '拒绝',
        
            'review_date': '审核日期',
            'reviewer': '审核人',
        
            'review_notes': '审核备注',
            
            # 房产管理
            'properties': '房产',
            'property_management': '房产管理',
            'property_name': '房产名称',
            'property_address': '房产地址',
            'property_type': '房产类型',
            'property_size': '房产面积',
            'bedrooms': '卧室数',
            'bathrooms': '浴室数',
            'city': '城市',
            'state': '州/省',
            'zip_code': '邮编',
            
            # 业主管理
            'owners': '业主',
            'owner_management': '业主管理',
            'owner_name': '业主姓名',
            'owner_email': '业主邮箱',
            'owner_phone': '业主电话',
            'owner_properties': '我的房产',
            
            # 财务管理
            'finance': '财务',
            'income': '收入',
            'expense': '支出',
            'revenue': '营收',
            'management_fee': '管理费',
            'cleaning_fee': '清洁费',
            'total_income': '总收入',
            'net_income': '净收入',
            'gross_income': '总收入',
            
            # 统计信息
            'statistics': '统计',
            'total_properties': '房产总数',
            'total_owners': '业主总数',
            'total_cities': '城市数量',
            'total_states': '州数量',
            'active_properties': '活跃房产',
            'recent_activities': '最近活动',
            'quick_actions': '快速操作',
            
            # 系统信息
            'system_title': '房地产管理系统',
            'welcome_back': '欢迎回来',
            'today_is': '今天是',
            'have_a_nice_day': '祝您工作愉快！',
            'language': '语言',
            'chinese': '中文',
            'english': 'English',
            
            # 表单验证
            'field_required': '此字段为必填项',
            'invalid_email': '邮箱格式不正确',
            'password_too_short': '密码长度至少8位',
            'passwords_not_match': '两次输入的密码不一致',
            'invalid_credentials': '用户名或密码错误',
            
            # 操作消息
            'operation_success': '操作成功',
            'operation_failed': '操作失败',
            'data_saved': '数据已保存',
            'data_deleted': '数据已删除',
            'password_changed': '密码修改成功',
            
            
            # 页面标题
            'login_page_title': '登录 - 房地产管理系统',
            'dashboard_page_title': '仪表板 - 房地产管理系统',
            'register_page_title': '注册 - 房地产管理系统',
            'change_password_page_title': '修改密码 - 房地产管理系统',
        
            'reset_password_page_title': '重置密码 - 房地产管理系统',
            
            # 额外翻译
            'language_changed': '语言已切换',
            'no_recent_activities': '暂无最近活动',
            'view_all_properties': '查看所有房产',
            'view_all_owners': '查看所有业主',
            'reset_user_password': '重置用户密码',
            'financial_reports': '财务报表',
            'add_new_property': '添加新房产',
            'add_new_owner': '添加新业主',
            'income_details': '收入明细',
            'income_trends': '收入趋势',
            'account_settings': '账户设置',
            
            # 登录页面
            'please_select_user_type_and_login': '请选择用户类型并登录',
            'company_internal': '公司内部',
            'property_owner': '房屋业主',
            'no_account_yet': '还没有账号？',
            'register_now': '立即注册',
            'login_help': '登录帮助',
            'admin_login_help': '公司内部员工请选择"公司内部"',
            'owner_login_help': '房屋业主请选择"房屋业主"',
            'default_admin_account': '默认管理员账号: admin / admin123',
            
            # 登录消息
            'please_enter_username_password': '请输入用户名和密码',
            'user_type_mismatch': '用户类型不匹配',
            'session_creation_failed': '会话创建失败，请重试',
            
            # 财务报表相关
            '财务报表管理': '财务报表管理',
            '我的财务报表': '我的财务报表',
            '添加财务报表': '添加财务报表',
            '查看财务报表': '查看财务报表',
            '报表管理': '报表管理',
            '月度财务报表': '月度财务报表',
            '选择业主': '选择业主',
            '请选择业主': '请选择业主',
            '年份': '年份',
            '月份': '月份',
            '报表标题': '报表标题',
            '报表期间': '报表期间',
            'OneDrive链接': 'OneDrive链接',
            '上传时间': '上传时间',
            '上传者': '上传者',
            '备注': '备注',
            '备注信息': '备注信息',
            '可选备注信息': '可选备注信息',
            '例如：月度财务报表': '例如：月度财务报表',
            '请输入完整的OneDrive分享链接': '请输入完整的OneDrive分享链接',
            '添加报表': '添加报表',
            '查看报表': '查看报表',
            '查看': '查看',
            '删除': '删除',
            '确认删除': '确认删除',
            '取消': '取消',
            '筛选': '筛选',
            '重置': '重置',
            '所有年份': '所有年份',
            '所有月份': '所有月份',
            '所有业主': '所有业主',
            '当前显示': '当前显示',
            '清除筛选': '清除筛选',
            '选择年份': '选择年份',
            '报表统计': '报表统计',
            '总报表数': '总报表数',
            '本月报表': '本月报表',
            '当前年份': '当前年份',
            '条记录': '条记录',
            '财务报表列表': '财务报表列表',
            '管理业主的月度财务报表': '管理业主的月度财务报表',
            '查看您的月度财务报表和收益情况': '查看您的月度财务报表和收益情况',
            '暂无财务报表': '暂无财务报表',
            '您还没有任何财务报表，请联系管理员上传': '您还没有任何财务报表，请联系管理员上传',
            '年暂无财务报表记录': '年暂无财务报表记录',
            '查看所有报表': '查看所有报表',
            '财务报表通常在每月月底或次月初更新': '财务报表通常在每月月底或次月初更新',
            '如有疑问，请联系我们的客服团队': '如有疑问，请联系我们的客服团队',
            '使用说明': '使用说明',
            '财务报表按月度生成，包含您的收益和支出明细': '财务报表按月度生成，包含您的收益和支出明细',
            '点击"查看报表"按钮可以在新窗口中打开OneDrive文档': '点击"查看报表"按钮可以在新窗口中打开OneDrive文档',
            '如果报表链接无法访问，请联系管理员检查权限设置': '如果报表链接无法访问，请联系管理员检查权限设置',
            '建议定期下载保存重要的财务报表到本地': '建议定期下载保存重要的财务报表到本地',
            '确定要删除以下财务报表吗？': '确定要删除以下财务报表吗？',
            '业主': '业主',
            '显示最近的报表，如需查看更多请联系管理员': '显示最近的报表，如需查看更多请联系管理员',
            '请使用上方表单添加第一个财务报表': '请使用上方表单添加第一个财务报表',
            '返回仪表板': '返回仪表板',
            '房地产管理系统': '房地产管理系统',
            '月': '月',
            '年': '年',
            '系统管理员': '系统管理员',
        }
        
        # 英文翻译
        self.translations['en'] = {
            # Common
            'welcome': 'Welcome',
            'login': 'Login',
            'logout': 'Logout',
            'register': 'Register',
            'dashboard': 'Dashboard',
            'settings': 'Settings',
            'profile': 'Profile',
            'change_password': 'Change Password',
            'save': 'Save',
            'cancel': 'Cancel',
            'submit': 'Submit',
            'edit': 'Edit',
            'delete': 'Delete',
            'view': 'View',
            'search': 'Search',
            'filter': 'Filter',
            'export': 'Export',
            'import': 'Import',
            'refresh': 'Refresh',
            'back': 'Back',
            'next': 'Next',
            'previous': 'Previous',
            'confirm': 'Confirm',
            'yes': 'Yes',
            'no': 'No',
            'loading': 'Loading...',
            'success': 'Success',
            'error': 'Error',
            'warning': 'Warning',
            'info': 'Information',
            
            # User Management
            'username': 'Username',
            'password': 'Password',
            'email': 'Email',
            'full_name': 'Full Name',
            'user_type': 'User Type',
            'admin': 'Administrator',
            'owner': 'Owner',
            'employee': 'Employee',
            'current_password': 'Current Password',
            'new_password': 'New Password',
            'confirm_password': 'Confirm Password',
            'password_strength': 'Password Strength',
            'password_requirements': 'Password Requirements',
            'login_required': 'Please login first',
            'admin_required': 'Administrator privileges required',
            'super_admin_required': 'This feature is restricted to super administrators only',
            
            
            'approved': 'Approved',
            'rejected': 'Rejected',
            'pending': 'Pending',
            'approve': 'Approve',
            'reject': 'Reject',
        
            'review_date': 'Review Date',
            'reviewer': 'Reviewer',
        
            'review_notes': 'Review Notes',
            
            # Property Management
            'properties': 'Properties',
            'property_management': 'Property Management',
            'property_name': 'Property Name',
            'property_address': 'Property Address',
            'property_type': 'Property Type',
            'property_size': 'Property Size',
            'bedrooms': 'Bedrooms',
            'bathrooms': 'Bathrooms',
            'city': 'City',
            'state': 'State',
            'zip_code': 'ZIP Code',
            
            # Owner Management
            'owners': 'Owners',
            'owner_management': 'Owner Management',
            'owner_name': 'Owner Name',
            'owner_email': 'Owner Email',
            'owner_phone': 'Owner Phone',
            'owner_properties': 'My Properties',
            
            # Financial Management
            'finance': 'Finance',
            'income': 'Income',
            'expense': 'Expense',
            'revenue': 'Revenue',
            'management_fee': 'Management Fee',
            'cleaning_fee': 'Cleaning Fee',
            'total_income': 'Total Income',
            'net_income': 'Net Income',
            'gross_income': 'Gross Income',
            
            # Statistics
            'statistics': 'Statistics',
            'total_properties': 'Total Properties',
            'total_owners': 'Total Owners',
            'total_cities': 'Total Cities',
            'total_states': 'Total States',
            'active_properties': 'Active Properties',
            'recent_activities': 'Recent Activities',
            'quick_actions': 'Quick Actions',
            
            # System Information
            'system_title': 'Real Estate Management System',
            'welcome_back': 'Welcome back',
            'today_is': 'Today is',
            'have_a_nice_day': 'Have a nice day!',
            'language': 'Language',
            'chinese': '中文',
            'english': 'English',
            
            # Form Validation
            'field_required': 'This field is required',
            'invalid_email': 'Invalid email format',
            'password_too_short': 'Password must be at least 8 characters',
            'passwords_not_match': 'Passwords do not match',
            'invalid_credentials': 'Invalid username or password',
            
            # Operation Messages
            'operation_success': 'Operation successful',
            'operation_failed': 'Operation failed',
            'data_saved': 'Data saved',
            'data_deleted': 'Data deleted',
            'password_changed': 'Password changed successfully',
            
            
            # Page Titles
            'login_page_title': 'Login - Real Estate Management System',
            'dashboard_page_title': 'Dashboard - Real Estate Management System',
            'register_page_title': 'Register - Real Estate Management System',
            'change_password_page_title': 'Change Password - Real Estate Management System',
        
            'reset_password_page_title': 'Reset Password - Real Estate Management System',
            
            # Additional translations
            'language_changed': 'Language changed',
            'no_recent_activities': 'No recent activities',
            'view_all_properties': 'View All Properties',
            'view_all_owners': 'View All Owners',
            'reset_user_password': 'Reset User Password',
            'financial_reports': 'Financial Reports',
            'add_new_property': 'Add New Property',
            'add_new_owner': 'Add New Owner',
            'income_details': 'Income Details',
            'income_trends': 'Income Trends',
            'account_settings': 'Account Settings',
            
            # Login page
            'please_select_user_type_and_login': 'Please select user type and login',
            'company_internal': 'Company Internal',
            'property_owner': 'Property Owner',
            'no_account_yet': "Don't have an account yet?",
            'register_now': 'Register Now',
            'login_help': 'Login Help',
            'admin_login_help': 'Company employees please select "Company Internal"',
            'owner_login_help': 'Property owners please select "Property Owner"',
            'default_admin_account': 'Default admin account: admin / admin123',
            
            # Login message
            'please_enter_username_password': 'Please enter username and password',
            'user_type_mismatch': 'User type mismatch',
            'session_creation_failed': 'Session creation failed, please try again',
            
            # Financial Reports
            '财务报表管理': 'Financial Reports Management',
            '我的财务报表': 'My Financial Reports',
            '添加财务报表': 'Add Financial Report',
            '查看财务报表': 'View Financial Reports',
            '报表管理': 'Report Management',
            '月度财务报表': 'Monthly Financial Report',
            '选择业主': 'Select Owner',
            '请选择业主': 'Please select owner',
            '年份': 'Year',
            '月份': 'Month',
            '报表标题': 'Report Title',
            '报表期间': 'Report Period',
            'OneDrive链接': 'OneDrive Link',
            '上传时间': 'Upload Time',
            '上传者': 'Uploaded By',
            '备注': 'Notes',
            '备注信息': 'Notes Information',
            '可选备注信息': 'Optional notes',
            '例如：月度财务报表': 'e.g.: Monthly Financial Report',
            '请输入完整的OneDrive分享链接': 'Please enter complete OneDrive sharing link',
            '添加报表': 'Add Report',
            '查看报表': 'View Report',
            '查看': 'View',
            '删除': 'Delete',
            '确认删除': 'Confirm Delete',
            '取消': 'Cancel',
            '筛选': 'Filter',
            '重置': 'Reset',
            '所有年份': 'All Years',
            '所有月份': 'All Months',
            '所有业主': 'All Owners',
            '当前显示': 'Currently Showing',
            '清除筛选': 'Clear Filter',
            '选择年份': 'Select Year',
            '报表统计': 'Report Statistics',
            '总报表数': 'Total Reports',
            '本月报表': 'This Month Reports',
            '当前年份': 'Current Year',
            '条记录': 'Records',
            '财务报表列表': 'Financial Reports List',
            '管理业主的月度财务报表': 'Manage monthly financial reports for owners',
            '查看您的月度财务报表和收益情况': 'View your monthly financial reports and earnings',
            '暂无财务报表': 'No Financial Reports',
            '您还没有任何财务报表，请联系管理员上传': 'You don\'t have any financial reports yet, please contact administrator to upload',
            '年暂无财务报表记录': ' has no financial report records',
            '查看所有报表': 'View All Reports',
            '财务报表通常在每月月底或次月初更新': 'Financial reports are usually updated at the end of each month or early next month',
            '如有疑问，请联系我们的客服团队': 'If you have any questions, please contact our customer service team',
            '使用说明': 'Instructions',
            '财务报表按月度生成，包含您的收益和支出明细': 'Financial reports are generated monthly and include details of your income and expenses',
            '点击"查看报表"按钮可以在新窗口中打开OneDrive文档': 'Click "View Report" button to open OneDrive document in new window',
            '如果报表链接无法访问，请联系管理员检查权限设置': 'If report link is not accessible, please contact administrator to check permission settings',
            '建议定期下载保存重要的财务报表到本地': 'It is recommended to regularly download and save important financial reports locally',
            '确定要删除以下财务报表吗？': 'Are you sure you want to delete the following financial report?',
            '业主': 'Owner',
            '显示最近的报表，如需查看更多请联系管理员': 'Showing recent reports, contact administrator for more',
            '请使用上方表单添加第一个财务报表': 'Please use the form above to add the first financial report',
            '返回仪表板': 'Back to Dashboard',
            '房地产管理系统': 'Real Estate Management System',
            '月': 'Month',
            '年': 'Year',
            '系统管理员': 'System Administrator',
        }
    
    def get_current_language(self):
        """获取当前语言"""
        # 优先从session获取
        if 'language' in session:
            return session['language']
        
        # 从请求头获取
        if request and hasattr(request, 'accept_languages'):
            browser_lang = request.accept_languages.best_match(self.supported_languages)
            if browser_lang:
                return browser_lang
        
        return self.default_language
    
    def set_language(self, language):
        """设置语言"""
        if language in self.supported_languages:
            session['language'] = language
            return True
        return False
    
    def get_text(self, key, language=None):
        """获取翻译文本"""
        if language is None:
            language = self.get_current_language()
        
        if language in self.translations and key in self.translations[language]:
            return self.translations[language][key]
        
        # 回退到默认语言
        if self.default_language in self.translations and key in self.translations[self.default_language]:
            return self.translations[self.default_language][key]
        
        # 如果都没有找到，返回key本身
        return key
    
    def get_all_texts(self, language=None):
        """获取所有翻译文本"""
        if language is None:
            language = self.get_current_language()
        
        return self.translations.get(language, self.translations[self.default_language])

# 全局语言管理器实例
language_manager = LanguageManager()

# Flask模板函数
def get_text(key, language=None):
    """模板中使用的翻译函数"""
    return language_manager.get_text(key, language)

def get_current_language():
    """获取当前语言"""
    return language_manager.get_current_language()

def is_chinese():
    """判断是否为中文"""
    return language_manager.get_current_language() == 'zh'

def is_english():
    """判断是否为英文"""
    return language_manager.get_current_language() == 'en' 