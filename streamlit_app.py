"""
AI求职助手 - Gemini + Material Design 风格
酷炫的渐变、动画和现代设计
"""
import streamlit as st
import requests
import json
from pathlib import Path
import time

# 后端 API 地址
BACKEND_URL = "https://unleisured-polly-welcomingly.ngrok-free.dev"

# 页面配置
st.set_page_config(
    page_title="AI求职助手 | Gemini Style",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Gemini 渐变 + OpenAI 打字机风格 CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=SF+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');

:root {
    --gemini-purple: #8e44ad;
    --gemini-blue: #3498db;
    --gemini-pink: #e91e63;
    --openai-green: #10a37f;
    --openai-dark: #202123;
    --shadow-1: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    --shadow-2: 0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23);
    --shadow-3: 0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23);
    --shadow-4: 0 14px 28px rgba(0,0,0,0.25), 0 10px 10px rgba(0,0,0,0.22);
}

/* 全局背景 Gemini 渐变动画 */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #4facfe 75%, #00f2fe 100%);
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
    font-family: 'SF Mono', 'Courier New', monospace;
    font-size: 16px;
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Hero 区域 - OpenAI 风格 */
.hero-section {
    background: linear-gradient(135deg, rgba(16, 163, 127, 0.95) 0%, rgba(142, 68, 173, 0.95) 100%);
    border-radius: 24px;
    padding: 64px 48px;
    margin: 24px auto;
    max-width: 1200px;
    box-shadow: var(--shadow-4);
    position: relative;
    overflow: hidden;
    animation: fadeInUp 0.8s ease-out;
    text-align: center;
}

.hero-section::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    animation: rotate 20s linear infinite;
}

@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.hero-title {
    font-family: 'SF Mono', 'Courier New', monospace;
    font-size: 64px;
    font-weight: 600;
    color: white;
    margin: 0 auto;
    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    position: relative;
    z-index: 1;
    animation: slideInLeft 0.8s ease-out;
    letter-spacing: -1px;
}

.hero-subtitle {
    font-family: 'SF Mono', 'Courier New', monospace;
    font-size: 24px;
    color: rgba(255,255,255,0.9);
    margin-top: 24px;
    position: relative;
    z-index: 1;
    animation: slideInLeft 1s ease-out;
    letter-spacing: 0.5px;
}

.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    backdrop-filter: blur(10px);
    border-radius: 999px;
    padding: 8px 20px;
    font-size: 14px;
    color: white;
    margin-bottom: 16px;
    position: relative;
    z-index: 1;
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

/* Material Design 卡片 - 居中大字体 */
.material-card {
    background: white;
    border-radius: 16px;
    padding: 32px;
    margin: 24px auto;
    max-width: 1200px;
    box-shadow: var(--shadow-2);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    animation: fadeInUp 0.6s ease-out;
}

.material-card:hover {
    box-shadow: var(--shadow-4);
    transform: translateY(-4px);
}

.material-card h3, .material-card h4 {
    font-family: 'SF Mono', 'Courier New', monospace;
    font-size: 28px;
    font-weight: 600;
    text-align: center;
    margin-bottom: 24px;
}

