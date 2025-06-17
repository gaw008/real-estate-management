#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复财务报表表结构
将基于owner_id的表改为基于property_id的表
"""

from financial_reports import financial_reports_manager

def fix_financial_reports_table():
    """修复财务报表表结构"""
    print("🔧 修复财务报表表结构...")
    
    conn = financial_reports_manager.get_db_connection()
    if not conn:
        print("❌ 数据库连接失败")
        return False
    
    cursor = conn.cursor()
    
    try:
        # 1. 检查现有表是否有数据
        cursor.execute("SELECT COUNT(*) FROM financial_reports")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"⚠️  现有表中有 {count} 条数据")
            print("将备份现有数据到临时表...")
            
            # 备份现有数据
            cursor.execute("""
                CREATE TABLE financial_reports_backup AS 
                SELECT * FROM financial_reports
            """)
            print("✅ 数据备份完成")
        
        # 2. 删除现有表
        print("🗑️  删除现有的financial_reports表...")
        cursor.execute("DROP TABLE IF EXISTS financial_reports")
        
        # 3. 删除property_assignments表（如果存在）
        print("🗑️  删除property_assignments表...")
        cursor.execute("DROP TABLE IF EXISTS property_assignments")
        
        conn.commit()
        print("✅ 旧表删除成功")
        
        # 4. 重新创建正确的表结构
        print("🔨 创建新的表结构...")
        success = financial_reports_manager.create_reports_table()
        
        if success:
            print("✅ 新表结构创建成功")
            
            # 5. 验证新表结构
            cursor.execute("DESCRIBE financial_reports")
            columns = cursor.fetchall()
            print("📋 新的表结构:")
            for col in columns:
                print(f"  📝 {col[0]} - {col[1]}")
            
            return True
        else:
            print("❌ 新表结构创建失败")
            return False
        
    except Exception as e:
        print(f"❌ 修复过程出错: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def test_new_table():
    """测试新表的功能"""
    print("\n🧪 测试新表功能...")
    
    # 获取一个房产进行测试
    properties = financial_reports_manager.get_properties_list()
    if not properties:
        print("❌ 无法获取房产列表")
        return False
    
    test_property = properties[0]
    property_id = test_property['id']
    property_name = test_property['name']
    
    print(f"📋 使用测试房产: {property_name} (ID: {property_id})")
    
    # 测试添加财务报表
    success, message = financial_reports_manager.add_financial_report(
        property_id=property_id,
        report_year=2024,
        report_month=12,
        report_title="2024年12月财务报表测试",
        onedrive_link="https://onedrive.live.com/test-link",
        uploaded_by=1,
        notes="表结构修复后的测试数据"
    )
    
    if success:
        print(f"✅ 测试成功: {message}")
        
        # 验证数据是否保存
        reports = financial_reports_manager.get_all_reports(
            year=2024, 
            month=12, 
            property_id=property_id
        )
        
        if reports and reports['reports']:
            print("✅ 数据验证成功，报表已正确保存")
            return True
        else:
            print("❌ 数据验证失败")
            return False
    else:
        print(f"❌ 测试失败: {message}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🛠️  财务报表表结构修复工具")
    print("=" * 60)
    
    # 步骤1: 修复表结构
    fix_success = fix_financial_reports_table()
    
    if fix_success:
        # 步骤2: 测试新表功能
        test_success = test_new_table()
        
        if test_success:
            print("\n🎉 修复完成！财务报表功能现在可以正常工作了。")
        else:
            print("\n⚠️  表结构修复成功，但功能测试失败。")
    else:
        print("\n❌ 表结构修复失败。")

if __name__ == "__main__":
    main() 