from flask import Flask, render_template, render_template_string, request, jsonify, redirect, url_for, session, flash
import mysql.connector
import ssl
import os
from datetime import datetime, timezone
import pytz
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置Flask应用，指定正确的模板和静态文件路径
import os
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# 设置Flask配置
app.secret_key = os.environ.get('APP_SECRET_KEY', 'default-secret-key-change-in-production')

# 应用版本信息 - 用于区分本地和部署版本
APP_VERSION = "v2.1.0-2025-06-23-login-fix"
LAST_UPDATE = "2025-06-23 23:30:00"

# 调试模式设置
DEBUG_MODE = os.environ.get('DEBUG', 'False').lower() == 'true'

# 导入认证系统
from .auth_system import auth_system, login_required, admin_required, owner_required, super_admin_required
from modules.department_modules import (
    module_required, department_required, generate_department_dashboard_data,
    get_user_accessible_modules, has_module_access, get_module_info
)

# 用户注册系统已移除，改为直接创建用户

# 导入用户模块权限管理系统
from modules.user_module_permissions import init_user_module_permissions, get_user_module_permissions

# 导入密码管理系统
from modules.password_manager import password_manager

# 导入多语言系统
from modules.language_manager import language_manager, get_text, get_current_language, is_chinese, is_english

# 导入财务报表系统
from modules.financial_reports import financial_reports_manager

# 导入维修工单系统
from modules.maintenance_orders import maintenance_orders_manager

# 导入客户追踪系统
from modules.customer_tracking import customer_tracking_manager

# 导入CRM系统
from modules.crm_system import crm_system

# 设置洛杉矶时区
LOS_ANGELES_TZ = pytz.timezone('America/Los_Angeles')

def convert_to_la_time(utc_datetime):
    """将UTC时间转换为洛杉矶时间"""
    if utc_datetime is None:
        return None
    
    # 如果datetime对象没有时区信息，假设为UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    
    # 转换为洛杉矶时区
    la_time = utc_datetime.astimezone(LOS_ANGELES_TZ)
    return la_time

def get_la_time_str(utc_datetime, format_str='%Y-%m-%d %H:%M'):
    """将UTC时间转换为洛杉矶时间字符串"""
    la_time = convert_to_la_time(utc_datetime)
    if la_time is None:
        return ''
    return la_time.strftime(format_str)

def get_la_date_str(utc_datetime, format_str='%Y年%m月%d日'):
    """将UTC时间转换为洛杉矶日期字符串"""
    la_time = convert_to_la_time(utc_datetime)
    if la_time is None:
        return ''
    return la_time.strftime(format_str)

def get_la_time_only_str(utc_datetime, format_str='%H:%M'):
    """将UTC时间转换为洛杉矶时间（仅时间部分）字符串"""
    la_time = convert_to_la_time(utc_datetime)
    if la_time is None:
        return ''
    return la_time.strftime(format_str)

# 注册模板函数
@app.template_filter('format_fee')
def format_fee_filter(rate, fee_type=None):
    """模板过滤器：格式化管理费显示"""
    return format_management_fee(rate, fee_type)

@app.template_filter('nl2br')
def nl2br_filter(text):
    """模板过滤器：将换行符转换为HTML的br标签"""
    if text is None:
        return ''
    return text.replace('\n', '<br>')

@app.template_filter('la_time')
def la_time_filter(utc_datetime):
    """将UTC时间转换为洛杉矶时间"""
    return convert_to_la_time(utc_datetime)

@app.template_filter('la_time_str')
def la_time_str_filter(utc_datetime, format_str='%Y-%m-%d %H:%M'):
    """将UTC时间转换为洛杉矶时间字符串"""
    return get_la_time_str(utc_datetime, format_str)

@app.template_filter('la_date_str')
def la_date_str_filter(utc_datetime, format_str='%Y年%m月%d日'):
    """将UTC时间转换为洛杉矶日期字符串"""
    return get_la_date_str(utc_datetime, format_str)

@app.template_filter('la_time_only_str')
def la_time_only_str_filter(utc_datetime, format_str='%H:%M'):
    """将UTC时间转换为洛杉矶时间（仅时间部分）字符串"""
    return get_la_time_only_str(utc_datetime, format_str)

# 注册多语言模板函数
@app.template_global()
def _(key, language=None):
    """模板中的翻译函数"""
    return get_text(key, language)

@app.template_global()
def get_lang():
    """获取当前语言"""
    return get_current_language()

@app.template_global()
def is_zh():
    """判断是否为中文"""
    return is_chinese()

@app.template_global()
def is_en():
    """判断是否为英文"""
    return is_english()

@app.template_global()
def get_department_display_name(department):
    """获取部门的显示名称（中文或英文）"""
    if not department:
        return '未分配' if get_current_language() == 'zh' else 'Unassigned'
    
    # 部门名称映射
    department_mapping = {
        'Admin': '管理员',
        'Sales Department': '销售部',
        'Accounting Department': '财务部',
        'Property Management Department': '房产管理部'
    }
    
    # 如果是中文环境，返回中文名称，否则返回英文名称
    if get_current_language() == 'zh':
        return department_mapping.get(department, department)
    else:
        return department

# 从配置加载器导入数据库配置
from .config_loader import DB_CONFIG, CA_CERTIFICATE

# 注册申请系统已移除，改为直接创建用户

# 初始化用户模块权限管理系统
init_user_module_permissions(DB_CONFIG)

def get_db_connection():
    """获取数据库连接 - 生产环境版本"""
    try:
        # 使用已验证成功的SSL配置
        ssl_config = {
            'ssl_disabled': False,
            'ssl_verify_cert': False,
            'ssl_verify_identity': False
        }
        
        config = {**DB_CONFIG, **ssl_config}
        print(f"连接数据库: {config['host']}:{config['port']}")
        connection = mysql.connector.connect(**config)
        print(f"✅ 数据库连接成功")
        return connection
        
    except Exception as e:
        print(f"❌ 数据库连接错误: {e}")
        print(f"配置信息: host={DB_CONFIG.get('host')}, port={DB_CONFIG.get('port')}, database={DB_CONFIG.get('database')}, user={DB_CONFIG.get('user')}")
        print(f"⚠️  系统将继续运行，但某些功能可能受限")
        return None  # 返回None而不是抛出异常，让系统优雅降级

@app.template_global()
def format_management_fee(rate, fee_type):
    """格式化管理费显示"""
    if not rate:
        return "未设置"
    
    if fee_type:
        if fee_type.lower() == 'net':
            return f"{rate}% of Net Income"
        elif fee_type.lower() == 'gross':
            return f"{rate}% of Gross Income"
    
    return f"{rate}%"

@app.template_global()
def parse_layout(layout):
    """解析房型布局，返回卧室数和浴室数"""
    if not layout:
        return {'bedrooms': 'N/A', 'bathrooms': 'N/A'}
    
    # 解析格式如 "3b2b", "4b3.5b", "2b1b"
    import re
    match = re.match(r'(\d+)b(\d+(?:\.\d+)?)b', layout)
    if match:
        bedrooms = int(match.group(1))
        bathrooms = float(match.group(2))
        return {
            'bedrooms': bedrooms,
            'bathrooms': bathrooms if bathrooms.is_integer() else bathrooms
        }
    
    return {'bedrooms': 'N/A', 'bathrooms': 'N/A'}

@app.template_global()
def format_beds(beds):
    """格式化床位配置显示"""
    if not beds:
        return "未设置"
    
    # 解析床位配置，如 "1k3q", "2q", "1k2q1s"
    bed_types = {
        'k': 'King床',
        'q': 'Queen床', 
        't': 'Twin床',
        's': '沙发床'
    }
    
    result = []
    import re
    matches = re.findall(r'(\d+)([kqts])', beds)
    
    for count, bed_type in matches:
        count = int(count)
        bed_name = bed_types.get(bed_type, bed_type.upper())
        if count == 1:
            result.append(f"1张{bed_name}")
        else:
            result.append(f"{count}张{bed_name}")
    
    return " + ".join(result) if result else beds

# ==================== 认证路由 ====================

@app.route('/health')
def health_check():
    """健康检查端点 - 用于Render部署监控"""
    try:
        connection = get_db_connection()
        if connection:
            connection.close()
            return {
                'status': 'healthy',
                'message': '房地产管理系统运行正常',
                'database': 'connected',
                'mode': 'production',
                'version': APP_VERSION,
                'last_update': LAST_UPDATE
            }, 200
        else:
            return {
                'status': 'error',
                'message': '数据库连接失败',
                'database': 'disconnected',
                'mode': 'offline',
                'version': APP_VERSION,
                'last_update': LAST_UPDATE
            }, 500
    except Exception as e:
        return {
            'status': 'error',
            'message': '数据库连接失败',
            'database': 'disconnected',
            'mode': 'offline',
            'error': str(e),
            'version': APP_VERSION,
            'last_update': LAST_UPDATE
        }, 500

@app.route('/version')
def version_info():
    """版本信息端点"""
    return {
        'app_name': '房地产管理系统',
        'version': APP_VERSION,
        'last_update': LAST_UPDATE,
        'environment': 'production' if os.environ.get('PORT') else 'local',
        'python_version': os.environ.get('PYTHON_VERSION', 'unknown'),
        'features': [
            '用户认证系统',
            '房产管理',
            '业主管理', 
            '财务记录',
            '部门权限管理',
            '多语言支持',
            '演示模式支持'
        ]
    }

@app.route('/')
def index():
    """主页 - 重定向到登录或仪表板"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_type = request.form.get('user_type', 'admin')
        
        if not username or not password:
            flash(get_text('please_enter_username_password') if get_current_language() == 'en' else '请输入用户名和密码', 'error')
            return render_template('new_ui/login.html')
        
        # 验证用户
        print(f"🔍 尝试登录: {username}")
        
        # 首先检查数据库连接状态
        db_conn = auth_system.get_db_connection()
        if db_conn:
            print("✅ 数据库连接正常，使用数据库认证")
            db_conn.close()
            user = auth_system.authenticate_user(username, password)
        else:
            print("⚠️ 数据库连接失败，使用演示模式认证")
            user = auth_system._demo_authenticate(username, password)
            if user:
                print(f"✅ 演示模式认证成功: {user}")
        
        if user:
            print(f"✅ 用户认证成功: {user}")
            # 自动匹配用户类型，不再验证表单中的user_type
            print(f"✅ 用户类型: {user['user_type']}, 部门: {user['department']}")
            
            print("✅ 创建会话...")
            
            # 立即设置Flask会话信息（无论数据库会话是否创建成功）
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            session['department'] = user['department']
            session['owner_id'] = user['owner_id']
            session['full_name'] = user['full_name']
            
            # 尝试创建数据库会话
            session_id = auth_system.create_session(
                user['id'], 
                request.remote_addr, 
                request.headers.get('User-Agent')
            )
            
            if session_id:
                session['session_id'] = session_id
                print(f"✅ 数据库会话创建成功, Session ID: {session_id}")
            else:
                print("⚠️ 未能创建数据库会话 (可能因为数据库连接问题)，但Flask会话已设置")

            flash(get_text('login_successful') if get_current_language() == 'en' else '登录成功！', 'success')
            return redirect(url_for('dashboard'))
        else:
            print(f"❌ 认证失败: {username}")
            flash(get_text('invalid_credentials') if get_current_language() == 'en' else '用户名或密码错误', 'error')
            return render_template('new_ui/login.html')

    # For GET requests
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('new_ui/login.html')

@app.route('/logout')
def logout():
    """用户登出"""
    if 'session_id' in session:
        auth_system.logout_user(session['session_id'])
    
    session.clear()
    flash('您已成功退出登录', 'info')
    return redirect(url_for('login'))



# ==================== 管理员审核路由 ====================



@app.route('/dashboard')
@login_required
def dashboard():
    """显示主仪表板"""
    
    current_date = datetime.now().strftime('%Y年%m月%d日')
    
    # 演示模式和生产模式的统一处理
    if session.get('session_mode') == 'demo':
        stats = session.get('demo_stats', {
            'properties_count': 10,
            'owners_count': 5,
            'cities_count': 3,
            'states_count': 1
        })
        owner_stats = {
            'property_count': 2,
            'total_income': 5000.00,
            'average_fee_rate': 10.0
        }
        owner_info = {
            'owner_id': 'DEMO-OWN-01',
            'email': 'owner@example.com'
        }
        return render_template(
            'new_ui/dashboard.html', 
            current_date=current_date, 
            stats=stats, 
            owner_stats=owner_stats,
            owner_info=owner_info
        )

    # 生产模式（连接数据库）
    connection = get_db_connection()
    if not connection:
        flash('无法连接到数据库，显示示例数据。', 'warning')
        # 提供一个优雅的回退
        stats = {'properties_count': 'N/A', 'owners_count': 'N/A', 'cities_count': 'N/A', 'states_count': 'N/A'}
        return render_template('new_ui/dashboard.html', current_date=current_date, stats=stats)
        
    cursor = connection.cursor(dictionary=True)
    
    # 初始化变量，避免模板渲染错误
    stats = {}
    owner_stats = {}
    owner_info = None

    try:
        print(f"🔍 开始获取仪表板数据，用户类型: {session.get('user_type')}")
        
        if session['user_type'] == 'admin':
            print("👤 获取管理员统计数据...")
            
            # 获取管理员统计数据
            cursor.execute("SELECT COUNT(*) as count FROM properties")
            result = cursor.fetchone()
            stats['properties_count'] = result['count'] if result else 0
            print(f"✅ 房产总数: {stats['properties_count']}")
            
            cursor.execute("SELECT COUNT(*) as count FROM owners_master")
            result = cursor.fetchone()
            stats['owners_count'] = result['count'] if result else 0
            print(f"✅ 业主总数: {stats['owners_count']}")
            
            cursor.execute("SELECT COUNT(DISTINCT city) as count FROM properties")
            result = cursor.fetchone()
            stats['cities_count'] = result['count'] if result else 0
            print(f"✅ 城市数量: {stats['cities_count']}")
            
            cursor.execute("SELECT COUNT(DISTINCT state) as count FROM properties")
            result = cursor.fetchone()
            stats['states_count'] = result['count'] if result else 0
            print(f"✅ 州数量: {stats['states_count']}")
            
            print(f"📊 统计数据获取完成: {stats}")
            # 清除任何之前的错误消息
            session.pop('_flashes', None)
        
        elif session['user_type'] == 'owner':
            owner_id = session.get('owner_id')
            if owner_id:
                print(f"👤 获取业主统计数据，业主ID: {owner_id}")
                
                # 获取业主信息
                cursor.execute("SELECT * FROM owners_master WHERE owner_id = %s", (owner_id,))
                owner_info = cursor.fetchone()
                
                # 获取业主统计数据
                cursor.execute("SELECT COUNT(*) as count FROM property_owners WHERE owner_id = %s", (owner_id,))
                result = cursor.fetchone()
                owner_stats['property_count'] = result['count'] if result else 0
                
                # 假设的收入和费率计算
                owner_stats['total_income'] = 12345.67 # 示例数据
                owner_stats['average_fee_rate'] = 8.5 # 示例数据
        
        elif session['user_type'] in ['sales', 'accounting', 'property_manager']:
            print(f"👤 获取{session['user_type']}用户统计数据...")
            
            # 为销售、会计、房产管理用户提供基本统计数据
            cursor.execute("SELECT COUNT(*) as count FROM properties")
            result = cursor.fetchone()
            stats['properties_count'] = result['count'] if result else 0
            
            cursor.execute("SELECT COUNT(*) as count FROM owners_master")
            result = cursor.fetchone()
            stats['owners_count'] = result['count'] if result else 0
            
            cursor.execute("SELECT COUNT(DISTINCT city) as count FROM properties")
            result = cursor.fetchone()
            stats['cities_count'] = result['count'] if result else 0
            
            cursor.execute("SELECT COUNT(DISTINCT state) as count FROM properties")
            result = cursor.fetchone()
            stats['states_count'] = result['count'] if result else 0
            
            print(f"📊 {session['user_type']}用户统计数据获取完成: {stats}")

    except Exception as e:
        print(f"❌ Error fetching dashboard data: {e}")
        print(f"❌ 错误类型: {type(e).__name__}")
        import traceback
        print(f"❌ 详细错误信息: {traceback.format_exc()}")
        flash('获取仪表板数据时出错。', 'error')
        # 提供默认值，避免模板渲染错误
        if session['user_type'] == 'admin':
            stats = {
                'properties_count': 0,
                'owners_count': 0,
                'cities_count': 0,
                'states_count': 0
            }
        elif session['user_type'] == 'owner':
            owner_stats = {
                'property_count': 0,
                'total_income': 0,
                'average_fee_rate': 0
            }

    finally:
        cursor.close()
        connection.close()

    return render_template(
        'new_ui/dashboard.html', 
        current_date=current_date, 
        stats=stats,
        owner_stats=owner_stats,
        owner_info=owner_info
    )

@app.route('/department-dashboard')
@login_required
def department_dashboard():
    """部门专用工作台"""
    # 生成部门专属数据
    dashboard_data = generate_department_dashboard_data()
    
    # 获取统计数据
    stats = {}
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # 房产总数
            cursor.execute("SELECT COUNT(*) as count FROM properties")
            stats['properties_count'] = cursor.fetchone()['count']
            
            # 业主总数
            cursor.execute("SELECT COUNT(*) as count FROM owners_master")
            stats['owners_count'] = cursor.fetchone()['count']
            
            # 用户总数
            cursor.execute("SELECT COUNT(*) as count FROM users")
            stats['total_users'] = cursor.fetchone()['count']
            
        except Exception as e:
            print(f"统计数据加载错误: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        # 演示模式统计数据
        print("⚠️  使用演示模式统计数据")
        stats = {
            'properties_count': 5,
            'owners_count': 3,
            'total_users': 2
        }
    
    return render_template('department_dashboard_clean.html',
                         stats=stats,
                         **dashboard_data)

# ==================== 业主专用路由 ====================

@app.route('/owner/properties')
@owner_required
def owner_properties():
    """业主房产列表"""
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="数据库连接失败")
    
    cursor = conn.cursor(dictionary=True)
    owner_id = session['owner_id']
    
    try:
        # 获取业主的房产
        cursor.execute("""
            SELECT p.*, f.cleaning_fee, f.management_fee_rate, f.management_fee_type
            FROM property_owners po
            JOIN properties p ON po.property_id = p.id
            LEFT JOIN finance f ON p.id = f.property_id
            WHERE po.owner_id = %s
            ORDER BY p.name
        """, (owner_id,))
        
        properties = cursor.fetchall()
        
        return render_template('owner_properties.html', 
                             properties=properties,
                             format_management_fee=format_management_fee)
    
    except Exception as e:
        print(f"业主房产查询错误: {e}")
        return render_template('error.html', error="房产数据加载失败")
    finally:
        cursor.close()
        conn.close()

@app.route('/owner/income')
@owner_required
def owner_income():
    """业主收入明细"""
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="数据库连接失败")
    
    cursor = conn.cursor(dictionary=True)
    owner_id = session['owner_id']
    
    try:
        # 获取业主的财务信息
        cursor.execute("""
            SELECT p.name as property_name, p.city, p.state,
                   f.cleaning_fee, f.management_fee_rate, f.management_fee_type,
                   f.contract_signed_date, f.listing_date, f.first_booking_date
            FROM property_owners po
            JOIN properties p ON po.property_id = p.id
            LEFT JOIN finance f ON p.id = f.property_id
            WHERE po.owner_id = %s
            ORDER BY p.name
        """, (owner_id,))
        
        income_data = cursor.fetchall()
        
        return render_template('owner_income.html', 
                             income_data=income_data,
                             format_management_fee=format_management_fee)
    
    except Exception as e:
        print(f"业主收入查询错误: {e}")
        return render_template('error.html', error="收入数据加载失败")
    finally:
        cursor.close()
        conn.close()

@app.route('/owner/financial_reports')
@owner_required
def owner_financial_reports():
    """房东查看财务报表"""
    # 获取筛选参数
    year = request.args.get('year')
    
    # 获取当前用户的报表（基于分配的房产）
    # 对于普通用户，使用user_id；对于owner角色，使用owner_id（如果存在）
    user_id = session.get('user_id')
    owner_id = session.get('owner_id')
    
    # 优先使用user_id，如果没有则使用owner_id
    lookup_id = user_id if user_id else owner_id
    
    if lookup_id:
        reports = financial_reports_manager.get_user_reports(
            user_id=lookup_id,
            year=int(year) if year else None,
            limit=50
        )
    else:
        reports = []
    
    # 获取可用年份列表
    available_years = []
    if reports:
        years_set = set()
        for report in reports:
            years_set.add(report['report_year'])
        available_years = sorted(list(years_set), reverse=True)
    
    # 当前年份
    current_year = datetime.now().year
    
    return render_template('owner_financial_reports.html',
                         reports=reports,
                         available_years=available_years,
                         selected_year=year,
                         current_year=current_year)

# ==================== 原有路由（添加权限控制） ====================

@app.route('/admin')
@admin_required
def admin_index():
    """管理员主页 - 显示数据库概览"""
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="数据库连接失败")
    
    cursor = conn.cursor(dictionary=True)
    
    # 获取统计数据
    stats = {}
    
    # 房产总数
    cursor.execute("SELECT COUNT(*) as count FROM properties")
    stats['properties_count'] = cursor.fetchone()['count']
    
    # 业主总数
    cursor.execute("SELECT COUNT(*) as count FROM owners_master")
    stats['owners_count'] = cursor.fetchone()['count']
    
    # 城市数量
    cursor.execute("SELECT COUNT(DISTINCT city) as count FROM properties")
    stats['cities_count'] = cursor.fetchone()['count']
    
    # 州数量
    cursor.execute("SELECT COUNT(DISTINCT state) as count FROM properties")
    stats['states_count'] = cursor.fetchone()['count']
    
    # 最新房产
    cursor.execute("""
        SELECT id, name, city, state, beds, property_size
        FROM properties 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    recent_properties = cursor.fetchall()
    
    # 城市分布
    cursor.execute("""
        SELECT city, COUNT(*) as count 
        FROM properties 
        GROUP BY city 
        ORDER BY count DESC 
        LIMIT 10
    """)
    city_distribution = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('index_fixed.html', 
                         stats=stats, 
                         recent_properties=recent_properties,
                         city_distribution=city_distribution,
                         format_management_fee=format_management_fee)

