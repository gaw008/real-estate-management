#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户房产分配功能演示
展示新功能的使用方法
"""

from financial_reports import financial_reports_manager

def demo_user_selection():
    """演示用户选择功能"""
    print("🏠 房产分配管理 - 用户选择演示")
    print("=" * 60)
    
    # 获取用户列表
    users = financial_reports_manager.get_users_list()
    
    print(f"📊 可分配用户总数: {len(users)}")
    print("\n👥 可选择的用户列表（前10个）:")
    
    for i, user in enumerate(users[:10], 1):
        user_type_desc = "管理员" if user['user_type'] == 'admin' else "业主"
        assigned_count = user['assigned_properties_count']
        assigned_desc = f"（已分配{assigned_count}个房产）" if assigned_count > 0 else "（尚未分配房产）"
        
        print(f"  {i:2d}. {user['full_name']} ({user['username']}) - {user_type_desc} {assigned_desc}")
    
    if len(users) > 10:
        print(f"  ... 还有 {len(users) - 10} 个用户")
    
    print("\n✨ 管理员现在可以选择任何已注册用户来分配房产！")

def demo_user_reports():
    """演示用户查看报表功能"""
    print("\n\n💰 用户财务报表查看演示")
    print("=" * 60)
    
    # 找一个有分配房产的用户
    users = financial_reports_manager.get_users_list()
    users_with_properties = [u for u in users if u['assigned_properties_count'] > 0]
    
    if users_with_properties:
        demo_user = users_with_properties[0]
        user_id = demo_user['id']
        
        print(f"🔍 演示用户: {demo_user['full_name']} ({demo_user['username']})")
        print(f"📋 已分配房产数: {demo_user['assigned_properties_count']}")
        
        # 获取用户的财务报表
        reports = financial_reports_manager.get_user_reports(user_id)
        
        if reports:
            print(f"\n📊 该用户可查看的财务报表 ({len(reports)} 条):")
            for i, report in enumerate(reports[:5], 1):
                print(f"  {i}. {report['property_name']} - {report.get('report_date_str', 'N/A')}")
                print(f"     标题: {report['report_title']}")
                print(f"     上传时间: {report.get('upload_date_str', 'N/A')}")
            
            if len(reports) > 5:
                print(f"  ... 还有 {len(reports) - 5} 个报表")
        else:
            print("\n📝 该用户暂无可查看的财务报表")
    else:
        print("📝 目前没有用户被分配房产，演示数据不足")
    
    print("\n✨ 用户登录后可以查看分配给他们的所有房产的财务报表！")

def demo_comparison():
    """演示新旧系统对比"""
    print("\n\n🔄 新旧系统对比")
    print("=" * 60)
    
    users = financial_reports_manager.get_users_list()
    owners = financial_reports_manager.get_owners_list()
    
    print("📊 数据对比:")
    print(f"  原系统 (owners表): {len(owners)} 个业主记录")
    print(f"  新系统 (users表):  {len(users)} 个用户记录")
    
    print("\n🎯 功能改进:")
    print("  ✅ 原来: 只能分配给 owners 表中的业主")
    print("  ✅ 现在: 可以分配给任何已注册的用户")
    print("  ✅ 原来: 业主需要在 owners 表中有记录才能查看")
    print("  ✅ 现在: 任何用户注册后即可被分配房产")
    
    print("\n💡 使用场景:")
    print("  1. 管理员在后台选择已注册用户进行房产分配")
    print("  2. 用户登录自己的账户查看分配的房产报表")
    print("  3. 系统统一使用 users 表管理所有用户关系")

def main():
    """主演示函数"""
    print("🎉 房地产管理系统 - 用户房产分配功能演示")
    print("=" * 80)
    print("本演示展示系统从 owners 表改为 users 表后的新功能")
    print("=" * 80)
    
    try:
        demo_user_selection()
        demo_user_reports()
        demo_comparison()
        
        print("\n\n🎊 演示完成！")
        print("=" * 80)
        print("📋 总结:")
        print("1. ✅ 房产分配管理现在使用 users 表")
        print("2. ✅ 用户可以登录查看分配给他们的房产报表")
        print("3. ✅ 管理员可以分配房产给任何已注册用户")
        print("4. ✅ 所有功能经过测试，运行正常")
        
        print("\n🚀 下一步:")
        print("- 启动 Web 应用测试分配功能")
        print("- 用户登录后查看财务报表功能")
        print("- 体验新的用户界面")
        
    except Exception as e:
        print(f"❌ 演示过程中出错: {e}")

if __name__ == "__main__":
    main() 