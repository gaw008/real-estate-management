from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import mysql.connector
import ssl
import os
from datetime import datetime
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

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
        # 尝试多种SSL配置方式
        ssl_configs = [
            # 方式1：使用CA证书
            {
                'ssl_disabled': False,
                'ssl_verify_cert': True,
                'ssl_verify_identity': False,
                'ssl_ca': CA_CERTIFICATE
            },
            # 方式2：禁用证书验证
            {
                'ssl_disabled': False,
                'ssl_verify_cert': False,
                'ssl_verify_identity': False
            },
            # 方式3：完全禁用SSL（不推荐，但作为备用）
            {
                'ssl_disabled': True
            }
        ]
        
        for i, ssl_config in enumerate(ssl_configs, 1):
            try:
                config = {**DB_CONFIG, **ssl_config}
                print(f"尝试连接数据库 (方式{i}): {config['host']}:{config['port']}")
                connection = mysql.connector.connect(**config)
                print(f"✅ 数据库连接成功 (方式{i})")
                
                # 保存成功的配置供后续使用
                global _successful_ssl_config
                _successful_ssl_config = ssl_config
                return connection
            except Exception as ssl_e:
                print(f"❌ 方式{i}连接失败: {ssl_e}")
                continue
        
        # 所有方式都失败
        print("❌ 所有SSL配置方式都失败")
        return None
        
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