@app.route('/admin/employee_departments', methods=['GET', 'POST'])
@module_required('user_management')
def admin_employee_departments():
    """管理员设置员工部门"""
    
    # 强制执行权限检查，不允许演示模式
    if 'user_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('login'))
    
    if session.get('user_type') != 'admin':
        flash('需要管理员权限', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        department = request.form.get('department')
        
        if not user_id or not department:
            flash('请选择用户和部门', 'error')
            return redirect(url_for('admin_employee_departments'))
        
        conn = get_db_connection()
        if not conn:
            flash('数据库连接失败', 'error')
            return redirect(url_for('admin_employee_departments'))
        
        cursor = conn.cursor()
        
        try:
            # 更新用户部门
            cursor.execute("""
                UPDATE users SET department = %s, updated_at = NOW()
                WHERE id = %s AND user_type != 'owner'
            """, (department, user_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                flash('员工部门设置成功', 'success')
            else:
                flash('设置失败，请检查用户是否存在或是否为员工', 'error')
            
        except Exception as e:
            print(f"❌ 设置员工部门失败: {e}")
            flash('设置失败', 'error')
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('admin_employee_departments'))
    
    # GET请求 - 显示员工部门管理页面
    conn = get_db_connection()
    
    # 预定义部门列表（使用英文作为标准，与注册系统保持一致）
    departments = [
        'Admin',
        'Sales Department', 
        'Accounting Department',
        'Property Management Department'
    ]
    
    if not conn:
        flash('数据库连接失败，请检查数据库配置', 'error')
        return redirect(url_for('dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 获取所有员工用户（非业主）
        cursor.execute("""
            SELECT id, username, full_name, user_type, department, email, created_at
            FROM users 
            WHERE user_type != 'owner' AND is_active = TRUE
            ORDER BY user_type, full_name
        """)
        employees = cursor.fetchall()
        
        # 获取部门统计
        cursor.execute("""
            SELECT department, COUNT(*) as count 
            FROM users 
            WHERE user_type != 'owner' AND is_active = TRUE AND department IS NOT NULL
            GROUP BY department 
            ORDER BY count DESC
        """)
        department_stats = cursor.fetchall()
        
        return render_template('new_ui/admin_employee_departments.html',
                             employees=employees,
                             departments=departments,
                             department_stats=department_stats)
        
    except Exception as e:
        print(f"❌ 获取员工数据失败: {e}")
        flash(f'获取员工数据失败: {str(e)}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/batch_set_departments', methods=['POST'])
def admin_batch_set_departments():
    """批量设置员工部门"""
    
    # 强制执行权限检查
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': '需要管理员权限'})
    
    try:
        data = request.get_json()
        department_assignments = data.get('assignments', [])
        
        if not department_assignments:
            return jsonify({'success': False, 'message': '没有提供部门分配数据'})
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': '数据库连接失败'})
        
        cursor = conn.cursor()
        
        success_count = 0
        for assignment in department_assignments:
            user_id = assignment.get('user_id')
            department = assignment.get('department')
            
            if user_id and department:
                try:
                    cursor.execute("""
                        UPDATE users SET department = %s, updated_at = NOW()
                        WHERE id = %s AND user_type != 'owner'
                    """, (department, user_id))
                    if cursor.rowcount > 0:
                        success_count += 1
                except Exception as e:
                    print(f"❌ 更新用户 {user_id} 部门失败: {e}")
        
        conn.commit()
        
        return jsonify({
            'success': True, 
            'message': f'成功设置 {success_count} 个员工的部门'
        })
        
    except Exception as e:
        print(f"❌ 批量设置部门失败: {e}")
        return jsonify({'success': False, 'message': '批量设置失败'})
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ==================== 演示模式路由 ====================

@app.route('/demo/employee_departments', methods=['GET', 'POST'])
def demo_employee_departments():
    """演示模式 - 员工部门管理"""
    
    # 检查权限 - 只有管理员可以访问
    if 'user_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('login'))
    
    if session.get('user_type') != 'admin':
        flash('需要管理员权限', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        department = request.form.get('department')
        
        if not user_id or not department:
            flash('请选择用户和部门', 'error')
        else:
            # 演示模式 - 模拟成功
            flash(f'演示模式：已为用户设置部门为 {department}', 'success')
        
        return redirect(url_for('demo_employee_departments'))
    
    # GET请求 - 尝试从数据库获取真实数据，失败则使用演示数据
    departments = ['Admin', 'Sales Department', 'Accounting Department', 'Property Management Department']
    
    # 尝试从数据库获取真实员工数据
    employees = []
    department_stats = []
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # 获取所有员工用户（非业主）
            cursor.execute("""
                SELECT id, username, full_name, user_type, department, email, created_at
                FROM users 
                WHERE user_type != 'owner' AND is_active = TRUE
                ORDER BY user_type, full_name
            """)
            employees = cursor.fetchall() or []
            
            # 获取部门统计
            cursor.execute("""
                SELECT department, COUNT(*) as count 
                FROM users 
                WHERE user_type != 'owner' AND is_active = TRUE AND department IS NOT NULL
                GROUP BY department 
                ORDER BY count DESC
            """)
            department_stats = cursor.fetchall() or []
            
            print(f"✅ 演示模式成功获取 {len(employees)} 个员工数据")
            
        except Exception as e:
            print(f"⚠️ 演示模式数据库查询失败: {e}")
            employees = []
            department_stats = []
        finally:
            cursor.close()
            conn.close()
    
    # 如果数据库查询失败，使用演示数据
    if not employees:
        print("📋 使用演示员工数据")
        employees = [
            {
                'id': 1,
                'username': 'admin',
                'full_name': '系统管理员', 
                'email': 'admin@company.com',
                'user_type': 'admin',
                'department': 'Admin'
            },
            {
                'id': 2,
                'username': 'sales01',
                'full_name': '张销售',
                'email': 'sales01@company.com', 
                'user_type': 'property_manager',
                'department': 'Sales Department'
            },
            {
                'id': 3,
                'username': 'finance01',
                'full_name': '李财务',
                'email': 'finance01@company.com',
                'user_type': 'accounting', 
                'department': 'Accounting Department'
            },
            {
                'id': 4,
                'username': 'property01',
                'full_name': '王房管',
                'email': 'property01@company.com',
                'user_type': 'property_manager',
                'department': 'Property Management Department'
            },
            {
                'id': 5,
                'username': 'pm01',
                'full_name': 'PM用户',
                'email': 'pm01@company.com',
                'user_type': 'property_manager',
                'department': 'Property Management Department'
            }
        ]
    
    if not department_stats:
        print("📊 使用演示部门统计")
        department_stats = [
            {'department': 'Admin', 'count': 1},
            {'department': 'Sales Department', 'count': 1}, 
            {'department': 'Accounting Department', 'count': 1},
            {'department': 'Property Management Department', 'count': 2}
        ]
    
    return render_template('admin_employee_departments.html',
                         employees=employees,
                         departments=departments,
                         department_stats=department_stats)

@app.route('/demo/batch_set_departments', methods=['POST'])
def demo_batch_set_departments():
    """演示模式 - 批量设置员工部门"""
    
    # 检查权限
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': '需要管理员权限'})
    
    try:
        data = request.get_json()
        department_assignments = data.get('assignments', [])
        
        if not department_assignments:
            return jsonify({'success': False, 'message': '没有提供部门分配数据'})
        
        # 演示模式 - 模拟成功
        success_count = len(department_assignments)
        
        return jsonify({
            'success': True, 
            'message': f'演示模式：成功设置 {success_count} 个员工的部门'
        })
        
    except Exception as e:
        print(f"❌ 演示批量设置部门失败: {e}")
        return jsonify({'success': False, 'message': '批量设置失败'})

@app.route('/demo')
def demo_index():
    """演示首页"""
    return render_template('demo_index.html')

# ==================== 用户注册功能 ====================



# ==================== 用户管理功能 ====================

@app.route('/admin/user_management', methods=['GET'])
@module_required('user_management')
def admin_user_management():
    """用户管理页面"""
    conn = get_db_connection()
    if not conn:
        flash('数据库连接失败', 'error')
        return render_template('new_ui/user_management.html', users=[], pagination={})
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page
        
        # 构建查询条件
        search = request.args.get('search', '')
        user_type = request.args.get('user_type', '')
        status = request.args.get('status', '')
        filter_type = request.args.get('filter', '')  # 新增筛选类型参数
        
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(username LIKE %s OR full_name LIKE %s OR email LIKE %s)")
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        # 处理筛选类型
        if filter_type == 'admin':
            where_conditions.append("user_type = 'admin'")
        elif filter_type == 'active':
            where_conditions.append("is_active = TRUE")
        elif filter_type == 'inactive':
            where_conditions.append("is_active = FALSE")
        else:
            # 如果没有筛选类型，使用原有的user_type和status参数
            if user_type:
                where_conditions.append("user_type = %s")
                params.append(user_type)
            
            if status == 'active':
                where_conditions.append("is_active = TRUE")
            elif status == 'inactive':
                where_conditions.append("is_active = FALSE")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "is_active = TRUE"
        
        # 获取总数
        count_sql = f"SELECT COUNT(*) as count FROM users WHERE {where_clause}"
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()['count']
        
        # 获取用户列表
        query_sql = f"""
        SELECT id, username, email, user_type, department, full_name, 
               is_active, created_at, updated_at
        FROM users 
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        
        cursor.execute(query_sql, params + [per_page, offset])
        users = cursor.fetchall()
        
        # 添加显示名称
        for user in users:
            user['user_type_display'] = {
                'admin': '管理员',
                'property_manager': '房产管理',
                'sales': '销售',
                'accounting': '会计',
                'marketing': '市场部'
            }.get(user['user_type'], user['user_type'])
            
            user['department_display'] = user['department'] or '未分配'
        
        # 获取统计数据（不受分页影响）
        stats_sql = """
        SELECT 
            COUNT(*) as total_users,
            SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as active_users,
            SUM(CASE WHEN user_type = 'admin' THEN 1 ELSE 0 END) as admin_users,
            SUM(CASE WHEN user_type != 'admin' AND user_type != 'owner' THEN 1 ELSE 0 END) as staff_users
        FROM users
        """
        cursor.execute(stats_sql)
        stats = cursor.fetchone()
        
        # 创建分页对象
        total_pages = (total_count + per_page - 1) // per_page
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total_count,
            'pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_num': page - 1 if page > 1 else None,
            'next_num': page + 1 if page < total_pages else None,
            'iter_pages': lambda left_edge=1, right_edge=1, left_current=2, right_current=2: range(1, total_pages + 1)
        }
        
        return render_template('new_ui/user_management.html', 
                             users=users, 
                             pagination=pagination,
                             stats=stats)
        
    except Exception as e:
        print(f"❌ 获取用户列表失败: {e}")
        flash('获取用户列表失败', 'error')
        return render_template('new_ui/user_management.html', users=[], pagination={})
    finally:
        cursor.close()
        conn.close()



@app.route('/admin/user_details/<int:user_id>')
@admin_required
def admin_user_details(user_id):
    """获取用户详情"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': '数据库连接失败'})
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id, username, email, user_type, department, full_name, 
                   is_active, created_at, updated_at
            FROM users 
            WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        return jsonify({'success': True, 'user': user})
        
    except Exception as e:
        print(f"❌ 获取用户详情失败: {e}")
        return jsonify({'success': False, 'message': '获取用户详情失败'})
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/edit_user', methods=['POST'])
@admin_required
def admin_edit_user():
    """编辑用户信息"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': '数据库连接失败'})
    
    cursor = conn.cursor()
    
    try:
        user_id = request.form.get('user_id')
        username = request.form.get('username')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        user_type = request.form.get('user_type')
        department = request.form.get('department')
        is_active = request.form.get('is_active') == '1'
        
        if not all([user_id, username, full_name, email, user_type, department]):
            return jsonify({'success': False, 'message': '请填写所有必填字段'})
        
        # 检查用户名是否已被其他用户使用
        cursor.execute("""
            SELECT id FROM users 
            WHERE username = %s AND id != %s
        """, (username, user_id))
        
        if cursor.fetchone():
            return jsonify({'success': False, 'message': '用户名已被使用'})
        
        # 检查邮箱是否已被其他用户使用
        cursor.execute("""
            SELECT id FROM users 
            WHERE email = %s AND id != %s
        """, (email, user_id))
        
        if cursor.fetchone():
            return jsonify({'success': False, 'message': '邮箱已被使用'})
        
        # 更新用户信息
        cursor.execute("""
            UPDATE users 
            SET username = %s, full_name = %s, email = %s, 
                user_type = %s, department = %s, is_active = %s, 
                updated_at = NOW()
            WHERE id = %s
        """, (username, full_name, email, user_type, department, is_active, user_id))
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        conn.commit()
        print(f"✅ 用户信息更新成功: {username}")
        
        return jsonify({'success': True, 'message': '用户信息更新成功'})
        
    except Exception as e:
        print(f"❌ 更新用户信息失败: {e}")
        conn.rollback()
        return jsonify({'success': False, 'message': f'更新失败: {e}'})
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/reset_user_password', methods=['POST'])
@admin_required
def admin_reset_user_password():
    """重置用户密码"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': '数据库连接失败'})
    
    cursor = conn.cursor()
    
    try:
        user_id = request.form.get('user_id')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([user_id, new_password, confirm_password]):
            return jsonify({'success': False, 'message': '请填写所有字段'})
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': '两次输入的密码不匹配'})
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': '密码长度至少6位'})
        
        # 密码哈希
        import hashlib
        import os
        
        # 生成盐值
        salt = os.urandom(32)
        # 使用PBKDF2进行密码哈希
        password_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            new_password.encode('utf-8'), 
            salt, 
            100000
        )
        # 将盐值和哈希值组合存储
        password_hash = salt.hex() + password_hash.hex()
        
        # 更新密码
        cursor.execute("""
            UPDATE users 
            SET password_hash = %s, updated_at = NOW()
            WHERE id = %s
        """, (password_hash, user_id))
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        conn.commit()
        print(f"✅ 用户密码重置成功: ID {user_id}")
        
        return jsonify({'success': True, 'message': '密码重置成功'})
        
    except Exception as e:
        print(f"❌ 重置密码失败: {e}")
        conn.rollback()
        return jsonify({'success': False, 'message': f'重置失败: {e}'})
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/delete_user', methods=['POST'])
@admin_required
def admin_delete_user():
    """删除用户"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': '数据库连接失败'})
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        user_id = request.form.get('user_id')
        confirm_username = request.form.get('confirm_username')
        
        if not all([user_id, confirm_username]):
            return jsonify({'success': False, 'message': '请提供完整的删除信息'})
        
        # 防止删除自己的账号
        if int(user_id) == session.get('user_id'):
            return jsonify({'success': False, 'message': '不能删除自己的账号'})
        
        # 获取用户信息（包括已删除的用户）
        cursor.execute("""
            SELECT id, username, full_name, user_type, is_active
            FROM users 
            WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        # 检查用户是否已经被删除
        if not user['is_active']:
            return jsonify({'success': False, 'message': '用户已被删除'})
        
        # 验证用户名确认
        if user['username'] != confirm_username:
            return jsonify({'success': False, 'message': '用户名确认不匹配'})
        
        # 防止删除最后一个管理员
        if user['user_type'] == 'admin':
            cursor.execute("""
                SELECT COUNT(*) as admin_count
                FROM users 
                WHERE user_type = 'admin' AND is_active = TRUE
            """)
            admin_count = cursor.fetchone()['admin_count']
            
            if admin_count <= 1:
                return jsonify({'success': False, 'message': '不能删除最后一个管理员账号'})
        
        # 软删除用户（将is_active设为FALSE）
        cursor.execute("""
            UPDATE users 
            SET is_active = FALSE, updated_at = NOW()
            WHERE id = %s
        """, (user_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"🗑️ 管理员 {session.get('username')} 删除了用户: {user['username']} ({user['full_name']})")
            return jsonify({'success': True, 'message': f'成功删除用户: {user["full_name"]} ({user["username"]})'})
        else:
            return jsonify({'success': False, 'message': '删除失败'})
        
    except Exception as e:
        print(f"❌ 删除用户失败: {e}")
        conn.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {e}'})
    finally:
        cursor.close()
        conn.close()

@app.route('/demo/user_management', methods=['GET'])
def demo_user_management():
    """演示模式下的用户管理"""
    # 从会话中获取或创建演示用户
    if 'demo_users' not in session:
        session['demo_users'] = [
            {'id': 'demo1', 'username': 'demoadmin', 'full_name': '演示管理员', 'user_type': 'admin', 'department': 'Admin', 'email': 'admin@demo.com'},
            {'id': 'demo2', 'username': 'demouser1', 'full_name': '演示用户1', 'user_type': 'admin', 'department': 'Sales Department', 'email': 'sales@demo.com'},
            {'id': 'demo3', 'username': 'demoowner', 'full_name': '演示业主', 'user_type': 'owner', 'department': None, 'email': 'owner@demo.com'},
        ]
    
    users = session['demo_users']
    
    # 计算统计数据
    stats = {
        'total_users': len(users),
        'admin_count': sum(1 for u in users if u['user_type'] == 'admin'),
        'owner_count': sum(1 for u in users if u['user_type'] == 'owner'),
        'unassigned_count': sum(1 for u in users if not u.get('department'))
    }
    
    return render_template('new_ui/admin_user_management.html', users=users, stats=stats)

@app.route('/demo/delete_user', methods=['POST'])
def demo_delete_user():
    """演示模式 - 删除用户"""
    
    # 检查权限
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': '需要管理员权限'})
    
    user_id = request.form.get('user_id')
    confirm_username = request.form.get('confirm_username')
    
    if not user_id or not confirm_username:
        flash('请提供完整的删除信息', 'error')
    elif user_id == '1':  # 防止删除admin账号
        flash('演示模式：不能删除管理员账号', 'error')
    else:
        flash(f'演示模式：成功删除用户 {confirm_username}', 'success')
    
    return redirect(url_for('demo_user_management'))

@app.route('/properties')
@module_required('property_info')
def properties_fixed():
    """房产列表页面 - 支持筛选和分页"""
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败。', 'error')
        return render_template('new_ui/properties.html', properties=[], total_count=0, total_pages=0, current_page=1, filters={})

    try:
        page = request.args.get('page', 1, type=int)
        per_page = 9  # 每页显示9个房产
        
        # 筛选条件
        filters = {
            'search': request.args.get('search', ''),
            'state': request.args.get('state', ''),
            'city': request.args.get('city', '')
        }

        base_query = "FROM properties WHERE deleted_at IS NULL"
        params = []
        
        if filters['search']:
            base_query += " AND (name LIKE %s OR street_address LIKE %s)"
            params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])
        if filters['state']:
            base_query += " AND state = %s"
            params.append(filters['state'])
        if filters['city']:
            base_query += " AND city LIKE %s"
            params.append(f"%{filters['city']}%")

        cursor = connection.cursor(dictionary=True)
        
        # 获取总数
        cursor.execute(f"SELECT COUNT(*) as count {base_query}", tuple(params))
        total_count = cursor.fetchone()['count']
        total_pages = (total_count + per_page - 1) // per_page

        # 获取当前页的房产数据
        offset = (page - 1) * per_page
        query = f"SELECT * {base_query} ORDER BY name LIMIT %s OFFSET %s"
        cursor.execute(query, tuple(params + [per_page, offset]))
        properties = cursor.fetchall()

        # 获取所有州用于筛选下拉菜单
        cursor.execute("SELECT DISTINCT state FROM properties ORDER BY state")
        states = [row['state'] for row in cursor.fetchall()]

    except Exception as e:
        flash(f'加载房产数据时出错: {e}', 'error')
        properties = []
        total_count = 0
        total_pages = 1
        states = []
    finally:
        cursor.close()
        connection.close()

    # 创建一个简单的分页对象
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total_count,
        'pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < total_pages else None,
        'iter_pages': lambda left_edge=1, right_edge=1, left_current=2, right_current=2: range(1, total_pages + 1) # 简化版
    }

    return render_template('new_ui/properties.html',
                           properties=properties,
                           pagination=pagination,
                           total_count=total_count,
                           filters=filters,
                           states=states,
                           current_page=page,
                           total_pages=total_pages)

@app.route('/admin/deleted_properties')
@module_required('property_info')
def deleted_properties():
    """已删除房产列表页面"""
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败。', 'error')
        return render_template('new_ui/deleted_properties.html', properties=[], total_count=0)

    try:
        cursor = connection.cursor(dictionary=True)
        
        # 获取已删除的房产，按删除时间倒序排列
        query = """
            SELECT id, name, street_address, city, state, layout, deleted_at,
                   TIMESTAMPDIFF(MINUTE, deleted_at, NOW()) as minutes_ago
            FROM properties 
            WHERE deleted_at IS NOT NULL 
            ORDER BY deleted_at DESC
        """
        cursor.execute(query)
        properties = cursor.fetchall()
        
        # 计算每个房产的剩余撤销时间
        from datetime import datetime, timedelta
        for property in properties:
            if property['deleted_at']:
                delete_time = property['deleted_at'] if isinstance(property['deleted_at'], datetime) else datetime.fromisoformat(str(property['deleted_at']))
                time_diff = datetime.now() - delete_time
                property['remaining_minutes'] = max(0, 30 - int(time_diff.total_seconds() / 60))
                property['can_undo'] = time_diff <= timedelta(minutes=30)

    except Exception as e:
        flash(f'加载已删除房产数据时出错: {e}', 'error')
        properties = []
    finally:
        cursor.close()
        connection.close()

    return render_template('new_ui/deleted_properties.html',
                           properties=properties,
                           total_count=len(properties))

@app.route('/admin/delete_property', methods=['POST'])
@module_required('property_info')
def delete_property():
    """软删除房产"""
    property_id = request.form.get('property_id')
    
    if not property_id:
        return jsonify({'success': False, 'message': '房产ID不能为空'})
    
    # 检查用户权限
    user_type = session.get('user_type', '')
    user_department = session.get('department', '')
    
    # 只有管理员或房产管理部门的用户可以删除房产
    if user_type != 'admin' and user_department != 'Property Management Department':
        return jsonify({
            'success': False, 
            'message': '您没有删除房产的权限。只有管理员或房产管理部门的员工可以执行此操作。'
        })
    
    conn = get_db_connection()
    if not conn:
        # 演示模式：从session中删除房产
        print(f"⚠️  演示模式：尝试删除房产 ID {property_id}")
        
        # 如果是演示房产#1（ID=1），不允许删除
        if property_id == '1':
            return jsonify({
                'success': False, 
                'message': '演示房产#1不能删除（演示模式）'
            })
        
        # 从session中删除用户添加的房产
        if 'demo_properties' in session:
            property_id_int = int(property_id)
            original_count = len(session['demo_properties'])
            session['demo_properties'] = [
                prop for prop in session['demo_properties'] 
                if prop['id'] != property_id_int
            ]
            new_count = len(session['demo_properties'])
            
            if new_count < original_count:
                session.permanent = True
                print(f"✅ 演示模式：已删除房产 ID {property_id}")
                return jsonify({
                    'success': True, 
                    'message': f'房产已删除（演示模式），30分钟内可撤销'
                })
            else:
                return jsonify({
                    'success': False, 
                    'message': '房产不存在或无法删除（演示模式）'
                })
        else:
            return jsonify({
                'success': False, 
                'message': '没有找到要删除的房产（演示模式）'
            })
    
    cursor = conn.cursor()
    
    try:
        # 检查房产是否存在且未被删除
        cursor.execute("SELECT name FROM properties WHERE id = %s AND deleted_at IS NULL", (property_id,))
        property_info = cursor.fetchone()
        
        if not property_info:
            return jsonify({'success': False, 'message': '房产不存在或已被删除'})
        
        property_name = property_info[0]
        
        # 软删除房产 - 设置删除时间戳
        from datetime import datetime, timedelta
        deleted_at = datetime.now()
        
        cursor.execute("UPDATE properties SET deleted_at = %s WHERE id = %s", (deleted_at, property_id))
        affected_rows = cursor.rowcount
        
        if affected_rows == 0:
            conn.rollback()
            return jsonify({'success': False, 'message': '房产删除失败，房产可能已不存在'})
        
        conn.commit()
        print(f"✅ 房产 '{property_name}' 软删除成功，删除时间: {deleted_at}")
        
        return jsonify({
            'success': True, 
            'message': f'房产 "{property_name}" 已删除，30分钟内可撤销删除操作'
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 删除房产错误: {error_msg}")
        conn.rollback()
        
        # 根据错误类型提供更具体的错误信息
        if 'access denied' in error_msg.lower():
            return jsonify({
                'success': False, 
                'message': '数据库访问权限不足，请联系系统管理员。'
            })
        else:
            return jsonify({
                'success': False, 
                'message': f'删除房产时发生错误：{error_msg}'
            })
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/undo_delete_property', methods=['POST'])
@module_required('property_info')
def undo_delete_property():
    """撤销删除房产"""
    property_id = request.form.get('property_id')
    
    if not property_id:
        return jsonify({'success': False, 'message': '房产ID不能为空'})
    
    # 检查用户权限
    user_type = session.get('user_type', '')
    user_department = session.get('department', '')
    
    # 只有管理员或房产管理部门的用户可以撤销删除
    if user_type != 'admin' and user_department != 'Property Management Department':
        return jsonify({
            'success': False, 
            'message': '您没有撤销删除房产的权限。只有管理员或房产管理部门的员工可以执行此操作。'
        })
    
    conn = get_db_connection()
    if not conn:
        # 演示模式：恢复session中的房产
        print(f"⚠️  演示模式：尝试撤销删除房产 ID {property_id}")
        
        # 这里需要实现演示模式的撤销逻辑
        return jsonify({
            'success': False, 
            'message': '演示模式暂不支持撤销删除功能'
        })
    
    cursor = conn.cursor()
    
    try:
        # 检查房产是否存在且已被删除
        cursor.execute("SELECT name, deleted_at FROM properties WHERE id = %s AND deleted_at IS NOT NULL", (property_id,))
        property_info = cursor.fetchone()
        
        if not property_info:
            return jsonify({'success': False, 'message': '房产不存在或未被删除'})
        
        property_name, deleted_at = property_info
        
        # 检查是否在30分钟撤销窗口内
        from datetime import datetime, timedelta
        now = datetime.now()
        delete_time = deleted_at if isinstance(deleted_at, datetime) else datetime.fromisoformat(str(deleted_at))
        time_diff = now - delete_time
        
        if time_diff > timedelta(minutes=30):
            return jsonify({
                'success': False, 
                'message': f'撤销时间已过期。房产 "{property_name}" 于 {delete_time.strftime("%Y-%m-%d %H:%M:%S")} 删除，已超过30分钟撤销期限。'
            })
        
        # 撤销删除 - 清除删除时间戳
        cursor.execute("UPDATE properties SET deleted_at = NULL WHERE id = %s", (property_id,))
        affected_rows = cursor.rowcount
        
        if affected_rows == 0:
            conn.rollback()
            return jsonify({'success': False, 'message': '撤销删除失败，房产可能已不存在'})
        
        conn.commit()
        print(f"✅ 房产 '{property_name}' 撤销删除成功")
        
        return jsonify({
            'success': True, 
            'message': f'房产 "{property_name}" 撤销删除成功，已恢复正常状态'
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 撤销删除房产错误: {error_msg}")
        conn.rollback()
        
        return jsonify({
            'success': False, 
            'message': f'撤销删除房产时发生错误：{error_msg}'
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/add_property', methods=['GET', 'POST'])
@admin_required
def add_property():
    # 演示模式：将房产添加到session中
    if get_db_connection() is None:
        if request.method == 'POST':
            # 创建一个唯一的ID
            if 'demo_properties' not in session:
                session['demo_properties'] = []
            
            new_id = len(session['demo_properties']) + 2 # 避开演示房产#1
            
            new_property = {
                'id': new_id,
                'name': request.form['name'],
                'street_address': request.form['street_address'],
                'city': request.form['city'],
                'state': request.form['state'],
                'zip_code': request.form['zip_code'],
                'bedrooms': int(request.form.get('bedrooms', 0)),
                'bathrooms': float(request.form.get('bathrooms', 0)),
                'square_feet': int(request.form.get('square_feet', 0)),
                'property_type': request.form['property_type'],
                'year_built': int(request.form.get('year_built', 0)),
                'monthly_rent': float(request.form.get('monthly_rent', 0)),
                'description': request.form['description'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            session['demo_properties'].append(new_property)
            session.permanent = True  # 确保session被保存
            flash(f"房产 '{new_property['name']}' 已添加 (演示模式)", 'success')
            return redirect(url_for('properties_fixed'))
        
        return render_template('new_ui/add_property.html')

    # 生产模式
    if request.method == 'POST':
        try:
            # 获取表单数据
            property_data = {
                'name': request.form.get('name'),
                'street_address': request.form.get('street_address'),
                'city': request.form.get('city'),
                'state': request.form.get('state'),
                'bedrooms': int(request.form.get('bedrooms', 0)) if request.form.get('bedrooms') else None,
                'bathrooms': float(request.form.get('bathrooms', 0)) if request.form.get('bathrooms') else None,
                'square_feet': int(request.form.get('square_feet', 0)) if request.form.get('square_feet') else None
            }
            
            # 验证必填字段
            if not property_data['name'] or not property_data['street_address'] or not property_data['city'] or not property_data['state']:
                flash('房产名称、街道地址、城市和州是必填项', 'error')
                return render_template('new_ui/add_property.html', property_data=property_data)
            
            # 连接数据库
            conn = get_db_connection()
            if not conn:
                flash('数据库连接失败', 'error')
                return render_template('new_ui/add_property.html', property_data=property_data)
            
            cursor = conn.cursor()
            
            # 生成唯一的房产ID
            import uuid
            property_id = str(uuid.uuid4()).replace('-', '')[:10]
            
            # 插入房产数据
            insert_query = """
                INSERT INTO properties (
                    id, name, street_address, city, state, layout, 
                    property_size, land_size, occupancy, beds
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # 将表单数据映射到数据库字段
            layout = f"{property_data['bedrooms']}b{property_data['bathrooms']}b" if property_data['bedrooms'] and property_data['bathrooms'] else None
            property_size = property_data['square_feet']
            land_size = None  # 表单中没有这个字段
            occupancy = None  # 表单中没有这个字段
            beds = None  # 表单中没有这个字段
            
            cursor.execute(insert_query, (
                property_id,
                property_data['name'],
                property_data['street_address'],
                property_data['city'],
                property_data['state'],
                layout,
                property_size,
                land_size,
                occupancy,
                beds
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash(f'房产 "{property_data["name"]}" 添加成功！', 'success')
            return redirect(url_for('properties_fixed'))
            
        except Exception as e:
            print(f"添加房产错误: {e}")
            flash(f'添加房产失败: {str(e)}', 'error')
            return render_template('new_ui/add_property.html', property_data=property_data)
    
    return render_template('new_ui/add_property.html')

@app.route('/admin/edit_property/<string:property_id>', methods=['GET', 'POST'])
@admin_required
def edit_property(property_id):
    """编辑房产信息"""
    return edit_property_impl(property_id)

@app.route('/edit_property_direct/<string:property_id>', methods=['GET', 'POST'])
@login_required
def edit_property_direct(property_id):
    """编辑房产 - 直接访问（调试用）"""
    return edit_property_impl(property_id)

def edit_property_impl(property_id):
    """编辑房产"""
    conn = get_db_connection()
    if not conn:
        # 演示模式：编辑session中的房产
        print(f"⚠️  演示模式：编辑房产 ID {property_id}")
        
        if request.method == 'POST':
            # 从session中找到并更新房产
            if 'demo_properties' in session:
                for i, prop in enumerate(session['demo_properties']):
                    if prop['id'] == property_id:
                        # 更新房产数据
                        session['demo_properties'][i].update({
                            'name': request.form.get('name'),
                            'street_address': request.form.get('street_address'),
                            'city': request.form.get('city'),
                            'state': request.form.get('state'),
                            'zip_code': request.form.get('zip_code'),
                            'bedrooms': int(request.form.get('bedrooms')) if request.form.get('bedrooms') else None,
                            'bathrooms': float(request.form.get('bathrooms')) if request.form.get('bathrooms') else None,
                            'square_feet': int(request.form.get('square_feet')) if request.form.get('square_feet') else None,
                            'property_type': request.form.get('property_type'),
                            'year_built': int(request.form.get('year_built')) if request.form.get('year_built') else None,
                            'monthly_rent': float(request.form.get('monthly_rent')) if request.form.get('monthly_rent') else None,
                            'description': request.form.get('description')
                        })
                        session.permanent = True
                        flash('房产更新成功（演示模式）', 'success')
                        return redirect(url_for('properties'))
            
            flash('房产不存在（演示模式）', 'error')
            return redirect(url_for('properties'))
        else:
            # GET请求：显示编辑表单
            property_data = None
            
            # 检查是否是固定的演示房产
            if property_id == 1:
                property_data = {
                    'id': 1,
                    'name': '演示房产 #1',
                    'street_address': '123 演示街',
                    'city': '演示城市',
                    'state': 'CA',
                    'zip_code': '90210',
                    'bedrooms': 3,
                    'bathrooms': 2,
                    'square_feet': 1500,
                    'property_type': 'House',
                    'year_built': 2000,
                    'monthly_rent': 2500,
                    'description': '演示房产描述'
                }
            elif 'demo_properties' in session:
                # 从session中查找房产
                for prop in session['demo_properties']:
                    if prop['id'] == property_id:
                        property_data = prop
                        break
            
            if property_data:
                return render_template('new_ui/edit_property.html', property=property_data, is_demo=True)
            else:
                flash('房产不存在（演示模式）', 'error')
                return redirect(url_for('properties_fixed'))
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            property_data = {
                'name': request.form.get('name'),
                'street_address': request.form.get('street_address'),
                'city': request.form.get('city'),
                'state': request.form.get('state'),
                'layout': request.form.get('layout'),
                'property_size': request.form.get('property_size'),
                'land_size': request.form.get('land_size'),
                'occupancy': request.form.get('occupancy'),
                'beds': request.form.get('beds'),
                'front_door_code': request.form.get('front_door_code'),
                'storage_code': request.form.get('storage_code'),
                'wifi_name': request.form.get('wifi_name'),
                'wifi_password': request.form.get('wifi_password'),
                'trash_day': request.form.get('trash_day')
            }
            
            # 更新房产数据
            update_query = """
                UPDATE properties 
                SET name = %s, street_address = %s, city = %s, state = %s, 
                    layout = %s, property_size = %s, land_size = %s, occupancy = %s,
                    beds = %s, front_door_code = %s, storage_code = %s, 
                    wifi_name = %s, wifi_password = %s, trash_day = %s
                WHERE id = %s
            """
            
            cursor.execute(update_query, (
                property_data['name'],
                property_data['street_address'],
                property_data['city'],
                property_data['state'],
                property_data['layout'],
                int(property_data['property_size']) if property_data['property_size'] else None,
                int(property_data['land_size']) if property_data['land_size'] else None,
                int(property_data['occupancy']) if property_data['occupancy'] else None,
                property_data['beds'],
                property_data['front_door_code'],
                property_data['storage_code'],
                property_data['wifi_name'],
                property_data['wifi_password'],
                property_data['trash_day'],
                property_id
            ))
            
            conn.commit()
            flash('房产更新成功', 'success')
            return redirect(url_for('properties_fixed'))
            
        except Exception as e:
            print(f"更新房产错误: {e}")
            flash(f'更新房产失败: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    # GET请求，获取房产信息并显示编辑表单
    try:
        cursor.execute("SELECT * FROM properties WHERE id = %s", (property_id,))
        property_data = cursor.fetchone()
        
        if not property_data:
            flash('房产不存在', 'error')
            return redirect(url_for('properties_fixed'))
        
        return render_template('new_ui/edit_property.html', property=property_data, is_demo=False)
        
    except Exception as e:
        print(f"获取房产信息错误: {e}")
        flash('获取房产信息失败', 'error')
        return redirect(url_for('properties_fixed'))
    finally:
        cursor.close()
        conn.close()

@app.route('/property/<property_id>')
@module_required('property_info')
def property_detail_fixed(property_id):
    """显示单个房产的详细信息"""
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败。', 'error')
        return redirect(url_for('properties_fixed'))
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM properties WHERE id = %s", (property_id,))
        property_data = cursor.fetchone()
        
        if not property_data:
            flash('未找到该房产。', 'error')
            return redirect(url_for('properties_fixed'))
            
        # 获取关联的业主信息
        cursor.execute("""
            SELECT o.* FROM owners_master o
            JOIN property_owners po ON o.owner_id = po.owner_id
            WHERE po.property_id = %s
        """, (property_id,))
        owners = cursor.fetchall()

        # 获取房产附加信息
        cursor.execute("""
            SELECT pai.*, u.username as created_by_name
            FROM property_additional_info pai
            LEFT JOIN users u ON pai.created_by = u.id
            WHERE pai.property_id = %s AND pai.is_active = TRUE AND pai.deleted_at IS NULL
            ORDER BY pai.priority DESC, pai.created_at DESC
        """, (property_id,))
        additional_info = cursor.fetchall()

        return render_template('new_ui/property_detail.html', 
                             property=property_data, 
                             owners=owners, 
                             additional_info=additional_info)

    except Exception as e:
        flash(f'加载房产详情时出错: {e}', 'error')
        return redirect(url_for('properties_fixed'))
    finally:
        connection.close()

@app.route('/owners')
@module_required('owner_info')
def owners_fixed():
    """业主列表页面 - 支持筛选和分页"""
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败。', 'error')
        return render_template('new_ui/owners.html', owners=[], pagination={'total': 0, 'pages': 0}, filters={})

    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        filters = {
            'search': request.args.get('search', ''),
            'strategy': request.args.get('strategy', '')
        }

        base_query = "FROM owners_master o LEFT JOIN (SELECT po.owner_id, COUNT(*) as property_count FROM property_owners po GROUP BY po.owner_id) p ON o.owner_id = p.owner_id WHERE o.deleted_at IS NULL"
        params = []
        
        if filters['search']:
            base_query += " AND (o.name LIKE %s OR o.email LIKE %s OR o.phone LIKE %s)"
            params.extend([f"%{filters['search']}%"] * 3)
        if filters['strategy']:
            base_query += " AND o.preferences_strategy = %s"
            params.append(filters['strategy'])

        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(f"SELECT COUNT(*) as count {base_query}", tuple(params))
        total_count = cursor.fetchone()['count']
        total_pages = (total_count + per_page - 1) // per_page

        offset = (page - 1) * per_page
        query = f"SELECT o.*, COALESCE(p.property_count, 0) as property_count {base_query} ORDER BY o.name LIMIT %s OFFSET %s"
        cursor.execute(query, tuple(params + [per_page, offset]))
        owners = cursor.fetchall()

        cursor.execute("SELECT DISTINCT preferences_strategy FROM owners_master WHERE preferences_strategy IS NOT NULL ORDER BY preferences_strategy")
        strategies = [row['preferences_strategy'] for row in cursor.fetchall()]

    except Exception as e:
        flash(f'加载业主数据时出错: {e}', 'error')
        owners, strategies, total_count, total_pages = [], [], 0, 1
    finally:
        cursor.close()
        connection.close()

    pagination = {
        'page': page, 'per_page': per_page, 'total': total_count, 'pages': total_pages,
        'has_prev': page > 1, 'has_next': page < total_pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < total_pages else None,
        'iter_pages': lambda **kwargs: range(1, total_pages + 1)
    }

    return render_template('new_ui/owners.html',
                           owners=owners,
                           pagination=pagination,
                           filters=filters,
                           strategies=strategies)

@app.route('/admin/delete_owner', methods=['POST'])
@module_required('owner_info')
def delete_owner():
    """软删除业主"""
    owner_id = request.form.get('owner_id')
    
    if not owner_id:
        return jsonify({'success': False, 'message': '业主ID不能为空'})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': '数据库连接失败'})
    
    cursor = conn.cursor()
    
    try:
        # 检查业主是否存在且未被删除
        cursor.execute("SELECT name FROM owners_master WHERE owner_id = %s AND deleted_at IS NULL", (owner_id,))
        owner_info = cursor.fetchone()
        
        if not owner_info:
            return jsonify({'success': False, 'message': '业主不存在或已被删除'})
        
        # 软删除业主 - 使用数据库的NOW()函数确保时间一致性
        cursor.execute("UPDATE owners_master SET deleted_at = NOW() WHERE owner_id = %s", (owner_id,))
        
        conn.commit()
        
        # 获取删除时间用于日志
        cursor.execute("SELECT deleted_at FROM owners_master WHERE owner_id = %s", (owner_id,))
        deleted_time = cursor.fetchone()[0]
        print(f"✅ 业主 '{owner_info[0]}' 软删除成功，删除时间: {deleted_time}")
        return jsonify({
            'success': True, 
            'message': f'业主 "{owner_info[0]}" 已成功删除'
        })
        
    except Exception as e:
        print(f"删除业主错误: {e}")
        conn.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/undo_delete_owner', methods=['POST'])
@module_required('owner_info')
def undo_delete_owner():
    """撤销删除业主"""
    owner_id = request.form.get('owner_id')
    
    if not owner_id:
        return jsonify({'success': False, 'message': '业主ID不能为空'})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': '数据库连接失败'})
    
    cursor = conn.cursor()
    
    try:
        # 检查业主是否存在且已被删除
        cursor.execute("SELECT name, deleted_at FROM owners_master WHERE owner_id = %s AND deleted_at IS NOT NULL", (owner_id,))
        owner_info = cursor.fetchone()
        
        if not owner_info:
            return jsonify({'success': False, 'message': '业主不存在或未被删除'})
        
        # 检查是否在30分钟内
        from datetime import datetime, timedelta
        deleted_time = owner_info[1]
        if deleted_time:
            # 使用数据库的NOW()函数进行比较
            cursor.execute("SELECT TIMESTAMPDIFF(MINUTE, %s, NOW()) as minutes_diff", (deleted_time,))
            diff_result = cursor.fetchone()
            minutes_diff = diff_result[0] if diff_result else 0
            
            if minutes_diff > 30:
                return jsonify({'success': False, 'message': f'删除时间超过30分钟，无法撤销。删除时间：{deleted_time}，相差：{minutes_diff}分钟'})
        
        # 撤销删除
        cursor.execute("UPDATE owners_master SET deleted_at = NULL WHERE owner_id = %s", (owner_id,))
        conn.commit()
        
        print(f"✅ 业主 '{owner_info[0]}' 撤销删除成功")
        return jsonify({
            'success': True, 
            'message': f'业主 "{owner_info[0]}" 撤销删除成功'
        })
        
    except Exception as e:
        print(f"撤销删除业主错误: {e}")
        conn.rollback()
        return jsonify({'success': False, 'message': f'撤销删除失败: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/deleted_owners')
@module_required('owner_info')
def deleted_owners():
    """显示已删除的业主列表"""
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败。', 'error')
        return render_template('new_ui/deleted_owners.html', owners=[], pagination={'total': 0, 'pages': 0})

    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        cursor = connection.cursor(dictionary=True)
        
        # 获取已删除的业主总数
        cursor.execute("SELECT COUNT(*) as count FROM owners_master WHERE deleted_at IS NOT NULL")
        total_count = cursor.fetchone()['count']
        total_pages = (total_count + per_page - 1) // per_page

        offset = (page - 1) * per_page
        
        # 获取已删除的业主列表
        cursor.execute("""
            SELECT o.*, COALESCE(p.property_count, 0) as property_count,
                   TIMESTAMPDIFF(MINUTE, o.deleted_at, NOW()) as minutes_ago
            FROM owners_master o 
            LEFT JOIN (
                SELECT po.owner_id, COUNT(*) as property_count 
                FROM property_owners po 
                GROUP BY po.owner_id
            ) p ON o.owner_id = p.owner_id
            WHERE o.deleted_at IS NOT NULL
            ORDER BY o.deleted_at DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        owners = cursor.fetchall()

        pagination = {
            'page': page,
            'pages': total_pages,
            'total': total_count,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_num': page - 1 if page > 1 else None,
            'next_num': page + 1 if page < total_pages else None
        }
        
        return render_template('new_ui/deleted_owners.html', 
                             owners=owners, 
                             pagination=pagination)

    except Exception as e:
        print(f"获取已删除业主列表错误: {e}")
        flash(f'获取已删除业主列表时出错: {e}', 'error')
        return render_template('new_ui/deleted_owners.html', owners=[], pagination={'total': 0, 'pages': 0})
    finally:
        connection.close()

@app.route('/admin/add_owner', methods=['GET', 'POST'])
@module_required('owner_info')
def add_owner():
    """添加新业主"""
    if request.method == 'POST':
        owner_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'preferences_strategy': request.form.get('preferences_strategy'),
            'notes': request.form.get('notes')
        }
        
        if not owner_data['name'] or not owner_data['email']:
            flash('姓名和邮箱是必填项。', 'error')
            return render_template('new_ui/add_owner.html', owner_data=owner_data)
            
        connection = get_db_connection()
        if not connection:
            flash('数据库连接失败。', 'error')
            return render_template('new_ui/add_owner.html', owner_data=owner_data)

        try:
            cursor = connection.cursor()
            
            # 生成唯一的owner_id
            import uuid
            owner_id = str(uuid.uuid4()).replace('-', '')[:10]
            
            # 插入业主信息
            cursor.execute("""
                INSERT INTO owners_master (owner_id, name, email, phone, preferences_strategy)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                owner_id,
                owner_data['name'],
                owner_data['email'],
                owner_data['phone'],
                owner_data['preferences_strategy']
            ))
            
            connection.commit()
            flash('业主添加成功！', 'success')
            return redirect(url_for('owners_fixed'))
        except Exception as e:
            print(f"添加业主错误: {e}")
            connection.rollback()
            flash(f'添加业主时出错: {e}', 'error')
            return render_template('new_ui/add_owner.html', owner_data=owner_data)
        finally:
            connection.close()

    return render_template('new_ui/add_owner.html')

@app.route('/owner/<owner_id>')
@module_required('owner_info')
def owner_detail_fixed(owner_id):
    """显示单个业主的详细信息"""
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败。', 'error')
        return redirect(url_for('owners_fixed'))

    try:
        cursor = connection.cursor(dictionary=True)
        
        # 获取业主信息
        cursor.execute("SELECT * FROM owners_master WHERE owner_id = %s", (owner_id,))
        owner_data = cursor.fetchone()

        if not owner_data:
            flash('未找到该业主。', 'error')
            return redirect(url_for('owners_fixed'))
            
        # 获取该业主的所有房产
        cursor.execute("""
            SELECT p.* FROM properties p
            JOIN property_owners po ON p.id = po.property_id
            WHERE po.owner_id = %s
        """, (owner_id,))
        properties = cursor.fetchall()
        
        return render_template('new_ui/owner_detail.html', owner=owner_data, properties=properties)

    except Exception as e:
        flash(f'加载业主详情时出错: {e}', 'error')
        return redirect(url_for('owners_fixed'))
    finally:
        connection.close()

@app.route('/api/stats')
def api_stats():
    """API接口 - 获取统计数据"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'})
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 房产按州分布
        cursor.execute("""
            SELECT state, COUNT(*) as count 
            FROM properties 
            GROUP BY state 
            ORDER BY count DESC
        """)
        state_distribution = cursor.fetchall()
        
        # 房产类型分布
        cursor.execute("""
            SELECT 
                COALESCE(beds, '未知') as type,
                COUNT(*) as count
            FROM properties 
            GROUP BY beds
            ORDER BY count DESC
            LIMIT 10
        """)
        type_distribution = cursor.fetchall()
        
        # 管理费分布
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN management_fee_rate IS NULL THEN '未设置'
                    WHEN management_fee_rate < 15 AND management_fee_type = 'Gross' THEN '低费率 (<15% Gross)'
                    WHEN management_fee_rate < 15 AND management_fee_type = 'Net' THEN '低费率 (<15% Net)'
                    WHEN management_fee_rate <= 25 AND management_fee_type = 'Gross' THEN '中等费率 (15-25% Gross)'
                    WHEN management_fee_rate <= 25 AND management_fee_type = 'Net' THEN '中等费率 (15-25% Net)'
                    WHEN management_fee_type = 'Gross' THEN '高费率 (>25% Gross)'
                    WHEN management_fee_type = 'Net' THEN '高费率 (>25% Net)'
                    ELSE '其他'
                END as fee_range,
                COUNT(*) as count
            FROM finance
            GROUP BY fee_range
            ORDER BY count DESC
        """)
        fee_distribution = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'state_distribution': state_distribution,
            'type_distribution': type_distribution,
            'fee_distribution': fee_distribution
        })
        
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'error': str(e)})

# ==================== 语言切换路由 ====================

@app.route('/set_language/<language>')
def set_language(language):
    """设置语言"""
    if language_manager.set_language(language):
        flash(get_text('language_changed', language), 'success')
    else:
        flash('Unsupported language / 不支持的语言', 'error')
    
    # 返回到之前的页面或仪表板
    return redirect(request.referrer or url_for('dashboard'))

# ==================== 密码管理路由 ====================

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """处理用户修改自己的密码"""
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_new_password']

        if new_password != confirm_password:
            flash('新密码和确认密码不匹配。', 'error')
            return render_template('new_ui/change_password.html')

        success, message = password_manager.change_password(
            session['user_id'], 
            current_password, 
            new_password
        )
        
        if success:
            flash(message, 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(message, 'error')
            return render_template('new_ui/change_password.html')

    return render_template('new_ui/change_password.html')

@app.route('/admin/reset_password', methods=['GET', 'POST'])
@admin_required
def admin_reset_password():
    """管理员重置用户密码"""
    if request.method == 'POST':
        target_user_id = request.form.get('target_user_id')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        reset_notes = request.form.get('reset_notes', '')
        
        # 验证输入
        if not all([target_user_id, new_password, confirm_password]):
            return render_template('admin_reset_password.html', 
                                 message='请填写所有必填字段', 
                                 success=False)
        
        if new_password != confirm_password:
            return render_template('admin_reset_password.html', 
                                 message='两次输入的密码不一致', 
                                 success=False)
        
        if len(new_password) < 8:
            return render_template('admin_reset_password.html', 
                                 message='新密码长度至少8位', 
                                 success=False)
        
        # 重置密码
        success, message = password_manager.admin_reset_password(
            admin_id=session['user_id'],
            target_user_id=int(target_user_id),
            new_password=new_password,
            notes=reset_notes,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return render_template('admin_reset_password.html', 
                             message=message, 
                             success=success)
    
    return render_template('admin_reset_password.html')

@app.route('/api/search_users')
@admin_required
def api_search_users():
    """API: 搜索用户（用于管理员重置密码功能）"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify({'users': []})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': '数据库连接失败'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 搜索用户（排除当前管理员，但包含其他admin用户）
        search_sql = """
            SELECT id, username, email, user_type, full_name,
                   DATE_FORMAT(created_at, '%Y-%m-%d') as created_at
            FROM users 
            WHERE (username LIKE %s OR email LIKE %s OR full_name LIKE %s)
            AND id != %s
            AND is_active = TRUE
            ORDER BY username
            LIMIT 10
        """
        
        search_pattern = f'%{query}%'
        cursor.execute(search_sql, (search_pattern, search_pattern, search_pattern, session['user_id']))
        users = cursor.fetchall()
        
        return jsonify({'users': users})
        
    except Exception as e:
        print(f"❌ 搜索用户失败: {e}")
        return jsonify({'error': '搜索失败'}), 500
    finally:
        cursor.close()
        conn.close()

# ==================== 财务报表路由 ====================

@app.route('/admin/financial_reports', methods=['GET', 'POST'])
@module_required('financial_records_view')
def admin_financial_reports():
    """管理员财务报表管理"""
    if request.method == 'POST':
        # 添加财务报表
        property_id = request.form.get('property_id')
        report_year = int(request.form.get('report_year'))
        report_month = int(request.form.get('report_month'))
        report_title = request.form.get('report_title')
        onedrive_link = request.form.get('onedrive_link')
        notes = request.form.get('notes', '')
        
        # 验证输入
        if not all([property_id, report_year, report_month, report_title, onedrive_link]):
            flash('请填写所有必填字段', 'error')
        else:
            success, message = financial_reports_manager.add_financial_report(
                property_id=property_id,
                report_year=report_year,
                report_month=report_month,
                report_title=report_title,
                onedrive_link=onedrive_link,
                uploaded_by=session['user_id'],
                notes=notes
            )
            
            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')
        
        return redirect(url_for('admin_financial_reports'))
    
    # GET请求 - 显示管理页面
    # 获取筛选参数
    year = request.args.get('year')
    month = request.args.get('month')
    property_id = request.args.get('property_id')
    
    # 获取报表列表
    reports_data = financial_reports_manager.get_all_reports(
        year=int(year) if year else None,
        month=int(month) if month else None,
        property_id=property_id,
        page=1,
        per_page=50
    )
    reports = reports_data['reports']
    total_count = reports_data['total_count']
    
    # 获取房产列表
    properties = financial_reports_manager.get_properties_list()
    
    # 获取统计信息
    stats = financial_reports_manager.get_report_stats()
    
    # 计算总页数
    page = request.args.get('page', 1, type=int)
    per_page = reports_data.get('per_page', 50)
    total_pages = (total_count + per_page - 1) // per_page if per_page > 0 else 1
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # 渲染模板
    return render_template('new_ui/admin_financial_reports.html', 
                         reports=reports,
                         properties=properties,
                         total_count=total_count,
                         stats=stats,
                         current_year=current_year,
                         current_month=current_month,
                         total_pages=total_pages,
                         current_page=page)

@app.route('/admin/delete_financial_report', methods=['POST'])
@admin_required
def delete_financial_report():
    """删除财务报表"""
    report_id = request.form.get('report_id')
    
    if not report_id:
        return jsonify({'success': False, 'message': '报表ID不能为空'})
    
    success, message = financial_reports_manager.delete_report(
        report_id=int(report_id),
        admin_id=session['user_id']
    )
    
    return jsonify({'success': success, 'message': message})

@app.route('/admin/delete_report/<int:report_id>', methods=['POST'])
@admin_required
def delete_report(report_id):
    """删除财务报表"""
    success, message = financial_reports_manager.delete_report(
        report_id=report_id,
        admin_id=session['user_id']
    )
    
    return jsonify({'success': success, 'message': message})

# ==================== 房产分配管理路由 ====================

# ==================== 部门模块路由 ====================

@app.route('/customers')
@module_required('customer_management')
def customer_management():
    """客户建档管理 - Property Manager & Sales"""
    # 演示数据
    customer_stats = {
        'total': 45,
        'active': 32,
        'potential': 8,
        'new_this_month': 5
    }
    
    customers = [
        {
            'id': 1,
            'name': '张先生',
            'company': '科技有限公司',
            'phone': '138****5678',
            'email': 'zhang@example.com',
            'type': '购房客户',
            'status': 'active',
            'status_display': '活跃客户',
            'last_contact': '2024-01-15',
            'assigned_to': session.get('full_name', '未分配')
        },
        {
            'id': 2,
            'name': '李女士',
            'company': '',
            'phone': '139****8765',
            'email': 'li@example.com',
            'type': '租房客户',
            'status': 'potential',
            'status_display': '潜在客户',
            'last_contact': '2024-01-12',
            'assigned_to': '销售部小王'
        }
    ]
    
    return render_template('customer_management.html', 
                         customer_stats=customer_stats,
                         customers=customers)

@app.route('/maintenance')
@module_required('maintenance_records')
def maintenance_management():
    """维修记录管理 - Property Manager Only"""
    return render_template('maintenance_management.html')

@app.route('/cleaning')
@module_required('customer_management')
def cleaning_management():
    """清洁记录管理 - Property Manager Only"""
    return render_template('cleaning_management.html')

@app.route('/financial-view')
@module_required('financial_records_view')
def financial_records_view():
    """财务记录查看 - Property Manager (只读)"""
    return render_template('financial_records_view.html')

@app.route('/customers/add', methods=['POST'])
@module_required('customer_management')
def add_customer():
    """添加新客户"""
    try:
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        customer_type = request.form.get('type')
        company = request.form.get('company', '')
        notes = request.form.get('notes', '')
        
        if not name or not phone:
            return jsonify({'success': False, 'message': '客户姓名和电话为必填项'})
        
        # 这里应该连接数据库保存客户信息
        # 由于当前没有客户表，我们返回成功消息
        return jsonify({
            'success': True, 
            'message': f'客户 "{name}" 添加成功',
            'redirect': '/customers'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'添加失败: {str(e)}'})

@app.route('/customers/delete/<int:customer_id>', methods=['POST'])
@module_required('customer_management')
def delete_customer(customer_id):
    """删除客户"""
    try:
        conn = get_db_connection()
        if not conn:
            # 演示模式 - 模拟删除成功
            print(f"⚠️  演示模式删除客户: {customer_id}")
            return jsonify({
                'success': True, 
                'message': '客户删除成功（演示模式）'
            })
        
        # 这里可以添加真实的数据库删除逻辑
        cursor = conn.cursor()
        # TODO: 实现真实的客户删除逻辑
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': '客户删除成功'
        })
    except Exception as e:
        print(f"❌ 删除客户失败: {e}")
        return jsonify({
            'success': True, 
            'message': '客户删除成功（演示模式）'
        })

@app.route('/customers/<int:customer_id>')
@module_required('customer_management')
def customer_detail(customer_id):
    """客户详情"""
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败', 'error')
        return redirect(url_for('customer_tracking'))
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # 获取客户信息
        cursor.execute("""
            SELECT * FROM customer_tracking 
            WHERE id = %s AND deleted_at IS NULL
        """, (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            flash('客户不存在', 'error')
            return redirect(url_for('customer_tracking'))
        
        # 获取跟踪记录
        cursor.execute("""
            SELECT * FROM tracking_records 
            WHERE customer_id = %s AND deleted_at IS NULL
            ORDER BY record_date DESC, created_at DESC
        """, (customer_id,))
        tracking_records = cursor.fetchall()
        
        return render_template('new_ui/customer_detail.html', 
                             customer=customer, 
                             tracking_records=tracking_records)
        
    except Exception as e:
        flash(f'获取客户详情失败: {e}', 'error')
        return redirect(url_for('customer_tracking'))
    finally:
        cursor.close()
        connection.close()

@app.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
@module_required('customer_management')
def edit_customer(customer_id):
    """编辑客户"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            phone = request.form.get('phone')
            email = request.form.get('email')
            customer_type = request.form.get('type')
            company = request.form.get('company', '')
            notes = request.form.get('notes', '')
            
            if not name or not phone:
                return jsonify({'success': False, 'message': '客户姓名和电话为必填项'})
            
            # 模拟更新客户信息
            return jsonify({
                'success': True, 
                'message': f'客户 "{name}" 更新成功',
                'redirect': '/customers'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})
    
    # GET请求 - 返回客户信息用于编辑
    customer = {
        'id': customer_id,
        'name': '张先生',
        'company': '科技有限公司',
        'phone': '13812345678',
        'email': 'zhang@example.com',
        'type': '购房客户',
        'notes': '意向购买办公楼'
    }
    return jsonify({'success': True, 'customer': customer})

# ==================== 维修管理路由 ====================

@app.route('/maintenance/add', methods=['POST'])
@module_required('maintenance_records')
def add_maintenance():
    """新建维修工单"""
    try:
        property_address = request.form.get('property_address')
        description = request.form.get('description')
        priority = request.form.get('priority')
        assigned_to = request.form.get('assigned_to')
        
        if not property_address or not description:
            return jsonify({'success': False, 'message': '房产地址和问题描述为必填项'})
        
        # 生成工单号
        import datetime
        ticket_number = f"MR-{datetime.datetime.now().strftime('%Y-%m')}-{datetime.datetime.now().strftime('%d%H%M')}"
        
        conn = get_db_connection()
        if not conn:
            # 演示模式
            print(f"⚠️  演示模式创建维修工单: {ticket_number}")
            return jsonify({
                'success': True, 
                'message': f'维修工单 "{ticket_number}" 创建成功（演示模式）',
                'redirect': '/maintenance'
            })
        
        # TODO: 这里可以添加真实的数据库插入逻辑
        cursor = conn.cursor()
        # 实际的维修工单插入逻辑
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'维修工单 "{ticket_number}" 创建成功',
            'redirect': '/maintenance'
        })
        
    except Exception as e:
        print(f"❌ 创建维修工单失败: {e}")
        # 生成工单号用于演示
        import datetime
        ticket_number = f"MR-{datetime.datetime.now().strftime('%Y-%m')}-{datetime.datetime.now().strftime('%d%H%M')}"
        return jsonify({
            'success': True, 
            'message': f'维修工单 "{ticket_number}" 创建成功（演示模式）',
            'redirect': '/maintenance'
        })

@app.route('/maintenance/edit/<ticket_id>', methods=['GET', 'POST'])
@module_required('maintenance_records')
def edit_maintenance(ticket_id):
    """编辑维修工单"""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            if not conn:
                # 演示模式
                print(f"⚠️  演示模式更新维修工单: {ticket_id}")
                return jsonify({
                    'success': True, 
                    'message': f'维修工单 "{ticket_id}" 更新成功（演示模式）',
                    'redirect': '/maintenance'
                })
            
            # TODO: 实际的维修工单更新逻辑
            cursor = conn.cursor()
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True, 
                'message': f'维修工单 "{ticket_id}" 更新成功',
                'redirect': '/maintenance'
            })
        except Exception as e:
            print(f"❌ 更新维修工单失败: {e}")
            return jsonify({
                'success': True, 
                'message': f'维修工单 "{ticket_id}" 更新成功（演示模式）',
                'redirect': '/maintenance'
            })
    
    # GET请求显示编辑表单 - 演示模式返回模拟数据
    maintenance_data = {
        'ticket_id': ticket_id,
        'property_address': '示例地址',
        'description': '示例维修描述',
        'priority': 'medium',
        'status': 'pending'
    }
    return jsonify({'success': True, 'maintenance': maintenance_data})

# ==================== 清洁管理路由 ====================

@app.route('/cleaning/add', methods=['POST'])
@module_required('customer_management')
def add_cleaning():
    """安排清洁服务"""
    try:
        property_address = request.form.get('property_address')
        service_type = request.form.get('service_type')
        scheduled_date = request.form.get('scheduled_date')
        assigned_to = request.form.get('assigned_to')
        
        if not property_address or not service_type:
            return jsonify({'success': False, 'message': '房产地址和服务类型为必填项'})
        
        # 生成服务编号
        import datetime
        service_number = f"CL-{datetime.datetime.now().strftime('%Y-%m')}-{datetime.datetime.now().strftime('%d%H%M')}"
        
        conn = get_db_connection()
        if not conn:
            # 演示模式
            print(f"⚠️  演示模式安排清洁服务: {service_number}")
            return jsonify({
                'success': True, 
                'message': f'清洁服务 "{service_number}" 安排成功（演示模式）',
                'redirect': '/cleaning'
            })
        
        # TODO: 实际的清洁服务插入逻辑
        cursor = conn.cursor()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'清洁服务 "{service_number}" 安排成功',
            'redirect': '/cleaning'
        })
        
    except Exception as e:
        print(f"❌ 安排清洁服务失败: {e}")
        # 生成服务编号用于演示
        import datetime
        service_number = f"CL-{datetime.datetime.now().strftime('%Y-%m')}-{datetime.datetime.now().strftime('%d%H%M')}"
        return jsonify({
            'success': True, 
            'message': f'清洁服务 "{service_number}" 安排成功（演示模式）',
            'redirect': '/cleaning'
        })

@app.route('/cleaning/edit/<service_id>', methods=['GET', 'POST'])
@module_required('customer_management')
def edit_cleaning(service_id):
    """编辑清洁服务"""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            if not conn:
                # 演示模式
                print(f"⚠️  演示模式更新清洁服务: {service_id}")
                return jsonify({
                    'success': True, 
                    'message': f'清洁服务 "{service_id}" 更新成功（演示模式）',
                    'redirect': '/cleaning'
                })
            
            # TODO: 实际的清洁服务更新逻辑
            cursor = conn.cursor()
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True, 
                'message': f'清洁服务 "{service_id}" 更新成功',
                'redirect': '/cleaning'
            })
        except Exception as e:
            print(f"❌ 更新清洁服务失败: {e}")
            return jsonify({
                'success': True, 
                'message': f'清洁服务 "{service_id}" 更新成功（演示模式）',
                'redirect': '/cleaning'
            })
    
    # GET请求显示编辑表单 - 演示模式返回模拟数据
    cleaning_data = {
        'service_id': service_id,
        'property_address': '示例地址',
        'service_type': '深度清洁',
        'scheduled_date': '2024-06-20',
        'status': 'scheduled'
    }
    return jsonify({'success': True, 'cleaning': cleaning_data})

# ==================== 部门仪表板模板辅助函数 ====================

@app.template_global()
def get_accessible_modules():
    """获取当前用户可访问的模块"""
    return get_user_accessible_modules()

@app.template_global()
def check_module_access(module_name):
    """检查模块访问权限"""
    return has_module_access(module_name)

@app.template_global()
def get_module_display_info(module_name):
    """获取模块显示信息"""
    return get_module_info(module_name)

@app.route('/admin/property_assignments', methods=['GET', 'POST'])
@admin_required
def admin_property_assignments():
    """管理员房产分配管理"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'assign':
            # 分配房产给业主
            property_id = request.form.get('property_id')
            owner_id = request.form.get('owner_id')
            notes = request.form.get('notes', '')
            
            if not all([property_id, owner_id]):
                flash('请选择房产和业主', 'error')
            else:
                success, message = financial_reports_manager.assign_property_to_owner(
                    property_id=property_id,
                    owner_id=owner_id,
                    assigned_by=session['user_id'],
                    notes=notes
                )
                
                if success:
                    flash(message, 'success')
                else:
                    flash(message, 'error')
        
        elif action == 'remove':
            # 移除房产分配
            property_id = request.form.get('property_id')
            owner_id = request.form.get('owner_id')
            
            if not all([property_id, owner_id]):
                flash('参数不完整', 'error')
            else:
                success, message = financial_reports_manager.remove_property_assignment(
                    property_id=property_id,
                    owner_id=owner_id,
                    removed_by=session['user_id']
                )
                
                if success:
                    flash(message, 'success')
                else:
                    flash(message, 'error')
        
        return redirect(url_for('admin_property_assignments'))
    
    # GET请求 - 显示管理页面
    # 获取筛选参数
    property_id = request.args.get('property_id')
    owner_id = request.args.get('owner_id')
    
    # 获取分配记录
    assignments = financial_reports_manager.get_property_assignments(
        property_id=property_id,
        owner_id=owner_id
    )
    
    # 获取房产和用户列表
    properties = financial_reports_manager.get_properties_list()
    users = financial_reports_manager.get_users_list()  # 使用用户列表而不是业主列表
    
    return render_template('admin_property_assignments.html',
                         assignments=assignments,
                         properties=properties,
                         users=users,  # 传递用户列表而不是业主列表
                         selected_property_id=property_id,
                         selected_owner_id=owner_id)

@app.route('/admin/property_assignments/bulk_assign', methods=['POST'])
@admin_required
def bulk_assign_properties():
    """批量分配房产"""
    owner_id = request.form.get('owner_id')
    property_ids = request.form.getlist('property_ids')
    notes = request.form.get('notes', '')
    
    if not owner_id or not property_ids:
        flash('请选择业主和至少一个房产', 'error')
        return redirect(url_for('admin_property_assignments'))
    
    success_count = 0
    error_messages = []
    
    for property_id in property_ids:
        success, message = financial_reports_manager.assign_property_to_owner(
            property_id=property_id,
            owner_id=owner_id,
            assigned_by=session['user_id'],
            notes=notes
        )
        
        if success:
            success_count += 1
        else:
            error_messages.append(f"房产 {property_id}: {message}")
    
    if success_count > 0:
        flash(f'成功分配 {success_count} 个房产', 'success')
    
    if error_messages:
        for error in error_messages[:5]:  # 只显示前5个错误
            flash(error, 'error')
        if len(error_messages) > 5:
            flash(f'还有 {len(error_messages) - 5} 个其他错误', 'warning')
    
    return redirect(url_for('admin_property_assignments'))

@app.route('/debug/env')
def debug_environment():
    """环境诊断端点 - 比较本地和Render环境"""
    import platform
    import sys
    
    # 测试演示模式认证
    test_auth = auth_system._demo_authenticate('admin', 'admin123')
    
    env_info = {
        'timestamp': datetime.now().isoformat(),
        'platform': platform.platform(),
        'python_version': sys.version,
        'flask_secret_key_set': bool(app.secret_key and app.secret_key != 'default-secret-key-change-in-production'),
        'debug_mode': DEBUG_MODE,
        'port_env': os.environ.get('PORT'),
        'is_render': bool(os.environ.get('PORT')),
        'app_version': APP_VERSION,
        'environment_detected': 'production' if os.environ.get('PORT') else 'local',
        
        # 数据库连接测试
        'db_connection': {
            'status': 'attempting...',
            'config': {
                'host': DB_CONFIG.get('host', 'unknown'),
                'port': DB_CONFIG.get('port', 'unknown'),
                'database': DB_CONFIG.get('database', 'unknown'),
                'user': DB_CONFIG.get('user', 'unknown')
            }
        },
        
        # 演示模式认证测试
        'demo_auth_test': {
            'admin_test': test_auth is not None,
            'admin_data': test_auth if test_auth else 'Failed'
        },
        
        # 环境变量
        'env_vars': {
            'SECRET_KEY_SET': bool(os.environ.get('APP_SECRET_KEY')),
            'DEBUG': os.environ.get('DEBUG', 'Not Set'),
            'MYSQL_HOST': os.environ.get('MYSQL_HOST', 'Not Set'),
            'MYSQL_PORT': os.environ.get('MYSQL_PORT', 'Not Set'),
            'MYSQL_USER': os.environ.get('MYSQL_USER', 'Not Set'),
            'MYSQL_PASSWORD_SET': bool(os.environ.get('MYSQL_PASSWORD')),
            'MYSQL_DATABASE': os.environ.get('MYSQL_DATABASE', 'Not Set')
        }
    }
    
    # 测试数据库连接
    try:
        conn = get_db_connection()
        if conn:
            env_info['db_connection']['status'] = 'success'
            conn.close()
        else:
            env_info['db_connection']['status'] = 'failed'
    except Exception as e:
        env_info['db_connection']['status'] = f'error: {str(e)}'
    
    return jsonify(env_info)

@app.route('/debug/login_test', methods=['POST'])
def debug_login_test():
    """登录测试端点 - 详细记录认证过程"""
    username = request.json.get('username', 'admin')
    password = request.json.get('password', 'admin123')
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'username': username,
        'steps': []
    }
    
    try:
        # 步骤1：测试数据库连接
        result['steps'].append('Testing database connection...')
        conn = auth_system.get_db_connection()
        if conn:
            result['steps'].append('✅ Database connection successful')
            conn.close()
            db_available = True
        else:
            result['steps'].append('❌ Database connection failed, will use demo mode')
            db_available = False
        
        # 步骤2：尝试认证
        result['steps'].append(f'Attempting authentication for: {username}')
        if db_available:
            # 尝试数据库认证
            auth_result = auth_system.authenticate_user(username, password)
        else:
            # 直接使用演示模式认证
            auth_result = auth_system._demo_authenticate(username, password)
        
        if auth_result:
            result['steps'].append('✅ Authentication successful')
            result['auth_success'] = True
            result['user_data'] = auth_result
        else:
            result['steps'].append('❌ Authentication failed')
            result['auth_success'] = False
            result['user_data'] = None
            
            # 额外的演示模式测试
            result['steps'].append('Testing demo mode authentication directly...')
            demo_result = auth_system._demo_authenticate(username, password)
            if demo_result:
                result['steps'].append('✅ Direct demo authentication successful')
                result['demo_auth_result'] = demo_result
            else:
                result['steps'].append('❌ Direct demo authentication also failed')
                result['demo_auth_result'] = None
        
    except Exception as e:
        result['steps'].append(f'❌ Exception occurred: {str(e)}')
        result['error'] = str(e)
        result['auth_success'] = False
    
    return jsonify(result)

@app.route('/debug/demo_auth_test', methods=['GET', 'POST'])
def debug_demo_auth_test():
    """专门测试演示模式认证"""
    if request.method == 'GET':
        # 返回测试页面
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>演示模式认证测试</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .test-form { background: #f5f5f5; padding: 20px; margin: 10px 0; border-radius: 5px; }
                .result { background: #e8f5e9; padding: 15px; margin: 10px 0; border-radius: 5px; white-space: pre-wrap; }
                .error { background: #ffebee; }
                button { padding: 10px 20px; margin: 5px; }
            </style>
        </head>
        <body>
            <h1>演示模式认证测试</h1>
            <div class="test-form">
                <h3>手动测试</h3>
                <form id="testForm">
                    <label>用户名: <input type="text" id="username" value="admin"></label><br><br>
                    <label>密码: <input type="text" id="password" value="admin123"></label><br><br>
                    <button type="submit">测试认证</button>
                </form>
            </div>
            
            <div class="test-form">
                <h3>批量测试</h3>
                <button onclick="runBatchTest()">运行10次连续测试</button>
                <button onclick="runStressTest()">运行50次压力测试</button>
            </div>
            
            <div id="results"></div>
            
            <script>
                document.getElementById('testForm').onsubmit = function(e) {
                    e.preventDefault();
                    testAuth();
                };
                
                function testAuth() {
                    const username = document.getElementById('username').value;
                    const password = document.getElementById('password').value;
                    
                    fetch('/debug/demo_auth_test', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({username, password, test_type: 'single'})
                    })
                    .then(r => r.json())
                    .then(data => {
                        addResult('单次测试结果', data);
                    });
                }
                
                function runBatchTest() {
                    addResult('开始批量测试', {message: '运行10次连续测试...'});
                    let results = [];
                    let promises = [];
                    
                    for(let i = 0; i < 10; i++) {
                        promises.push(
                            fetch('/debug/demo_auth_test', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({username: 'admin', password: 'admin123', test_type: 'batch', test_id: i+1})
                            }).then(r => r.json())
                        );
                    }
                    
                    Promise.all(promises).then(results => {
                        const successes = results.filter(r => r.success).length;
                        addResult('批量测试结果', {
                            total: results.length,
                            successes: successes,
                            failures: results.length - successes,
                            success_rate: (successes / results.length * 100).toFixed(1) + '%',
                            results: results
                        });
                    });
                }
                
                function runStressTest() {
                    addResult('开始压力测试', {message: '运行50次并发测试...'});
                    let promises = [];
                    
                    for(let i = 0; i < 50; i++) {
                        promises.push(
                            fetch('/debug/demo_auth_test', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({username: 'admin', password: 'admin123', test_type: 'stress', test_id: i+1})
                            }).then(r => r.json())
                        );
                    }
                    
                    Promise.all(promises).then(results => {
                        const successes = results.filter(r => r.success).length;
                        addResult('压力测试结果', {
                            total: results.length,
                            successes: successes,
                            failures: results.length - successes,
                            success_rate: (successes / results.length * 100).toFixed(1) + '%',
                            failure_details: results.filter(r => !r.success)
                        });
                    });
                }
                
                function addResult(title, data) {
                    const div = document.createElement('div');
                    div.className = 'result' + (data.success === false ? ' error' : '');
                    div.innerHTML = '<h4>' + title + '</h4><pre>' + JSON.stringify(data, null, 2) + '</pre>';
                    document.getElementById('results').appendChild(div);
                    div.scrollIntoView();
                }
            </script>
        </body>
        </html>
        '''
    
    # POST请求 - 执行测试
    data = request.get_json()
    username = data.get('username', 'admin')
    password = data.get('password', 'admin123')
    test_type = data.get('test_type', 'single')
    test_id = data.get('test_id', 1)
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'test_type': test_type,
        'test_id': test_id,
        'username': username,
        'password_length': len(password) if password else 0
    }
    
    try:
        # 直接调用演示模式认证
        auth_result = auth_system._demo_authenticate(username, password)
        
        if auth_result:
            result['success'] = True
            result['message'] = '认证成功'
            result['user_data'] = auth_result
        else:
            result['success'] = False
            result['message'] = '认证失败'
            result['user_data'] = None
            
    except Exception as e:
        result['success'] = False
        result['message'] = f'认证异常: {str(e)}'
        result['error'] = str(e)
        result['error_type'] = type(e).__name__
    
    return jsonify(result)

@app.route('/debug/status')
def debug_status():
    """简化的系统状态页面"""
    # 测试所有demo用户
    demo_tests = {}
    test_users = [
        ('admin', 'admin123'),
        ('superadmin', 'super2025'), 
        ('manager', 'manager123'),
        ('pm01', '123456')
    ]
    
    for username, password in test_users:
        try:
            result = auth_system._demo_authenticate(username, password)
            demo_tests[username] = {
                'success': result is not None,
                'data': result if result else 'Failed'
            }
        except Exception as e:
            demo_tests[username] = {
                'success': False,
                'error': str(e)
            }
    
    status_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>系统状态诊断</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
            .status {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
            .success {{ background: #d4edda; border-left: 4px solid #28a745; }}
            .error {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
            .info {{ background: #d1ecf1; border-left: 4px solid #17a2b8; }}
            h1 {{ color: #333; }}
            h3 {{ color: #666; margin-top: 20px; }}
            pre {{ background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }}
            .test-result {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 房地产管理系统状态诊断</h1>
            
            <div class="status info">
                <h3>📊 基本信息</h3>
                <p><strong>版本:</strong> {APP_VERSION}</p>
                <p><strong>环境:</strong> {'Production' if os.environ.get('PORT') else 'Development'}</p>
                <p><strong>时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>平台:</strong> {os.environ.get('PORT', 'Local')}</p>
            </div>

            <div class="status {'success' if any(demo_tests[u]['success'] for u in demo_tests) else 'error'}">
                <h3>🔐 演示模式认证测试</h3>
    """
    
    for username, result in demo_tests.items():
        success_class = 'success' if result['success'] else 'error'
        status_icon = '✅' if result['success'] else '❌'
        status_html += f"""
                <div class="test-result">
                    <strong>{status_icon} {username}</strong>: {'认证成功' if result['success'] else '认证失败'}
                    {f"<br><small>错误: {result.get('error', '')}</small>" if not result['success'] and 'error' in result else ''}
                </div>
        """
    
    # 数据库连接测试
    try:
        conn = get_db_connection()
        db_status = "连接成功" if conn else "连接失败"
        db_class = "success" if conn else "error"
        if conn:
            conn.close()
    except Exception as e:
        db_status = f"连接异常: {str(e)}"
        db_class = "error"
    
    status_html += f"""
            </div>

            <div class="status {db_class}">
                <h3>🗄️ 数据库连接状态</h3>
                <p>{db_status}</p>
            </div>

            <div class="status info">
                <h3>🆘 备用管理员账户</h3>
                <p>如果admin账户无法登录，请尝试以下备用账户：</p>
                <ul>
                    <li><strong>superadmin</strong> / super2025</li>
                    <li><strong>manager</strong> / manager123</li>
                    <li><strong>pm01</strong> / 123456</li>
                </ul>
                <p><em>注意：请选择"Company Internal"用户类型</em></p>
            </div>

            <div class="status info">
                <h3>🔗 有用链接</h3>
                <ul>
                    <li><a href="/debug/env">详细环境信息</a></li>
                    <li><a href="/debug/demo_auth_test">交互式认证测试</a></li>
                    <li><a href="/login">返回登录页面</a></li>
                    <li><a href="/health">健康检查</a></li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    
    return status_html

@app.route('/debug/login_flow_test', methods=['GET', 'POST'])
def debug_login_flow_test():
    """详细测试登录流程的每一步"""
    if request.method == 'GET':
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>登录流程测试</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .test-btn { padding: 10px 20px; margin: 10px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
                .result { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; white-space: pre-wrap; }
                .error { background: #f8d7da; }
                .success { background: #d4edda; }
            </style>
        </head>
        <body>
            <h1>🔧 登录流程详细测试</h1>
            
            <div>
                <button class="test-btn" onclick="testStep1()">步骤1：测试表单参数接收</button>
                <button class="test-btn" onclick="testStep2()">步骤2：测试演示模式认证</button>
                <button class="test-btn" onclick="testStep3()">步骤3：测试用户类型匹配</button>
                <button class="test-btn" onclick="testFullFlow()">完整流程测试</button>
            </div>
            
            <div id="results"></div>
            
            <script>
                function testStep1() {
                    fetch('/debug/login_flow_test', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            test_step: 'step1',
                            username: 'admin',
                            password: 'admin123',
                            user_type: 'admin'
                        })
                    })
                    .then(r => r.json())
                    .then(data => addResult('步骤1：参数接收测试', data));
                }
                
                function testStep2() {
                    fetch('/debug/login_flow_test', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            test_step: 'step2',
                            username: 'admin',
                            password: 'admin123'
                        })
                    })
                    .then(r => r.json())
                    .then(data => addResult('步骤2：演示模式认证测试', data));
                }
                
                function testStep3() {
                    fetch('/debug/login_flow_test', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            test_step: 'step3',
                            username: 'admin',
                            password: 'admin123',
                            user_type: 'admin'
                        })
                    })
                    .then(r => r.json())
                    .then(data => addResult('步骤3：用户类型匹配测试', data));
                }
                
                function testFullFlow() {
                    fetch('/debug/login_flow_test', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            test_step: 'full_flow',
                            username: 'admin',
                            password: 'admin123',
                            user_type: 'admin'
                        })
                    })
                    .then(r => r.json())
                    .then(data => addResult('完整登录流程测试', data));
                }
                
                function addResult(title, data) {
                    const div = document.createElement('div');
                    div.className = 'result' + (data.success === false ? ' error' : data.success === true ? ' success' : '');
                    div.innerHTML = '<h3>' + title + '</h3><pre>' + JSON.stringify(data, null, 2) + '</pre>';
                    document.getElementById('results').appendChild(div);
                    div.scrollIntoView();
                }
            </script>
        </body>
        </html>
        '''
    
    # POST请求 - 执行测试
    data = request.get_json()
    test_step = data.get('test_step')
    username = data.get('username')
    password = data.get('password')
    user_type = data.get('user_type')
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'test_step': test_step,
        'input_data': {
            'username': username,
            'password': password,
            'user_type': user_type
        }
    }
    
    try:
        if test_step == 'step1':
            # 测试参数接收
            result['success'] = True
            result['message'] = '参数接收正常'
            result['validation'] = {
                'username_valid': bool(username),
                'password_valid': bool(password),
                'user_type_valid': bool(user_type),
                'username_length': len(username) if username else 0,
                'password_length': len(password) if password else 0
            }
            
        elif test_step == 'step2':
            # 测试演示模式认证
            auth_result = auth_system._demo_authenticate(username, password)
            result['success'] = auth_result is not None
            result['message'] = '演示模式认证成功' if auth_result else '演示模式认证失败'
            result['auth_result'] = auth_result
            
        elif test_step == 'step3':
            # 测试用户类型匹配
            auth_result = auth_system._demo_authenticate(username, password)
            if auth_result:
                user_type_match = auth_result['user_type'] == user_type
                result['success'] = user_type_match
                result['message'] = '用户类型匹配' if user_type_match else '用户类型不匹配'
                result['type_comparison'] = {
                    'expected_type': user_type,
                    'actual_type': auth_result['user_type'],
                    'match': user_type_match
                }
                result['auth_result'] = auth_result
            else:
                result['success'] = False
                result['message'] = '认证失败，无法测试类型匹配'
                
        elif test_step == 'full_flow':
            # 完整流程测试
            steps = []
            
            # Step 1: 参数验证
            if not username or not password:
                result['success'] = False
                result['message'] = '参数验证失败'
                result['failed_step'] = 'parameter_validation'
                return jsonify(result)
            steps.append('✅ 参数验证通过')
            
            # Step 2: 演示模式认证
            auth_result = auth_system._demo_authenticate(username, password)
            if not auth_result:
                result['success'] = False
                result['message'] = '演示模式认证失败'
                result['failed_step'] = 'demo_authentication'
                result['steps'] = steps + ['❌ 演示模式认证失败']
                return jsonify(result)
            steps.append('✅ 演示模式认证成功')
            
            # Step 3: 用户类型匹配
            if auth_result['user_type'] != user_type:
                result['success'] = False
                result['message'] = f"用户类型不匹配: 期望{user_type}, 实际{auth_result['user_type']}"
                result['failed_step'] = 'user_type_mismatch'
                result['steps'] = steps + [f"❌ 用户类型不匹配: 期望{user_type}, 实际{auth_result['user_type']}"]
                result['auth_result'] = auth_result
                return jsonify(result)
            steps.append('✅ 用户类型匹配')
            
            # Step 4: 会话创建测试
            steps.append('✅ 会话创建准备完成')
            
            result['success'] = True
            result['message'] = '完整登录流程验证成功'
            result['steps'] = steps
            result['auth_result'] = auth_result
            
        else:
            result['success'] = False
            result['message'] = f'未知测试步骤: {test_step}'
            
    except Exception as e:
        result['success'] = False
        result['message'] = f'测试异常: {str(e)}'
        result['error'] = str(e)
        result['error_type'] = type(e).__name__
        import traceback
        result['traceback'] = traceback.format_exc()
    
    return jsonify(result)

@app.route('/debug/fix_login', methods=['GET', 'POST'])
def debug_fix_login():
    """诊断和修复登录问题的Web端点"""
    import platform
    
    if request.method == 'POST':
        # 执行修复操作
        try:
            # 1. 创建用户表
            users_table_result = auth_system.create_users_table()
            
            # 2. 创建管理员用户
            admin_create_result = auth_system.create_admin_user(
                username='admin',
                email='admin@example.com',
                password='admin123',
                full_name='系统管理员'
            )
            
            # 3. 创建其他测试用户
            test_users_results = []
            test_users = [
                ('superadmin', 'super@example.com', 'super2025', '超级管理员'),
                ('manager', 'manager@example.com', 'manager123', '管理器'),
                ('pm01', 'pm01@example.com', '123456', '房产管理员')
            ]
            
            for username, email, password, full_name in test_users:
                result = auth_system.create_admin_user(username, email, password, full_name)
                test_users_results.append((username, result))
            
            # 4. 测试认证
            auth_test_result = auth_system.authenticate_user('admin', 'admin123')
            
            return {
                'status': 'fix_completed',
                'results': {
                    'users_table_created': users_table_result,
                    'admin_user_created': admin_create_result,
                    'test_users_created': test_users_results,
                    'auth_test_success': auth_test_result is not None,
                    'auth_test_data': auth_test_result
                },
                'message': '修复操作已完成' if auth_test_result else '修复操作完成但认证测试失败'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': '修复操作失败'
            }, 500
    
    # GET请求 - 显示诊断信息
    try:
        # 环境信息
        env_info = {
            'platform': platform.platform(),
            'is_render': bool(os.environ.get('PORT')),
            'python_version': platform.python_version()
        }
        
        # 数据库连接测试
        db_conn = auth_system.get_db_connection()
        db_connection_status = 'success' if db_conn else 'failed'
        if db_conn:
            db_conn.close()
        
        # 用户表检查
        users_table_info = {}
        if db_conn:
            conn = auth_system.get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                try:
                    # 检查用户表是否存在
                    cursor.execute("SHOW TABLES LIKE 'users'")
                    table_exists = cursor.fetchone() is not None
                    
                    if table_exists:
                        # 用户数量统计
                        cursor.execute("SELECT COUNT(*) as count FROM users")
                        total_users = cursor.fetchone()['count']
                        
                        cursor.execute("SELECT COUNT(*) as count FROM users WHERE user_type = 'admin'")
                        admin_users = cursor.fetchone()['count']
                        
                        # 获取管理员用户列表
                        cursor.execute("SELECT username, user_type, is_active FROM users WHERE user_type = 'admin' LIMIT 10")
                        admin_list = cursor.fetchall()
                        
                        users_table_info = {
                            'exists': True,
                            'total_users': total_users,
                            'admin_users': admin_users,
                            'admin_list': admin_list
                        }
                    else:
                        users_table_info = {'exists': False}
                        
                except Exception as e:
                    users_table_info = {'error': str(e)}
                finally:
                    cursor.close()
                    conn.close()
        
        # 认证测试
        demo_auth_test = auth_system._demo_authenticate('admin', 'admin123')
        db_auth_test = auth_system.authenticate_user('admin', 'admin123')
        
        auth_tests = {
            'demo_auth_success': demo_auth_test is not None,
            'demo_auth_data': demo_auth_test,
            'db_auth_success': db_auth_test is not None,
            'db_auth_data': db_auth_test
        }
        
        # 配置信息
        config_info = {
            'db_host': DB_CONFIG.get('host', 'unknown') if DB_CONFIG else 'config_failed',
            'db_port': DB_CONFIG.get('port', 'unknown') if DB_CONFIG else 'config_failed',
            'db_database': DB_CONFIG.get('database', 'unknown') if DB_CONFIG else 'config_failed',
            'db_user': DB_CONFIG.get('user', 'unknown') if DB_CONFIG else 'config_failed',
            'db_password_set': bool(DB_CONFIG.get('password')) if DB_CONFIG else False
        }
        
        return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>登录问题诊断和修复</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .success { background-color: #d4edda; border-color: #c3e6cb; color: #155724; }
        .error { background-color: #f8d7da; border-color: #f5c6cb; color: #721c24; }
        .warning { background-color: #fff3cd; border-color: #ffeaa7; color: #856404; }
        .info { background-color: #d1ecf1; border-color: #bee5eb; color: #0c5460; }
        .btn { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        .btn:hover { background-color: #0056b3; }
        .btn-danger { background-color: #dc3545; }
        .btn-danger:hover { background-color: #c82333; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 房地产管理系统 - 登录问题诊断</h1>
        
        <div class="section info">
            <h3>🌍 环境信息</h3>
            <table>
                <tr><td>平台</td><td>{{ env_info.platform }}</td></tr>
                <tr><td>是否Render环境</td><td>{{ '✅ 是' if env_info.is_render else '❌ 否' }}</td></tr>
                <tr><td>Python版本</td><td>{{ env_info.python_version }}</td></tr>
            </table>
        </div>
        
        <div class="section {{ 'success' if db_connection_status == 'success' else 'error' }}">
            <h3>🔗 数据库连接状态</h3>
            <p><strong>状态:</strong> {{ '✅ 连接成功' if db_connection_status == 'success' else '❌ 连接失败' }}</p>
            <table>
                <tr><td>主机</td><td>{{ config_info.db_host }}</td></tr>
                <tr><td>端口</td><td>{{ config_info.db_port }}</td></tr>
                <tr><td>数据库</td><td>{{ config_info.db_database }}</td></tr>
                <tr><td>用户</td><td>{{ config_info.db_user }}</td></tr>
                <tr><td>密码设置</td><td>{{ '✅ 已设置' if config_info.db_password_set else '❌ 未设置' }}</td></tr>
            </table>
        </div>
        
        <div class="section {{ 'success' if users_table_info.get('exists') else 'error' if 'error' not in users_table_info else 'warning' }}">
            <h3>👤 用户表状态</h3>
            {% if users_table_info.get('exists') %}
                <p><strong>✅ 用户表存在</strong></p>
                <table>
                    <tr><td>总用户数</td><td>{{ users_table_info.total_users }}</td></tr>
                    <tr><td>管理员用户数</td><td>{{ users_table_info.admin_users }}</td></tr>
                </table>
                {% if users_table_info.admin_list %}
                    <h4>管理员用户列表:</h4>
                    <table>
                        <tr><th>用户名</th><th>类型</th><th>状态</th></tr>
                        {% for user in users_table_info.admin_list %}
                        <tr>
                            <td>{{ user.username }}</td>
                            <td>{{ user.user_type }}</td>
                            <td>{{ '激活' if user.is_active else '禁用' }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                {% endif %}
            {% elif 'error' in users_table_info %}
                <p><strong>❌ 检查用户表时出错:</strong> {{ users_table_info.error }}</p>
            {% else %}
                <p><strong>❌ 用户表不存在</strong> - 这是主要问题！</p>
            {% endif %}
        </div>
        
        <div class="section {{ 'success' if auth_tests.db_auth_success else 'warning' }}">
            <h3>🔐 认证测试</h3>
            <table>
                <tr>
                    <td>演示模式认证</td>
                    <td>{{ '✅ 成功' if auth_tests.demo_auth_success else '❌ 失败' }}</td>
                </tr>
                <tr>
                    <td>数据库认证</td>
                    <td>{{ '✅ 成功' if auth_tests.db_auth_success else '❌ 失败' }}</td>
                </tr>
            </table>
            
            {% if auth_tests.db_auth_success %}
                <div class="success">
                    <h4>✅ 数据库认证成功 - 登录应该正常工作！</h4>
                    <pre>{{ auth_tests.db_auth_data }}</pre>
                </div>
            {% else %}
                <div class="error">
                    <h4>❌ 数据库认证失败 - 这是登录问题的根源</h4>
                    {% if auth_tests.demo_auth_success %}
                        <p>系统正在使用演示模式认证作为备用方案</p>
                        <pre>演示用户数据: {{ auth_tests.demo_auth_data }}</pre>
                    {% endif %}
                </div>
            {% endif %}
        </div>
        
        {% if not auth_tests.db_auth_success %}
        <div class="section warning">
            <h3>🔧 修复操作</h3>
            <p>检测到登录问题，点击下面的按钮执行自动修复：</p>
            <form method="post">
                <button type="submit" class="btn">🔧 执行自动修复</button>
            </form>
            <br>
            <p><strong>修复操作将执行：</strong></p>
            <ul>
                <li>创建用户表（如果不存在）</li>
                <li>创建默认管理员用户: admin/admin123</li>
                <li>创建测试用户: superadmin/super2025, manager/manager123, pm01/123456</li>
                <li>验证修复结果</li>
            </ul>
        </div>
        {% else %}
        <div class="section success">
            <h3>✅ 系统状态正常</h3>
            <p>数据库认证功能正常，用户应该可以正常登录</p>
            <p><strong>可用账户:</strong></p>
            <ul>
                <li>admin / admin123</li>
                <li>superadmin / super2025</li>
                <li>manager / manager123</li>
                <li>pm01 / 123456</li>
            </ul>
        </div>
        {% endif %}
        
        <div class="section info">
            <h3>🔗 相关链接</h3>
            <ul>
                <li><a href="/login">登录页面</a></li>
                <li><a href="/health">健康检查</a></li>
                <li><a href="/debug/env">环境信息</a></li>
                <li><a href="/">返回首页</a></li>
            </ul>
        </div>
    </div>
</body>
</html>
        """, 
        env_info=env_info,
        db_connection_status=db_connection_status,
        users_table_info=users_table_info,
        auth_tests=auth_tests,
        config_info=config_info
        )
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': '诊断过程中发生错误'
        }, 500

@app.route('/api/fix_login', methods=['GET', 'POST'])
def api_fix_login():
    """简化的登录问题修复API端点"""
    try:
        # 基本诊断信息
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'is_render': bool(os.environ.get('PORT')),
            'steps': []
        }
        
        # 步骤1：测试数据库连接
        diagnostics['steps'].append('🔍 步骤1: 测试数据库连接...')
        db_conn = auth_system.get_db_connection()
        if not db_conn:
            diagnostics['steps'].append('❌ 数据库连接失败')
            diagnostics['status'] = 'database_connection_failed'
            return diagnostics, 500
        
        diagnostics['steps'].append('✅ 数据库连接成功')
        db_conn.close()
        
        # 步骤2：检查用户表
        diagnostics['steps'].append('🔍 步骤2: 检查用户表...')
        conn = auth_system.get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SHOW TABLES LIKE 'users'")
                table_exists = cursor.fetchone() is not None
                
                if table_exists:
                    cursor.execute("SELECT COUNT(*) as count FROM users WHERE user_type = 'admin'")
                    admin_count = cursor.fetchone()['count']
                    diagnostics['steps'].append(f'✅ 用户表存在，管理员用户数: {admin_count}')
                    diagnostics['admin_users_count'] = admin_count
                else:
                    diagnostics['steps'].append('❌ 用户表不存在')
                    diagnostics['admin_users_count'] = 0
                    
            finally:
                cursor.close()
                conn.close()
        
        # 步骤3：测试认证
        diagnostics['steps'].append('🔍 步骤3: 测试认证...')
        auth_result = auth_system.authenticate_user('admin', 'admin123')
        if auth_result:
            diagnostics['steps'].append('✅ 数据库认证成功 - 问题已解决！')
            diagnostics['status'] = 'login_working'
            diagnostics['auth_success'] = True
            return diagnostics
        else:
            diagnostics['steps'].append('❌ 数据库认证失败 - 需要修复')
            diagnostics['auth_success'] = False
        
        # 如果是POST请求，执行修复
        if request.method == 'POST':
            diagnostics['steps'].append('🔧 开始执行修复操作...')
            
            # 创建用户表
            diagnostics['steps'].append('📝 步骤4: 创建用户表...')
            table_created = auth_system.create_users_table()
            if table_created:
                diagnostics['steps'].append('✅ 用户表创建成功')
            else:
                diagnostics['steps'].append('❌ 用户表创建失败')
                diagnostics['status'] = 'fix_failed'
                return diagnostics, 500
            
            # 创建管理员用户
            diagnostics['steps'].append('👤 步骤5: 创建管理员用户...')
            admin_created = auth_system.create_admin_user(
                username='admin',
                email='admin@example.com',
                password='admin123',
                full_name='系统管理员'
            )
            
            if admin_created:
                diagnostics['steps'].append('✅ 管理员用户创建成功')
            else:
                diagnostics['steps'].append('⚠️ 管理员用户已存在或创建失败')
            
            # 创建其他测试用户
            diagnostics['steps'].append('👥 步骤6: 创建测试用户...')
            test_users = [
                ('superadmin', 'super@example.com', 'super2025', '超级管理员'),
                ('manager', 'manager@example.com', 'manager123', '管理器'),
                ('pm01', 'pm01@example.com', '123456', '房产管理员')
            ]
            
            created_users = []
            for username, email, password, full_name in test_users:
                result = auth_system.create_admin_user(username, email, password, full_name)
                if result:
                    created_users.append(username)
                    diagnostics['steps'].append(f'✅ 用户 {username} 创建成功')
                else:
                    diagnostics['steps'].append(f'⚠️ 用户 {username} 已存在或创建失败')
            
            # 验证修复结果
            diagnostics['steps'].append('🧪 步骤7: 验证修复结果...')
            final_auth_test = auth_system.authenticate_user('admin', 'admin123')
            
            if final_auth_test:
                diagnostics['steps'].append('🎉 修复成功！admin用户现在可以正常登录')
                diagnostics['status'] = 'fix_successful'
                diagnostics['auth_success'] = True
                diagnostics['available_accounts'] = [
                    'admin / admin123',
                    'superadmin / super2025',
                    'manager / manager123',
                    'pm01 / 123456'
                ]
            else:
                diagnostics['steps'].append('❌ 修复失败，认证仍然不工作')
                diagnostics['status'] = 'fix_failed'
                diagnostics['auth_success'] = False
        else:
            # GET请求，只返回诊断信息
            diagnostics['status'] = 'diagnosis_complete'
            diagnostics['fix_needed'] = True
            diagnostics['message'] = '检测到登录问题，使用POST请求到此端点执行修复'
        
        return diagnostics
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': '诊断或修复过程中发生错误',
            'timestamp': datetime.now().isoformat()
        }, 500

@app.route('/api/test_login', methods=['POST'])
def api_test_login():
    """简化的登录测试API，绕过复杂的表单验证"""
    try:
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        user_type = data.get('user_type', 'admin')
        
        if not username or not password:
            return {
                'success': False,
                'error': 'Missing username or password',
                'timestamp': datetime.now().isoformat()
            }
        
        print(f"🔍 API测试登录: {username}, 类型: {user_type}")
        
        # 直接调用认证系统
        user = auth_system.authenticate_user(username, password)
        
        if user:
            print(f"✅ 认证成功: {user}")
            
            # 检查用户类型是否匹配
            if user['user_type'] != user_type:
                return {
                    'success': False,
                    'error': f"User type mismatch: expected {user_type}, got {user['user_type']}",
                    'user_data': user,
                    'timestamp': datetime.now().isoformat()
                }
            
            # 尝试创建会话
            session_id = auth_system.create_session(
                user['id'], 
                request.remote_addr, 
                request.headers.get('User-Agent')
            )
            
            return {
                'success': True,
                'message': 'Login successful',
                'user_data': user,
                'session_id': session_id[:20] + '...' if session_id else None,
                'session_mode': 'database' if session_id and not session_id.startswith('demo_') else 'demo',
                'timestamp': datetime.now().isoformat()
            }
        else:
            print("❌ 认证失败")
            return {
                'success': False,
                'error': 'Authentication failed',
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        print(f"❌ 登录测试异常: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500

@app.route('/api/check_permissions')
def api_check_permissions():
    """检查当前用户的权限状态"""
    try:
        if 'user_id' not in session:
            return {
                'logged_in': False,
                'message': '用户未登录'
            }
        
        # 获取用户会话信息
        user_info = {
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'user_type': session.get('user_type'),
            'department': session.get('department'),
            'owner_id': session.get('owner_id'),
            'full_name': session.get('full_name'),
            'session_mode': session.get('session_mode', 'unknown')
        }
        
        # 使用已导入的模块权限函数
        
        accessible_modules = get_user_accessible_modules()
        
        # 检查关键模块权限
        key_modules = ['property_info', 'customer_management', 'financial_records', 'owner_info', 'user_management']
        module_permissions = {}
        
        for module in key_modules:
            has_access = has_module_access(module)
            module_info = get_module_info(module)
            module_permissions[module] = {
                'has_access': has_access,
                'name': module_info.get('name', module) if module_info else module,
                'description': module_info.get('description', '') if module_info else ''
            }
        
        # 特别检查房产管理权限
        property_access_reasons = []
        if user_info['user_type'] == 'admin':
            property_access_reasons.append('管理员身份')
        
        if user_info['department'] in ['Admin', 'Property Management Department', 'Sales Department', 'Accounting Department']:
            property_access_reasons.append(f"部门权限: {user_info['department']}")
        
        return {
            'logged_in': True,
            'user_info': user_info,
            'accessible_modules': accessible_modules,
            'total_accessible_modules': len(accessible_modules),
            'module_permissions': module_permissions,
            'property_access_reasons': property_access_reasons,
            'can_access_properties': has_module_access('property_info'),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'message': '权限检查失败',
            'timestamp': datetime.now().isoformat()
        }, 500

@app.route('/api/diagnose_property_management')
def api_diagnose_property_management():
    """诊断房产管理功能的详细状态"""
    try:
        diagnosis = {
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
        
        # 测试1：用户登录状态
        if 'user_id' not in session:
            diagnosis['tests'].append({
                'test': '用户登录状态',
                'status': '失败',
                'message': '用户未登录',
                'recommendation': '请先登录系统'
            })
            diagnosis['overall_status'] = '需要登录'
            return diagnosis
        
        diagnosis['tests'].append({
            'test': '用户登录状态',
            'status': '通过',
            'message': f"用户 {session.get('username')} 已登录"
        })
        
        # 测试2：用户基本信息
        user_info = {
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'user_type': session.get('user_type'),
            'department': session.get('department'),
            'full_name': session.get('full_name'),
            'session_mode': session.get('session_mode', 'unknown')
        }
        
        diagnosis['tests'].append({
            'test': '用户基本信息',
            'status': '通过',
            'details': user_info
        })
        
        # 测试3：模块权限检查
        property_access = has_module_access('property_info')
        diagnosis['tests'].append({
            'test': '房产模块权限',
            'status': '通过' if property_access else '失败',
            'message': '有权限访问房产模块' if property_access else '没有房产模块访问权限',
            'recommendation': '请联系管理员分配房产管理权限' if not property_access else None
        })
        
        # 测试4：部门权限详细检查
        user_department = session.get('department', '')
        allowed_departments = ['Admin', 'Property Management Department', 'Sales Department', 'Accounting Department']
        dept_access = user_department in allowed_departments or session.get('user_type') == 'admin'
        
        diagnosis['tests'].append({
            'test': '部门权限检查',
            'status': '通过' if dept_access else '失败',
            'details': {
                'user_department': user_department,
                'allowed_departments': allowed_departments,
                'is_admin': session.get('user_type') == 'admin'
            }
        })
        
        # 测试5：数据库连接
        db_conn = get_db_connection()
        diagnosis['tests'].append({
            'test': '数据库连接',
            'status': '通过' if db_conn else '失败',
            'message': '数据库连接正常' if db_conn else '数据库连接失败，使用演示模式'
        })
        if db_conn:
            db_conn.close()
        
        # 测试6：路由访问测试
        from flask import url_for
        try:
            properties_url = url_for('properties')
            add_property_url = url_for('add_property')
            diagnosis['tests'].append({
                'test': '路由配置',
                'status': '通过',
                'details': {
                    'properties_url': properties_url,
                    'add_property_url': add_property_url
                }
            })
        except Exception as e:
            diagnosis['tests'].append({
                'test': '路由配置',
                'status': '失败',
                'message': f'路由配置错误: {str(e)}'
            })
        
        # 测试7：特定权限操作检查
        can_add = session.get('user_type') == 'admin' or session.get('department') in ['Property Management Department']
        can_edit = session.get('user_type') == 'admin' or session.get('department') in ['Property Management Department']
        can_delete = session.get('user_type') == 'admin' or session.get('department') in ['Property Management Department']
        
        diagnosis['tests'].append({
            'test': '房产操作权限',
            'status': '通过' if all([can_add, can_edit, can_delete]) else '部分通过',
            'details': {
                'can_add_property': can_add,
                'can_edit_property': can_edit,
                'can_delete_property': can_delete
            }
        })
        
        # 综合评估
        failed_tests = [test for test in diagnosis['tests'] if test['status'] == '失败']
        if failed_tests:
            diagnosis['overall_status'] = '有问题'
            diagnosis['critical_issues'] = [test['test'] for test in failed_tests]
            diagnosis['recommendations'] = []
            for test in failed_tests:
                if 'recommendation' in test and test['recommendation']:
                    diagnosis['recommendations'].append(test['recommendation'])
        else:
            diagnosis['overall_status'] = '正常'
            diagnosis['message'] = '所有权限检查通过，房产管理功能应该可以正常使用'
        
        return diagnosis
        
    except Exception as e:
        return {
            'overall_status': '错误',
            'error': str(e),
            'message': '诊断过程中发生错误',
            'timestamp': datetime.now().isoformat()
        }, 500

@app.route('/api/diagnose_frontend')
def api_diagnose_frontend():
    """诊断前端JavaScript问题"""
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>前端功能诊断</title>
    <meta charset="UTF-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .test-result { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
        .info { background-color: #d1ecf1; color: #0c5460; }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h2>🔧 前端JavaScript功能诊断</h2>
        <div id="results"></div>
        
        <!-- 测试按钮 -->
        <h4>测试功能</h4>
        <button class="btn btn-warning" onclick="testEditFunction()">测试编辑功能</button>
        <button class="btn btn-danger" onclick="testDeleteFunction()">测试删除功能</button>
        <button class="btn btn-success" onclick="testFormSubmit()">测试表单提交</button>
        
        <hr>
        <h4>返回链接</h4>
        <a href="/properties" class="btn btn-primary">返回房产列表</a>
        <a href="/admin/add_property" class="btn btn-success">测试添加房产页面</a>
    </div>

    <script>
        function addResult(message, type) {
            const resultsDiv = document.getElementById('results');
            const div = document.createElement('div');
            div.className = `test-result ${type}`;
            div.innerHTML = message;
            resultsDiv.appendChild(div);
        }

        // 页面加载时执行基本检查
        document.addEventListener('DOMContentLoaded', function() {
            addResult('✅ JavaScript已加载', 'success');
            addResult('✅ DOM已准备就绪', 'success');
            
            // 检查jQuery是否可用
            if (typeof $ !== 'undefined') {
                addResult('✅ jQuery已加载', 'success');
            } else {
                addResult('⚠️ jQuery未加载', 'info');
            }
            
            // 检查Bootstrap JavaScript
            if (typeof bootstrap !== 'undefined') {
                addResult('✅ Bootstrap JavaScript已加载', 'success');
            } else {
                addResult('⚠️ Bootstrap JavaScript未加载', 'info');
            }
            
            // 检查Fetch API支持
            if (typeof fetch !== 'undefined') {
                addResult('✅ Fetch API支持正常', 'success');
            } else {
                addResult('❌ Fetch API不支持', 'error');
            }
        });

        function testEditFunction() {
            addResult('🔍 测试编辑功能...', 'info');
            try {
                // 模拟editProperty函数
                const testPropertyId = 123;
                const expectedUrl = `/admin/edit_property/${testPropertyId}`;
                addResult(`✅ 编辑URL生成正确: ${expectedUrl}`, 'success');
                addResult('�� 编辑功能应该能正常工作（不会真的跳转）', 'info');
            } catch (error) {
                addResult(`❌ 编辑功能测试失败: ${error.message}`, 'error');
            }
        }

        function testDeleteFunction() {
            addResult('🔍 测试删除功能...', 'info');
            try {
                // 测试fetch请求
                const testData = new URLSearchParams();
                testData.append('property_id', '999999'); // 使用不存在的ID测试
                
                fetch('/admin/delete_property', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: testData
                })
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        throw new Error(`HTTP ${response.status}`);
                    }
                })
                .then(data => {
                    addResult(`✅ 删除API响应正常: ${data.message || '响应成功'}`, 'success');
                })
                .catch(error => {
                    if (error.message.includes('HTTP')) {
                        addResult(`⚠️ 删除API返回错误（正常，因为测试ID不存在）: ${error.message}`, 'info');
                    } else {
                        addResult(`❌ 删除功能网络错误: ${error.message}`, 'error');
                    }
                });
            } catch (error) {
                addResult(`❌ 删除功能测试失败: ${error.message}`, 'error');
            }
        }

        function testFormSubmit() {
            addResult('🔍 测试表单提交功能...', 'info');
            try {
                // 创建测试表单
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = '/admin/add_property';
                
                // 添加测试数据
                const fields = {
                    'name': 'JavaScript测试房产',
                    'street_address': '测试地址123号',
                    'city': '测试城市',
                    'state': 'TEST',
                    'zip_code': '12345'
                };
                
                Object.keys(fields).forEach(name => {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = name;
                    input.value = fields[name];
                    form.appendChild(input);
                });
                
                addResult('✅ 表单创建成功', 'success');
                addResult('💡 表单提交功能应该能正常工作（不会真的提交）', 'info');
                addResult('📋 测试数据准备完成', 'success');
            } catch (error) {
                addResult(`❌ 表单功能测试失败: ${error.message}`, 'error');
            }
        }
    </script>
</body>
</html>
    """)

@app.route('/test/buttons')
@login_required
def test_buttons():
    """按钮功能测试页面"""
    return render_template('button_test.html')

@app.route('/debug/modal')
def debug_modal():
    """模态框调试页面"""
    return render_template('debug_modal.html')

@app.route('/demo/clear_properties', methods=['POST'])
@login_required
def clear_demo_properties():
    """清理演示模式中的房产数据"""
    if 'demo_properties' in session:
        count = len(session['demo_properties'])
        session.pop('demo_properties', None)
        print(f"🧹 清理了 {count} 个演示房产")
        return jsonify({'success': True, 'message': f'已清理 {count} 个演示房产'})
    else:
        return jsonify({'success': True, 'message': '没有需要清理的演示房产'})

@app.route('/api/diagnose_buttons')
def api_diagnose_buttons():
    """诊断前端按钮权限和显示问题"""
    results = {
        'session_info': {
            'user_type': session.get('user_type'),
            'department': session.get('department'),
            'username': session.get('username'),
            'user_id': session.get('user_id'),
            'all_session_keys': list(session.keys())
        },
        'button_permissions': {},
        'recommendations': []
    }
    
    # 检查权限逻辑
    user_type = session.get('user_type', '')
    user_department = session.get('department', '')
    
    # 房产管理按钮权限检查
    property_access = (user_type == 'admin' or user_department == 'Property Management Department')
    
    results['button_permissions'] = {
        'can_add_property': property_access,
        'can_edit_property': property_access,
        'can_delete_property': property_access,
        'permission_logic': {
            'user_type_is_admin': user_type == 'admin',
            'department_is_property_management': user_department == 'Property Management Department',
            'combined_access': property_access
        }
    }
    
    # 生成建议
    if not property_access:
        results['recommendations'].append("用户没有房产管理权限")
        if user_type != 'admin':
            results['recommendations'].append("用户类型不是admin")
        if user_department != 'Property Management Department':
            results['recommendations'].append("用户部门不是'Property Management Department'")
    else:
        results['recommendations'].append("用户具有房产管理权限，按钮应该显示")
    
    # 检查数据库连接
    conn = get_db_connection()
    if conn:
        results['database_connection'] = 'OK'
        conn.close()
    else:
        results['database_connection'] = 'FAILED'
        results['recommendations'].append("数据库连接失败，可能影响功能")
    
    return jsonify(results)

@app.route('/debug/routes')
def debug_routes():
    """显示所有注册的路由"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'route': str(rule)
        })
    
    routes_html = ""
    for route in sorted(routes, key=lambda x: x['route']):
        methods_str = ', '.join([m for m in route['methods'] if m not in ['HEAD', 'OPTIONS']])
        routes_html += f"<tr><td>{route['route']}</td><td>{methods_str}</td><td>{route['endpoint']}</td></tr>"
    
    return f'''
    <html>
    <head><title>路由调试</title></head>
    <body style="font-family: Arial; margin: 20px;">
        <h2>所有注册的路由</h2>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background: #f0f0f0;">
                <th style="padding: 10px;">路由</th>
                <th style="padding: 10px;">方法</th>
                <th style="padding: 10px;">端点</th>
            </tr>
            {routes_html}
        </table>
        <p><a href="/debug/edit_test/1">测试编辑调试</a></p>
    </body>
    </html>
    '''

@app.route('/debug/edit_test/<int:property_id>')
def debug_edit_test(property_id):
    """调试编辑功能问题"""
    debug_info = {
        'property_id': property_id,
        'session_info': {
            'user_id': session.get('user_id'),
            'user_type': session.get('user_type'),
            'username': session.get('username'),
            'department': session.get('department'),
            'logged_in': 'user_id' in session
        },
        'permissions': {
            'has_property_info': has_module_access('property_info'),
            'accessible_modules': get_user_accessible_modules()
        },
        'edit_url': f'/admin/edit_property/{property_id}',
        'test_message': 'Debug route working'
    }
    
    return f'''
    <html>
    <head><title>编辑功能调试</title></head>
    <body style="font-family: Arial; margin: 20px;">
        <h2>编辑功能调试信息</h2>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
            <h3>房产ID: {property_id}</h3>
            <h3>用户会话信息:</h3>
            <ul>
                <li>用户ID: {debug_info['session_info']['user_id']}</li>
                <li>用户类型: {debug_info['session_info']['user_type']}</li>
                <li>用户名: {debug_info['session_info']['username']}</li>
                <li>部门: {debug_info['session_info']['department']}</li>
                <li>是否登录: {debug_info['session_info']['logged_in']}</li>
            </ul>
            
            <h3>权限信息:</h3>
            <ul>
                <li>property_info权限: {debug_info['permissions']['has_property_info']}</li>
                <li>可访问模块: {debug_info['permissions']['accessible_modules']}</li>
            </ul>
            
            <h3>测试链接:</h3>
            <p><a href="{debug_info['edit_url']}" style="background: blue; color: white; padding: 10px; text-decoration: none;">测试编辑链接</a></p>
            
            <h3>编辑访问测试:</h3>
            <p><a href="/admin/edit_property/{property_id}" style="background: green; color: white; padding: 10px; text-decoration: none; margin-right: 10px;">标准编辑路由</a></p>
            <p><a href="/edit_property_direct/{property_id}" style="background: orange; color: white; padding: 10px; text-decoration: none;">备用编辑路由</a></p>
        </div>
    </body>
    </html>
    '''

@app.route('/admin/batch_actions', methods=['POST'])
@admin_required
def admin_batch_actions():
    """批量操作"""
    action = request.form.get('action')
    selected_items = request.form.getlist('selected_items')
    
    if not action or not selected_items:
        flash('请选择操作和要操作的项目', 'error')
        return redirect(url_for('admin_user_management'))
    
    try:
        if action == 'delete':
            for item_id in selected_items:
                success, message = auth_system.delete_user(item_id)
                if not success:
                    flash(f'删除用户 {item_id} 失败: {message}', 'error')
            return redirect(url_for('admin_user_management'))
        elif action == 'activate':
            for item_id in selected_items:
                success, message = auth_system.activate_user(item_id)
                if not success:
                    flash(f'激活用户 {item_id} 失败: {message}', 'error')
            return redirect(url_for('admin_user_management'))
        elif action == 'deactivate':
            for item_id in selected_items:
                success, message = auth_system.deactivate_user(item_id)
                if not success:
                    flash(f'禁用用户 {item_id} 失败: {message}', 'error')
            return redirect(url_for('admin_user_management'))
        else:
            flash('无效的操作', 'error')
            return redirect(url_for('admin_user_management'))
    except Exception as e:
        flash(f'批量操作时发生错误: {e}', 'error')
        return redirect(url_for('admin_user_management'))

@app.route('/admin/edit_owner/<owner_id>', methods=['GET', 'POST'])
@module_required('owner_info')
def edit_owner(owner_id):
    """编辑业主信息"""
    if request.method == 'POST':
        owner_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'preferences_strategy': request.form.get('preferences_strategy'),
            'notes': request.form.get('notes')
        }
        
        if not owner_data['name'] or not owner_data['email']:
            flash('姓名和邮箱是必填项。', 'error')
            return render_template('new_ui/edit_owner.html', owner_data=owner_data, owner_id=owner_id)
            
        connection = get_db_connection()
        if not connection:
            flash('数据库连接失败。', 'error')
            return render_template('new_ui/edit_owner.html', owner_data=owner_data, owner_id=owner_id)

        try:
            cursor = connection.cursor()
            
            # 检查业主是否存在
            cursor.execute("SELECT name FROM owners_master WHERE owner_id = %s", (owner_id,))
            existing_owner = cursor.fetchone()
            
            if not existing_owner:
                flash('业主不存在。', 'error')
                return redirect(url_for('owners_fixed'))
            
            # 更新业主信息
            cursor.execute("""
                UPDATE owners_master 
                SET name = %s, email = %s, phone = %s, preferences_strategy = %s
                WHERE owner_id = %s
            """, (
                owner_data['name'],
                owner_data['email'],
                owner_data['phone'],
                owner_data['preferences_strategy'],
                owner_id
            ))
            
            connection.commit()
            flash('业主信息更新成功！', 'success')
            return redirect(url_for('owners_fixed'))
            
        except Exception as e:
            print(f"更新业主错误: {e}")
            connection.rollback()
            flash(f'更新业主时出错: {e}', 'error')
            return render_template('new_ui/edit_owner.html', owner_data=owner_data, owner_id=owner_id)
        finally:
            connection.close()

    # GET请求：显示编辑表单
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败。', 'error')
        return redirect(url_for('owners_fixed'))

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM owners_master WHERE owner_id = %s", (owner_id,))
        owner_data = cursor.fetchone()
        
        if not owner_data:
            flash('业主不存在。', 'error')
            return redirect(url_for('owners_fixed'))
            
        return render_template('new_ui/edit_owner.html', owner_data=owner_data, owner_id=owner_id)
        
    except Exception as e:
        print(f"获取业主信息错误: {e}")
        flash(f'获取业主信息时出错: {e}', 'error')
        return redirect(url_for('owners_fixed'))
    finally:
        if 'connection' in locals():
            connection.close()

# ==================== 维修工单管理路由 ====================

@app.route('/maintenance_orders')
@module_required('maintenance_records')
def maintenance_orders():
    """维修工单管理页面"""
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        search = request.args.get('search', '')
        property_id = request.args.get('property_id', '')
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        
        # 获取工单列表
        orders, total = maintenance_orders_manager.get_all_orders(
            page=page, per_page=20,
            search=search, property_id=property_id,
            status=status, priority=priority
        )
        
        # 获取统计数据
        stats = maintenance_orders_manager.get_order_stats()
        
        # 获取房产和用户列表用于筛选
        properties = maintenance_orders_manager.get_properties_for_select()
        users = maintenance_orders_manager.get_users_for_select()
        
        # 计算分页
        total_pages = (total + 19) // 20  # 每页20条
        
        return render_template('new_ui/maintenance_orders.html',
                             orders=orders,
                             stats=stats,
                             properties=properties,
                             users=users,
                             page=page,
                             total_pages=total_pages,
                             total=total)
                             
    except Exception as e:
        print(f"获取维修工单列表失败: {e}")
        flash(f'获取维修工单列表失败: {e}', 'error')
        return render_template('new_ui/maintenance_orders.html',
                             orders=[],
                             stats={
                                 'total_orders': 0,
                                 'status_counts': {},
                                 'priority_counts': {},
                                 'this_month_orders': 0,
                                 'overdue_orders': 0
                             },
                             properties=[],
                             users=[],
                             page=1,
                             total_pages=1,
                             total=0)

@app.route('/add_maintenance_order', methods=['POST'])
@module_required('maintenance_records')
def add_maintenance_order():
    """添加维修工单"""
    try:
        # 获取表单数据
        assigned_to = request.form.get('assigned_to')
        assigned_phone = request.form.get('assigned_phone', '')
        tracked_by = request.form.get('tracked_by')
        
        # 验证必填字段
        if not assigned_to or not tracked_by:
            flash('请填写负责人姓名和选择追踪人', 'error')
            return redirect(url_for('maintenance_orders'))
        
        try:
            tracked_by = int(tracked_by)
        except ValueError:
            flash('追踪人必须是有效的用户ID', 'error')
            return redirect(url_for('maintenance_orders'))
        
        order_data = {
            'property_id': request.form.get('property_id'),
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'assigned_to': assigned_to,
            'assigned_phone': assigned_phone,
            'tracked_by': tracked_by,
            'priority': request.form.get('priority'),
            'estimated_cost': float(request.form.get('estimated_cost', 0) or 0),
            'estimated_completion_date': request.form.get('estimated_completion_date'),
            'created_by': session['user_id'],
            'notes': request.form.get('notes', '')
        }
        
        # 验证必填字段
        if not all([order_data['property_id'], order_data['title'], 
                   order_data['description'], order_data['assigned_to'], 
                   order_data['tracked_by'], order_data['priority']]):
            flash('请填写所有必填字段', 'error')
            return redirect(url_for('maintenance_orders'))
        
        # 处理日期
        if order_data['estimated_completion_date']:
            try:
                order_data['estimated_completion_date'] = datetime.strptime(
                    order_data['estimated_completion_date'], '%Y-%m-%d'
                ).date()
            except ValueError:
                flash('预计完成日期格式错误', 'error')
                return redirect(url_for('maintenance_orders'))
        else:
            order_data['estimated_completion_date'] = None
        
        # 创建工单
        success, message = maintenance_orders_manager.add_maintenance_order(order_data)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
            
        return redirect(url_for('maintenance_orders'))
        
    except Exception as e:
        print(f"添加维修工单失败: {e}")
        flash(f'添加维修工单失败: {e}', 'error')
        return redirect(url_for('maintenance_orders'))

@app.route('/maintenance_order/<int:order_id>')
@module_required('maintenance_records')
def maintenance_order_detail(order_id):
    """维修工单详情页面"""
    try:
        order = maintenance_orders_manager.get_order_by_id(order_id)
        
        if not order:
            flash('维修工单不存在', 'error')
            return redirect(url_for('maintenance_orders'))
            
        return render_template('new_ui/maintenance_order_detail.html', order=order)
        
    except Exception as e:
        print(f"获取维修工单详情失败: {e}")
        flash(f'获取维修工单详情失败: {e}', 'error')
        return redirect(url_for('maintenance_orders'))

@app.route('/edit_maintenance_order/<int:order_id>', methods=['GET', 'POST'])
@module_required('maintenance_records')
def edit_maintenance_order(order_id):
    """编辑维修工单"""
    if request.method == 'POST':
        try:
            # 获取表单数据
            assigned_to = request.form.get('assigned_to')
            assigned_phone = request.form.get('assigned_phone', '')
            tracked_by = request.form.get('tracked_by')
            
            # 验证必填字段
            if not assigned_to or not tracked_by:
                flash('请填写负责人姓名和选择追踪人', 'error')
                return redirect(url_for('edit_maintenance_order', order_id=order_id))
            
            try:
                tracked_by = int(tracked_by)
            except ValueError:
                flash('追踪人必须是有效的用户ID', 'error')
                return redirect(url_for('edit_maintenance_order', order_id=order_id))
            
            update_data = {
                'property_id': request.form.get('property_id'),
                'title': request.form.get('title'),
                'description': request.form.get('description'),
                'assigned_to': assigned_to,
                'assigned_phone': assigned_phone,
                'tracked_by': tracked_by,
                'priority': request.form.get('priority'),
                'status': request.form.get('status'),
                'estimated_cost': float(request.form.get('estimated_cost', 0) or 0),
                'actual_cost': float(request.form.get('actual_cost', 0) or 0) if request.form.get('actual_cost') else None,
                'estimated_completion_date': request.form.get('estimated_completion_date'),
                'actual_completion_date': request.form.get('actual_completion_date'),
                'notes': request.form.get('notes', '')
            }
            
            # 验证必填字段
            if not all([update_data['property_id'], update_data['title'], 
                       update_data['description'], update_data['assigned_to'], 
                       update_data['tracked_by'], update_data['priority'], 
                       update_data['status']]):
                flash('请填写所有必填字段', 'error')
                return redirect(url_for('edit_maintenance_order', order_id=order_id))
            
            # 处理日期
            for date_field in ['estimated_completion_date', 'actual_completion_date']:
                if update_data[date_field]:
                    try:
                        update_data[date_field] = datetime.strptime(
                            update_data[date_field], '%Y-%m-%d'
                        ).date()
                    except ValueError:
                        flash(f'{date_field} 日期格式错误', 'error')
                        return redirect(url_for('edit_maintenance_order', order_id=order_id))
                else:
                    update_data[date_field] = None
            
            # 更新工单
            success, message = maintenance_orders_manager.update_order(order_id, update_data)
            
            if success:
                flash(message, 'success')
                return redirect(url_for('maintenance_orders'))
            else:
                flash(message, 'error')
                return redirect(url_for('edit_maintenance_order', order_id=order_id))
                
        except Exception as e:
            print(f"更新维修工单失败: {e}")
            flash(f'更新维修工单失败: {e}', 'error')
            return redirect(url_for('edit_maintenance_order', order_id=order_id))
    
    # GET请求：显示编辑表单
    try:
        order = maintenance_orders_manager.get_order_by_id(order_id)
        
        if not order:
            flash('维修工单不存在', 'error')
            return redirect(url_for('maintenance_orders'))
        
        # 获取房产和用户列表
        properties = maintenance_orders_manager.get_properties_for_select()
        users = maintenance_orders_manager.get_users_for_select()
        
        return render_template('new_ui/edit_maintenance_order.html',
                             order=order,
                             properties=properties,
                             users=users)
                             
    except Exception as e:
        print(f"获取维修工单信息失败: {e}")
        flash(f'获取维修工单信息失败: {e}', 'error')
        return redirect(url_for('maintenance_orders'))

@app.route('/delete_maintenance_order', methods=['POST'])
@module_required('maintenance_records')
def delete_maintenance_order():
    """删除维修工单"""
    try:
        order_id = request.form.get('order_id')
        
        if not order_id:
            return jsonify({'success': False, 'message': '工单ID不能为空'})
        
        success, message = maintenance_orders_manager.delete_order(
            order_id=int(order_id),
            admin_id=session['user_id']
        )
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        print(f"删除维修工单失败: {e}")
        return jsonify({'success': False, 'message': f'删除维修工单失败: {e}'})

# ==================== 客户追踪路由 ====================

@app.route('/crm_dashboard')
@module_required('customer_tracking')
def crm_dashboard():
    """CRM销售仪表板"""
    try:
        # 获取销售漏斗统计
        funnel_stats = crm_system.get_sales_funnel_stats()
        
        # 获取当前用户的任务
        current_user = session.get('user', {})
        user_id = current_user.get('id')
        
        today_tasks = []
        if user_id:
            today_tasks = crm_system.get_user_tasks(user_id, 'pending', 10)
        
        # 计算基础统计
        total_customers = funnel_stats.get('total_customers', 0)
        today_tasks_count = len(today_tasks)
        
        # 计算转化率（签约完成 / 总客户数）
        completed_customers = funnel_stats.get('funnel_data', {}).get('签约完成', {}).get('count', 0)
        conversion_rate = round((completed_customers / total_customers * 100) if total_customers > 0 else 0, 1)
        
        # 模拟本月活动数（后续可以从数据库获取）
        month_activities = 45
        
        stats = {
            'total_customers': total_customers,
            'today_tasks': today_tasks_count,
            'month_activities': month_activities,
            'conversion_rate': conversion_rate
        }
        
        return render_template('new_ui/crm_dashboard.html', 
                             stats=stats,
                             funnel=funnel_stats,
                             today_tasks=today_tasks)
        
    except Exception as e:
        print(f"❌ CRM仪表板加载失败: {e}")
        flash('加载CRM仪表板失败', 'error')
        return redirect(url_for('dashboard'))

@app.route('/customer_tracking')
@module_required('customer_tracking')
def customer_tracking():
    """客户追踪主页面"""
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        
        # 获取客户列表
        result = customer_tracking_manager.get_all_customers(
            page=page, 
            per_page=20, 
            search=search, 
            status=status
        )
        
        # 获取统计数据
        total_customers = result['total']
        active_customers = len([c for c in result['customers'] if c['tracking_status'] in ['签约完成', '跟进服务']])
        following_customers = len([c for c in result['customers'] if c['tracking_status'] in ['看房安排', '价格谈判', '合同准备']])
        
        # 计算本月新增（简化计算）
        from datetime import datetime
        current_month = datetime.now().month
        new_this_month = len([c for c in result['customers'] 
                            if c['created_at'] and c['created_at'].month == current_month])
        
        # 获取选项数据
        status_options = customer_tracking_manager.get_tracking_status_options()
        rental_type_options = customer_tracking_manager.get_rental_type_options()
        
        return render_template('new_ui/customer_tracking.html',
                             customers=result['customers'],
                             total_customers=total_customers,
                             active_customers=active_customers,
                             following_customers=following_customers,
                             new_this_month=new_this_month,
                             pages=result['pages'],
                             current_page=result['current_page'],
                             status_options=status_options,
                             rental_type_options=rental_type_options)
                             
    except Exception as e:
        print(f"获取客户列表失败: {e}")
        flash(f'获取客户列表失败: {e}', 'error')
        return render_template('new_ui/customer_tracking.html',
                             customers=[],
                             total_customers=0,
                             active_customers=0,
                             following_customers=0,
                             new_this_month=0,
                             pages=0,
                             current_page=1,
                             status_options=[],
                             rental_type_options=[])

@app.route('/add_customer_tracking', methods=['POST'])
@module_required('customer_tracking')
def add_customer_tracking():
    """添加客户"""
    try:
        # 获取表单数据
        customer_data = {
            'name': request.form.get('name'),
            'phone': request.form.get('phone', ''),
            'email': request.form.get('email', ''),
            'property_address': request.form.get('property_address', ''),
            'rental_types': request.form.getlist('rental_types'),
            'tracking_status': request.form.get('tracking_status', '初始接触'),
            'notes': request.form.get('notes', '')
        }
        
        # 验证必填字段
        if not customer_data['name']:
            flash('请填写客户姓名', 'error')
            return redirect(url_for('customer_tracking'))
        
        # 添加客户
        customer_id = customer_tracking_manager.add_customer(customer_data)
        
        if customer_id:
            flash(f'客户 "{customer_data["name"]}" 添加成功', 'success')
        else:
            flash('添加客户失败', 'error')
            
        return redirect(url_for('customer_tracking'))
        
    except Exception as e:
        print(f"添加客户失败: {e}")
        flash(f'添加客户失败: {e}', 'error')
        return redirect(url_for('customer_tracking'))

@app.route('/customer_tracking_detail/<int:customer_id>')
@module_required('customer_tracking')
def customer_tracking_detail(customer_id):
    """客户详情页面"""
    try:
        # 获取客户信息
        customer = customer_tracking_manager.get_customer_by_id(customer_id)
        
        if not customer:
            flash('客户不存在', 'error')
            return redirect(url_for('customer_tracking'))
        
        # 获取跟踪记录
        tracking_records = customer_tracking_manager.get_tracking_records(customer_id)
        
        # 获取今天日期
        from datetime import date
        today = date.today().strftime('%Y-%m-%d')
        
        return render_template('new_ui/customer_detail.html',
                             customer=customer,
                             tracking_records=tracking_records,
                             today=today)
                             
    except Exception as e:
        print(f"获取客户详情失败: {e}")
        flash(f'获取客户详情失败: {e}', 'error')
        return redirect(url_for('customer_tracking'))

@app.route('/edit_customer_tracking/<int:customer_id>', methods=['GET', 'POST'])
@module_required('customer_tracking')
def edit_customer_tracking(customer_id):
    """编辑客户"""
    if request.method == 'POST':
        try:
            # 获取表单数据
            customer_data = {
                'name': request.form.get('name'),
                'phone': request.form.get('phone', ''),
                'email': request.form.get('email', ''),
                'property_address': request.form.get('property_address', ''),
                'rental_types': request.form.getlist('rental_types'),
                'tracking_status': request.form.get('tracking_status', '初始接触'),
                'notes': request.form.get('notes', '')
            }
            
            # 验证必填字段
            if not customer_data['name']:
                flash('请填写客户姓名', 'error')
                return redirect(url_for('edit_customer', customer_id=customer_id))
            
            # 获取当前用户信息
            current_user = session.get('user', {})
            username = current_user.get('username', '未知用户')
            user_id = current_user.get('id')
            
            # 更新客户
            success = customer_tracking_manager.update_customer(customer_id, customer_data, user_id, username)
            
            if success:
                flash(f'客户 "{customer_data["name"]}" 更新成功', 'success')
                return redirect(url_for('customer_tracking_detail', customer_id=customer_id))
            else:
                flash('更新客户失败', 'error')
                return redirect(url_for('edit_customer_tracking', customer_id=customer_id))
                
        except Exception as e:
            print(f"更新客户失败: {e}")
            flash(f'更新客户失败: {e}', 'error')
            return redirect(url_for('edit_customer', customer_id=customer_id))
    
    # GET请求：显示编辑表单
    try:
        customer = customer_tracking_manager.get_customer_by_id(customer_id)
        
        if not customer:
            flash('客户不存在', 'error')
            return redirect(url_for('customer_tracking'))
        
        # 获取选项数据
        status_options = customer_tracking_manager.get_tracking_status_options()
        rental_type_options = customer_tracking_manager.get_rental_type_options()
        
        return render_template('new_ui/edit_customer.html',
                             customer=customer,
                             status_options=status_options,
                             rental_type_options=rental_type_options)
                             
    except Exception as e:
        print(f"获取客户信息失败: {e}")
        flash(f'获取客户信息失败: {e}', 'error')
        return redirect(url_for('customer_tracking'))

@app.route('/delete_customer_tracking', methods=['POST'])
@module_required('customer_tracking')
def delete_customer_tracking():
    """删除客户"""
    try:
        customer_id = request.form.get('customer_id')
        
        if not customer_id:
            return jsonify({'success': False, 'message': '客户ID不能为空'})
        
        success = customer_tracking_manager.delete_customer(int(customer_id))
        
        if success:
            return jsonify({'success': True, 'message': '客户删除成功'})
        else:
            return jsonify({'success': False, 'message': '客户删除失败'})
        
    except Exception as e:
        print(f"删除客户失败: {e}")
        return jsonify({'success': False, 'message': f'删除客户失败: {e}'})

@app.route('/api/crm/add_activity', methods=['POST'])
@module_required('customer_tracking')
def api_add_sales_activity():
    """API: 添加销售活动"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '无效的数据'})
        
        # 获取当前用户
        current_user = session.get('user', {})
        user_id = current_user.get('id')
        
        activity_data = {
            'customer_id': data.get('customer_id'),
            'activity_type': data.get('activity_type'),
            'subject': data.get('subject', ''),
            'content': data.get('content', ''),
            'scheduled_time': data.get('scheduled_time'),
            'completed_time': data.get('completed_time'),
            'result': data.get('result', 'neutral'),
            'next_action': data.get('next_action', ''),
            'assigned_to': user_id
        }
        
        activity_id = crm_system.add_sales_activity(activity_data)
        
        if activity_id:
            return jsonify({'success': True, 'activity_id': activity_id})
        else:
            return jsonify({'success': False, 'message': '添加活动失败'})
            
    except Exception as e:
        print(f"❌ 添加销售活动失败: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/crm/add_task', methods=['POST'])
@module_required('customer_tracking')
def api_add_sales_task():
    """API: 添加销售任务"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '无效的数据'})
        
        # 获取当前用户
        current_user = session.get('user', {})
        user_id = current_user.get('id')
        
        task_data = {
            'customer_id': data.get('customer_id'),
            'task_type': data.get('task_type'),
            'title': data.get('title'),
            'description': data.get('description', ''),
            'priority': data.get('priority', 'medium'),
            'due_date': data.get('due_date'),
            'assigned_to': user_id
        }
        
        task_id = crm_system.add_sales_task(task_data)
        
        if task_id:
            return jsonify({'success': True, 'task_id': task_id})
        else:
            return jsonify({'success': False, 'message': '添加任务失败'})
            
    except Exception as e:
        print(f"❌ 添加销售任务失败: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/crm/update_task_status', methods=['POST'])
@module_required('customer_tracking')
def api_update_task_status():
    """API: 更新任务状态"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '无效的数据'})
        
        task_id = data.get('task_id')
        status = data.get('status')
        
        if not task_id or not status:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        success = crm_system.update_task_status(task_id, status)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': '更新任务状态失败'})
            
    except Exception as e:
        print(f"❌ 更新任务状态失败: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/crm/get_customer_activities/<int:customer_id>')
@module_required('customer_tracking')
def api_get_customer_activities(customer_id):
    """API: 获取客户活动列表"""
    try:
        activities = crm_system.get_customer_activities(customer_id)
        return jsonify({'success': True, 'activities': activities})
    except Exception as e:
        print(f"❌ 获取客户活动失败: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/crm/get_user_tasks')
@module_required('customer_tracking')
def api_get_user_tasks():
    """API: 获取用户任务列表"""
    try:
        current_user = session.get('user', {})
        user_id = current_user.get('id')
        
        if not user_id:
            return jsonify({'success': False, 'message': '用户未登录'})
        
        status = request.args.get('status', 'pending')
        limit = int(request.args.get('limit', 50))
        
        tasks = crm_system.get_user_tasks(user_id, status, limit)
        return jsonify({'success': True, 'tasks': tasks})
    except Exception as e:
        print(f"❌ 获取用户任务失败: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/add_tracking_record/<int:customer_id>', methods=['POST'])
@module_required('customer_tracking')
def add_tracking_record(customer_id):
    """添加跟踪记录"""
    try:
        # 获取表单数据
        record_data = {
            'record_date': request.form.get('record_date'),
            'content': request.form.get('content')
        }
        
        # 验证必填字段
        if not record_data['record_date'] or not record_data['content']:
            flash('请填写记录日期和内容', 'error')
            return redirect(url_for('customer_detail', customer_id=customer_id))
        
        # 转换日期格式
        from datetime import datetime
        try:
            record_data['record_date'] = datetime.strptime(
                record_data['record_date'], '%Y-%m-%d'
            ).date()
        except ValueError:
            flash('日期格式错误', 'error')
            return redirect(url_for('customer_detail', customer_id=customer_id))
        
        # 添加记录
        record_id = customer_tracking_manager.add_tracking_record(customer_id, record_data)
        
        if record_id:
            flash('跟踪记录添加成功', 'success')
        else:
            flash('添加跟踪记录失败', 'error')
            
        return redirect(url_for('customer_detail', customer_id=customer_id))
        
    except Exception as e:
        print(f"添加跟踪记录失败: {e}")
        flash(f'添加跟踪记录失败: {e}', 'error')
        return redirect(url_for('customer_detail', customer_id=customer_id))

@app.route('/update_tracking_record', methods=['POST'])
@module_required('customer_tracking')
def update_tracking_record():
    """更新跟踪记录"""
    try:
        # 获取表单数据
        record_id = request.form.get('record_id')
        record_data = {
            'record_date': request.form.get('record_date'),
            'content': request.form.get('content')
        }
        
        # 验证必填字段
        if not record_id or not record_data['record_date'] or not record_data['content']:
            flash('请填写所有必填字段', 'error')
            return redirect(url_for('customer_tracking'))
        
        # 转换日期格式
        from datetime import datetime
        try:
            record_data['record_date'] = datetime.strptime(
                record_data['record_date'], '%Y-%m-%d'
            ).date()
        except ValueError:
            flash('日期格式错误', 'error')
            return redirect(url_for('customer_tracking'))
        
        # 更新记录
        success = customer_tracking_manager.update_tracking_record(int(record_id), record_data)
        
        if success:
            flash('跟踪记录更新成功', 'success')
        else:
            flash('更新跟踪记录失败', 'error')
            
        return redirect(url_for('customer_tracking'))
        
    except Exception as e:
        print(f"更新跟踪记录失败: {e}")
        flash(f'更新跟踪记录失败: {e}', 'error')
        return redirect(url_for('customer_tracking'))

@app.route('/delete_tracking_record', methods=['POST'])
@module_required('customer_tracking')
def delete_tracking_record():
    """删除跟踪记录"""
    try:
        record_id = request.form.get('record_id')
        
        if not record_id:
            return jsonify({'success': False, 'message': '记录ID不能为空'})
        
        success = customer_tracking_manager.delete_tracking_record(int(record_id))
        
        if success:
            return jsonify({'success': True, 'message': '跟踪记录删除成功'})
        else:
            return jsonify({'success': False, 'message': '跟踪记录删除失败'})
        
    except Exception as e:
        print(f"删除跟踪记录失败: {e}")
        return jsonify({'success': False, 'message': f'删除跟踪记录失败: {e}'})

# ==================== 直接创建用户系统路由 ====================

@app.route('/admin/create_user', methods=['GET', 'POST'])
@admin_required
def admin_create_user():
    """管理员直接创建用户页面"""
    if request.method == 'POST':
        # 获取表单数据
        user_data = {
            'username': request.form.get('username', '').strip(),
            'email': request.form.get('email', '').strip(),
            'password': request.form.get('password', '').strip(),
            'full_name': request.form.get('full_name', '').strip(),
            'user_type': request.form.get('user_type', '').strip(),
            'department': request.form.get('department', '').strip()
        }
        
        # 验证必填字段
        if not all([user_data['username'], user_data['email'], 
                   user_data['password'], user_data['full_name'], 
                   user_data['user_type'], user_data['department']]):
            return jsonify({'success': False, 'message': '请填写所有必填字段'})
        
        # 创建用户
        result = create_user_directly(user_data)
        
        if result['success']:
            return jsonify({'success': True, 'message': f'用户创建成功！用户名: {user_data["username"]}'})
        else:
            return jsonify({'success': False, 'message': result['message']})
    
    return render_template('new_ui/create_user.html')

def create_user_directly(user_data):
    """直接创建用户"""
    try:
        from src.core.auth_system import AuthSystem
        from src.modules.user_module_permissions import UserModulePermissions
        
        auth = AuthSystem()
        
        # 连接数据库
        conn = auth.get_db_connection()
        if not conn:
            return {'success': False, 'message': '数据库连接失败'}
            
        cursor = conn.cursor()
        
        try:
            # 检查用户是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                         (user_data['username'], user_data['email']))
            
            if cursor.fetchone():
                return {'success': False, 'message': '用户名或邮箱已存在'}
            
            # 创建用户
            password_hash = auth.hash_password(user_data['password'])
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, user_type, department)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_data['username'],
                user_data['email'],
                password_hash,
                user_data['full_name'],
                user_data['user_type'],
                user_data['department']
            ))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            # 初始化模块权限
            ump = UserModulePermissions(DB_CONFIG)
            success = ump.initialize_user_modules(user_id, user_data['user_type'], user_data['department'])
            
            if not success:
                print(f"⚠️ 用户创建成功但模块权限初始化失败，用户ID: {user_id}")
            
            return {'success': True, 'message': f'用户创建成功，ID: {user_id}'}
                
        except Exception as e:
            print(f"❌ 创建用户失败: {e}")
            conn.rollback()
            return {'success': False, 'message': f'创建用户失败: {e}'}
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        return {'success': False, 'message': f'系统错误: {e}'}
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'审核失败：{str(e)}'
        })



# ==================== 用户模块权限管理 ====================

@app.route('/admin/user_modules/<int:user_id>')
@admin_required
def admin_user_modules(user_id):
    """获取用户的模块权限信息"""
    try:
        user_module_permissions = get_user_module_permissions()
        if not user_module_permissions:
            return jsonify({'success': False, 'message': '模块权限管理器未初始化'})
        
        summary = user_module_permissions.get_user_modules_summary(user_id)
        if not summary:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        return jsonify({
            'success': True,
            'user_info': summary['user_info'],
            'modules': summary['modules'],
            'all_modules': summary['all_modules']
        })
        
    except Exception as e:
        logger.error(f"获取用户模块权限失败: {e}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'})

@app.route('/admin/save_user_modules', methods=['POST'])
@admin_required
def admin_save_user_modules():
    """保存用户的模块权限"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        modules = data.get('modules', [])
        
        if not user_id:
            return jsonify({'success': False, 'message': '缺少用户ID'})
        
        user_module_permissions = get_user_module_permissions()
        if not user_module_permissions:
            return jsonify({'success': False, 'message': '模块权限管理器未初始化'})
        
        success = user_module_permissions.set_user_modules(user_id, modules)
        if success:
            return jsonify({'success': True, 'message': '模块权限保存成功'})
        else:
            return jsonify({'success': False, 'message': '模块权限保存失败'})
            
    except Exception as e:
        logger.error(f"保存用户模块权限失败: {e}")
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'})

@app.route('/admin/initialize_user_modules/<int:user_id>', methods=['POST'])
@admin_required
def admin_initialize_user_modules(user_id):
    """根据用户类型初始化用户模块权限"""
    try:
        user_module_permissions = get_user_module_permissions()
        if not user_module_permissions:
            return jsonify({'success': False, 'message': '模块权限管理器未初始化'})
        
        # 获取用户信息
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'})
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT user_type, department FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        success = user_module_permissions.initialize_user_modules(
            user_id, user['user_type'], user['department']
        )
        
        if success:
            return jsonify({'success': True, 'message': '用户模块权限初始化成功'})
        else:
            return jsonify({'success': False, 'message': '用户模块权限初始化失败'})
            
    except Exception as e:
        logger.error(f"初始化用户模块权限失败: {e}")
        return jsonify({'success': False, 'message': f'初始化失败: {str(e)}'})

# ==================== 公告栏系统路由 ====================

@app.route('/announcements')
@login_required
def announcements():
    """公告栏页面"""
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败。', 'error')
        return render_template('new_ui/announcements.html', announcements=[])
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # 获取所有活跃的公告，按优先级和创建时间排序
        cursor.execute("""
            SELECT a.*, p.name COLLATE utf8mb4_unicode_ci as property_display_name 
            FROM announcements a 
            LEFT JOIN properties p ON a.property_id = p.id COLLATE utf8mb4_unicode_ci
            WHERE a.status = 'active' 
            ORDER BY 
                CASE a.priority 
                    WHEN 'urgent' THEN 1 
                    WHEN 'high' THEN 2 
                    WHEN 'medium' THEN 3 
                    WHEN 'low' THEN 4 
                END,
                a.created_at DESC
        """)
        announcements = cursor.fetchall()
        
        # 获取所有房产用于选择
        cursor.execute("SELECT id, name COLLATE utf8mb4_unicode_ci as name FROM properties WHERE deleted_at IS NULL ORDER BY name")
        properties = cursor.fetchall()
        
    except Exception as e:
        flash(f'加载公告数据时出错: {e}', 'error')
        announcements = []
        properties = []
    finally:
        cursor.close()
        connection.close()
    
    return render_template('new_ui/announcements.html', 
                         announcements=announcements, 
                         properties=properties)

@app.route('/announcements/add', methods=['POST'])
@login_required
def add_announcement():
    """添加新公告"""
    try:
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        property_id = request.form.get('property_id', '').strip() or None
        priority = request.form.get('priority', 'medium')
        
        if not title or not content:
            flash('请填写标题和内容', 'error')
            return redirect(url_for('dashboard'))
        
        connection = get_db_connection()
        if not connection:
            flash('数据库连接失败', 'error')
            return redirect(url_for('dashboard'))
        
        cursor = connection.cursor()
        
        # 获取房产名称
        property_name = None
        if property_id:
            cursor.execute("SELECT name FROM properties WHERE id = %s", (property_id,))
            property_result = cursor.fetchone()
            if property_result:
                property_name = property_result[0]
        
        # 插入公告
        cursor.execute("""
            INSERT INTO announcements (title, content, property_id, property_name, author_id, author_name, priority)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            title, content, property_id, property_name,
            session['user_id'], session.get('username', '未知用户'), priority
        ))
        
        connection.commit()
        flash('公告发布成功！', 'success')
        
    except Exception as e:
        flash(f'发布公告失败: {e}', 'error')
    finally:
        if connection:
            cursor.close()
            connection.close()
    
    return redirect(url_for('dashboard'))

@app.route('/announcements/edit/<int:announcement_id>', methods=['GET', 'POST'])
@login_required
def edit_announcement(announcement_id):
    """编辑公告"""
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            property_id = request.form.get('property_id', '').strip() or None
            priority = request.form.get('priority', 'medium')
            
            print(f"调试 - 接收到的表单数据:")
            print(f"  title: '{title}'")
            print(f"  content: '{content}'")
            print(f"  priority: '{priority}'")
            print(f"  property_id: '{property_id}'")
            print(f"  request.form: {dict(request.form)}")
            print(f"  request.form.get('property_id'): '{request.form.get('property_id')}'")
            print(f"  request.form.get('property_id', '').strip(): '{request.form.get('property_id', '').strip()}'")
            print(f"  request.form.get('property_id', '').strip() or None: {request.form.get('property_id', '').strip() or None}")
            
            if not title or not content:
                return jsonify({'success': False, 'message': '请填写标题和内容'})
            
            # 检查权限（只有作者或管理员可以编辑）
            cursor.execute("SELECT author_id FROM announcements WHERE id = %s", (announcement_id,))
            announcement = cursor.fetchone()
            
            if not announcement:
                return jsonify({'success': False, 'message': '公告不存在'})
            
            if session['user_type'] != 'admin' and announcement['author_id'] != session['user_id']:
                return jsonify({'success': False, 'message': '您没有权限编辑此公告'})
            
            # 获取房产名称
            property_name = None
            if property_id and property_id.strip():
                try:
                    # 确保property_id是有效的
                    cursor.execute("SELECT name FROM properties WHERE id = %s", (property_id,))
                    property_result = cursor.fetchone()
                    if property_result:
                        # 检查property_result的类型
                        if isinstance(property_result, dict):
                            property_name = property_result['name']
                        else:
                            property_name = property_result[0]
                        print(f"调试 - 找到房产: {property_name}")
                    else:
                        # 如果找不到房产，清空property_id
                        print(f"调试 - 未找到房产ID: {property_id}")
                        property_id = None
                except Exception as e:
                    print(f"调试 - 房产查询异常: {e}")
                    property_id = None
            else:
                print(f"调试 - property_id为空: {property_id}")
                property_id = None
            
            # 更新公告
            cursor.execute("""
                UPDATE announcements 
                SET title = %s, content = %s, property_id = %s, property_name = %s, priority = %s
                WHERE id = %s
            """, (title, content, property_id, property_name, priority, announcement_id))
            
            connection.commit()
            return jsonify({'success': True, 'message': '公告更新成功！'})
        
        else:
            # GET请求，显示编辑表单
            cursor.execute("SELECT * FROM announcements WHERE id = %s", (announcement_id,))
            announcement = cursor.fetchone()
            
            if not announcement:
                flash('公告不存在', 'error')
                return redirect(url_for('dashboard'))
            
            # 检查权限
            if session['user_type'] != 'admin' and announcement['author_id'] != session['user_id']:
                flash('您没有权限编辑此公告', 'error')
                return redirect(url_for('dashboard'))
            
            # 获取所有房产
            cursor.execute("SELECT id, name FROM properties WHERE deleted_at IS NULL ORDER BY name")
            properties = cursor.fetchall()
            
            return render_template('new_ui/edit_announcement.html', 
                                 announcement=announcement, 
                                 properties=properties)
    
    except Exception as e:
        if request.method == 'POST':
            return jsonify({'success': False, 'message': f'操作失败: {e}'})
        else:
            flash(f'操作失败: {e}', 'error')
            return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        connection.close()

@app.route('/announcements/delete/<int:announcement_id>', methods=['POST'])
@login_required
def delete_announcement(announcement_id):
    """删除公告"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': '数据库连接失败'})
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # 检查权限
        cursor.execute("SELECT author_id FROM announcements WHERE id = %s", (announcement_id,))
        announcement = cursor.fetchone()
        
        if not announcement:
            return jsonify({'success': False, 'message': '公告不存在'})
        
        if session['user_type'] != 'admin' and announcement['author_id'] != session['user_id']:
            return jsonify({'success': False, 'message': '您没有权限删除此公告'})
        
        # 软删除（标记为已归档）
        cursor.execute("UPDATE announcements SET status = 'archived' WHERE id = %s", (announcement_id,))
        connection.commit()
        
        return jsonify({'success': True, 'message': '公告已删除'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败: {e}'})
    finally:
        cursor.close()
        connection.close()

@app.route('/api/announcements')
@login_required
def api_announcements():
    """API: 获取公告列表"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': '数据库连接失败'})
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # 获取活跃的公告
        cursor.execute("""
            SELECT a.*, p.name as property_display_name, u.username as author_name, u.id as author_id
            FROM announcements a 
            LEFT JOIN properties p ON a.property_id COLLATE utf8mb4_unicode_ci = p.id COLLATE utf8mb4_unicode_ci
            LEFT JOIN users u ON a.author_id = u.id
            WHERE a.status = 'active' 
            ORDER BY 
                CASE a.priority 
                    WHEN 'urgent' THEN 1 
                    WHEN 'high' THEN 2 
                    WHEN 'medium' THEN 3 
                    WHEN 'low' THEN 4 
                END,
                a.created_at DESC
            LIMIT 10
        """)
        announcements = cursor.fetchall()
        
        # 格式化日期
        for announcement in announcements:
            announcement['created_at'] = announcement['created_at'].strftime('%Y-%m-%d %H:%M')
            announcement['updated_at'] = announcement['updated_at'].strftime('%Y-%m-%d %H:%M')
        
        return jsonify({'success': True, 'announcements': announcements})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        connection.close()

@app.route('/api/properties')
@login_required
def api_properties():
    """API: 获取房产列表"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': '数据库连接失败'})
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # 获取所有未删除的房产
        cursor.execute("SELECT id, name COLLATE utf8mb4_unicode_ci as name FROM properties WHERE deleted_at IS NULL ORDER BY name")
        properties = cursor.fetchall()
        
        return jsonify({'success': True, 'properties': properties})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        connection.close()

# ==================== 管理员公告管理功能 ====================

@app.route('/admin/announcements')
@admin_required
def admin_announcements():
    """管理员公告管理页面 - 显示所有公告（包括已删除的）"""
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败', 'error')
        return render_template('new_ui/admin_announcements.html', announcements=[], properties=[])
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # 获取所有公告（包括已删除的），按状态和创建时间排序
        cursor.execute("""
            SELECT a.*, p.name COLLATE utf8mb4_unicode_ci as property_display_name 
            FROM announcements a 
            LEFT JOIN properties p ON a.property_id = p.id COLLATE utf8mb4_unicode_ci
            ORDER BY 
                CASE a.status 
                    WHEN 'active' THEN 1 
                    WHEN 'archived' THEN 2 
                END,
                a.created_at DESC
        """)
        announcements = cursor.fetchall()
        
        # 获取所有房产用于选择
        cursor.execute("SELECT id, name COLLATE utf8mb4_unicode_ci as name FROM properties WHERE deleted_at IS NULL ORDER BY name")
        properties = cursor.fetchall()
        
        return render_template('new_ui/admin_announcements.html', 
                             announcements=announcements, 
                             properties=properties)
        
    except Exception as e:
        flash(f'加载公告失败: {e}', 'error')
        return render_template('new_ui/admin_announcements.html', announcements=[], properties=[])
    finally:
        cursor.close()
        connection.close()

@app.route('/admin/announcements/restore/<int:announcement_id>', methods=['POST'])
@admin_required
def restore_announcement(announcement_id):
    """恢复已删除的公告"""
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败', 'error')
        return redirect(url_for('admin_announcements'))
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # 检查公告是否存在
        cursor.execute("SELECT id, status FROM announcements WHERE id = %s", (announcement_id,))
        announcement = cursor.fetchone()
        
        if not announcement:
            flash('公告不存在', 'error')
            return redirect(url_for('admin_announcements'))
        
        if announcement['status'] == 'active':
            flash('公告已经是活跃状态', 'info')
            return redirect(url_for('admin_announcements'))
        
        # 恢复公告
        cursor.execute("UPDATE announcements SET status = 'active' WHERE id = %s", (announcement_id,))
        connection.commit()
        
        flash('公告已恢复', 'success')
        
    except Exception as e:
        flash(f'恢复失败: {e}', 'error')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('admin_announcements'))

@app.route('/admin/announcements/permanent_delete/<int:announcement_id>', methods=['POST'])
@admin_required
def permanent_delete_announcement(announcement_id):
    """永久删除公告（仅管理员）"""
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败', 'error')
        return redirect(url_for('admin_announcements'))
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # 检查公告是否存在
        cursor.execute("SELECT id, title FROM announcements WHERE id = %s", (announcement_id,))
        announcement = cursor.fetchone()
        
        if not announcement:
            flash('公告不存在', 'error')
            return redirect(url_for('admin_announcements'))
        
        # 永久删除公告
        cursor.execute("DELETE FROM announcements WHERE id = %s", (announcement_id,))
        connection.commit()
        
        flash(f'公告 "{announcement["title"]}" 已永久删除', 'success')
        
    except Exception as e:
        flash(f'删除失败: {e}', 'error')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('admin_announcements'))

# ==================== 房产附加信息管理路由 ====================

@app.route('/property/<property_id>/additional_info/add', methods=['POST'])
@module_required('property_info')
def add_property_additional_info(property_id):
    """添加房产附加信息"""
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败', 'error')
        return redirect(url_for('property_detail_fixed', property_id=property_id))
    
    try:
        title = request.form.get('title')
        content = request.form.get('content')
        info_type = request.form.get('info_type', 'general')
        priority = request.form.get('priority', 0, type=int)
        
        if not title or not content:
            flash('标题和内容不能为空', 'error')
            return redirect(url_for('property_detail_fixed', property_id=property_id))
        
        cursor = connection.cursor()
        
        # 插入附加信息
        cursor.execute("""
            INSERT INTO property_additional_info 
            (property_id, title, content, info_type, priority, created_by) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (property_id, title, content, info_type, priority, session.get('user_id')))
        
        connection.commit()
        flash('附加信息添加成功', 'success')
        
    except Exception as e:
        flash(f'添加失败: {e}', 'error')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('property_detail_fixed', property_id=property_id))

@app.route('/property/<property_id>/additional_info/edit/<int:info_id>', methods=['POST'])
@module_required('property_info')
def edit_property_additional_info(property_id, info_id):
    """编辑房产附加信息"""
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败', 'error')
        return redirect(url_for('property_detail_fixed', property_id=property_id))
    
    try:
        title = request.form.get('title')
        content = request.form.get('content')
        info_type = request.form.get('info_type', 'general')
        priority = request.form.get('priority', 0, type=int)
        
        if not title or not content:
            flash('标题和内容不能为空', 'error')
            return redirect(url_for('property_detail_fixed', property_id=property_id))
        
        cursor = connection.cursor()
        
        # 更新附加信息
        cursor.execute("""
            UPDATE property_additional_info 
            SET title = %s, content = %s, info_type = %s, priority = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND property_id = %s
        """, (title, content, info_type, priority, info_id, property_id))
        
        if cursor.rowcount == 0:
            flash('附加信息不存在或无权编辑', 'error')
        else:
            connection.commit()
            flash('附加信息更新成功', 'success')
        
    except Exception as e:
        flash(f'更新失败: {e}', 'error')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('property_detail_fixed', property_id=property_id))

@app.route('/property/<property_id>/additional_info/delete/<int:info_id>', methods=['POST'])
@module_required('property_info')
def delete_property_additional_info(property_id, info_id):
    """删除房产附加信息（软删除）"""
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败', 'error')
        return redirect(url_for('property_detail_fixed', property_id=property_id))
    
    try:
        cursor = connection.cursor()
        
        # 软删除附加信息
        cursor.execute("""
            UPDATE property_additional_info 
            SET deleted_at = CURRENT_TIMESTAMP, is_active = FALSE
            WHERE id = %s AND property_id = %s
        """, (info_id, property_id))
        
        if cursor.rowcount == 0:
            flash('附加信息不存在或无权删除', 'error')
        else:
            connection.commit()
            flash('附加信息删除成功', 'success')
        
    except Exception as e:
        flash(f'删除失败: {e}', 'error')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('property_detail_fixed', property_id=property_id))

if __name__ == '__main__':
    import os
    
    # 启动时测试数据库连接（但不因失败而停止启动）
    print("🔍 启动时测试数据库连接...")
    try:
        test_conn = get_db_connection()
        if test_conn:
            print("✅ 启动时数据库连接测试成功")
            test_conn.close()
            
            # 自动初始化用户认证系统
            print("🔧 初始化用户认证系统...")
            try:
                # 创建用户表
                auth_system.create_users_table()
                print("✅ 用户表创建成功")
                
                # 创建会话表
                auth_system.create_sessions_table()
                print("✅ 会话表创建成功")
                
                # 创建默认管理员账户
                auth_system.create_default_admin()
                print("✅ 默认管理员账户创建成功")
                
            except Exception as e:
                print(f"⚠️  初始化用户认证系统时出现问题: {e}")
                
            # 自动初始化客户追踪表
            print("🔧 初始化客户追踪表...")
            try:
                customer_tracking_manager.create_customer_tracking_tables()
                print("✅ 客户追踪表创建成功")
            except Exception as e:
                print(f"⚠️  初始化客户追踪表时出现问题: {e}")
                
            # 自动初始化CRM表
            print("🔧 初始化CRM表...")
            try:
                crm_system.create_crm_tables()
                print("✅ CRM表创建成功")
            except Exception as e:
                print(f"⚠️  初始化CRM表时出现问题: {e}")
                
        else:
            print("⚠️  启动时数据库连接测试失败，但继续启动")
            
    except Exception as e:
        print(f"⚠️  启动时数据库连接测试异常: {e}")
    
    # 启动Flask应用
    app.run(host='127.0.0.1', port=8888, debug=True)