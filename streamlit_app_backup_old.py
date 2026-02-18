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

/* 隐藏右下角的管理按钮和其他 Streamlit 默认元素 */
.stDeployButton,
button[kind="header"],
[data-testid="stToolbar"],
[data-testid="manage-app"],
.viewerBadge_container__1QSob,
.styles_viewerBadge__1yB5_,
footer,
#MainMenu {
    display: none !important;
    visibility: hidden !important;
}

.main .block-container {
    max-width: var(--maxw);
    padding: 2rem 1.5rem 4rem;
    line-height: 1.8;
}

/* 增加所有文本的行间距 */
p, li, div {
    line-height: 1.8;
    margin-bottom: 0.8em;
}

/* 标题间距 */
h1, h2, h3, h4 {
    margin-top: 1.5em;
    margin-bottom: 0.8em;
    line-height: 1.3;
}

/* 列表间距 */
ul, ol {
    margin: 1em 0;
    padding-left: 2em;
}

li {
    margin-bottom: 0.6em;
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
    text-align: center;
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
    font: 500 14px/1 "IBM Plex Mono", monospace;
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
    font-size: clamp(50px, 9vw, 84px);
    letter-spacing: -1.4px;
    line-height: 1.1;
    margin-bottom: 12px;
    text-align: center;
}

.sub {
    color: var(--muted);
    font-size: 25px;
    line-height: 1.65;
    max-width: 680px;
    text-align: center;
    margin: 0 auto;
}

/* 面板 */
.panel {
    border: 1px solid var(--line);
    border-radius: 18px;
    background: #fff;
    padding: 32px;
    margin-bottom: 24px;
    line-height: 1.8;
}

.panel h2 {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 20px;
    line-height: 1.3;
}

.panel p {
    color: var(--muted);
    font-size: 19px;
    line-height: 1.8;
    margin-bottom: 20px;
}

/* 按钮 */
.stButton > button {
    background: var(--primary);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 14px 28px;
    font-size: 18px;
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
    padding: 14px;
    font-size: 18px;
}

.stTextArea > div > div > textarea {
    min-height: 200px;
}

/* 标签页 */
.stTabs [data-baseweb="tab-list"] {
    gap: 16px;
    border-bottom: 1px solid var(--line);
    margin-bottom: 24px;
}

.stTabs [data-baseweb="tab"] {
    padding: 16px 28px;
    font-size: 18px;
    font-weight: 500;
    color: var(--muted);
}

.stTabs [aria-selected="true"] {
    color: var(--text);
    border-bottom: 2px solid var(--text);
}

/* Expander 间距 */
.stExpander {
    margin-bottom: 16px;
    border: 1px solid var(--line);
    border-radius: 12px;
}

.stExpander > div {
    padding: 20px;
}

/* Markdown 内容间距 */
.stMarkdown {
    line-height: 1.8;
}

.stMarkdown p {
    margin-bottom: 1em;
}

.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    margin-top: 1.5em;
    margin-bottom: 0.8em;
}

.stMarkdown ul, .stMarkdown ol {
    margin: 1em 0;
    padding-left: 2em;
}

.stMarkdown li {
    margin-bottom: 0.6em;
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
    font-size: 22px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 8px;
}

.job-meta {
    display: flex;
    gap: 16px;
    font-size: 17px;
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
    font-size: 42px;
    font-weight: 800;
    color: var(--primary);
    margin-bottom: 6px;
}

