#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
房地产管理系统 - Aiven MySQL 数据导入脚本
Real Estate Management System - Aiven MySQL Data Import Script
"""

import pandas as pd
import mysql.connector
import tempfile
import ssl
import os
import re
from datetime import datetime
import hashlib
import logging
from config_loader import DB_CONFIG, CA_CERTIFICATE

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AivenMySQLImporter:
    def __init__(self):
        # 从配置加载器导入数据库连接配置
        self.config = DB_CONFIG.copy() if DB_CONFIG else {}
        
        # 从配置加载器获取CA证书
        self.ca_cert = CA_CERTIFICATE
        
        self.connection = None
        self.ca_cert_file = None

    def setup_ssl_cert(self):
        """设置SSL证书文件"""
        try:
            # 创建临时证书文件
            self.ca_cert_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem')
            self.ca_cert_file.write(self.ca_cert)
            self.ca_cert_file.close()
            
            # 更新配置以包含SSL证书
            self.config['ssl_ca'] = self.ca_cert_file.name
            logger.info(f"SSL证书文件创建成功: {self.ca_cert_file.name}")
            
        except Exception as e:
            logger.error(f"创建SSL证书文件失败: {str(e)}")
            raise

    def connect(self):
        """连接到Aiven MySQL数据库"""
        try:
            self.setup_ssl_cert()
            logger.info("正在连接到Aiven MySQL数据库...")
            
            self.connection = mysql.connector.connect(**self.config)
            logger.info("✅ 数据库连接成功！")
            
            # 测试连接
            cursor = self.connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            logger.info(f"MySQL版本: {version[0]}")
            cursor.close()
            
        except mysql.connector.Error as e:
            logger.error(f"❌ 数据库连接失败: {str(e)}")
            raise

    def create_tables(self):
        """创建数据库表结构"""
        logger.info("开始创建数据库表结构...")
        
        cursor = self.connection.cursor()
        
        try:
            # 删除现有表（如果存在）
            drop_tables = [
                "DROP TABLE IF EXISTS finance",
                "DROP TABLE IF EXISTS property_owners", 
                "DROP TABLE IF EXISTS owners_master",
                "DROP TABLE IF EXISTS properties"
            ]
            
            for drop_sql in drop_tables:
                cursor.execute(drop_sql)
            logger.info("清理现有表结构")

            # 1. 创建Properties表
            properties_sql = """
            CREATE TABLE properties (
                id VARCHAR(20) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                street_address TEXT,
                city VARCHAR(50),
                state VARCHAR(30),
                layout VARCHAR(20),
                property_size INT,
                land_size INT,
                occupancy INT,
                beds VARCHAR(50),
                front_door_code TEXT,
                storage_code TEXT,
                wifi_name VARCHAR(100),
                wifi_password VARCHAR(100),
                trash_day VARCHAR(20),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_location (state, city),
                INDEX idx_occupancy (occupancy),
                INDEX idx_size (property_size),
                INDEX idx_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(properties_sql)
            logger.info("✅ Properties表创建成功")

            # 2. 创建Owners_Master表
            owners_master_sql = """
            CREATE TABLE owners_master (
                owner_id VARCHAR(20) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                phone VARCHAR(50),
                email VARCHAR(500),
                preferences_strategy TEXT,
                hobbies TEXT,
                residence VARCHAR(100),
                language VARCHAR(50),
                total_properties INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_name (name(50)),
                INDEX idx_email (email(100))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(owners_master_sql)
            logger.info("✅ Owners_Master表创建成功")

            # 3. 创建Property_Owners关系表
            property_owners_sql = """
            CREATE TABLE property_owners (
                property_id VARCHAR(20),
                owner_id VARCHAR(20),
                is_primary BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                PRIMARY KEY (property_id, owner_id),
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
                FOREIGN KEY (owner_id) REFERENCES owners_master(owner_id) ON DELETE CASCADE,
                
                INDEX idx_owner_properties (owner_id, is_primary)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(property_owners_sql)
            logger.info("✅ Property_Owners表创建成功")

            # 4. 创建Finance表
            finance_sql = """
            CREATE TABLE finance (
                property_id VARCHAR(20) PRIMARY KEY,
                owner_clean TEXT,
                cleaning_fee DECIMAL(10,2),
                management_fee_rate DECIMAL(5,2),
                management_fee_type ENUM('Net','Gross') DEFAULT 'Net',
                contract_signed_date DATE,
                listing_date DATE,
                first_booking_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
                
                INDEX idx_contract_date (contract_signed_date),
                INDEX idx_listing_date (listing_date),
                INDEX idx_management_fee (management_fee_rate, management_fee_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(finance_sql)
            logger.info("✅ Finance表创建成功")

            self.connection.commit()
            logger.info("🎉 所有表结构创建完成！")

        except mysql.connector.Error as e:
            logger.error(f"❌ 创建表失败: {str(e)}")
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def clean_management_fee(self, fee_str):
        """清理管理费百分比字符串"""
        if pd.isna(fee_str) or fee_str == '':
            return None, 'Net'
        
        # 提取数字和类型
        match = re.search(r'(\d+(?:\.\d+)?)%(Net|Gross)', str(fee_str))
        if match:
            rate = float(match.group(1))
            fee_type = match.group(2)
            return rate, fee_type
        return None, 'Net'

    def clean_date(self, date_str):
        """清理日期字符串"""
        if pd.isna(date_str) or date_str == '':
            return None
        try:
            # 尝试多种日期格式
            formats = ['%Y/%m/%d', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']
            for fmt in formats:
                try:
                    return datetime.strptime(str(date_str), fmt).date()
                except ValueError:
                    continue
            return None
        except:
            return None

    def generate_owner_id(self, name, email="", phone=""):
        """生成唯一的业主ID"""
        # 使用姓名、邮箱、电话的组合生成MD5哈希
        unique_string = f"{str(name).strip()}{str(email).strip()}{str(phone).strip()}"
        return hashlib.md5(unique_string.encode('utf-8')).hexdigest()[:10]

    def import_properties(self):
        """导入房产数据"""
        logger.info("开始导入房产数据...")
        
        try:
            df = pd.read_csv('Database - Properties.csv')
            logger.info(f"读取到 {len(df)} 条房产记录")
            
            # 准备插入数据
            insert_sql = """
            INSERT INTO properties (
                id, name, street_address, city, state, layout, 
                property_size, land_size, occupancy, beds,
                front_door_code, storage_code, wifi_name, wifi_password, trash_day
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor = self.connection.cursor()
            
            for idx, row in df.iterrows():
                try:
                    # 清理所有字段，处理NaN值
                    def clean_field(field_value):
                        if pd.isna(field_value):
                            return ''
                        return str(field_value).strip()
                    
                    def clean_numeric(field_value):
                        if pd.isna(field_value) or field_value == '' or str(field_value).lower() == 'nan':
                            return None
                        try:
                            return int(float(field_value))
                        except:
                            return None
                    
                    values = (
                        clean_field(row.get('id', '')),
                        clean_field(row.get('name', '')),
                        clean_field(row.get('street_address', '')),
                        clean_field(row.get('city', '')),
                        clean_field(row.get('state', '')),
                        clean_field(row.get('layout', '')),
                        clean_numeric(row.get('property size')),
                        clean_numeric(row.get('land size')),
                        clean_numeric(row.get('occupancy')),
                        clean_field(row.get('beds', '')),
                        clean_field(row.get('front_door_code', '')),
                        clean_field(row.get('storage_code', '')),
                        clean_field(row.get('wifi_name', '')),
                        clean_field(row.get('wifi_password', '')),
                        clean_field(row.get('trash_day', ''))
                    )
                    cursor.execute(insert_sql, values)
                except Exception as e:
                    logger.error(f"处理第{idx}行数据时出错: {str(e)}")
                    logger.error(f"问题数据: {dict(row)}")
                    continue
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ 成功导入 {len(df)} 条房产记录")
            
        except Exception as e:
            logger.error(f"❌ 导入房产数据失败: {str(e)}")
            raise

    def import_owners(self):
        """导入业主数据"""
        logger.info("开始导入业主数据...")
        
        try:
            df = pd.read_csv('Database - Owners.csv')
            logger.info(f"读取到 {len(df)} 条业主记录")
            
            # 去重处理，生成唯一的业主记录
            owners_dict = {}
            property_owner_relations = []
            
            for _, row in df.iterrows():
                # 清理字段
                def clean_field(field_value):
                    if pd.isna(field_value):
                        return ''
                    return str(field_value).strip()
                
                property_id = clean_field(row.get('id', ''))
                name = clean_field(row.get('name', ''))
                phone = clean_field(row.get('phone', ''))
                email = clean_field(row.get('email', ''))
                
                if not name:
                    continue
                
                # 生成业主ID
                owner_id = self.generate_owner_id(name, email, phone)
                
                # 收集业主信息（去重）
                if owner_id not in owners_dict:
                    owners_dict[owner_id] = {
                        'owner_id': owner_id,
                        'name': name,
                        'phone': phone,
                        'email': email,
                        'preferences_strategy': clean_field(row.get('preferences staragy', '')),
                        'hobbies': clean_field(row.get('hobbies', '')),
                        'residence': clean_field(row.get('residence', '')),
                        'language': clean_field(row.get('lanaguage', ''))
                    }
                
                # 收集房产-业主关系
                if property_id:
                    property_owner_relations.append({
                        'property_id': property_id,
                        'owner_id': owner_id,
                        'is_primary': True  # 默认为主要业主
                    })
            
            # 插入业主数据
            owners_insert_sql = """
            INSERT INTO owners_master (
                owner_id, name, phone, email, preferences_strategy,
                hobbies, residence, language
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor = self.connection.cursor()
            
            for owner in owners_dict.values():
                values = (
                    owner['owner_id'],
                    owner['name'],
                    owner['phone'],
                    owner['email'],
                    owner['preferences_strategy'],
                    owner['hobbies'],
                    owner['residence'],
                    owner['language']
                )
                cursor.execute(owners_insert_sql, values)
            
            logger.info(f"✅ 成功导入 {len(owners_dict)} 条业主记录")
            
            # 插入房产-业主关系（先检查房产ID是否存在）
            relation_insert_sql = """
            INSERT INTO property_owners (property_id, owner_id, is_primary)
            VALUES (%s, %s, %s)
            """
            
            # 先查询现有的房产ID
            cursor.execute("SELECT id FROM properties")
            existing_property_ids = {row[0] for row in cursor.fetchall()}
            
            valid_relations = []
            for relation in property_owner_relations:
                if relation['property_id'] in existing_property_ids:
                    valid_relations.append(relation)
                else:
                    logger.warning(f"跳过不存在的房产ID: {relation['property_id']}")
            
            for relation in valid_relations:
                values = (
                    relation['property_id'],
                    relation['owner_id'],
                    relation['is_primary']
                )
                cursor.execute(relation_insert_sql, values)
            
            logger.info(f"✅ 成功导入 {len(valid_relations)} 条房产-业主关系")
            
            self.connection.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"❌ 导入业主数据失败: {str(e)}")
            raise

    def import_finance(self):
        """导入财务数据"""
        logger.info("开始导入财务数据...")
        
        try:
            df = pd.read_csv('Database - Finance.csv')
            logger.info(f"读取到 {len(df)} 条财务记录")
            
            insert_sql = """
            INSERT INTO finance (
                property_id, owner_clean, cleaning_fee, management_fee_rate,
                management_fee_type, contract_signed_date, listing_date, first_booking_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor = self.connection.cursor()
            
            # 先查询现有的房产ID
            cursor.execute("SELECT id FROM properties")
            existing_property_ids = {row[0] for row in cursor.fetchall()}
            
            successful_inserts = 0
            
            for _, row in df.iterrows():
                # 清理字段
                def clean_field(field_value):
                    if pd.isna(field_value):
                        return ''
                    return str(field_value).strip()
                
                property_id = clean_field(row.get('id', ''))
                if not property_id or property_id not in existing_property_ids:
                    if property_id:
                        logger.warning(f"跳过不存在的房产ID: {property_id}")
                    continue
                
                # 处理管理费
                fee_rate, fee_type = self.clean_management_fee(row.get('manegement_fee_pct', ''))
                
                # 处理清洁费
                cleaning_fee = row.get('cleaning_fee', 0)
                if pd.isna(cleaning_fee) or cleaning_fee == '' or str(cleaning_fee).lower() == 'nan':
                    cleaning_fee = None
                else:
                    try:
                        cleaning_fee = float(cleaning_fee)
                    except:
                        cleaning_fee = None
                
                values = (
                    property_id,
                    clean_field(row.get('owner_clean', '')),
                    cleaning_fee,
                    fee_rate,
                    fee_type,
                    self.clean_date(row.get('contract_signed_date', '')),
                    self.clean_date(row.get('listing_date', '')),
                    self.clean_date(row.get('first_booking_date', ''))
                )
                cursor.execute(insert_sql, values)
                successful_inserts += 1
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ 成功导入 {successful_inserts} 条财务记录")
            
        except Exception as e:
            logger.error(f"❌ 导入财务数据失败: {str(e)}")
            raise

    def update_statistics(self):
        """更新统计信息"""
        logger.info("更新业主统计信息...")
        
        cursor = self.connection.cursor()
        
        try:
            # 更新业主的房产统计
            update_sql = """
            UPDATE owners_master om
            SET total_properties = (
                SELECT COUNT(*) FROM property_owners po WHERE po.owner_id = om.owner_id
            )
            """
            
            cursor.execute(update_sql)
            self.connection.commit()
            
            logger.info("✅ 统计信息更新完成")
            
        except Exception as e:
            logger.error(f"❌ 更新统计信息失败: {str(e)}")
        finally:
            cursor.close()

    def verify_data(self):
        """验证导入的数据"""
        logger.info("验证导入的数据...")
        
        cursor = self.connection.cursor()
        
        try:
            # 检查各表的记录数
            tables = ['properties', 'owners_master', 'property_owners', 'finance']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"📊 {table}: {count} 条记录")
            
            # 检查数据完整性 - 前5条记录
            cursor.execute("""
                SELECT p.id, p.name, om.name as owner_name, f.management_fee_rate
                FROM properties p
                LEFT JOIN property_owners po ON p.id = po.property_id
                LEFT JOIN owners_master om ON po.owner_id = om.owner_id
                LEFT JOIN finance f ON p.id = f.property_id
                LIMIT 5
            """)
            
            results = cursor.fetchall()
            logger.info("📋 数据样例:")
            for row in results:
                rate_str = f"{row[3]}%" if row[3] else "无"
                logger.info(f"  房产: {row[1]}, 业主: {row[2]}, 管理费率: {rate_str}")
                
        except Exception as e:
            logger.error(f"❌ 数据验证失败: {str(e)}")
        finally:
            cursor.close()

    def run_import(self):
        """执行完整的导入流程"""
        try:
            logger.info("🚀 开始房地产数据库导入流程...")
            
            # 1. 连接数据库
            self.connect()
            
            # 2. 创建表结构
            self.create_tables()
            
            # 3. 导入数据
            self.import_properties()
            self.import_owners()
            self.import_finance()
            
            # 4. 更新统计信息
            self.update_statistics()
            
            # 5. 验证数据
            self.verify_data()
            
            logger.info("🎉 数据导入完成！数据库已准备就绪。")
            
        except Exception as e:
            logger.error(f"💥 导入过程中出现错误: {str(e)}")
            raise
        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")
        
        if self.ca_cert_file and os.path.exists(self.ca_cert_file.name):
            os.unlink(self.ca_cert_file.name)
            logger.info("SSL证书临时文件已删除")

if __name__ == "__main__":
    importer = AivenMySQLImporter()
    importer.run_import() 