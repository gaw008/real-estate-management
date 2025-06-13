#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
房地产数据可视化查询系统
基于Streamlit构建的交互式数据分析平台
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import psycopg2
import os
from dotenv import load_dotenv
import altair as alt
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 导入AI查询助手
try:
    from ai_query_assistant import ai_assistant
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# 加载环境变量
load_dotenv()

# 页面配置
st.set_page_config(
    page_title="房地产数据分析系统",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .reportview-container {
        margin-top: -2em;
    }
    .stDeployButton {display:none;}
    .stDecoration {display:none;}
    
    .metric-container {
        background-color: #f0f2f6;
        border: 2px solid #e1e5e9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    h1 {
        color: #1f77b4;
        font-family: 'Arial', sans-serif;
    }
    
    .stSelectbox label {
        font-weight: bold;
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_database_connection():
    """创建数据库连接"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'real_estate_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', '5432')
        )
        return conn
    except Exception as e:
        st.error(f"数据库连接失败: {e}")
        return None

@st.cache_data(ttl=300)  # 缓存5分钟
def load_data(query):
    """执行SQL查询并返回数据"""
    try:
        # 每次查询都创建新连接，避免缓存连接对象
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'real_estate_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', '5432')
        )
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"查询执行失败: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_summary_stats():
    """获取数据概览统计"""
    queries = {
        'properties_count': "SELECT COUNT(*) as count FROM properties",
        'owners_count': "SELECT COUNT(DISTINCT owner_id) as count FROM owners", 
        'finance_count': "SELECT COUNT(*) as count FROM finance",
        'cities_count': "SELECT COUNT(DISTINCT city) as count FROM properties WHERE city IS NOT NULL"
    }
    
    stats = {}
    for key, query in queries.items():
        df = load_data(query)
        stats[key] = df['count'].iloc[0] if not df.empty else 0
    
    return stats

def main():
    """主函数"""
    
    # 标题和介绍
    st.title("🏠 房地产数据分析系统")
    st.markdown("---")
    
    # 侧边栏
    st.sidebar.title("📊 导航菜单")
    
    # 构建菜单选项
    menu_options = ["📈 数据概览", "🔍 数据查询", "📊 可视化分析", "🏠 房产分析", "👥 业主分析", "💰 财务分析"]
    
    # 如果AI助手可用，添加到菜单
    if AI_AVAILABLE:
        menu_options.insert(1, "🤖 AI智能问答")
    
    page = st.sidebar.selectbox("选择功能页面", menu_options)
    
    # 根据选择显示不同页面
    if page == "📈 数据概览":
        show_overview()
    elif page == "🤖 AI智能问答":
        show_ai_assistant()
    elif page == "🔍 数据查询":
        show_data_query()
    elif page == "📊 可视化分析":
        show_visualization()
    elif page == "🏠 房产分析":
        show_property_analysis()
    elif page == "👥 业主分析":
        show_owner_analysis()
    elif page == "💰 财务分析":
        show_finance_analysis()

def show_overview():
    """显示数据概览页面"""
    st.header("📈 数据概览")
    
    # 获取统计数据
    stats = get_summary_stats()
    
    # 创建指标卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🏠 房产总数",
            value=f"{stats['properties_count']:,}",
            delta=f"覆盖{stats['cities_count']}个城市"
        )
    
    with col2:
        st.metric(
            label="👥 业主数量",
            value=f"{stats['owners_count']:,}",
            delta="独立业主"
        )
    
    with col3:
        st.metric(
            label="💰 财务记录",
            value=f"{stats['finance_count']:,}",
            delta="财务数据"
        )
    
    with col4:
        completion_rate = round((stats['finance_count'] / max(stats['properties_count'], 1)) * 100, 1)
        st.metric(
            label="📊 数据完整度",
            value=f"{completion_rate}%",
            delta="财务数据覆盖率"
        )
    
    st.markdown("---")
    
    # 快速统计图表
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌍 城市分布")
        city_query = """
        SELECT city, COUNT(*) as property_count
        FROM properties 
        WHERE city IS NOT NULL AND city != 'nan'
        GROUP BY city 
        ORDER BY property_count DESC 
        LIMIT 10
        """
        city_data = load_data(city_query)
        
        if not city_data.empty:
            fig = px.pie(
                city_data, 
                values='property_count', 
                names='city',
                title="前10个城市房产分布"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏗️ 房型分布")
        layout_query = """
        SELECT layout, COUNT(*) as count
        FROM properties 
        WHERE layout IS NOT NULL AND layout != 'nan'
        GROUP BY layout 
        ORDER BY count DESC
        LIMIT 8
        """
        layout_data = load_data(layout_query)
        
        if not layout_data.empty:
            fig = px.bar(
                layout_data,
                x='layout',
                y='count',
                title="房型分布统计",
                color='count',
                color_continuous_scale='viridis'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

def show_data_query():
    """显示数据查询页面"""
    st.header("🔍 数据查询")
    
    # 查询类型选择
    query_type = st.selectbox(
        "选择查询类型",
        ["预定义查询", "自定义SQL查询", "高级筛选"]
    )
    
    if query_type == "预定义查询":
        show_predefined_queries()
    elif query_type == "自定义SQL查询":
        show_custom_query()
    else:
        show_advanced_filter()

def show_predefined_queries():
    """显示预定义查询"""
    st.subheader("📋 预定义查询")
    
    query_options = {
        "所有房产信息": "SELECT * FROM properties LIMIT 100",
        "所有业主信息": "SELECT * FROM owners LIMIT 100", 
        "所有财务记录": "SELECT * FROM finance LIMIT 100",
        "房产与业主关联": """
            SELECT p.id, p.name, p.city, p.state, p.layout, o.name as owner_name, o.email
            FROM properties p
            LEFT JOIN owners o ON p.owner_id = o.owner_id
            LIMIT 50
        """,
        "加州房产统计": """
            SELECT city, COUNT(*) as property_count, 
                   AVG(CAST(property_size AS NUMERIC)) as avg_size
            FROM properties 
            WHERE state = 'California'
            GROUP BY city
            ORDER BY property_count DESC
        """,
        "有效合同统计": """
            SELECT COUNT(*) as total_contracts,
                   COUNT(CASE WHEN contract_signed_date IS NOT NULL THEN 1 END) as signed_contracts
            FROM finance
        """
    }
    
    selected_query = st.selectbox("选择预定义查询", list(query_options.keys()))
    
    if st.button("执行查询"):
        df = load_data(query_options[selected_query])
        if not df.empty:
            st.success(f"查询成功！返回 {len(df)} 行数据")
            st.dataframe(df, use_container_width=True)
            
            # 提供下载选项
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 下载CSV文件",
                data=csv,
                file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("查询未返回任何数据")

def show_custom_query():
    """显示自定义SQL查询"""
    st.subheader("🔧 自定义SQL查询")
    
    # SQL编辑器
    sql_query = st.text_area(
        "输入SQL查询语句",
        value="SELECT * FROM properties LIMIT 10;",
        height=150,
        help="请输入有效的SQL查询语句。注意：只支持SELECT查询。"
    )
    
    # 表结构参考
    with st.expander("📚 表结构参考"):
        st.markdown("""
        **表名和主要字段：**
        
        **properties表：**
        - id, name, street_address, city, state, layout
        - property_size, occupancy, beds, wifi_name, trash_day
        
        **owners表：**
        - id, owner_id, name, phone, email
        
        **finance表：**
        - id, owner_clean, manegement_fee_pct, contract_signed_date
        """)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🚀 执行查询", type="primary"):
            if sql_query.strip().upper().startswith('SELECT'):
                try:
                    df = load_data(sql_query)
                    if not df.empty:
                        st.success(f"查询成功！返回 {len(df)} 行数据")
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.warning("查询未返回任何数据")
                except Exception as e:
                    st.error(f"查询执行失败: {e}")
            else:
                st.error("只支持SELECT查询语句")

def show_advanced_filter():
    """显示高级筛选"""
    st.subheader("🎯 高级筛选")
    
    # 筛选选项
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 城市筛选
        cities = load_data("SELECT DISTINCT city FROM properties WHERE city IS NOT NULL ORDER BY city")
        selected_cities = st.multiselect(
            "选择城市",
            options=cities['city'].tolist() if not cities.empty else [],
            default=[]
        )
    
    with col2:
        # 州筛选
        states = load_data("SELECT DISTINCT state FROM properties WHERE state IS NOT NULL ORDER BY state")
        selected_states = st.multiselect(
            "选择州",
            options=states['state'].tolist() if not states.empty else [],
            default=[]
        )
    
    with col3:
        # 房型筛选
        layouts = load_data("SELECT DISTINCT layout FROM properties WHERE layout IS NOT NULL ORDER BY layout")
        selected_layouts = st.multiselect(
            "选择房型",
            options=layouts['layout'].tolist() if not layouts.empty else [],
            default=[]
        )
    
    # 构建筛选查询
    base_query = "SELECT * FROM properties WHERE 1=1"
    conditions = []
    
    if selected_cities:
        city_list = "', '".join(selected_cities)
        conditions.append(f"city IN ('{city_list}')")
    
    if selected_states:
        state_list = "', '".join(selected_states)
        conditions.append(f"state IN ('{state_list}')")
    
    if selected_layouts:
        layout_list = "', '".join(selected_layouts)
        conditions.append(f"layout IN ('{layout_list}')")
    
    if conditions:
        final_query = base_query + " AND " + " AND ".join(conditions) + " LIMIT 100"
    else:
        final_query = base_query + " LIMIT 100"
    
    if st.button("应用筛选"):
        df = load_data(final_query)
        if not df.empty:
            st.success(f"筛选结果：{len(df)} 条记录")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("没有符合条件的记录")

def show_visualization():
    """显示可视化分析页面"""
    st.header("📊 可视化分析")
    
    # 图表类型选择
    chart_type = st.selectbox(
        "选择图表类型",
        ["地理分布图", "趋势分析图", "对比分析图", "相关性分析"]
    )
    
    if chart_type == "地理分布图":
        show_geographic_analysis()
    elif chart_type == "趋势分析图":
        show_trend_analysis()
    elif chart_type == "对比分析图":
        show_comparison_analysis()
    else:
        show_correlation_analysis()

def show_geographic_analysis():
    """显示地理分布分析"""
    st.subheader("🗺️ 地理分布分析")
    
    # 加载地理数据
    geo_query = """
    SELECT state, city, COUNT(*) as property_count,
           AVG(CASE WHEN property_size != '' AND property_size IS NOT NULL 
               THEN CAST(property_size AS NUMERIC) END) as avg_size
    FROM properties 
    WHERE state IS NOT NULL AND city IS NOT NULL
    GROUP BY state, city
    ORDER BY property_count DESC
    """
    
    geo_data = load_data(geo_query)
    
    if not geo_data.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # 按州分组的条形图
            state_summary = geo_data.groupby('state').agg({
                'property_count': 'sum',
                'avg_size': 'mean'
            }).reset_index()
            
            fig = px.bar(
                state_summary,
                x='state',
                y='property_count',
                title="各州房产数量分布",
                color='property_count',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 城市气泡图
            fig = px.scatter(
                geo_data,
                x='property_count',
                y='avg_size',
                size='property_count',
                color='state',
                hover_name='city',
                title="城市房产规模vs数量",
                labels={'property_count': '房产数量', 'avg_size': '平均面积'}
            )
            st.plotly_chart(fig, use_container_width=True)

def show_property_analysis():
    """显示房产分析页面"""
    st.header("🏠 房产分析")
    
    # 房产概览统计
    property_stats_query = """
    SELECT 
        COUNT(*) as total_properties,
        COUNT(DISTINCT city) as cities_count,
        COUNT(DISTINCT state) as states_count,
        COUNT(DISTINCT layout) as layout_types,
        AVG(CASE WHEN property_size != '' AND property_size IS NOT NULL 
            THEN CAST(property_size AS NUMERIC) END) as avg_property_size
    FROM properties
    """
    
    stats_df = load_data(property_stats_query)
    
    if not stats_df.empty:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("总房产数", f"{stats_df['total_properties'].iloc[0]:,}")
        with col2:
            st.metric("覆盖城市", f"{stats_df['cities_count'].iloc[0]}")
        with col3:
            st.metric("覆盖州", f"{stats_df['states_count'].iloc[0]}")
        with col4:
            st.metric("房型种类", f"{stats_df['layout_types'].iloc[0]}")
        with col5:
            avg_size = stats_df['avg_property_size'].iloc[0]
            st.metric("平均面积", f"{avg_size:.0f} sq ft" if pd.notna(avg_size) else "N/A")
    
    st.markdown("---")
    
    # 详细分析
    tab1, tab2, tab3 = st.tabs(["房型分析", "地区分析", "设施分析"])
    
    with tab1:
        show_layout_analysis()
    
    with tab2:
        show_regional_analysis()
    
    with tab3:
        show_amenity_analysis()

def show_layout_analysis():
    """房型分析"""
    st.subheader("🏗️ 房型分析")
    
    layout_query = """
    SELECT layout, COUNT(*) as count,
           AVG(CASE WHEN property_size != '' AND property_size IS NOT NULL 
               THEN CAST(property_size AS NUMERIC) END) as avg_size,
           AVG(CASE WHEN occupancy != '' AND occupancy IS NOT NULL 
               THEN CAST(occupancy AS NUMERIC) END) as avg_occupancy
    FROM properties 
    WHERE layout IS NOT NULL AND layout != 'nan'
    GROUP BY layout 
    ORDER BY count DESC
    """
    
    layout_data = load_data(layout_query)
    
    if not layout_data.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                layout_data.head(10),
                x='layout',
                y='count',
                title="房型数量分布",
                color='count',
                color_continuous_scale='viridis'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 平均面积对比
            filtered_data = layout_data[layout_data['avg_size'].notna()].head(10)
            if not filtered_data.empty:
                fig = px.scatter(
                    filtered_data,
                    x='avg_size',
                    y='avg_occupancy',
                    size='count',
                    color='layout',
                    title="房型面积vs入住人数",
                    labels={'avg_size': '平均面积', 'avg_occupancy': '平均入住人数'}
                )
                st.plotly_chart(fig, use_container_width=True)

def show_regional_analysis():
    """地区分析"""
    st.subheader("🌍 地区分析")
    
    regional_query = """
    SELECT state, city, COUNT(*) as property_count,
           COUNT(CASE WHEN wifi_name IS NOT NULL AND wifi_name != 'nan' THEN 1 END) as wifi_coverage
    FROM properties 
    WHERE state IS NOT NULL AND city IS NOT NULL
    GROUP BY state, city
    ORDER BY property_count DESC
    LIMIT 20
    """
    
    regional_data = load_data(regional_query)
    
    if not regional_data.empty:
        # WiFi覆盖率
        regional_data['wifi_rate'] = (regional_data['wifi_coverage'] / regional_data['property_count'] * 100).round(1)
        
        fig = px.sunburst(
            regional_data,
            path=['state', 'city'],
            values='property_count',
            title="地区房产分布（州-城市层级）"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # WiFi覆盖率分析
        st.subheader("📶 WiFi覆盖率分析")
        fig2 = px.bar(
            regional_data.head(15),
            x='wifi_rate',
            y='city',
            orientation='h',
            title="各城市WiFi覆盖率",
            color='wifi_rate',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig2, use_container_width=True)

def show_amenity_analysis():
    """设施分析"""
    st.subheader("🏪 设施分析")
    
    amenity_query = """
    SELECT 
        COUNT(CASE WHEN wifi_name IS NOT NULL AND wifi_name != 'nan' THEN 1 END) as has_wifi,
        COUNT(CASE WHEN front_door_code IS NOT NULL AND front_door_code != 'nan' THEN 1 END) as has_door_code,
        COUNT(CASE WHEN storage_code IS NOT NULL AND storage_code != 'nan' THEN 1 END) as has_storage,
        COUNT(*) as total
    FROM properties
    """
    
    amenity_data = load_data(amenity_query)
    
    if not amenity_data.empty:
        total = amenity_data['total'].iloc[0]
        amenities = {
            'WiFi': amenity_data['has_wifi'].iloc[0],
            '门禁密码': amenity_data['has_door_code'].iloc[0], 
            '储物设施': amenity_data['has_storage'].iloc[0]
        }
        
        # 设施覆盖率饼图
        amenity_df = pd.DataFrame([
            {'设施': k, '数量': v, '覆盖率': f"{v/total*100:.1f}%"} 
            for k, v in amenities.items()
        ])
        
        fig = px.pie(
            amenity_df,
            values='数量',
            names='设施',
            title="房产设施覆盖情况"
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

def show_owner_analysis():
    """显示业主分析页面"""
    st.header("👥 业主分析")
    
    # 业主统计
    owner_stats_query = """
    SELECT 
        COUNT(DISTINCT owner_id) as unique_owners,
        COUNT(*) as total_records,
        COUNT(CASE WHEN email IS NOT NULL AND email != 'nan' THEN 1 END) as has_email,
        COUNT(CASE WHEN phone IS NOT NULL AND phone != 'nan' THEN 1 END) as has_phone
    FROM owners
    """
    
    stats = load_data(owner_stats_query)
    
    if not stats.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("独立业主数", f"{stats['unique_owners'].iloc[0]:,}")
        with col2:
            st.metric("总记录数", f"{stats['total_records'].iloc[0]:,}")
        with col3:
            email_rate = stats['has_email'].iloc[0] / stats['total_records'].iloc[0] * 100
            st.metric("邮箱完整度", f"{email_rate:.1f}%")
        with col4:
            phone_rate = stats['has_phone'].iloc[0] / stats['total_records'].iloc[0] * 100
            st.metric("电话完整度", f"{phone_rate:.1f}%")

def show_finance_analysis():
    """显示财务分析页面"""
    st.header("💰 财务分析")
    
    # 财务概览
    finance_stats_query = """
    SELECT 
        COUNT(*) as total_records,
        COUNT(CASE WHEN contract_signed_date IS NOT NULL THEN 1 END) as signed_contracts,
        COUNT(CASE WHEN manegement_fee_pct IS NOT NULL AND manegement_fee_pct != 'nan' THEN 1 END) as has_fee_info
    FROM finance
    """
    
    stats = load_data(finance_stats_query)
    
    if not stats.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("财务记录总数", f"{stats['total_records'].iloc[0]:,}")
        with col2:
            signed_rate = stats['signed_contracts'].iloc[0] / stats['total_records'].iloc[0] * 100
            st.metric("合同签署率", f"{signed_rate:.1f}%")
        with col3:
            fee_rate = stats['has_fee_info'].iloc[0] / stats['total_records'].iloc[0] * 100
            st.metric("费率信息完整度", f"{fee_rate:.1f}%")
    
    # 管理费类型分析
    st.subheader("📊 管理费类型分析")
    fee_query = """
    SELECT manegement_fee_pct, COUNT(*) as count
    FROM finance 
    WHERE manegement_fee_pct IS NOT NULL AND manegement_fee_pct != 'nan'
    GROUP BY manegement_fee_pct
    ORDER BY count DESC
    """
    
    fee_data = load_data(fee_query)
    
    if not fee_data.empty:
        fig = px.pie(
            fee_data,
            values='count',
            names='manegement_fee_pct',
            title="管理费类型分布"
        )
        st.plotly_chart(fig, use_container_width=True)

def show_trend_analysis():
    """趋势分析"""
    st.subheader("📈 趋势分析")
    
    # 合同签署趋势
    trend_query = """
    SELECT 
        DATE_TRUNC('month', TO_DATE(contract_signed_date, 'YYYY-MM-DD')) as month,
        COUNT(*) as contracts_signed
    FROM finance 
    WHERE contract_signed_date IS NOT NULL 
    AND contract_signed_date != 'nan'
    GROUP BY DATE_TRUNC('month', TO_DATE(contract_signed_date, 'YYYY-MM-DD'))
    ORDER BY month
    """
    
    trend_data = load_data(trend_query)
    
    if not trend_data.empty:
        fig = px.line(
            trend_data,
            x='month',
            y='contracts_signed',
            title="合同签署趋势",
            markers=True
        )
        fig.update_layout(xaxis_title="月份", yaxis_title="签署合同数")
        st.plotly_chart(fig, use_container_width=True)

def show_comparison_analysis():
    """对比分析"""
    st.subheader("📊 对比分析")
    
    # 不同州的房产对比
    state_comparison_query = """
    SELECT state, 
           COUNT(*) as property_count,
           AVG(CASE WHEN property_size != '' AND property_size IS NOT NULL 
               THEN CAST(property_size AS NUMERIC) END) as avg_size,
           COUNT(DISTINCT city) as cities_count
    FROM properties 
    WHERE state IS NOT NULL AND state != 'nan'
    GROUP BY state
    ORDER BY property_count DESC
    LIMIT 5
    """
    
    comparison_data = load_data(state_comparison_query)
    
    if not comparison_data.empty:
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('房产数量对比', '平均面积对比'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        fig.add_trace(
            go.Bar(x=comparison_data['state'], y=comparison_data['property_count'], name='房产数量'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=comparison_data['state'], y=comparison_data['avg_size'], name='平均面积'),
            row=1, col=2
        )
        
        fig.update_layout(title_text="各州房产对比分析")
        st.plotly_chart(fig, use_container_width=True)

def show_correlation_analysis():
    """相关性分析"""
    st.subheader("🔗 相关性分析")
    
    correlation_query = """
    SELECT 
        CAST(property_size AS NUMERIC) as property_size,
        CAST(occupancy AS NUMERIC) as occupancy,
        LENGTH(beds) as bed_complexity
    FROM properties 
    WHERE property_size IS NOT NULL AND property_size != 'nan'
    AND occupancy IS NOT NULL AND occupancy != 'nan'
    AND CAST(property_size AS NUMERIC) > 0
    AND CAST(occupancy AS NUMERIC) > 0
    """
    
    corr_data = load_data(correlation_query)
    
    if not corr_data.empty and len(corr_data) > 10:
        fig = px.scatter(
            corr_data,
            x='property_size',
            y='occupancy',
            title="房产面积与入住人数相关性",
            trendline="ols",
            labels={'property_size': '房产面积', 'occupancy': '入住人数'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 相关系数
        correlation = corr_data['property_size'].corr(corr_data['occupancy'])
        st.metric("相关系数", f"{correlation:.3f}")

def show_ai_assistant():
    """显示AI智能问答页面"""
    st.header("🤖 AI智能问答助手")
    
    if not AI_AVAILABLE:
        st.error("❌ AI查询助手模块加载失败，请检查依赖包是否正确安装")
        return
    
    # 显示AI状态
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        **🎯 功能说明:**
        - 用自然语言询问房地产数据相关问题
        - AI会自动生成SQL查询并执行
        - 支持中文和英文提问
        - 内置安全机制，只支持数据查询
        """)
    
    with col2:
        # 显示AI配置状态
        if ai_assistant.use_openai:
            st.success("🟢 OpenAI API 已配置")
            st.info(f"模型: {ai_assistant.model}")
        else:
            st.warning("🟡 使用内置模式匹配")
            st.info("可配置OpenAI API获得更强能力")
    
    # 问题输入区域
    st.markdown("---")
    st.subheader("💬 提出您的问题")
    
    # 示例问题
    with st.expander("💡 问题示例参考"):
        st.markdown("""
        **统计类问题:**
        - 有多少房产？
        - 业主总数是多少？
        - WiFi覆盖率如何？
        
        **分布类问题:**
        - 各个城市的房产分布如何？
        - 房型分布统计
        - 加州有多少房产？
        
        **对比类问题:**
        - 哪个城市房产最多？
        - 平均房产面积是多少？
        - 合同签约情况如何？
        
        **复杂查询:**
        - 加州哪个城市房产面积最大？
        - 有多少业主提供了联系方式？
        - 哪些房产有WiFi？
        """)
    
    # 输入框
    user_question = st.text_area(
        "请输入您的问题：",
        height=100,
        placeholder="例如：有多少房产位于加州？各个城市的房产分布如何？"
    )
    
    # 按钮区域
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        ask_button = st.button("🚀 AI问答", type="primary")
    
    with col2:
        clear_button = st.button("🗑️ 清除")
    
    if clear_button:
        st.experimental_rerun()
    
    # 处理用户问题
    if ask_button and user_question.strip():
        with st.spinner("🤔 AI正在思考..."):
            try:
                # 生成SQL查询
                sql_query, method = ai_assistant.generate_sql_query(user_question)
                
                if not sql_query:
                    st.error(f"❌ {method}")
                    st.markdown("**💡 建议:**")
                    st.markdown("- 尝试使用更具体的描述")
                    st.markdown("- 参考示例问题格式")
                    st.markdown("- 使用预定义查询功能")
                    return
                
                # 显示生成的SQL
                st.markdown("---")
                st.subheader("🔍 AI生成的查询")
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.code(sql_query, language='sql')
                with col2:
                    st.info(f"生成方式: {method}")
                
                # 解释查询
                explanation = ai_assistant.explain_query(sql_query, user_question)
                st.markdown(f"**{explanation}**")
                
                # 执行查询
                st.subheader("📊 查询结果")
                
                df = load_data(sql_query)
                
                if df.empty:
                    st.warning("📝 查询未返回任何数据")
                    return
                
                # 智能结果摘要
                summary = ai_assistant.format_results(df, user_question)
                st.markdown(summary)
                
                # 显示详细数据表格
                st.markdown("**📋 详细数据:**")
                st.dataframe(df, use_container_width=True)
                
                # 下载选项
                if len(df) > 0:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 下载结果CSV",
                        data=csv,
                        file_name=f"ai_query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                # 如果数据适合可视化，提供图表
                if len(df) <= 20 and len(df.columns) == 2:
                    st.subheader("📈 数据可视化")
                    
                    # 根据数据类型选择图表
                    col1_data = df.iloc[:, 0]
                    col2_data = df.iloc[:, 1]
                    
                    if pd.api.types.is_numeric_dtype(col2_data):
                        # 条形图
                        fig = px.bar(
                            df, 
                            x=df.columns[0], 
                            y=df.columns[1],
                            title=f"{user_question} - 可视化结果"
                        )
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 如果数据量适中，也显示饼图
                        if len(df) <= 10:
                            fig2 = px.pie(
                                df,
                                values=df.columns[1],
                                names=df.columns[0],
                                title=f"{user_question} - 分布图"
                            )
                            st.plotly_chart(fig2, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ 查询执行失败: {str(e)}")
                st.markdown("**🔧 可能的解决方法:**")
                st.markdown("- 检查数据库连接")
                st.markdown("- 尝试更简单的问题")
                st.markdown("- 使用预定义查询")
    
    elif ask_button:
        st.warning("⚠️ 请输入问题后再提交")
    
    # 底部提示
    st.markdown("---")
    st.markdown("**💡 使用提示:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **✅ 推荐问法:**
        - "有多少房产在加州？"
        - "WiFi覆盖率是多少？"
        - "各城市房产分布情况"
        """)
    
    with col2:
        st.markdown("""
        **❌ 避免问法:**
        - 过于模糊的问题
        - 非数据相关的问题
        - 修改数据的请求
        """)

if __name__ == "__main__":
    main() 