/* Streamlit 组件覆盖 - 打字机风格 */
.stButton > button {
    background: linear-gradient(135deg, var(--openai-green) 0%, var(--gemini-purple) 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 16px 40px;
    font-family: 'SF Mono', 'Courier New', monospace;
    font-size: 18px;
    font-weight: 600;
    box-shadow: var(--shadow-2);
    transition: all 0.3s ease;
    letter-spacing: 0.5px;
}

.stButton > button:hover {
    box-shadow: var(--shadow-3);
    transform: translateY(-2px);
}

.stTextArea textarea, .stTextInput input, .stNumberInput input {
    border-radius: 12px;
    border: 2px solid #e0e0e0;
    transition: all 0.3s ease;
    font-family: 'SF Mono', 'Courier New', monospace;
    font-size: 16px;
    padding: 12px;
}

.stTextArea textarea:focus, .stTextInput input:focus, .stNumberInput input:focus {
    border-color: var(--openai-green);
    box-shadow: 0 0 0 3px rgba(16, 163, 127, 0.1);
}

/* 标签 */
.tag {
    display: inline-block;
    background: linear-gradient(135deg, rgba(16, 163, 127, 0.1), rgba(142, 68, 173, 0.1));
    color: var(--gemini-purple);
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 14px;
    font-weight: 600;
    margin: 4px;
    font-family: 'SF Mono', 'Courier New', monospace;
}

/* 成功/失败日志 - 打字机风格 */
.success-log {
    background: #f6ffed;
    border-left: 4px solid #10a37f;
    padding: 1.2rem;
    margin: 0.5rem 0;
    border-radius: 8px;
    font-family: 'SF Mono', 'Courier New', monospace;
    font-size: 16px;
}

.error-log {
    background: #fff2f0;
    border-left: 4px solid #ff4d4f;
    padding: 1.2rem;
    margin: 0.5rem 0;
    border-radius: 8px;
    font-family: 'SF Mono', 'Courier New', monospace;
    font-size: 16px;
}

/* 动画 */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes slideInLeft {
    from {
        opacity: 0;
        transform: translateX(-30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* 隐藏 Streamlit 默认元素 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 全局文字大小 */
.stMarkdown, .stText, p, div {
    font-size: 18px;
    line-height: 1.6;
}

/* 背景区域文字白色 */
.hero-section, .hero-section *, 
div[style*="background: linear-gradient"] *,
div[style*="background: rgba(255,255,255,0.1)"] * {
    color: white !important;
}

/* 卡片内容黑色 */
.material-card, .material-card * {
    color: #333 !important;
}

/* 步骤指示器文字白色 */
.step-indicator div {
    color: white !important;
}

/* Tab 标签样式 */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    justify-content: center;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'SF Mono', 'Courier New', monospace;
    font-size: 18px;
    font-weight: 600;
    padding: 12px 24px;
}
</style>
""", unsafe_allow_html=True)

# Hero 区域
st.markdown("""
<div class="hero-section">
    <div class="hero-badge">
        <span class="brand-dot"></span>
        AI-Powered • Material Design • DeepSeek Driven
    </div>
    <h1 class="hero-title">AI 求职助手</h1>
    <p class="hero-subtitle">智能简历分析 • 自动职位匹配 • 一键批量投递 • 一站式求职解决方案</p>
</div>
""", unsafe_allow_html=True)

# 初始化 session state
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

# 步骤指示器
steps = ["上传简历", "AI分析", "职位匹配", "自动投递"]
step_html = '<div class="step-indicator">'
for i, step_name in enumerate(steps, 1):
    status = "done" if i < st.session_state.step else ("active" if i == st.session_state.step else "")
    step_html += f'''
    <div class="step {status}">
        <div class="step-circle">{i}</div>
        <div style="font-size: 14px; color: white; font-weight: 500;">{step_name}</div>
    </div>
    '''
step_html += '</div>'
st.markdown(step_html, unsafe_allow_html=True)

# 主要内容区域
tab1, tab2, tab3, tab4 = st.tabs(["📄 简历分析", "🚀 自动投递", "📚 文档中心", "❓ 帮助中心"])

with tab1:
    st.markdown('<div class="material-card">', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📤 上传简历")

        # 文件上传
        uploaded_file = st.file_uploader(
            "支持 PDF、DOCX、TXT 格式",
            type=['pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png'],
            help="上传您的简历文件"
        )

        if uploaded_file:
            # 读取文件内容
            if uploaded_file.type == "text/plain":
                st.session_state.resume_text = uploaded_file.read().decode("utf-8")
            else:
                # PDF/DOCX 需要解析，暂时提示用户粘贴
                st.warning("⚠️ PDF/DOCX 文件需要解析，请直接粘贴简历文本")
            
            st.success(f"✅ 已上传: {uploaded_file.name}")
            st.session_state.step = max(st.session_state.step, 1)

        st.markdown("---")
        st.markdown("### ✍️ 或直接粘贴简历")

        resume_input = st.text_area(
            "粘贴您的简历内容",
            value=st.session_state.resume_text,
            height=300,
            placeholder="在此粘贴您的简历文本..."
        )

        if resume_input != st.session_state.resume_text:
            st.session_state.resume_text = resume_input
            st.session_state.step = max(st.session_state.step, 1)

        col_btn1, col_btn2, col_btn3 = st.columns(3)

        with col_btn1:
            if st.button("🚀 开始分析", use_container_width=True, key="analyze_btn"):
                if not st.session_state.resume_text:
                    st.error("请先上传或粘贴简历！")
                else:
                    with st.spinner("🤖 AI 正在分析您的简历..."):
                        try:
                            response = requests.post(
                                f"{BACKEND_URL}/api/analysis/resume",
                                json={
                                    "resume_text": st.session_state.resume_text,
                                    "analysis_type": "full"
                                },
                                timeout=120
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                if data.get('success'):
                                    st.session_state.analysis_result = data.get('results', {})
                                    st.session_state.step = 2
                                    st.success("✅ 分析完成！")
                                    st.rerun()
                                else:
                                    st.error(f"❌ 分析失败: {data.get('message', '未知错误')}")
                            else:
                                st.error(f"❌ 服务器错误: HTTP {response.status_code}")
                        except requests.exceptions.Timeout:
                            st.error("❌ 分析超时，请稍后重试")
                        except Exception as e:
                            st.error(f"❌ 分析失败: {str(e)}")

        with col_btn2:
            if st.button("📝 加载示例", use_container_width=True, key="load_example_btn"):
                st.session_state.resume_text = """陈盈桦
AI-Native 应用工程师

技能：
- Python, FastAPI, SQL, Docker
- RAG, LangChain, 向量数据库
- React, TypeScript, Streamlit

经验：
- 量化数据管道开发
- AI 工作流设计
- 模型质量门控系统"""
                st.session_state.step = 1
                st.rerun()

        with col_btn3:
            if st.button("🔄 重置", use_container_width=True, key="reset_btn"):
                st.session_state.resume_text = ""
                st.session_state.analysis_result = None
                st.session_state.step = 0
                st.rerun()

    with col2:
        st.markdown("### 📊 分析结果")
        
        if st.session_state.analysis_result:
            results = st.session_state.analysis_result
            
            # 职业分析
            if 'career_analysis' in results:
                with st.expander("🎯 职业分析", expanded=True):
                    st.markdown(results['career_analysis'])
            
            # 岗位推荐
            if 'job_recommendations' in results:
                with st.expander("💼 岗位推荐", expanded=True):
                    st.markdown(results['job_recommendations'])
            
            # 面试辅导
            if 'interview_preparation' in results:
                with st.expander("🎤 面试辅导", expanded=True):
                    st.markdown(results['interview_preparation'])
            
            # 质量审核
            if 'quality_audit' in results:
                with st.expander("✅ 质量审核", expanded=True):
                    st.markdown(results['quality_audit'])
        else:
            st.info("👈 请先上传简历并点击「开始分析」")

    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="material-card">', unsafe_allow_html=True)
    
    # Credits 购买区域
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); border-radius: 16px; margin-bottom: 32px;">
        <h2 style="color: white; font-size: 36px; margin-bottom: 16px;">💎 选择您的投递套餐</h2>
        <p style="color: rgba(255,255,255,0.9); font-size: 18px;">一次付费，后台自动投递，完成后邮件通知</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 定价卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background: white; padding: 24px; border-radius: 12px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <div style="font-size: 14px; color: #666; margin-bottom: 8px;">体验包</div>
            <div style="font-size: 32px; font-weight: bold; color: #333; margin-bottom: 4px;">¥19.9</div>
            <div style="font-size: 24px; color: #10a37f; font-weight: bold; margin-bottom: 16px;">50个岗位</div>
            <div style="font-size: 12px; color: #999;">¥0.40/个</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("选择体验包", key="buy_50", use_container_width=True):
            st.session_state.selected_package = {"name": "体验包", "credits": 50, "price": 19.9}
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #10a37f 0%, #667eea 100%); padding: 24px; border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(16,163,127,0.3); position: relative;">
            <div style="position: absolute; top: -10px; right: 10px; background: #ff4d4f; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">🔥 最热</div>
            <div style="font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 8px;">标准包</div>
            <div style="font-size: 32px; font-weight: bold; color: white; margin-bottom: 4px;">¥39.9</div>
            <div style="font-size: 24px; color: white; font-weight: bold; margin-bottom: 16px;">150个岗位</div>
            <div style="font-size: 12px; color: rgba(255,255,255,0.8);">¥0.27/个</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("选择标准包", key="buy_150", use_container_width=True, type="primary"):
            st.session_state.selected_package = {"name": "标准包", "credits": 150, "price": 39.9}
    
    with col3:
        st.markdown("""
        <div style="background: white; padding: 24px; border-radius: 12px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <div style="font-size: 14px; color: #666; margin-bottom: 8px;">专业包</div>
            <div style="font-size: 32px; font-weight: bold; color: #333; margin-bottom: 4px;">¥69.9</div>
            <div style="font-size: 24px; color: #10a37f; font-weight: bold; margin-bottom: 16px;">300个岗位</div>
            <div style="font-size: 12px; color: #999;">¥0.23/个</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("选择专业包", key="buy_300", use_container_width=True):
            st.session_state.selected_package = {"name": "专业包", "credits": 300, "price": 69.9}
    
    with col4:
        st.markdown("""
        <div style="background: white; padding: 24px; border-radius: 12px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <div style="font-size: 14px; color: #666; margin-bottom: 8px;">旗舰包</div>
            <div style="font-size: 32px; font-weight: bold; color: #333; margin-bottom: 4px;">¥129.9</div>
            <div style="font-size: 24px; color: #10a37f; font-weight: bold; margin-bottom: 16px;">700个岗位</div>
            <div style="font-size: 12px; color: #999;">¥0.19/个</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("选择旗舰包", key="buy_700", use_container_width=True):
            st.session_state.selected_package = {"name": "旗舰包", "credits": 700, "price": 129.9}
    
    # 如果选择了套餐，显示购买表单
    if 'selected_package' in st.session_state:
        st.markdown("---")
        pkg = st.session_state.selected_package
        
        st.success(f"✅ 已选择：{pkg['name']} - {pkg['credits']}个岗位 - ¥{pkg['price']}")
        
        col_form1, col_form2 = st.columns([2, 1])
        
        with col_form1:
            st.markdown("### 📝 填写投递信息")
            
            email = st.text_input("📧 邮箱", placeholder="接收投递结果通知", key="email_input")
            resume_text = st.text_area("📄 简历内容", placeholder="粘贴您的简历...", height=200, value=st.session_state.resume_text, key="resume_buy_input")
            keyword = st.text_input("🔍 岗位关键词", placeholder="例如：Python工程师", value="Python工程师", key="keyword_buy_input")
            city = st.text_input("📍 城市", placeholder="例如：北京", value="北京", key="city_buy_input")
            
            st.markdown("### 💳 支付方式")
            payment_method = st.radio("", ["支付宝", "微信支付"], horizontal=True, key="payment_method")
            
            if st.button("🚀 立即购买并开始投递", type="primary", use_container_width=True, key="confirm_buy"):
                if not email or not resume_text:
                    st.error("❌ 请填写邮箱和简历内容")
                else:
                    with st.spinner("正在创建订单..."):
                        try:
                            # 调用后端创建订单
                            response = requests.post(
                                f"{BACKEND_URL}/api/credits/purchase",
                                json={
                                    "email": email,
                                    "package": pkg['name'],
                                    "credits": pkg['credits'],
                                    "price": pkg['price'],
                                    "payment_method": payment_method,
                                    "resume_text": resume_text,
                                    "job_keyword": keyword,
                                    "city": city
                                },
                                timeout=30
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                if data.get('success'):
                                    st.success("✅ 订单创建成功！")
                                    st.info(f"""
                                    📧 投递任务已加入队列
                                    
                                    - 投递数量：{pkg['credits']} 个岗位
                                    - 预计时间：{pkg['credits'] * 5 // 60} 分钟
                                    - 通知邮箱：{email}
                                    
                                    您可以关闭此页面，完成后会发送邮件通知！
                                    """)
                                    
                                    # 显示支付二维码（模拟）
                                    st.markdown(f"""
                                    <div style="text-align: center; padding: 32px; background: white; border-radius: 12px; margin-top: 16px;">
                                        <h3 style="color: #333;">扫码支付 ¥{pkg['price']}</h3>
                                        <div style="width: 200px; height: 200px; background: #f0f0f0; margin: 16px auto; display: flex; align-items: center; justify-content: center; border-radius: 8px;">
                                            <p style="color: #999;">支付二维码</p>
                                        </div>
                                        <p style="color: #666; font-size: 14px;">使用{payment_method}扫码支付</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.error(f"❌ {data.get('message', '创建订单失败')}")
                            else:
                                st.error(f"❌ 服务器错误: HTTP {response.status_code}")
                        except Exception as e:
                            st.error(f"❌ 连接失败: {str(e)}")
        
        with col_form2:
            st.markdown("### ✨ 服务说明")
            st.info("""
            **购买后流程**
            
            1. ✅ 支付完成
            2. 🤖 后台自动投递
            3. 📸 记录投递截图
            4. 📧 邮件发送结果
            
            **邮件包含**
            
            - 投递成功数量
            - 投递失败原因
            - 所有投递截图
            - PDF 详细报告
            
            **注意事项**
            
            - 付款后可关闭页面
            - 投递失败自动退款
            - 7×24小时自动执行
            """)
    
    # 初始化 session state
    if 'login_step' not in st.session_state:
        st.session_state.login_step = 0
    if 'phone' not in st.session_state:
        st.session_state.phone = ""
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.1); border-radius: 12px; margin-top: 32px;">
        <h3 style="color: white;">🎯 或使用传统方式（需登录）</h3>
        <p style="color: rgba(255,255,255,0.8);">适合需要实时查看投递进度的用户</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 步骤 1：输入手机号
    if st.session_state.login_step == 0:
        st.markdown("#### 📱 步骤 1：登录 Boss 直聘")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            phone = st.text_input("手机号", placeholder="请输入11位手机号", max_chars=11, key="phone_input")
            
            if st.button("🔐 获取验证码", type="primary", use_container_width=True):
                if not phone or len(phone) != 11:
                    st.error("❌ 请输入正确的手机号")
                else:
                    with st.spinner("正在获取验证码..."):
                        try:
                            response = requests.post(
                                f"{BACKEND_URL}/api/simple-apply/init-login",
                                json={"phone": phone},
                                timeout=30
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                if data.get('success'):
                                    st.session_state.phone = phone
                                    st.session_state.login_step = 1
                                    st.success(f"✅ {data.get('message')}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {data.get('message', '获取验证码失败')}")
                            else:
                                st.error(f"❌ 服务器错误: HTTP {response.status_code}")
                        except Exception as e:
                            st.error(f"❌ 连接失败: {str(e)}")
        
        with col2:
            st.info("""
            **说明**
            
            1. 输入手机号
            2. 后端自动打开浏览器
            3. 自动填写手机号
            4. 自动获取验证码
            5. 等待短信验证码
            """)
    
    # 步骤 2：输入验证码
    elif st.session_state.login_step == 1:
        st.markdown("#### 🔑 步骤 2：输入验证码")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info(f"📱 验证码已发送到 {st.session_state.phone}")
            
            code = st.text_input("验证码", placeholder="请输入6位验证码", max_chars=6, key="code_input")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("✅ 确认登录", type="primary", use_container_width=True):
                    if not code or len(code) != 6:
                        st.error("❌ 请输入6位验证码")
                    else:
                        with st.spinner("正在登录..."):
                            try:
                                response = requests.post(
                                    f"{BACKEND_URL}/api/simple-apply/verify-code",
                                    json={"phone": st.session_state.phone, "code": code},
                                    timeout=30
                                )
                                
                                if response.status_code == 200:
                                    data = response.json()
                                    if data.get('success'):
                                        st.session_state.login_step = 2
                                        st.success(f"✅ {data.get('message')}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {data.get('message', '登录失败')}")
                                else:
                                    st.error(f"❌ 服务器错误: HTTP {response.status_code}")
                            except Exception as e:
                                st.error(f"❌ 连接失败: {str(e)}")
            
            with col_btn2:
                if st.button("🔙 返回", use_container_width=True):
                    st.session_state.login_step = 0
                    st.rerun()
        
        with col2:
            st.info("""
            **说明**
            
            1. 查收短信验证码
            2. 输入验证码
            3. 后端自动填写并登录
            4. 登录成功后开始投递
            """)
    
    # 步骤 3：开始投递
    elif st.session_state.login_step == 2:
        st.success(f"✅ 已登录：{st.session_state.phone}")
        
        if st.button("🔓 退出登录", key="logout_btn"):
            st.session_state.login_step = 0
            st.session_state.phone = ""
            st.rerun()
        
        st.markdown("---")
        st.markdown("#### 🎯 开始投递")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            keyword = st.text_input("🔍 搜索关键词", placeholder="例如：Python工程师", value="Python工程师", key="keyword_input")
            city = st.text_input("📍 城市", placeholder="例如：北京、上海", value="北京", key="city_input")
            max_count = st.number_input("📊 投递数量", min_value=1, max_value=50, value=10, key="count_input")
            resume_text = st.text_area("📄 简历内容", placeholder="粘贴你的简历内容...", height=200, value=st.session_state.resume_text, key="resume_input")
        
        with col2:
            st.info("""
            **使用说明**
            
            1. 输入关键词和城市
            2. 设置投递数量
            3. 粘贴简历内容
            4. 点击开始投递
            
            **注意事项**
            
            - 建议先测试 5-10 个
            - 投递间隔 5 秒
            - 自动生成求职信
            """)
        
        # 投递按钮
        if st.button("🚀 开始自动投递", type="primary", use_container_width=True, key="apply_btn"):
            if not resume_text.strip():
                st.warning("⚠️ 请输入简历内容")
            else:
                # 开始投递
                st.info(f"🔄 正在投递 {max_count} 个岗位，请稍候...")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # 调用后端 API
                    response = requests.post(
                        f"{BACKEND_URL}/api/simple-apply/apply",
                        json={
                            "phone": st.session_state.phone,
                            "resume_text": resume_text,
                            "job_keyword": keyword,
                            "city": city,
                            "count": max_count
                        },
                        timeout=600  # 10分钟超时
                    )
                    
                    progress_bar.progress(100)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get('success'):
                            st.success(f"✅ {result.get('message')}")
                            
                            # 显示统计
                            col_stat1, col_stat2, col_stat3 = st.columns(3)
                            with col_stat1:
                                st.metric("总数", result.get('total', 0))
                            with col_stat2:
                                st.metric("成功", result.get('success_count', 0), delta=None, delta_color="normal")
                            with col_stat3:
                                st.metric("失败", result.get('failed_count', 0), delta=None, delta_color="inverse")
                            
                            # 显示投递日志
                            if 'details' in result and result['details']:
                                st.markdown("### 📋 投递日志")
                                for detail in result['details']:
                                    if detail.get('success'):
                                        st.markdown(f"""
                                        <div class="success-log">
                                            ✅ <strong>{detail.get('job_title', '未知职位')}</strong> - {detail.get('company', '未知公司')}
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"""
                                        <div class="error-log">
                                            ❌ <strong>{detail.get('job_title', '未知职位')}</strong> - {detail.get('company', '未知公司')}
                                        </div>
                                        """, unsafe_allow_html=True)
                        else:
                            st.warning(f"⚠️ {result.get('message', '未找到符合条件的岗位')}")
                    else:
                        error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                        st.error(f"❌ 投递失败: {error_data.get('detail', f'HTTP {response.status_code}')}")
                        
                except requests.exceptions.Timeout:
                    st.error("❌ 请求超时，投递可能仍在进行中，请稍后查看投递记录")
                except requests.exceptions.ConnectionError:
                    st.error("❌ 无法连接到后端服务，请确保后端已启动并且 ngrok 地址正确")
                except Exception as e:
                    st.error(f"❌ 投递失败: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="material-card">', unsafe_allow_html=True)
    st.markdown("### 📚 文档中心")

    doc_col1, doc_col2 = st.columns(2)

    with doc_col1:
        st.markdown("""
        #### 📖 使用指南
        - 快速开始
        - 简历优化技巧
        - 面试准备指南
        - 职位搜索技巧
        """)

    with doc_col2:
        st.markdown("""
        #### 🔧 技术文档
        - API 接口说明
        - 数据格式规范
        - 错误代码说明
        - 集成示例
        """)

    st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="material-card">', unsafe_allow_html=True)
    st.markdown("### ❓ 帮助中心")

    with st.expander("❓ 如何使用自动投递？"):
        st.markdown("""
        1. 在「自动投递」标签页输入关键词和城市
        2. 设置投递数量（建议先测试 3-5 个）
        3. 粘贴你的简历内容
        4. 点击「开始自动投递」按钮
        5. 等待投递完成，查看投递日志
        """)

    with st.expander("❓ 支持哪些招聘平台？"):
        st.markdown("""
        目前支持：
        - Boss直聘（已实现）
        - 智联招聘（开发中）
        - 前程无忧（计划中）
        - 拉勾网（计划中）
        """)

    with st.expander("❓ 投递需要多长时间？"):
        st.markdown("""
        投递时间取决于：
        - 投递数量（每个岗位约 3-6 秒）
        - 网络速度
        - 服务器负载
        
        例如：投递 10 个岗位约需 30-60 秒
        """)

    with st.expander("❓ 如何提高投递成功率？"):
        st.markdown("""
        1. 使用精准的关键词
        2. 简历内容完整、格式清晰
        3. 选择合适的城市和岗位
        4. 避免短时间内大量投递
        """)

    with st.expander("❓ 数据安全吗？"):
        st.markdown("""
        - ✅ 所有数据仅用于投递
        - ✅ 不会存储您的个人信息
        - ✅ 使用加密传输
        - ✅ 符合数据保护法规
        """)

    st.markdown("---")
    st.markdown("""
    ### 📧 联系我们
    - 📮 GitHub: [emptyteabot/ai-job-helper](https://github.com/emptyteabot/ai-job-helper)
    - 🌐 后端地址: `https://unleisured-polly-welcomingly.ngrok-free.dev`
    """)

    st.markdown('</div>', unsafe_allow_html=True)

# 页脚
st.markdown("""
<div style="text-align: center; padding: 32px; color: white; font-size: 14px;">
    <div class="brand-dot"></div>
    <strong>AI 求职助手</strong> | Powered by DeepSeek & Material Design
    <br>
    <span style="opacity: 0.8;">© 2026 All Rights Reserved</span>
</div>
""", unsafe_allow_html=True)