.stat-label {
    font-size: 17px;
    color: var(--muted);
}
</style>
""", unsafe_allow_html=True)

# 配置 API Key - 从 Streamlit Secrets 读取
try:
    # 优先使用 DeepSeek API
    deepseek_keys = st.secrets.get("DEEPSEEK_API_KEYS", [])
    deepseek_key = st.secrets.get("DEEPSEEK_API_KEY", "")

    if deepseek_keys:
        # 多个 Key 轮换使用
        import random
        os.environ['OPENAI_API_KEY'] = random.choice(deepseek_keys)
        os.environ['DEEPSEEK_API_KEYS'] = ','.join(deepseek_keys)  # 传递所有 Key
    elif deepseek_key:
        os.environ['OPENAI_API_KEY'] = deepseek_key
    else:
        # 备用 OpenAI API
        os.environ['OPENAI_API_KEY'] = st.secrets.get("OPENAI_API_KEY", "")
        os.environ['OPENAI_BASE_URL'] = st.secrets.get("OPENAI_BASE_URL", "https://oneapi.gemiaude.com/v1")

    if deepseek_keys or deepseek_key:
        os.environ['OPENAI_BASE_URL'] = st.secrets.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        # 使用推理模型 deepseek-reasoner
        os.environ['DEEPSEEK_MODEL'] = st.secrets.get("DEEPSEEK_MODEL", "deepseek-reasoner")
        os.environ['DEEPSEEK_REASONING_MODEL'] = st.secrets.get("DEEPSEEK_REASONING_MODEL", "deepseek-reasoner")

    if not os.environ['OPENAI_API_KEY']:
        st.error("⚠️ 请在 Streamlit Cloud Secrets 中配置 API Key")
        st.info("Settings → Secrets → 添加:\nDEEPSEEK_API_KEY = \"sk-xxx\"\nDEEPSEEK_BASE_URL = \"https://api.deepseek.com\"")
except Exception as e:
    st.error(f"API Key 配置错误: {str(e)}")

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

# 简历分析函数（使用优化的推理模型流程）
def analyze_resume(resume_text, progress_placeholder=None):
    """简历分析 - 使用推理模型，4个核心Agent"""
    try:
        from app.core.optimized_pipeline import OptimizedJobPipeline
        import time

        if progress_placeholder:
            progress_placeholder.info("🔄 初始化推理引擎（DeepSeek Reasoner）...")

        pipeline = OptimizedJobPipeline()

        if progress_placeholder:
            progress_placeholder.info("🧠 4个专家 AI 正在深度分析（预计 2-4 分钟）...")

        start_time = time.time()

        # 使用优化的推理流程
        results = pipeline.process_resume(resume_text)

        elapsed = time.time() - start_time

        if progress_placeholder:
            progress_placeholder.success(f"✅ 深度分析完成！耗时 {elapsed:.1f} 秒")

        return results

    except Exception as e:
        if progress_placeholder:
            progress_placeholder.error(f"❌ 分析失败: {str(e)}")
        else:
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
                progress_placeholder = st.empty()
                results = analyze_resume(resume_text, progress_placeholder)

                if results:
                    st.session_state.analysis_results = results

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
                    progress_placeholder = st.empty()
                    results = analyze_resume(resume_text, progress_placeholder)

                    if results:
                        st.session_state.analysis_results = results

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

# Tab2: 岗位推荐（直接集成，无需后端）
with tab2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("## 💼 岗位推荐")
    st.markdown("<p>基于简历分析结果，智能推荐匹配岗位</p>", unsafe_allow_html=True)

    if st.session_state.analysis_results and 'job_recommendations' in st.session_state.analysis_results:
        st.markdown("### 📋 推荐岗位")
        st.markdown(st.session_state.analysis_results['job_recommendations'])
    else:
        st.info("💡 请先在「简历分析」标签页完成简历分析，系统会自动推荐匹配岗位")

        st.markdown("### 🔍 或者手动搜索岗位")
        col1, col2 = st.columns(2)
        with col1:
            keywords = st.text_input("搜索关键词", value="Python开发", key="manual_search_keywords")
        with col2:
            location = st.text_input("工作地点", value="北京", key="manual_search_location")

        if st.button("搜索岗位", type="primary", key="manual_search_btn"):
            st.info("🚧 手动搜索功能开发中，建议先完成简历分析获取智能推荐")

    st.markdown('</div>', unsafe_allow_html=True)

# Tab3: 自动投递（直接集成）
with tab3:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("## 🚀 自动投递")
    st.markdown("<p>自动投递到 Boss直聘、智联招聘、LinkedIn</p>", unsafe_allow_html=True)

    st.warning("⚠️ 自动投递功能需要浏览器自动化，建议本地运行")

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
            st.info("🚧 自动投递功能需要本地运行完整版")
            st.markdown("""
            **本地运行步骤：**
            1. 下载完整代码：`git clone https://github.com/emptyteabot/ai-job-helper.git`
            2. 安装依赖：`pip install -r requirements.txt`
            3. 运行：`streamlit run streamlit_app.py`
            4. 或运行后端：`python web_app.py`
            """)

    st.markdown('</div>', unsafe_allow_html=True)

# Tab4: 数据统计（用户隔离）
with tab4:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("## 📊 数据统计")
    st.markdown(f"<p>用户ID: {st.session_state.user_id[:8]}...</p>", unsafe_allow_html=True)

    # 模拟数据（实际应该从数据库读取）
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">0</div>
            <div class="stat-label">总投递</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">0%</div>
            <div class="stat-label">回复率</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">0</div>
            <div class="stat-label">面试邀请</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">0</div>
            <div class="stat-label">Offer</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📋 投递记录")
    st.info("💡 完成简历分析和投递后，数据会显示在这里（仅你可见）")

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
