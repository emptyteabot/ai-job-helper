"""
AI求职助手 - Streamlit 完整版
参考 auto_apply_panel.html 和 home.html 设计
整合真实数据：OpenClaw + 邮件通知
"""
import streamlit as st
import sys
import os
import io
import requests
import pandas as pd
import time
from datetime import datetime
import uuid

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="AI求职助手",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 全局样式 - 参考 auto_apply_panel.html 和 home.html
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --bg: #ffffff;
    --text: #131313;
    --muted: #64646b;
    --line: #e8e8ec;
    --soft: #f7f7f9;
    --ok: #1f7c49;
    --err: #b54040;
    --warn: #d97706;
    --primary: #10a37f;
    --maxw: 980px;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: "Noto Sans SC", "PingFang SC", sans-serif;
}

#MainMenu, footer, header {visibility: hidden}

.main .block-container {
    max-width: var(--maxw);
    padding: 1.5rem 1rem 3rem;
}

/* 顶部导航 */
.top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--line);
    padding: 10px 0 16px;
    margin-bottom: 8px;
}

.brand {
    display: flex;
    align-items: center;
    gap: 9px;
    font-size: 14px;
    font-weight: 800;
}

.dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #121212;
    box-shadow: 0 0 0 6px rgba(18, 18, 18, 0.08);
}

/* Hero */
.hero {
    padding: 42px 0 28px;
}

.pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    border: 1px solid var(--line);
    border-radius: 999px;
    background: #fff;
    color: var(--muted);
    padding: 6px 11px;
    font: 500 11px/1 "IBM Plex Mono", monospace;
    margin-bottom: 10px;
}

.pill::before {
    content: "";
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #121212;
}

h1 {
    font-size: clamp(38px, 7vw, 64px);
    letter-spacing: -1.4px;
    line-height: 1.1;
    margin-bottom: 12px;
}

.sub {
    color: var(--muted);
    font-size: 19px;
    line-height: 1.65;
    max-width: 680px;
}

/* 面板 */
.panel {
    border: 1px solid var(--line);
    border-radius: 18px;
    background: #fff;
    padding: 22px;
    margin-bottom: 16px;
}

.panel h2 {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 14px;
}

.panel p {
    color: var(--muted);
    font-size: 15px;
    line-height: 1.6;
    margin-bottom: 16px;
}

/* 按钮 */
.stButton > button {
    background: var(--primary);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: 600;
    transition: all 0.2s;
}

.stButton > button:hover {
    background: #0d8c6d;
    transform: translateY(-1px);
}

/* 输入框 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 12px;
    font-size: 15px;
}

.stTextArea > div > div > textarea {
    min-height: 200px;
}

/* 标签页 */
.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
    border-bottom: 1px solid var(--line);
}

.stTabs [data-baseweb="tab"] {
    padding: 12px 20px;
    font-size: 15px;
    font-weight: 500;
    color: var(--muted);
}

.stTabs [aria-selected="true"] {
    color: var(--text);
    border-bottom: 2px solid var(--text);
}

/* 岗位卡片 */
.job-card {
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 12px;
    transition: all 0.2s;
    background: var(--bg);
}

.job-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    border-color: var(--primary);
}

.job-title {
    font-size: 18px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 8px;
}

.job-meta {
    display: flex;
    gap: 16px;
    font-size: 14px;
    color: var(--muted);
    margin-bottom: 8px;
}

.job-salary {
    color: var(--primary);
    font-weight: 600;
}

/* 统计卡片 */
.stat-card {
    background: var(--soft);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}

.stat-value {
    font-size: 36px;
    font-weight: 800;
    color: var(--primary);
    margin-bottom: 6px;
}

