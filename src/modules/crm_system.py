#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CRM系统模块
Customer Relationship Management System
提供销售漏斗管理、活动管理、任务管理等功能
"""

import mysql.connector
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import json
from src.core.config_loader import DB_CONFIG

class CRMSystem:
    """CRM系统管理器"""
    
    def __init__(self):
        self.db_config = DB_CONFIG
        
        # 销售漏斗阶段定义
        self.sales_funnel_stages = [
            '潜在客户',      # 0 - 刚获得联系方式
            '初步接触',      # 1 - 已建立初步联系
            '需求分析',      # 2 - 了解客户需求
            '方案制定',      # 3 - 制定个性化方案
            '看房安排',      # 4 - 安排看房
            '价格谈判',      # 5 - 价格协商
            '合同准备',      # 6 - 准备合同
            '签约完成',      # 7 - 成功签约
            '跟进服务',      # 8 - 售后服务
            '流失客户'       # 9 - 客户流失
        ]
        
        # 销售活动类型
        self.activity_types = [
            '电话沟通',
            '邮件联系', 
            '面谈会议',
            '看房安排',
            '方案报价',
            '合同讨论',
            '其他活动'
        ]
        
        # 任务优先级
        self.task_priorities = [
            '低优先级',
            '中优先级', 
            '高优先级',
            '紧急'
        ]
    
    def get_db_connection(self):
        """获取数据库连接"""
        try:
            import mysql.connector
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return None
    
    def create_crm_tables(self):
        """创建CRM相关表"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            # 创建销售活动表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales_activities (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id INT NOT NULL,
                    activity_type VARCHAR(50) NOT NULL,
                    subject VARCHAR(200),
                    content TEXT,
                    scheduled_time DATETIME,
                    completed_time DATETIME,
                    result ENUM('positive', 'neutral', 'negative') DEFAULT 'neutral',
                    next_action TEXT,
                    assigned_to INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    deleted_at TIMESTAMP NULL,
                    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                    INDEX idx_customer_id (customer_id),
                    INDEX idx_activity_type (activity_type),
                    INDEX idx_scheduled_time (scheduled_time),
                    INDEX idx_assigned_to (assigned_to),
                    INDEX idx_deleted_at (deleted_at)
                )
            """)
            
            # 创建销售任务表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales_tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id INT NOT NULL,
                    task_type VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
                    due_date DATETIME,
                    assigned_to INT,
                    status ENUM('pending', 'in_progress', 'completed', 'cancelled') DEFAULT 'pending',
                    completed_at DATETIME,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    deleted_at TIMESTAMP NULL,
                    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                    INDEX idx_customer_id (customer_id),
                    INDEX idx_task_type (task_type),
                    INDEX idx_priority (priority),
                    INDEX idx_status (status),
                    INDEX idx_due_date (due_date),
                    INDEX idx_assigned_to (assigned_to),
                    INDEX idx_deleted_at (deleted_at)
                )
            """)
            
            # 创建客户评分表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customer_scores (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id INT NOT NULL,
                    score_type VARCHAR(50) NOT NULL,
                    score DECIMAL(3,1) NOT NULL,
                    factors JSON,
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                    INDEX idx_customer_id (customer_id),
                    INDEX idx_score_type (score_type),
                    INDEX idx_calculated_at (calculated_at)
                )
            """)
            
            # 创建销售漏斗统计表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales_funnel_stats (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    stage_name VARCHAR(50) NOT NULL,
                    stage_order INT NOT NULL,
                    customer_count INT DEFAULT 0,
                    conversion_rate DECIMAL(5,2) DEFAULT 0.00,
                    avg_days_in_stage DECIMAL(5,2) DEFAULT 0.00,
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_stage_order (stage_order),
                    INDEX idx_calculated_at (calculated_at)
                )
            """)
            
            conn.commit()
            print("✅ CRM表创建成功")
            return True
            
        except Exception as e:
            print(f"❌ 创建CRM表失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def add_sales_activity(self, activity_data: Dict[str, Any]) -> Optional[int]:
        """添加销售活动"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        try:
            query = """
                INSERT INTO sales_activities (
                    customer_id, activity_type, subject, content, 
                    scheduled_time, completed_time, result, next_action, assigned_to
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                activity_data['customer_id'],
                activity_data['activity_type'],
                activity_data.get('subject', ''),
                activity_data.get('content', ''),
                activity_data.get('scheduled_time'),
                activity_data.get('completed_time'),
                activity_data.get('result', 'neutral'),
                activity_data.get('next_action', ''),
                activity_data.get('assigned_to')
            )
            
            cursor.execute(query, values)
            activity_id = cursor.lastrowid
            conn.commit()
            
            print(f"✅ 销售活动添加成功，ID: {activity_id}")
            return activity_id
            
        except Exception as e:
            print(f"❌ 添加销售活动失败: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()
    
    def get_customer_activities(self, customer_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """获取客户的所有销售活动"""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            query = """
                SELECT sa.*, u.full_name as assigned_name
                FROM sales_activities sa
                LEFT JOIN users u ON sa.assigned_to = u.id
                WHERE sa.customer_id = %s AND sa.deleted_at IS NULL
                ORDER BY sa.created_at DESC
                LIMIT %s
            """
            cursor.execute(query, (customer_id, limit))
            activities = cursor.fetchall()
            
            return activities
            
        except Exception as e:
            print(f"❌ 获取客户活动失败: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def add_sales_task(self, task_data: Dict[str, Any]) -> Optional[int]:
        """添加销售任务"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        try:
            query = """
                INSERT INTO sales_tasks (
                    customer_id, task_type, title, description, 
                    priority, due_date, assigned_to, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                task_data['customer_id'],
                task_data['task_type'],
                task_data['title'],
                task_data.get('description', ''),
                task_data.get('priority', 'medium'),
                task_data.get('due_date'),
                task_data.get('assigned_to'),
                task_data.get('status', 'pending')
            )
            
            cursor.execute(query, values)
            task_id = cursor.lastrowid
            conn.commit()
            
            print(f"✅ 销售任务添加成功，ID: {task_id}")
            return task_id
            
        except Exception as e:
            print(f"❌ 添加销售任务失败: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()
    
    def get_user_tasks(self, user_id: int, status: str = 'pending', limit: int = 50) -> List[Dict[str, Any]]:
        """获取用户的任务列表"""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            query = """
                SELECT st.*, c.name as customer_name, u.full_name as assigned_name
                FROM sales_tasks st
                LEFT JOIN customers c ON st.customer_id = c.id
                LEFT JOIN users u ON st.assigned_to = u.id
                WHERE st.assigned_to = %s AND st.status = %s AND st.deleted_at IS NULL
                ORDER BY 
                    CASE st.priority 
                        WHEN 'urgent' THEN 1 
                        WHEN 'high' THEN 2 
                        WHEN 'medium' THEN 3 
                        WHEN 'low' THEN 4 
                    END,
                    st.due_date ASC
                LIMIT %s
            """
            cursor.execute(query, (user_id, status, limit))
            tasks = cursor.fetchall()
            
            return tasks
            
        except Exception as e:
            print(f"❌ 获取用户任务失败: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def update_task_status(self, task_id: int, status: str, completed_by: int = None) -> bool:
        """更新任务状态"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            if status == 'completed':
                query = """
                    UPDATE sales_tasks 
                    SET status = %s, completed_at = %s
                    WHERE id = %s AND deleted_at IS NULL
                """
                values = (status, datetime.now(), task_id)
            else:
                query = """
                    UPDATE sales_tasks 
                    SET status = %s, completed_at = NULL
                    WHERE id = %s AND deleted_at IS NULL
                """
                values = (status, task_id)
            
            cursor.execute(query, values)
            conn.commit()
            
            print(f"✅ 任务状态更新成功: {task_id} -> {status}")
            return True
            
        except Exception as e:
            print(f"❌ 更新任务状态失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def get_sales_funnel_stats(self) -> Dict[str, Any]:
        """获取销售漏斗统计"""
        conn = self.get_db_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 获取各阶段客户数量
            query = """
                SELECT tracking_status, COUNT(*) as count
                FROM customers 
                WHERE deleted_at IS NULL
                GROUP BY tracking_status
            """
            cursor.execute(query)
            stage_counts = cursor.fetchall()
            
            # 构建漏斗数据
            funnel_data = {}
            total_customers = 0
            
            for stage in self.sales_funnel_stages:
                count = 0
                for row in stage_counts:
                    if row['tracking_status'] == stage:
                        count = row['count']
                        break
                
                funnel_data[stage] = {
                    'count': count,
                    'percentage': 0
                }
                total_customers += count
            
            # 计算百分比
            if total_customers > 0:
                for stage in funnel_data:
                    funnel_data[stage]['percentage'] = round(
                        (funnel_data[stage]['count'] / total_customers) * 100, 2
                    )
            
            return {
                'funnel_data': funnel_data,
                'total_customers': total_customers,
                'stages': self.sales_funnel_stages
            }
            
        except Exception as e:
            print(f"❌ 获取销售漏斗统计失败: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()
    
    def get_user_performance_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取用户业绩统计"""
        conn = self.get_db_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # 获取用户的活动统计
            activity_query = """
                SELECT 
                    activity_type,
                    COUNT(*) as count,
                    COUNT(CASE WHEN result = 'positive' THEN 1 END) as positive_count
                FROM sales_activities 
                WHERE assigned_to = %s AND created_at >= %s AND deleted_at IS NULL
                GROUP BY activity_type
            """
            cursor.execute(activity_query, (user_id, start_date))
            activity_stats = cursor.fetchall()
            
            # 获取用户的任务统计
            task_query = """
                SELECT 
                    status,
                    COUNT(*) as count
                FROM sales_tasks 
                WHERE assigned_to = %s AND created_at >= %s AND deleted_at IS NULL
                GROUP BY status
            """
            cursor.execute(task_query, (user_id, start_date))
            task_stats = cursor.fetchall()
            
            # 获取用户负责的客户统计
            customer_query = """
                SELECT 
                    tracking_status,
                    COUNT(*) as count
                FROM customers 
                WHERE id IN (
                    SELECT DISTINCT customer_id 
                    FROM sales_activities 
                    WHERE assigned_to = %s AND deleted_at IS NULL
                ) AND deleted_at IS NULL
                GROUP BY tracking_status
            """
            cursor.execute(customer_query, (user_id,))
            customer_stats = cursor.fetchall()
            
            return {
                'activity_stats': activity_stats,
                'task_stats': task_stats,
                'customer_stats': customer_stats,
                'period_days': days
            }
            
        except Exception as e:
            print(f"❌ 获取用户业绩统计失败: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()

# 创建全局CRM系统实例
crm_system = CRMSystem() 