#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务报表管理系统
Financial Reports Management System
"""

import mysql.connector
from datetime import datetime, date
from config_loader import DB_CONFIG, CA_CERTIFICATE

class FinancialReportsManager:
    def __init__(self):
        pass
    
    def get_db_connection(self):
        """获取数据库连接"""
        try:
            # 设置SSL证书
            import tempfile
            ca_cert_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem')
            ca_cert_file.write(CA_CERTIFICATE)
            ca_cert_file.close()
            
            ssl_config = {
                'ssl_disabled': False,
                'ssl_verify_cert': False,
                'ssl_verify_identity': False,
                'ssl_ca': ca_cert_file.name
            }
            config = {**DB_CONFIG, **ssl_config}
            connection = mysql.connector.connect(**config)
            
            # 清理临时文件
            import os
            os.unlink(ca_cert_file.name)
            
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
            # 创建财务报表表（基于房产ID）
            reports_sql = """
            CREATE TABLE IF NOT EXISTS financial_reports (
                id INT AUTO_INCREMENT PRIMARY KEY,
                property_id VARCHAR(20) NOT NULL,
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
                
                UNIQUE KEY unique_property_month (property_id, report_year, report_month),
                INDEX idx_property_id (property_id),
                INDEX idx_report_date (report_year, report_month),
                INDEX idx_upload_date (upload_date),
                FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(reports_sql)
            
            # 创建房产分配表
            assignment_sql = """
            CREATE TABLE IF NOT EXISTS property_assignments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                property_id VARCHAR(20) NOT NULL,
                owner_id VARCHAR(20) NOT NULL,
                assigned_by INT NOT NULL,
                assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                UNIQUE KEY unique_property_owner (property_id, owner_id),
                INDEX idx_property_id (property_id),
                INDEX idx_owner_id (owner_id),
                INDEX idx_assigned_date (assigned_date),
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
                FOREIGN KEY (owner_id) REFERENCES owners_master(owner_id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(assignment_sql)
            conn.commit()
            print("✅ 财务报表表和房产分配表创建成功")
            return True
            
        except Exception as e:
            print(f"❌ 创建财务报表表失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def add_financial_report(self, property_id, report_year, report_month, report_title, onedrive_link, uploaded_by, notes=None):
        """添加财务报表（基于房产ID）"""
        conn = self.get_db_connection()
        if not conn:
            return False, "数据库连接失败"
        
        cursor = conn.cursor()
        
        try:
            # 检查是否已存在该月份的报表
            check_sql = """
                SELECT id FROM financial_reports 
                WHERE property_id = %s AND report_year = %s AND report_month = %s AND is_active = TRUE
            """
            cursor.execute(check_sql, (property_id, report_year, report_month))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有报表
                update_sql = """
                    UPDATE financial_reports 
                    SET report_title = %s, onedrive_link = %s, uploaded_by = %s, notes = %s, 
                        upload_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE property_id = %s AND report_year = %s AND report_month = %s AND is_active = TRUE
                """
                cursor.execute(update_sql, (report_title, onedrive_link, uploaded_by, notes, property_id, report_year, report_month))
                message = f"房产 {property_id} 的 {report_year}年{report_month}月财务报表已更新"
            else:
                # 插入新报表
                insert_sql = """
                    INSERT INTO financial_reports (property_id, report_year, report_month, report_title, onedrive_link, uploaded_by, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_sql, (property_id, report_year, report_month, report_title, onedrive_link, uploaded_by, notes))
                message = f"房产 {property_id} 的 {report_year}年{report_month}月财务报表添加成功"
            
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
    
    def assign_property_to_owner(self, property_id, owner_id, assigned_by, notes=None):
        """分配房产给业主"""
        conn = self.get_db_connection()
        if not conn:
            return False, "数据库连接失败"
        
        cursor = conn.cursor()
        
        try:
            # 检查房产是否存在
            cursor.execute("SELECT id, name FROM properties WHERE id = %s", (property_id,))
            property_data = cursor.fetchone()
            if not property_data:
                return False, "房产不存在"
            
            # 检查业主是否存在
            cursor.execute("SELECT owner_id, name FROM owners_master WHERE owner_id = %s", (owner_id,))
            owner_data = cursor.fetchone()
            if not owner_data:
                return False, "业主不存在"
            
            # 检查是否已经分配
            check_sql = """
                SELECT id FROM property_assignments 
                WHERE property_id = %s AND owner_id = %s AND is_active = TRUE
            """
            cursor.execute(check_sql, (property_id, owner_id))
            existing = cursor.fetchone()
            
            if existing:
                return False, f"房产 {property_id} 已经分配给业主 {owner_data[1]}"
            
            # 插入分配记录
            insert_sql = """
                INSERT INTO property_assignments (property_id, owner_id, assigned_by, notes)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (property_id, owner_id, assigned_by, notes))
            conn.commit()
            
            return True, f"房产 {property_data[1] or property_id} 成功分配给业主 {owner_data[1]}"
            
        except Exception as e:
            print(f"❌ 房产分配失败: {e}")
            conn.rollback()
            return False, f"分配失败: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    
    def remove_property_assignment(self, property_id, owner_id, removed_by):
        """移除房产分配"""
        conn = self.get_db_connection()
        if not conn:
            return False, "数据库连接失败"
        
        cursor = conn.cursor()
        
        try:
            # 软删除分配记录
            update_sql = """
                UPDATE property_assignments 
                SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE property_id = %s AND owner_id = %s AND is_active = TRUE
            """
            cursor.execute(update_sql, (property_id, owner_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True, "房产分配移除成功"
            else:
                return False, "分配记录不存在或已移除"
            
        except Exception as e:
            print(f"❌ 移除房产分配失败: {e}")
            conn.rollback()
            return False, f"移除失败: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    
    def get_owner_reports(self, owner_id, year=None, limit=None):
        """获取业主的财务报表（基于分配的房产）"""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 构建查询条件
            where_conditions = ["pa.owner_id = %s", "pa.is_active = TRUE", "fr.is_active = TRUE"]
            params = [owner_id]
            
            if year:
                where_conditions.append("fr.report_year = %s")
                params.append(year)
            
            where_clause = " AND ".join(where_conditions)
            
            # 查询报表
            query_sql = f"""
                SELECT fr.*, p.name as property_name, p.address as property_address,
                       u.full_name as uploaded_by_name, pa.assigned_date
                FROM property_assignments pa
                JOIN financial_reports fr ON pa.property_id = fr.property_id
                JOIN properties p ON fr.property_id = p.id
                LEFT JOIN users u ON fr.uploaded_by = u.id
                WHERE {where_clause}
                ORDER BY fr.report_year DESC, fr.report_month DESC, p.name
            """
            
            if limit:
                query_sql += f" LIMIT {limit}"
            
            cursor.execute(query_sql, params)
            reports = cursor.fetchall()
            
            # 格式化日期显示
            for report in reports:
                report['report_date_str'] = f"{report['report_year']}年{report['report_month']}月"
                report['upload_date_str'] = report['upload_date'].strftime('%Y-%m-%d %H:%M')
                report['assigned_date_str'] = report['assigned_date'].strftime('%Y-%m-%d') if report['assigned_date'] else ''
            
            return reports
            
        except Exception as e:
            print(f"❌ 获取财务报表失败: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def get_all_reports(self, year=None, month=None, property_id=None, page=1, per_page=20):
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
            
            if property_id:
                where_conditions.append("fr.property_id = %s")
                params.append(property_id)
            
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
                       p.name as property_name, p.address as property_address,
                       GROUP_CONCAT(CONCAT(om.name, ' (', om.owner_id, ')') SEPARATOR ', ') as assigned_owners
                FROM financial_reports fr
                LEFT JOIN users u ON fr.uploaded_by = u.id
                LEFT JOIN properties p ON fr.property_id = p.id
                LEFT JOIN property_assignments pa ON fr.property_id = pa.property_id AND pa.is_active = TRUE
                LEFT JOIN owners_master om ON pa.owner_id = om.owner_id
                WHERE {where_clause}
                GROUP BY fr.id
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
    
    def get_properties_list(self):
        """获取房产列表"""
        conn = self.get_db_connection()
        if not conn:
            # 数据库连接失败时使用模拟数据
            try:
                from mock_data_manager import mock_data_manager
                return mock_data_manager.get_properties_list()
            except ImportError:
                print("❌ 模拟数据管理器未找到")
                return []

        cursor = conn.cursor(dictionary=True)

        try:
            query_sql = """
                SELECT p.id, p.name, p.address, p.city, p.state,
                       COUNT(pa.id) as assigned_owners_count
                FROM properties p
                LEFT JOIN property_assignments pa ON p.id = pa.property_id AND pa.is_active = TRUE
                GROUP BY p.id
                ORDER BY p.name, p.address
            """
            cursor.execute(query_sql)
            properties = cursor.fetchall()
            return properties

        except Exception as e:
            print(f"❌ 获取房产列表失败: {e}")
            # 发生异常时也尝试使用模拟数据
            try:
                from mock_data_manager import mock_data_manager
                return mock_data_manager.get_properties_list()
            except ImportError:
                return []
        finally:
            cursor.close()
            conn.close()
    
    def get_owners_list(self):
        """获取业主列表"""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            query_sql = """
                SELECT om.owner_id, om.name, om.phone, om.email,
                       COUNT(pa.id) as assigned_properties_count
                FROM owners_master om
                LEFT JOIN property_assignments pa ON om.owner_id = pa.owner_id AND pa.is_active = TRUE
                GROUP BY om.owner_id
                ORDER BY om.name
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
    
    def get_property_assignments(self, property_id=None, owner_id=None):
        """获取房产分配记录"""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            where_conditions = ["pa.is_active = TRUE"]
            params = []
            
            if property_id:
                where_conditions.append("pa.property_id = %s")
                params.append(property_id)
            
            if owner_id:
                where_conditions.append("pa.owner_id = %s")
                params.append(owner_id)
            
            where_clause = " AND ".join(where_conditions)
            
            query_sql = f"""
                SELECT pa.*, p.name as property_name, p.address as property_address,
                       om.name as owner_name, om.phone as owner_phone, om.email as owner_email,
                       u.full_name as assigned_by_name
                FROM property_assignments pa
                JOIN properties p ON pa.property_id = p.id
                JOIN owners_master om ON pa.owner_id = om.owner_id
                LEFT JOIN users u ON pa.assigned_by = u.id
                WHERE {where_clause}
                ORDER BY pa.assigned_date DESC
            """
            
            cursor.execute(query_sql, params)
            assignments = cursor.fetchall()
            
            # 格式化日期显示
            for assignment in assignments:
                assignment['assigned_date_str'] = assignment['assigned_date'].strftime('%Y-%m-%d %H:%M')
            
            return assignments
            
        except Exception as e:
            print(f"❌ 获取房产分配记录失败: {e}")
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
            
            # 涉及房产数
            cursor.execute("""
                SELECT COUNT(DISTINCT property_id) as properties_count 
                FROM financial_reports 
                WHERE is_active = TRUE
            """)
            stats['properties_with_reports'] = cursor.fetchone()['properties_count']
            
            # 房产分配数
            cursor.execute("""
                SELECT COUNT(*) as assignments_count 
                FROM property_assignments 
                WHERE is_active = TRUE
            """)
            stats['total_assignments'] = cursor.fetchone()['assignments_count']
            
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