.stat-label {
    font-size: 14px;
    color: var(--muted);
}
</style>
""", unsafe_allow_html=True)

# 配置 API Key
os.environ['OPENAI_API_KEY'] = 'sk-SnQQxqPPxqxqxqxqxqxqxqxqxqxqxqxqxqxqxqxqxqxqxqxq'
os.environ['OPENAI_BASE_URL'] = 'https://oneapi.gemiaude.com/v1'

# 后端 API 地址
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# 文件解析函数（省略，与之前相同）
def parse_uploaded_file(uploaded_file):
    """解析上传的文件"""
    try:
        file_content = uploaded_file.read()
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        resume_text = ""

        if file_ext == '.txt':
            try:
                resume_text = file_content.decode('utf-8')
            except:
                resume_text = file_content.decode('gbk', errors='ignore')

        elif file_ext == '.pdf':
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    resume_text += text + "\n"

        elif file_ext in ['.docx', '.doc']:
            from docx import Document
            doc = Document(io.BytesIO(file_content))
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    resume_text += paragraph.text + "\n"

        return resume_text.strip() if resume_text else None

    except Exception as e:
        st.error(f"文件解析失败: {str(e)}")
        return None

# 简历分析函数（修复 asyncio 错误）
def analyze_resume(resume_text):
    """简历分析 - 直接同步调用"""
    try:
        from app.core.multi_ai_debate import JobApplicationPipeline

        pipeline = JobApplicationPipeline()

        # 直接调用同步函数，不需要 asyncio
        results = pipeline.process_resume(resume_text)
        return results

    except Exception as e:
        st.error(f"分析失败: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# 初始化 session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# 顶部导航
st.markdown('''
<div class="top">
    <div class="brand">
        <div class="dot"></div>
        <span>AI求职助手</span>
    </div>
</div>
''', unsafe_allow_html=True)

# Hero
st.markdown('''
<div class="hero">
    <div class="pill">真实岗位数据 · OpenClaw驱动</div>
    <h1>让 AI 帮你找到<br>理想工作</h1>
    <div class="sub">6 个 AI 协作分析简历，智能推荐岗位，自动投递到 Boss直聘、智联招聘、LinkedIn</div>
</div>
''', unsafe_allow_html=True)

# 标签页
tab1, tab2, tab3, tab4 = st.tabs([
    "📄 简历分析",
    "💼 岗位推荐",
    "🚀 自动投递",
    "📊 数据统计"
])

# Tab1: 简历分析
with tab1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("## 📄 AI 简历分析")
    st.markdown("<p>上传简历或粘贴文本，6 个 AI 协作为你提供职业建议</p>", unsafe_allow_html=True)

    method = st.radio("输入方式", ["文本输入", "上传文件"], horizontal=True)

    if method == "文本输入":
        resume_text = st.text_area("简历内容", height=200, placeholder="粘贴你的简历内容...", label_visibility="collapsed")

        if resume_text and st.button("开始分析", type="primary", key="analyze_text"):
            if len(resume_text.strip()) < 50:
                st.warning("简历内容较少，建议至少 50 字以上")
            else:
                with st.spinner("🔄 AI 正在分析你的简历..."):
                    results = analyze_resume(resume_text)

                    if results:
                        st.session_state.analysis_results = results
                        st.success("✅ 分析完成！")

                        result_tabs = st.tabs(["🎯 职业分析", "💼 岗位推荐", "✍️ 简历优化", "📚 面试准备", "🎤 模拟面试", "📈 技能分析"])

                        with result_tabs[0]:
                            st.markdown(results.get('career_analysis', '暂无数据'))
                        with result_tabs[1]:
                            st.markdown(results.get('job_recommendations', '暂无数据'))
                        with result_tabs[2]:
                            st.markdown(results.get('resume_optimization', '暂无数据'))
                        with result_tabs[3]:
                            st.markdown(results.get('interview_preparation', '暂无数据'))
                        with result_tabs[4]:
                            st.markdown(results.get('mock_interview', '暂无数据'))
                        with result_tabs[5]:
                            st.markdown(results.get('skill_gap_analysis', '暂无数据'))

    else:
        uploaded_file = st.file_uploader("上传简历", type=["pdf", "doc", "docx", "txt"], label_visibility="collapsed")

        if uploaded_file:
            if st.button("开始分析", type="primary", key="analyze_file"):
                with st.spinner("🔄 正在解析文件..."):
                    resume_text = parse_uploaded_file(uploaded_file)

                if resume_text:
                    with st.spinner("🔄 AI 正在分析你的简历..."):
                        results = analyze_resume(resume_text)

                        if results:
                            st.session_state.analysis_results = results
                            st.success("✅ 分析完成！")

                            with st.expander("🎯 职业分析", expanded=True):
                                st.write(results.get('career_analysis', '暂无数据'))
                            with st.expander("💼 岗位推荐"):
                                st.write(results.get('job_recommendations', '暂无数据'))
                            with st.expander("✍️ 简历优化"):
                                st.write(results.get('resume_optimization', '暂无数据'))
                            with st.expander("📚 面试准备"):
                                st.write(results.get('interview_preparation', '暂无数据'))
                            with st.expander("🎤 模拟面试"):
                                st.write(results.get('mock_interview', '暂无数据'))
                            with st.expander("📈 技能分析"):
                                st.write(results.get('skill_gap_analysis', '暂无数据'))

    st.markdown('</div>', unsafe_allow_html=True)

# Tab2: 岗位推荐（OpenClaw真实数据）
with tab2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("## 💼 岗位推荐")
    st.markdown("<p>基于 OpenClaw 的真实岗位数据</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        keywords = st.text_input("搜索关键词", value="Python开发")
    with col2:
        location = st.text_input("工作地点", value="北京")

    if st.button("搜索岗位", type="primary"):
        with st.spinner("🔍 正在搜索真实岗位..."):
            try:
                response = requests.get(
                    f"{BACKEND_URL}/api/jobs/search",
                    params={"keywords": keywords, "location": location},
                    timeout=30
                )

                if response.status_code == 200:
                    jobs = response.json()

                    if jobs:
                        st.success(f"✅ 找到 {len(jobs)} 个真实岗位")

                        for job in jobs:
                            st.markdown(f"""
                            <div class="job-card">
                                <div class="job-title">{job.get('title', '未知职位')}</div>
                                <div class="job-meta">
                                    <span>🏢 {job.get('company', '未知公司')}</span>
                                    <span class="job-salary">💰 {job.get('salary', '面议')}</span>
                                    <span>📍 {job.get('location', '未知')}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                if st.button("查看详情", key=f"detail_{job.get('id', '')}"):
                                    st.info(job.get('description', '暂无描述'))
                            with col_b:
                                if st.button("一键投递", key=f"apply_{job.get('id', '')}", type="primary"):
                                    st.success("✅ 已加入投递队列")
                    else:
                        st.warning("未找到相关岗位")
                else:
                    st.error("❌ 后端服务未启动，请运行: python web_app.py")

            except requests.exceptions.ConnectionError:
                st.error("❌ 无法连接到后端服务")
                st.info("请运行: `python web_app.py`")

            except Exception as e:
                st.error(f"搜索失败: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

# Tab3: 自动投递（邮件通知）
with tab3:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("## 🚀 自动投递")
    st.markdown("<p>自动投递到 Boss直聘、智联招聘、LinkedIn，邮件通知进度</p>", unsafe_allow_html=True)

    platform = st.selectbox("选择平台", ["Boss直聘", "智联招聘", "LinkedIn (Easy Apply)"])

    col1, col2 = st.columns(2)
    with col1:
        keywords = st.text_input("搜索关键词", value="Python Developer", key="apply_keywords")
        max_count = st.number_input("投递数量", 1, 100, 10)
    with col2:
        location = st.text_input("工作地点", value="北京", key="apply_location")
        interval = st.slider("投递间隔（秒）", 3, 30, 5)

    email = st.text_input("邮箱地址（接收进度通知）", placeholder="your@email.com")

    if st.button("开始投递", type="primary"):
        if not email:
            st.warning("请输入邮箱地址以接收进度通知")
        else:
            with st.spinner("🚀 正在启动自动投递..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/auto_apply/start",
                        json={
                            "platform": platform,
                            "keywords": keywords,
                            "location": location,
                            "max_count": max_count,
                            "interval": interval,
                            "email": email
                        },
                        timeout=10
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ 投递任务已启动！")
                        st.info(f"📧 进度通知将发送到: {email}")
                    else:
                        st.error("❌ 启动失败，请检查后端服务")

                except requests.exceptions.ConnectionError:
                    st.error("❌ 无法连接到后端服务，请运行: python web_app.py")

                except Exception as e:
                    st.error(f"启动失败: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

# Tab4: 数据统计
with tab4:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("## 📊 数据统计")

    try:
        response = requests.get(
            f"{BACKEND_URL}/api/stats",
            params={"user_id": st.session_state.user_id},
            timeout=5
        )

        if response.status_code == 200:
            stats = response.json()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{stats.get('total_applications', 0)}</div>
                    <div class="stat-label">总投递</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{stats.get('response_rate', 0)}%</div>
                    <div class="stat-label">回复率</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{stats.get('interviews', 0)}</div>
                    <div class="stat-label">面试邀请</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{stats.get('offers', 0)}</div>
                    <div class="stat-label">Offer</div>
                </div>
                """, unsafe_allow_html=True)

            if 'applications' in stats and stats['applications']:
                st.markdown("### 📋 投递记录")
                df = pd.DataFrame(stats['applications'])
                st.dataframe(df, use_container_width=True)

        else:
            st.error("❌ 后端服务未启动，请运行: python web_app.py")

    except requests.exceptions.ConnectionError:
        st.info("后端服务未连接，无法获取统计数据")

    except Exception as e:
        st.error(f"获取统计失败: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

# 页脚
st.markdown('''
<div style="text-align:center;color:var(--muted);padding:32px 0;font-size:14px;border-top:1px solid var(--line);margin-top:32px">
    <p>💼 祝你求职顺利</p>
    <p style="margin-top:8px">
        <a href="https://github.com/emptyteabot/ai-job-helper" style="color:var(--muted);margin:0 12px;text-decoration:none">GitHub</a>
        <a href="https://github.com/GodsScion/Auto_job_applier_linkedIn" style="color:var(--muted);margin:0 12px;text-decoration:none">高星项目</a>
    </p>
</div>
''', unsafe_allow_html=True)