@app.route('/health')
def health_check():
    """健康检查端点 - 用于Render部署监控"""
    try:
        db_status = 'connected' if get_db_connection() else 'disconnected'
        return {
            'status': 'healthy',
            'message': '房地产管理系统运行正常',
            'database': db_status,
            'mode': 'online' if db_status == 'connected' else 'demo'
        }, 200
    except Exception as e:
        return {
            'status': 'healthy',
            'message': '房地产管理系统运行正常',
            'database': 'disconnected',
            'mode': 'demo',
            'error': str(e)
        }, 200

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
        print(f"🔍 尝试登录: {username}, 类型: {user_type}")
        user = auth_system.authenticate_user(username, password)
        
        if user:
            print(f"✅ 用户认证成功: {user}")
            # 检查用户类型是否匹配
            if user['user_type'] != user_type:
                print(f"❌ 用户类型不匹配: 期望{user_type}, 实际{user['user_type']}")
                flash(get_text('user_type_mismatch') if get_current_language() == 'en' else '用户类型不匹配', 'error')
                return render_template('login_multilang.html')
            
            print("✅ 用户类型匹配，创建会话...")
            # 创建会话
            session_id = auth_system.create_session(
                user['id'], 
                request.remote_addr, 
                request.headers.get('User-Agent')
            )
            
            if session_id:
                print(f"✅ 会话创建成功: {session_id}")
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
                print("❌ 会话创建失败")
                flash(get_text('session_creation_failed') if get_current_language() == 'en' else '会话创建失败，请重试', 'error')
        else:
            print("❌ 用户认证失败")
            flash('用户名或密码错误', 'error')
    
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
            
            # 验证公司员工必须选择部门
            if not registration_data['department']:
                return render_template('register.html', 
                                     message='公司员工必须选择部门', 
                                     success=False)
            
            # 验证部门是否在允许的列表中
            allowed_departments = ['Admin', 'Sales Department', 'Accounting Department', 'Property Management Department']
            if registration_data['department'] not in allowed_departments:
                return render_template('register.html', 
                                     message='请选择有效的部门', 
                                     success=False)
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
    
    # 预定义部门列表
    departments = [
        '管理员', '销售', '财务', '房屋管理'
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
        
        return render_template('admin_employee_departments.html',
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
    departments = ['管理员', '销售', '财务', '房屋管理', 'Property Management', 'Sales Department', 'Accounting Department', 'Property Management Department']
    
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
                'department': '管理员'
            },
            {
                'id': 2,
                'username': 'sales01',
                'full_name': '张销售',
                'email': 'sales01@company.com', 
                'user_type': 'property_manager',
                'department': '销售'
            },
            {
                'id': 3,
                'username': 'finance01',
                'full_name': '李财务',
                'email': 'finance01@company.com',
                'user_type': 'accounting', 
                'department': '财务'
            },
            {
                'id': 4,
                'username': 'property01',
                'full_name': '王房管',
                'email': 'property01@company.com',
                'user_type': 'property_manager',
                'department': '房屋管理'
            },
            {
                'id': 5,
                'username': 'pm01',
                'full_name': 'PM用户',
                'email': 'pm01@company.com',
                'user_type': 'property_manager',
                'department': 'Property Management'
            }
        ]
    
    if not department_stats:
        print("📊 使用演示部门统计")
        department_stats = [
            {'department': '管理员', 'count': 1},
            {'department': '销售', 'count': 1}, 
            {'department': '财务', 'count': 1},
            {'department': '房屋管理', 'count': 1},
            {'department': 'Property Management', 'count': 1}
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

# ==================== 用户管理功能 ====================

@app.route('/admin/user_management', methods=['GET'])
@admin_required
def admin_user_management():
    """管理员用户管理页面"""
    
    # 获取筛选参数
    user_type_filter = request.args.get('user_type', '')
    search_query = request.args.get('search', '')
    
    conn = get_db_connection()
    if not conn:
        flash('数据库连接失败，请检查数据库配置', 'error')
        return redirect(url_for('dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 构建查询条件
        where_conditions = ["is_active = TRUE"]
        params = []
        
        if user_type_filter:
            where_conditions.append("user_type = %s")
            params.append(user_type_filter)
        
        if search_query:
            where_conditions.append("(username LIKE %s OR full_name LIKE %s OR email LIKE %s)")
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        where_clause = " AND ".join(where_conditions)
        
        # 获取用户列表
        cursor.execute(f"""
            SELECT id, username, full_name, user_type, department, email, created_at, last_login
            FROM users 
            WHERE {where_clause}
            ORDER BY created_at DESC
        """, params)
        
        users = cursor.fetchall()
        
        # 获取用户类型统计
        cursor.execute("""
            SELECT user_type, COUNT(*) as count
            FROM users 
            WHERE is_active = TRUE
            GROUP BY user_type
            ORDER BY count DESC
        """)
        user_type_stats = cursor.fetchall()
        
        return render_template('admin_user_management.html',
                             users=users,
                             user_type_stats=user_type_stats,
                             current_filter=user_type_filter,
                             current_search=search_query)
        
    except Exception as e:
        print(f"❌ 获取用户管理数据失败: {e}")
        flash(f'获取用户数据失败: {str(e)}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/delete_user', methods=['POST'])
@admin_required
def admin_delete_user():
    """删除用户账号"""
    
    user_id = request.form.get('user_id')
    confirm_username = request.form.get('confirm_username')
    
    if not user_id or not confirm_username:
        flash('请提供完整的删除信息', 'error')
        return redirect(url_for('admin_user_management'))
    
    # 防止删除自己的账号
    if int(user_id) == session.get('user_id'):
        flash('不能删除自己的账号', 'error')
        return redirect(url_for('admin_user_management'))
    
    conn = get_db_connection()
    if not conn:
        flash('数据库连接失败', 'error')
        return redirect(url_for('admin_user_management'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 获取要删除的用户信息
        cursor.execute("""
            SELECT id, username, full_name, user_type
            FROM users 
            WHERE id = %s AND is_active = TRUE
        """, (user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            flash('用户不存在或已被删除', 'error')
            return redirect(url_for('admin_user_management'))
        
        # 验证用户名确认
        if user['username'] != confirm_username:
            flash('用户名确认不匹配', 'error')
            return redirect(url_for('admin_user_management'))
        
        # 防止删除最后一个管理员
        if user['user_type'] == 'admin':
            cursor.execute("""
                SELECT COUNT(*) as admin_count
                FROM users 
                WHERE user_type = 'admin' AND is_active = TRUE
            """)
            admin_count = cursor.fetchone()['admin_count']
            
            if admin_count <= 1:
                flash('不能删除最后一个管理员账号', 'error')
                return redirect(url_for('admin_user_management'))
        
        # 软删除用户（将is_active设为FALSE）
        cursor.execute("""
            UPDATE users 
            SET is_active = FALSE, updated_at = NOW()
            WHERE id = %s
        """, (user_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            flash(f'成功删除用户: {user["full_name"]} ({user["username"]})', 'success')
            
            # 记录操作日志
            print(f"🗑️ 管理员 {session.get('username')} 删除了用户: {user['username']} ({user['full_name']})")
        else:
            flash('删除失败', 'error')
    
    except Exception as e:
        print(f"❌ 删除用户失败: {e}")
        flash('删除用户时发生错误', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_user_management'))

@app.route('/demo/user_management', methods=['GET'])
def demo_user_management():
    """演示模式 - 用户管理"""
    
    # 检查权限
    if 'user_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('login'))
    
    if session.get('user_type') != 'admin':
        flash('需要管理员权限', 'error')
        return redirect(url_for('dashboard'))
    
    # 尝试从数据库获取真实数据，失败则使用演示数据
    users = []
    user_type_stats = []
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # 获取筛选参数
            user_type_filter = request.args.get('user_type', '')
            search_query = request.args.get('search', '')
            
            # 构建查询条件
            where_conditions = ["is_active = TRUE"]
            params = []
            
            if user_type_filter:
                where_conditions.append("user_type = %s")
                params.append(user_type_filter)
            
            if search_query:
                where_conditions.append("(username LIKE %s OR full_name LIKE %s OR email LIKE %s)")
                search_pattern = f"%{search_query}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            where_clause = " AND ".join(where_conditions)
            
            # 获取用户列表
            cursor.execute(f"""
                SELECT id, username, full_name, user_type, department, email, created_at, last_login
                FROM users 
                WHERE {where_clause}
                ORDER BY created_at DESC
            """, params)
            
            users = cursor.fetchall() or []
            
            # 获取用户类型统计
            cursor.execute("""
                SELECT user_type, COUNT(*) as count
                FROM users 
                WHERE is_active = TRUE
                GROUP BY user_type
                ORDER BY count DESC
            """)
            user_type_stats = cursor.fetchall() or []
            
            print(f"✅ 演示模式成功获取 {len(users)} 个用户数据")
            
        except Exception as e:
            print(f"⚠️ 演示模式用户管理数据库查询失败: {e}")
            users = []
            user_type_stats = []
        finally:
            cursor.close()
            conn.close()
    
    # 如果数据库查询失败，使用演示数据
    if not users:
        print("📋 使用演示用户数据")
        users = [
            {
                'id': 1,
                'username': 'admin',
                'full_name': '系统管理员',
                'user_type': 'admin',
                'department': '管理员',
                'email': 'admin@company.com',
                'created_at': '2024-01-01 10:00:00',
                'last_login': '2024-01-15 14:30:00'
            },
            {
                'id': 5,
                'username': 'pm01',
                'full_name': 'PM用户',
                'user_type': 'property_manager',
                'department': 'Property Management',
                'email': 'pm01@company.com',
                'created_at': '2024-01-10 09:15:00',
                'last_login': '2024-01-12 16:45:00'
            },
            {
                'id': 2,
                'username': 'sales01',
                'full_name': '张销售',
                'user_type': 'sales',
                'department': '销售',
                'email': 'sales01@company.com',
                'created_at': '2024-01-05 11:20:00',
                'last_login': '2024-01-14 10:15:00'
            }
        ]
    
    if not user_type_stats:
        print("📊 使用演示用户类型统计")
        user_type_stats = [
            {'user_type': 'admin', 'count': 1},
            {'user_type': 'property_manager', 'count': 1},
            {'user_type': 'sales', 'count': 1}
        ]
    
    return render_template('admin_user_management.html',
                         users=users,
                         user_type_stats=user_type_stats,
                         current_filter=request.args.get('user_type', ''),
                         current_search=request.args.get('search', ''))

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

@app.route('/admin/add_property', methods=['GET', 'POST'])
@admin_required
def add_property():
    """添加新房产"""
    if request.method == 'POST':
        # 获取表单数据
        property_data = {
            'name': request.form.get('name'),
            'street_address': request.form.get('street_address'),
            'city': request.form.get('city'),
            'state': request.form.get('state'),
            'zip_code': request.form.get('zip_code'),
            'bedrooms': request.form.get('bedrooms'),
            'bathrooms': request.form.get('bathrooms'),
            'square_feet': request.form.get('square_feet'),
            'property_type': request.form.get('property_type'),
            'year_built': request.form.get('year_built'),
            'monthly_rent': request.form.get('monthly_rent'),
            'description': request.form.get('description')
        }
        
        # 验证必填字段
        required_fields = ['name', 'street_address', 'city', 'state', 'zip_code']
        for field in required_fields:
            if not property_data.get(field):
                flash(f'请填写{field}', 'error')
                return render_template('add_property.html', property_data=property_data)
        
        conn = get_db_connection()
        if not conn:
            flash('数据库连接失败', 'error')
            return render_template('add_property.html', property_data=property_data)
        
        cursor = conn.cursor()
        
        try:
            # 插入房产数据
            insert_query = """
                INSERT INTO properties (
                    name, street_address, city, state, zip_code, 
                    bedrooms, bathrooms, square_feet, property_type, 
                    year_built, monthly_rent, description, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
            """
            
            cursor.execute(insert_query, (
                property_data['name'],
                property_data['street_address'],
                property_data['city'],
                property_data['state'],
                property_data['zip_code'],
                int(property_data['bedrooms']) if property_data['bedrooms'] else None,
                float(property_data['bathrooms']) if property_data['bathrooms'] else None,
                int(property_data['square_feet']) if property_data['square_feet'] else None,
                property_data['property_type'],
                int(property_data['year_built']) if property_data['year_built'] else None,
                float(property_data['monthly_rent']) if property_data['monthly_rent'] else None,
                property_data['description']
            ))
            
            conn.commit()
            flash('房产添加成功', 'success')
            return redirect(url_for('properties'))
            
        except Exception as e:
            print(f"❌ 添加房产失败: {e}")
            flash('添加房产失败', 'error')
            return render_template('add_property.html', property_data=property_data)
        finally:
            cursor.close()
            conn.close()
    
    # GET请求 - 显示添加表单
    return render_template('add_property.html')

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

@app.route('/admin/add_owner', methods=['GET', 'POST'])
@admin_required
def add_owner():
    """添加新业主"""
    if request.method == 'POST':
        # 获取表单数据
        owner_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'preferences_strategy': request.form.get('preferences_strategy'),
            'notes': request.form.get('notes')
        }
        
        # 验证必填字段
        required_fields = ['name', 'email']
        for field in required_fields:
            if not owner_data.get(field):
                flash(f'请填写{field}', 'error')
                return render_template('add_owner.html', owner_data=owner_data)
        
        conn = get_db_connection()
        if not conn:
            flash('数据库连接失败', 'error')
            return render_template('add_owner.html', owner_data=owner_data)
        
        cursor = conn.cursor()
        
        try:
            # 检查邮箱是否已存在
            cursor.execute("SELECT owner_id FROM owners_master WHERE email = %s", (owner_data['email'],))
            if cursor.fetchone():
                flash('该邮箱已被注册', 'error')
                return render_template('add_owner.html', owner_data=owner_data)
            
            # 生成新的owner_id
            cursor.execute("SELECT MAX(owner_id) as max_id FROM owners_master")
            result = cursor.fetchone()
            new_owner_id = (result[0] if result[0] else 0) + 1
            
            # 插入业主数据
            insert_query = """
                INSERT INTO owners_master (
                    owner_id, name, email, phone, preferences_strategy, notes, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, NOW()
                )
            """
            
            cursor.execute(insert_query, (
                new_owner_id,
                owner_data['name'],
                owner_data['email'],
                owner_data['phone'],
                owner_data['preferences_strategy'],
                owner_data['notes']
            ))
            
            conn.commit()
            flash('业主添加成功', 'success')
            return redirect(url_for('owners'))
            
        except Exception as e:
            print(f"❌ 添加业主失败: {e}")
            flash('添加业主失败', 'error')
            return render_template('add_owner.html', owner_data=owner_data)
        finally:
            cursor.close()
            conn.close()
    
    # GET请求 - 显示添加表单
    return render_template('add_owner.html')

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
@admin_required
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
    
    # 当前年月
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    return render_template('admin_financial_reports.html',
                         reports=reports,
                         total_count=total_count,
                         properties=properties,
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

# ==================== 房产分配管理路由 ====================

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
                print("⚠️  继续启动应用，将使用演示模式")
        else:
            print("❌ 启动时数据库连接测试失败")
            print("⚠️  继续启动应用，将使用演示模式")
    except Exception as e:
        print(f"❌ 数据库连接测试异常: {e}")
        print("⚠️  继续启动应用，将使用演示模式")
    
    # 无论数据库连接是否成功，都启动Flask应用
    print("\n🚀 启动Flask应用...")
    port = int(os.environ.get('PORT', 8888))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"📍 服务器将在端口 {port} 启动")
    print(f"🔧 调试模式: {debug}")
    print(f"🌍 访问地址: http://0.0.0.0:{port}")
    
    app.run(debug=debug, host='0.0.0.0', port=port) 