from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import mysql.connector
import ssl
import os
from datetime import datetime
import json

app = Flask(__name__)

# 设置Flask配置
app.secret_key = os.environ.get('APP_SECRET_KEY', 'default-secret-key-change-in-production')

# 导入认证系统
from auth_system import auth_system, login_required, admin_required, owner_required, super_admin_required

# 导入用户注册系统
from user_registration import registration_system

# 导入密码管理系统
from password_manager import password_manager

# 导入多语言系统
from language_manager import language_manager, get_text, get_current_language, is_chinese, is_english

# 导入财务报表系统
from financial_reports import financial_reports_manager

# 注册模板函数
@app.template_filter('format_fee')
def format_fee_filter(rate, fee_type=None):
    """模板过滤器：格式化管理费显示"""
    return format_management_fee(rate, fee_type)

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

# 从配置加载器导入数据库配置
from config_loader import DB_CONFIG, CA_CERTIFICATE

def get_db_connection():
    """获取数据库连接"""
    try:
        # 为Aiven MySQL配置SSL连接
        ssl_config = {
            'ssl_disabled': False,
            'ssl_verify_cert': False,  # 禁用证书验证以解决自签名证书问题
            'ssl_verify_identity': False
        }
        
        # 合并配置
        config = {**DB_CONFIG, **ssl_config}
        
        print(f"尝试连接数据库: {config['host']}:{config['port']}")
        connection = mysql.connector.connect(**config)
        print("✅ 数据库连接成功")
        return connection
    except Exception as e:
        print(f"❌ 数据库连接错误: {e}")
        print(f"配置信息: host={DB_CONFIG.get('host')}, port={DB_CONFIG.get('port')}, database={DB_CONFIG.get('database')}, user={DB_CONFIG.get('user')}")
        return None

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

# ==================== 认证路由 ====================

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
            return render_template('login_multilang.html')
        
        # 验证用户
        user = auth_system.authenticate_user(username, password)
        
        if user:
            # 检查用户类型是否匹配
            if user['user_type'] != user_type:
                flash(get_text('user_type_mismatch') if get_current_language() == 'en' else '用户类型不匹配', 'error')
                return render_template('login_multilang.html')
            
            # 创建会话
            session_id = auth_system.create_session(
                user['id'], 
                request.remote_addr, 
                request.headers.get('User-Agent')
            )
            
            if session_id:
                # 设置会话信息
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['user_type'] = user['user_type']
                session['owner_id'] = user['owner_id']
                session['full_name'] = user['full_name']
                session['session_id'] = session_id
                
                welcome_msg = f'Welcome back, {user["full_name"]}!' if get_current_language() == 'en' else f'欢迎回来，{user["full_name"]}！'
                flash(welcome_msg, 'success')
                return redirect(url_for('dashboard'))
            else:
                flash(get_text('session_creation_failed') if get_current_language() == 'en' else '会话创建失败，请重试', 'error')
        else:
            flash(get_text('invalid_credentials'), 'error')
    
    return render_template('login_multilang.html')

