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
            'user_registration': '用户注册',
            'registration_review': '注册审核',
            'pending_registrations': '待审核注册',
            'approved': '已批准',
            'rejected': '已拒绝',
            'pending': '待审核',
            'approve': '批准',
            'reject': '拒绝',
            'registration_date': '注册日期',
            'review_date': '审核日期',
            'reviewer': '审核人',
            'registration_notes': '注册说明',
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
            'registration_submitted': '注册申请已提交',
            'registration_approved': '注册申请已批准',
            'registration_rejected': '注册申请已拒绝',
            
            # 页面标题
            'login_page_title': '登录 - 房地产管理系统',
            'dashboard_page_title': '仪表板 - 房地产管理系统',
            'register_page_title': '注册 - 房地产管理系统',
            'change_password_page_title': '修改密码 - 房地产管理系统',
            'admin_registrations_page_title': '注册审核 - 房地产管理系统',
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
            
            # Registration
            'user_registration': 'User Registration',
            'registration_review': 'Registration Review',
            'pending_registrations': 'Pending Registrations',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'pending': 'Pending',
            'approve': 'Approve',
            'reject': 'Reject',
            'registration_date': 'Registration Date',
            'review_date': 'Review Date',
            'reviewer': 'Reviewer',
            'registration_notes': 'Registration Notes',
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
            'registration_submitted': 'Registration application submitted',
            'registration_approved': 'Registration application approved',
            'registration_rejected': 'Registration application rejected',
            
            # Page Titles
            'login_page_title': 'Login - Real Estate Management System',
            'dashboard_page_title': 'Dashboard - Real Estate Management System',
            'register_page_title': 'Register - Real Estate Management System',
            'change_password_page_title': 'Change Password - Real Estate Management System',
            'admin_registrations_page_title': 'Registration Review - Real Estate Management System',
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