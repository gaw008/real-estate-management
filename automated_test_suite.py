#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
房地产管理系统 - 自动化测试套件
用于每次更新后的完整功能测试
"""

import sys
import traceback
import time
from datetime import datetime

# 导入测试模块
from financial_reports import financial_reports_manager

class TestSuite:
    """自动化测试套件"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
    
    def run_test(self, test_name, test_func):
        """运行单个测试"""
        print(f"\n🧪 {test_name}...")
        try:
            result = test_func()
            status = "✅ 通过" if result else "❌ 失败"
            self.test_results.append((test_name, result, None))
            print(f"{status}")
            return result
        except Exception as e:
            print(f"❌ 异常: {e}")
            self.test_results.append((test_name, False, str(e)))
            return False
    
    def test_database_connection(self):
        """测试数据库连接"""
        conn = financial_reports_manager.get_db_connection()
        if conn:
            conn.close()
            return True
        return False
    
    def test_properties_list(self):
        """测试房产列表"""
        properties = financial_reports_manager.get_properties_list()
        return len(properties) > 0
    
    def test_financial_reports_table(self):
        """测试财务报表表结构"""
        conn = financial_reports_manager.get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES LIKE 'financial_reports'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                return False
            
            cursor.execute("DESCRIBE financial_reports")
            columns = cursor.fetchall()
            required_columns = ['id', 'property_id', 'report_year', 'report_month', 'report_title', 'onedrive_link']
            existing_columns = [col[0] for col in columns]
            
            return all(col in existing_columns for col in required_columns)
            
        finally:
            cursor.close()
            conn.close()
    
    def test_get_all_reports(self):
        """测试获取所有报表"""
        reports_data = financial_reports_manager.get_all_reports()
        return isinstance(reports_data, dict) and 'reports' in reports_data and 'total_count' in reports_data
    
    def test_flask_app_import(self):
        """测试Flask应用导入"""
        try:
            import real_estate_web
            return hasattr(real_estate_web, 'app')
        except ImportError:
            return False
    
    def test_financial_report_routes(self):
        """测试财务报表路由"""
        try:
            import real_estate_web
            routes = [str(rule) for rule in real_estate_web.app.url_map.iter_rules()]
            financial_routes = [r for r in routes if 'financial' in r.lower()]
            return len(financial_routes) >= 2  # 至少有管理员和业主的财务报表路由
        except:
            return False
    
    def test_save_financial_report(self):
        """测试保存财务报表功能"""
        try:
            # 获取第一个房产
            properties = financial_reports_manager.get_properties_list()
            if not properties:
                return False
            
            property_id = properties[0]['id']
            
            # 测试保存报表
            success, message = financial_reports_manager.add_financial_report(
                property_id=property_id,
                report_year=2024,
                report_month=12,
                report_title="自动化测试报表",
                onedrive_link="https://test.onedrive.com/test",
                uploaded_by=1,  # 假设用户ID为1
                notes="自动化测试"
            )
            
            if success:
                # 验证报表已保存
                reports_data = financial_reports_manager.get_all_reports()
                test_reports = [r for r in reports_data['reports'] if r['report_title'] == "自动化测试报表"]
                
                if test_reports:
                    # 清理测试数据
                    financial_reports_manager.delete_report(test_reports[0]['id'], 1)
                    return True
            
            return False
            
        except Exception as e:
            print(f"测试保存报表时出错: {e}")
            return False
    
    def test_users_table(self):
        """测试用户表"""
        try:
            conn = financial_reports_manager.get_db_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES LIKE 'users'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                return False
            
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            
            return count > 0
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    def run_all_tests(self):
        """运行所有测试"""
        print("═" * 80)
        print("🧪 房地产管理系统 - 自动化测试套件")
        print(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("═" * 80)
        
        # 核心功能测试
        core_tests = [
            ("数据库连接", self.test_database_connection),
            ("房产列表获取", self.test_properties_list),
            ("财务报表表结构", self.test_financial_reports_table),
            ("用户表检查", self.test_users_table),
        ]
        
        # 应用功能测试
        app_tests = [
            ("Flask应用导入", self.test_flask_app_import),
            ("财务报表路由", self.test_financial_report_routes),
            ("获取所有报表", self.test_get_all_reports),
            ("保存财务报表", self.test_save_financial_report),
        ]
        
        print("\n🔧 核心功能测试")
        print("-" * 40)
        core_results = []
        for test_name, test_func in core_tests:
            result = self.run_test(test_name, test_func)
            core_results.append(result)
        
        print("\n🌐 应用功能测试")
        print("-" * 40)
        app_results = []
        for test_name, test_func in app_tests:
            result = self.run_test(test_name, test_func)
            app_results.append(result)
        
        # 生成测试报告
        self.generate_report(core_results, app_results)
    
    def generate_report(self, core_results, app_results):
        """生成测试报告"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "═" * 80)
        print("📊 测试结果报告")
        print("═" * 80)
        
        passed = sum(1 for _, result, _ in self.test_results if result)
        failed = len(self.test_results) - passed
        
        print(f"总测试数: {len(self.test_results)}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"⏱️  用时: {duration.total_seconds():.2f} 秒")
        
        # 详细结果
        print("\n📋 详细结果:")
        for test_name, result, error in self.test_results:
            status = "✅" if result else "❌"
            print(f"{status} {test_name}")
            if error:
                print(f"   错误: {error}")
        
        # 核心功能状态
        core_health = all(core_results)
        app_health = all(app_results)
        
        print(f"\n🏗️  核心功能状态: {'✅ 健康' if core_health else '❌ 异常'}")
        print(f"🌐 应用功能状态: {'✅ 健康' if app_health else '❌ 异常'}")
        
        if failed == 0:
            print("\n🎉 所有测试通过！系统运行正常。")
        else:
            print(f"\n⚠️  发现 {failed} 个问题，请检查上述错误信息。")
        
        # 生成建议
        self.generate_suggestions(core_health, app_health)
    
    def generate_suggestions(self, core_health, app_health):
        """生成修复建议"""
        if not core_health:
            print("\n🔧 核心功能修复建议:")
            print("- 检查数据库连接配置")
            print("- 确认Aiven MySQL服务状态")
            print("- 运行数据库修复脚本")
        
        if not app_health:
            print("\n🔧 应用功能修复建议:")
            print("- 检查Flask应用代码语法")
            print("- 确认所有路由正确定义")
            print("- 测试Web应用启动")
        
        print("\n📋 手动测试建议:")
        print("1. 启动Web应用: python3 real_estate_web.py")
        print("2. 登录管理员账户")
        print("3. 测试各个功能模块")
        print("4. 检查财务报表添加/删除功能")

def main():
    """主函数"""
    test_suite = TestSuite()
    test_suite.run_all_tests()

if __name__ == "__main__":
    main() 