@app.route('/logout')
def logout():
    """用户登出"""
    if 'session_id' in session:
        auth_system.logout_user(session['session_id'])
    
    session.clear()
    flash('您已成功退出登录', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        # 收集表单数据
        registration_data = {
            'username': request.form.get('username'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'full_name': request.form.get('full_name'),
            'user_type': request.form.get('user_type'),
        }
        
        # 验证必填字段
        required_fields = ['username', 'email', 'password', 'full_name', 'user_type']
        for field in required_fields:
            if not registration_data.get(field):
                return render_template('register.html', 
                                     message=f'请填写{field}', 
                                     success=False)
        
        # 验证密码确认
        if request.form.get('password') != request.form.get('confirm_password'):
            return render_template('register.html', 
                                 message='两次输入的密码不一致', 
                                 success=False)
        
        # 根据用户类型收集额外信息
        if registration_data['user_type'] == 'admin':
            registration_data['job_title'] = request.form.get('job_title')
            registration_data['department'] = request.form.get('department')
        else:  # owner
            registration_data['property_address'] = request.form.get('property_address')
            registration_data['phone'] = request.form.get('phone')
        
        # 提交注册申请
        success, message = registration_system.submit_registration(registration_data)
        
        if success:
            return render_template('register.html', 
                                 message='注册申请已提交，请等待管理员审核。审核通过后您将收到邮件通知。', 
                                 success=True)
        else:
            return render_template('register.html', 
                                 message=message, 
                                 success=False)
    
    return render_template('register.html')

# ==================== 管理员审核路由 ====================

@app.route('/admin/registrations')
@super_admin_required
def admin_registrations():
    """管理员查看注册申请列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    per_page = 20
    
    # 获取注册申请列表
    registrations, total_count = registration_system.get_all_registrations(
        status=status if status else None,
        page=page,
        per_page=per_page
    )
    
    # 获取统计信息
    stats = registration_system.get_registration_stats()
    
    # 计算分页信息
    total_pages = (total_count + per_page - 1) // per_page
    
    return render_template('admin_registrations.html',
                         registrations=registrations,
                         stats=stats,
                         current_page=page,
                         total_pages=total_pages,
                         total_count=total_count)

@app.route('/admin/registration/<int:registration_id>')
@super_admin_required
def registration_detail(registration_id):
    """查看注册申请详情"""
    conn = registration_system.get_db_connection()
    if not conn:
        flash('数据库连接失败', 'error')
        return redirect(url_for('admin_registrations'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 获取注册申请详情
        cursor.execute("""
            SELECT ur.*, u.username as reviewed_by_username
            FROM user_registrations ur
            LEFT JOIN users u ON ur.reviewed_by = u.id
            WHERE ur.id = %s
        """, (registration_id,))
        
        registration = cursor.fetchone()
        
        if not registration:
            flash('注册申请不存在', 'error')
            return redirect(url_for('admin_registrations'))
        
        return render_template('registration_detail.html', registration=registration)
        
    except Exception as e:
        print(f"获取注册详情失败: {e}")
        flash('获取注册详情失败', 'error')
        return redirect(url_for('admin_registrations'))
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/review_registration', methods=['POST'])
@super_admin_required
def review_registration():
    """审核注册申请"""
    registration_id = request.form.get('registration_id')
    action = request.form.get('action')
    admin_notes = request.form.get('admin_notes', '')
    
    if not registration_id or not action:
        flash('参数错误', 'error')
        return redirect(url_for('admin_registrations'))
    
    admin_id = session['user_id']
    
    if action == 'approve':
        success, message = registration_system.approve_registration(
            registration_id, admin_id, admin_notes
        )
    elif action == 'reject':
        if not admin_notes.strip():
            flash('拒绝申请时必须填写拒绝理由', 'error')
            return redirect(url_for('registration_detail', registration_id=registration_id))
        
        success, message = registration_system.reject_registration(
            registration_id, admin_id, admin_notes
        )
    else:
        flash('无效的操作', 'error')
        return redirect(url_for('admin_registrations'))
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin_registrations'))

@app.route('/dashboard')
@login_required
def dashboard():
    """用户仪表板"""
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="数据库连接失败")
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        if session['user_type'] == 'admin':
            # 管理员统计
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
            
            return render_template('dashboard_multilang.html', 
                                 stats=stats,
                                 current_date=datetime.now().strftime('%Y年%m月%d日'),
                                 recent_activities=[])
        
        else:
            # 业主统计
            owner_id = session['owner_id']
            
            # 获取业主信息
            cursor.execute("SELECT * FROM owners_master WHERE owner_id = %s", (owner_id,))
            owner_info = cursor.fetchone()
            
            # 业主房产统计
            cursor.execute("""
                SELECT COUNT(*) as property_count
                FROM property_owners 
                WHERE owner_id = %s
            """, (owner_id,))
            property_count = cursor.fetchone()['property_count']
            
            # 活跃房产数量
            cursor.execute("""
                SELECT COUNT(*) as active_properties
                FROM property_owners po
                JOIN properties p ON po.property_id = p.id
                WHERE po.owner_id = %s AND p.is_active = TRUE
            """, (owner_id,))
            active_properties = cursor.fetchone()['active_properties']
            
            owner_stats = {
                'property_count': property_count,
                'total_revenue': 0,  # 这里可以后续添加收入计算
                'active_properties': active_properties
            }
            
            return render_template('dashboard_multilang.html',
                                 owner_info=owner_info,
                                 owner_stats=owner_stats,
                                 current_date=datetime.now().strftime('%Y年%m月%d日'),
                                 recent_activities=[])
    
    except Exception as e:
        print(f"仪表板数据加载错误: {e}")
        return render_template('error.html', error="数据加载失败")
    finally:
        cursor.close()
        conn.close()

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

@app.route('/properties')
@admin_required
def properties():
    """房产列表页面"""
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="数据库连接失败")
    
    cursor = conn.cursor(dictionary=True)
    
    # 获取筛选参数
    city = request.args.get('city', '')
    state = request.args.get('state', '')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 12
    
    # 构建查询条件
    where_conditions = []
    params = []
    
    if city:
        where_conditions.append("city LIKE %s")
        params.append(f"%{city}%")
    
    if state:
        where_conditions.append("state = %s")
        params.append(state)
    
    if search:
        where_conditions.append("(name LIKE %s OR street_address LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])
    
    where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    
    # 获取总数
    count_query = f"SELECT COUNT(*) as count FROM properties{where_clause}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()['count']
    
    # 获取房产数据
    offset = (page - 1) * per_page
    query = f"""
        SELECT p.*, f.cleaning_fee, f.management_fee_rate, f.management_fee_type
        FROM properties p
        LEFT JOIN finance f ON p.id = f.property_id
        {where_clause}
        ORDER BY p.created_at DESC
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, params + [per_page, offset])
    properties_list = cursor.fetchall()
    
    # 获取筛选选项
    cursor.execute("SELECT DISTINCT state FROM properties ORDER BY state")
    states = [row['state'] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT city FROM properties ORDER BY city")
    cities = [row['city'] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    # 计算分页信息
    total_pages = (total_count + per_page - 1) // per_page
    
    return render_template('properties_fixed.html',
                         properties=properties_list,
                         states=states,
                         cities=cities,
                         current_page=page,
                         total_pages=total_pages,
                         total_count=total_count,
                         filters={
                             'city': city,
                             'state': state,
                             'search': search
                         },
                         format_management_fee=format_management_fee)

@app.route('/property/<property_id>')
@admin_required
def property_detail(property_id):
    """房产详情页面"""
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="数据库连接失败")
    
    cursor = conn.cursor(dictionary=True)
    
    # 获取房产详情
    cursor.execute("""
        SELECT p.*, f.cleaning_fee, f.management_fee_rate, f.management_fee_type, f.contract_signed_date
        FROM properties p
        LEFT JOIN finance f ON p.id = f.property_id
        WHERE p.id = %s
    """, (property_id,))
    
    property_data = cursor.fetchone()
    if not property_data:
        cursor.close()
        conn.close()
        return render_template('error.html', error="房产不存在")
    
    # 获取业主信息
    cursor.execute("""
        SELECT om.owner_id, om.name, om.phone, om.email, om.preferences_strategy
        FROM property_owners po
        JOIN owners_master om ON po.owner_id = om.owner_id
        WHERE po.property_id = %s
    """, (property_id,))
    owners = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('property_detail_fixed.html', 
                         property=property_data, 
                         owners=owners,
                         format_management_fee=format_management_fee)

@app.route('/owners')
@admin_required
def owners():
    """业主列表页面"""
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="数据库连接失败")
    
    cursor = conn.cursor(dictionary=True)
    
    # 获取筛选参数
    search = request.args.get('search', '')
    strategy = request.args.get('strategy', '')
    page = int(request.args.get('page', 1))
    per_page = 15
    
    # 构建查询条件
    where_conditions = []
    params = []
    
    if search:
        where_conditions.append("(name LIKE %s OR email LIKE %s OR phone LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    
    if strategy:
        where_conditions.append("preferences_strategy = %s")
        params.append(strategy)
    
    where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    
    # 获取总数
    count_query = f"SELECT COUNT(*) as count FROM owners_master{where_clause}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()['count']
    
    # 获取业主数据及其房产数量
    offset = (page - 1) * per_page
    query = f"""
        SELECT om.*, COUNT(po.property_id) as property_count
        FROM owners_master om
        LEFT JOIN property_owners po ON om.owner_id = po.owner_id
        {where_clause}
        GROUP BY om.owner_id
        ORDER BY om.name
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, params + [per_page, offset])
    owners_list = cursor.fetchall()
    
    # 获取策略选项
    cursor.execute("SELECT DISTINCT preferences_strategy FROM owners_master WHERE preferences_strategy IS NOT NULL ORDER BY preferences_strategy")
    strategies = [row['preferences_strategy'] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    # 计算分页信息
    total_pages = (total_count + per_page - 1) // per_page
    
    return render_template('owners_fixed.html',
                         owners=owners_list,
                         strategies=strategies,
                         current_page=page,
                         total_pages=total_pages,
                         total_count=total_count,
                         filters={
                             'search': search,
                             'strategy': strategy
                         },
                         format_management_fee=format_management_fee)

@app.route('/owner/<owner_id>')
@admin_required
def owner_detail(owner_id):
    """业主详情页面"""
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="数据库连接失败")
    
    cursor = conn.cursor(dictionary=True)
    
    # 获取业主详情
    cursor.execute("SELECT * FROM owners_master WHERE owner_id = %s", (owner_id,))
    owner_data = cursor.fetchone()
    if not owner_data:
        cursor.close()
        conn.close()
        return render_template('error.html', error="业主不存在")
    
    # 获取业主的房产
    cursor.execute("""
        SELECT p.id, p.name, p.city, p.state, p.beds, p.property_size, 
               f.cleaning_fee, f.management_fee_rate, f.management_fee_type
        FROM property_owners po
        JOIN properties p ON po.property_id = p.id
        LEFT JOIN finance f ON p.id = f.property_id
        WHERE po.owner_id = %s
        ORDER BY p.name
    """, (owner_id,))
    properties = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('owner_detail_fixed.html', 
                         owner=owner_data, 
                         properties=properties,
                         format_management_fee=format_management_fee)

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
    """用户修改密码"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证输入
        if not all([current_password, new_password, confirm_password]):
            return render_template('change_password.html', 
                                 message='请填写所有字段', 
                                 success=False)
        
        if new_password != confirm_password:
            return render_template('change_password.html', 
                                 message='两次输入的新密码不一致', 
                                 success=False)
        
        if len(new_password) < 8:
            return render_template('change_password.html', 
                                 message='新密码长度至少8位', 
                                 success=False)
        
        # 修改密码
        success, message = password_manager.change_password(
            user_id=session['user_id'],
            old_password=current_password,
            new_password=new_password,
            changed_by=session['user_id'],
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        if success:
            # 获取密码修改历史
            password_history = password_manager.get_password_change_history(session['user_id'], 5)
            return render_template('change_password.html', 
                                 message='密码修改成功！', 
                                 success=True,
                                 password_history=password_history)
        else:
            return render_template('change_password.html', 
                                 message=message, 
                                 success=False)
    
    # GET请求 - 显示修改密码页面
    password_history = password_manager.get_password_change_history(session['user_id'], 5)
    return render_template('change_password.html', password_history=password_history)

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
        # 搜索用户（排除当前管理员）
        search_sql = """
            SELECT id, username, email, user_type, full_name,
                   DATE_FORMAT(created_at, '%Y-%m-%d') as created_at
            FROM users 
            WHERE (username LIKE %s OR email LIKE %s OR full_name LIKE %s)
            AND id != %s
            AND user_type != 'admin'
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
@admin_required
def admin_financial_reports():
    """管理员财务报表管理"""
    if request.method == 'POST':
        # 添加财务报表
        owner_id = request.form.get('owner_id')
        report_year = int(request.form.get('report_year'))
        report_month = int(request.form.get('report_month'))
        report_title = request.form.get('report_title')
        onedrive_link = request.form.get('onedrive_link')
        notes = request.form.get('notes', '')
        
        # 验证输入
        if not all([owner_id, report_year, report_month, report_title, onedrive_link]):
            flash('请填写所有必填字段', 'error')
        else:
            success, message = financial_reports_manager.add_financial_report(
                owner_id=owner_id,
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
    owner_id = request.args.get('owner_id')
    
    # 获取报表列表
    reports, total_count = financial_reports_manager.get_all_reports(
        year=int(year) if year else None,
        month=int(month) if month else None,
        owner_id=owner_id,
        page=1,
        per_page=50
    )
    
    # 获取业主列表
    owners = financial_reports_manager.get_owners_list()
    
    # 获取统计信息
    stats = financial_reports_manager.get_report_stats()
    
    # 当前年月
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    return render_template('admin_financial_reports.html',
                         reports=reports,
                         total_count=total_count,
                         owners=owners,
                         stats=stats,
                         current_year=current_year,
                         current_month=current_month)

@app.route('/admin/delete_financial_report', methods=['POST'])
@admin_required
def delete_financial_report():
    """删除财务报表"""
    report_id = request.form.get('report_id')
    
    if not report_id:
        flash('报表ID不能为空', 'error')
    else:
        success, message = financial_reports_manager.delete_report(
            report_id=int(report_id),
            admin_id=session['user_id']
        )
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
    
    return redirect(url_for('admin_financial_reports'))

@app.route('/owner/financial_reports')
@owner_required
def owner_financial_reports():
    """房东查看财务报表"""
    # 获取筛选参数
    year = request.args.get('year')
    
    # 获取当前业主的报表
    reports = financial_reports_manager.get_owner_reports(
        owner_id=session['owner_id'],
        year=int(year) if year else None,
        limit=50
    )
    
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

if __name__ == '__main__':
    import os
    
    # 启动时测试数据库连接
    print("🔍 启动时测试数据库连接...")
    test_conn = get_db_connection()
    if test_conn:
        print("✅ 启动时数据库连接测试成功")
        test_conn.close()
        
        # 自动初始化用户认证系统
        print("🔧 初始化用户认证系统...")
        try:
            # 创建用户表
            if auth_system.create_users_table():
                print("✅ 用户表创建/检查完成")
            
            # 初始化用户注册系统
            print("🔧 初始化用户注册系统...")
            if registration_system.create_registration_tables():
                print("✅ 用户注册表创建/检查完成")
            
            # 初始化密码管理系统
            print("🔧 初始化密码管理系统...")
            if password_manager.create_password_tables():
                print("✅ 密码管理表创建/检查完成")
                
                # 初始化财务报表系统
                print("🔧 初始化财务报表系统...")
                # 导入财务报表系统
                if financial_reports_manager.create_reports_table():
                    print("✅ 财务报表表创建/检查完成")
                else:
                    print("❌ 财务报表表创建失败")
                
                # 创建默认管理员账户
                admin_created = auth_system.create_admin_user(
                    username="admin",
                    email="admin@company.com", 
                    password="admin123",
                    full_name="系统管理员"
                )
                
                if admin_created:
                    print("✅ 默认管理员账户创建成功")
                    print("   用户名: admin")
                    print("   密码: admin123")
                else:
                    print("ℹ️  管理员账户已存在")
                
                # 为现有业主创建用户账户
                if auth_system.create_owner_users_from_existing():
                    print("✅ 业主用户账户创建/更新完成")
                else:
                    print("⚠️  业主用户账户创建失败")
                
                # 调试用户表状态
                print("\n📋 用户表状态:")
                auth_system.debug_users_table()
                    
            else:
                print("❌ 用户表创建失败")
                
        except Exception as e:
            print(f"❌ 用户系统初始化失败: {e}")
    else:
        print("❌ 启动时数据库连接测试失败")
    
    port = int(os.environ.get('PORT', 8888))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port) 