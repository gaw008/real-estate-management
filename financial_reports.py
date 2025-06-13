#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务报表管理系统
Financial Reports Management System
"""

import mysql.connector
from datetime import datetime, date
from config_loader import DB_CONFIG

class FinancialReportsManager:
    def __init__(self):
        pass
    
    def get_db_connection(self):
        """获取数据库连接"""
        try:
            ssl_config = {
                'ssl_disabled': False,
                'ssl_verify_cert': False,
                'ssl_verify_identity': False
            }
            config = {**DB_CONFIG, **ssl_config}
            connection = mysql.connector.connect(**config)
            return connection
        except Exception as e:
            print(f"数据库连接错误: {e}")
            return None
    
    def create_reports_table(self):
        """创建财务报表表"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            # 创建财务报表表
            reports_sql = """
            CREATE TABLE IF NOT EXISTS financial_reports (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                report_year INT NOT NULL,
                report_month INT NOT NULL,
                report_title VARCHAR(200) NOT NULL,
                onedrive_link TEXT NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploaded_by INT NOT NULL,
                notes TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                UNIQUE KEY unique_username_month (username, report_year, report_month),
                INDEX idx_username (username),
                INDEX idx_report_date (report_year, report_month),
                INDEX idx_upload_date (upload_date),
                FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(reports_sql)
            conn.commit()
            print("✅ 财务报表表创建成功")
            return True
            
        except Exception as e:
            print(f"❌ 创建财务报表表失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def add_financial_report(self, username, report_year, report_month, report_title, onedrive_link, uploaded_by, notes=None):
        """添加财务报表"""
        conn = self.get_db_connection()
        if not conn:
            return False, "数据库连接失败"
        
        cursor = conn.cursor()
        
        try:
            # 检查是否已存在该月份的报表
            check_sql = """
                SELECT id FROM financial_reports 
                WHERE username = %s AND report_year = %s AND report_month = %s AND is_active = TRUE
            """
            cursor.execute(check_sql, (username, report_year, report_month))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有报表
                update_sql = """
                    UPDATE financial_reports 
                    SET report_title = %s, onedrive_link = %s, uploaded_by = %s, notes = %s, 
                        upload_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE username = %s AND report_year = %s AND report_month = %s AND is_active = TRUE
                """
                cursor.execute(update_sql, (report_title, onedrive_link, uploaded_by, notes, username, report_year, report_month))
                message = f"{report_year}年{report_month}月财务报表已更新"
            else:
                # 插入新报表
                insert_sql = """
                    INSERT INTO financial_reports (username, report_year, report_month, report_title, onedrive_link, uploaded_by, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_sql, (username, report_year, report_month, report_title, onedrive_link, uploaded_by, notes))
                message = f"{report_year}年{report_month}月财务报表添加成功"
            
            conn.commit()
            return True, message
            
        except mysql.connector.IntegrityError as e:
            print(f"❌ 财务报表添加失败（完整性错误）: {e}")
            return False, "该月份报表已存在或数据格式错误"
        except Exception as e:
            print(f"❌ 财务报表添加失败: {e}")
            conn.rollback()
            return False, f"添加失败: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    
    def get_owner_reports(self, username, year=None, limit=None):
        """获取业主的财务报表"""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 构建查询条件
            where_conditions = ["fr.username = %s", "fr.is_active = TRUE"]
            params = [username]
            
            if year:
                where_conditions.append("fr.report_year = %s")
                params.append(year)
            
            where_clause = " AND ".join(where_conditions)
            
            # 查询报表
            query_sql = f"""
                SELECT fr.*, u.full_name as uploaded_by_name,
                       u2.full_name as owner_name
                FROM financial_reports fr
                LEFT JOIN users u ON fr.uploaded_by = u.id
                LEFT JOIN users u2 ON fr.username = u2.username
                WHERE {where_clause}
                ORDER BY fr.report_year DESC, fr.report_month DESC
            """
            
            if limit:
                query_sql += f" LIMIT {limit}"
            
            cursor.execute(query_sql, params)
            reports = cursor.fetchall()
            
            # 格式化日期显示
            for report in reports:
                report['report_date_str'] = f"{report['report_year']}年{report['report_month']}月"
                report['upload_date_str'] = report['upload_date'].strftime('%Y-%m-%d %H:%M')
            
            return reports
            
        except Exception as e:
            print(f"❌ 获取财务报表失败: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def get_all_reports(self, year=None, month=None, username=None, page=1, per_page=20):
        """获取所有财务报表（管理员用）"""
        conn = self.get_db_connection()
        if not conn:
            return [], 0
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 构建查询条件
            where_conditions = ["fr.is_active = TRUE"]
            params = []
            
            if year:
                where_conditions.append("fr.report_year = %s")
                params.append(year)
            
            if month:
                where_conditions.append("fr.report_month = %s")
                params.append(month)
            
            if username:
                where_conditions.append("fr.username = %s")
                params.append(username)
            
            where_clause = " AND ".join(where_conditions)
            
            # 获取总数
            count_sql = f"""
                SELECT COUNT(*) as total
                FROM financial_reports fr
                WHERE {where_clause}
            """
            cursor.execute(count_sql, params)
            total_count = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * per_page
            query_sql = f"""
                SELECT fr.*, u.full_name as uploaded_by_name,
                       u2.full_name as owner_name, u2.email as owner_email
                FROM financial_reports fr
                LEFT JOIN users u ON fr.uploaded_by = u.id
                LEFT JOIN users u2 ON fr.username = u2.username
                WHERE {where_clause}
                ORDER BY fr.report_year DESC, fr.report_month DESC, fr.upload_date DESC
                LIMIT %s OFFSET %s
            """
            
            cursor.execute(query_sql, params + [per_page, offset])
            reports = cursor.fetchall()
            
            # 格式化日期显示
            for report in reports:
                report['report_date_str'] = f"{report['report_year']}年{report['report_month']}月"
                report['upload_date_str'] = report['upload_date'].strftime('%Y-%m-%d %H:%M')
            
            return reports, total_count
            
        except Exception as e:
            print(f"❌ 获取所有财务报表失败: {e}")
            return [], 0
        finally:
            cursor.close()
            conn.close()
    
    def delete_report(self, report_id, admin_id):
        """删除财务报表（软删除）"""
        conn = self.get_db_connection()
        if not conn:
            return False, "数据库连接失败"
        
        cursor = conn.cursor()
        
        try:
            # 软删除报表
            update_sql = """
                UPDATE financial_reports 
                SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            cursor.execute(update_sql, (report_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True, "财务报表删除成功"
            else:
                return False, "报表不存在或已删除"
            
        except Exception as e:
            print(f"❌ 删除财务报表失败: {e}")
            conn.rollback()
            return False, f"删除失败: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    
    def get_owners_list(self):
        """获取业主用户列表"""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            query_sql = """
                SELECT username, full_name, email, owner_id
                FROM users
                WHERE user_type = 'owner' AND is_active = TRUE
                ORDER BY full_name
            """
            cursor.execute(query_sql)
            owners = cursor.fetchall()
            return owners
            
        except Exception as e:
            print(f"❌ 获取业主列表失败: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def get_report_stats(self):
        """获取报表统计信息"""
        conn = self.get_db_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            stats = {}
            
            # 总报表数
            cursor.execute("SELECT COUNT(*) as total FROM financial_reports WHERE is_active = TRUE")
            stats['total_reports'] = cursor.fetchone()['total']
            
            # 本月报表数
            current_year = datetime.now().year
            current_month = datetime.now().month
            cursor.execute("""
                SELECT COUNT(*) as current_month 
                FROM financial_reports 
                WHERE is_active = TRUE AND report_year = %s AND report_month = %s
            """, (current_year, current_month))
            stats['current_month_reports'] = cursor.fetchone()['current_month']
            
            # 涉及业主数
            cursor.execute("""
                SELECT COUNT(DISTINCT username) as owners_count 
                FROM financial_reports 
                WHERE is_active = TRUE
            """)
            stats['owners_with_reports'] = cursor.fetchone()['owners_count']
            
            # 最近上传时间
            cursor.execute("""
                SELECT MAX(upload_date) as latest_upload 
                FROM financial_reports 
                WHERE is_active = TRUE
            """)
            latest = cursor.fetchone()['latest_upload']
            stats['latest_upload'] = latest.strftime('%Y-%m-%d %H:%M') if latest else '无'
            
            return stats
            
        except Exception as e:
            print(f"❌ 获取报表统计失败: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()

# 全局财务报表管理器实例
financial_reports_manager = FinancialReportsManager() 