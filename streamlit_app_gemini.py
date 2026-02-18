"""
AI求职助手 - Gemini + Material Design 风格
酷炫的渐变、动画和现代设计
"""
import streamlit as st
import requests
import json
from pathlib import Path
import time

# 页面配置
st.set_page_config(
    page_title="AI求职助手 | Gemini Style",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Material Design + Google 风格 CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto:wght@300;400;500;700&display=swap');

:root {
    --google-blue: #4285f4;
    --google-red: #ea4335;
    --google-yellow: #fbbc04;
    --google-green: #34a853;
    --purple: #9c27b0;
    --deep-purple: #673ab7;
    --shadow-1: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    --shadow-2: 0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23);
    --shadow-3: 0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23);
    --shadow-4: 0 14px 28px rgba(0,0,0,0.25), 0 10px 10px rgba(0,0,0,0.22);
}

/* 全局背景渐变动画 */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #4facfe 75%, #00f2fe 100%);
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
    font-family: 'Roboto', sans-serif;
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Hero 区域 */
.hero-section {
    background: linear-gradient(135deg, rgba(66, 133, 244, 0.95) 0%, rgba(156, 39, 176, 0.95) 100%);
    border-radius: 24px;
    padding: 48px 32px;
    margin: 24px 0;
    box-shadow: var(--shadow-4);
    position: relative;
    overflow: hidden;
    animation: fadeInUp 0.8s ease-out;
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
    font-family: 'Google Sans', sans-serif;
    font-size: 48px;
    font-weight: 700;
    color: white;
    margin: 0;
    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    position: relative;
    z-index: 1;
    animation: slideInLeft 0.8s ease-out;
}

.hero-subtitle {
    font-size: 20px;
    color: rgba(255,255,255,0.9);
    margin-top: 16px;
    position: relative;
    z-index: 1;
    animation: slideInLeft 1s ease-out;
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

/* Material Design 卡片 */
.material-card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    box-shadow: var(--shadow-2);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    animation: fadeInUp 0.6s ease-out;
}

.material-card:hover {
    box-shadow: var(--shadow-4);
    transform: translateY(-4px);
}

/* 胶囊按钮 */
.pill-button {
    display: inline-block;
    background: linear-gradient(135deg, var(--google-blue) 0%, var(--deep-purple) 100%);
    color: white;
    padding: 12px 32px;
    border-radius: 999px;
    font-weight: 500;
    text-decoration: none;
    box-shadow: var(--shadow-2);
    transition: all 0.3s ease;
    border: none;
    cursor: pointer;
    font-size: 16px;
}

.pill-button:hover {
    box-shadow: var(--shadow-3);
    transform: translateY(-2px);
}

/* 品牌点动画 */
.brand-dot {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--google-blue);
    margin-right: 8px;
    animation: pulse 2s ease-in-out infinite;
    box-shadow: 0 0 0 0 rgba(66, 133, 244, 0.7);
}

@keyframes pulse {
    0% {
        box-shadow: 0 0 0 0 rgba(66, 133, 244, 0.7);
    }
    70% {
        box-shadow: 0 0 0 10px rgba(66, 133, 244, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(66, 133, 244, 0);
    }
}

/* 步骤指示器 */
.step-indicator {
    display: flex;
    justify-content: space-between;
    margin: 32px 0;
    padding: 0 16px;
}

.step {
    flex: 1;
    text-align: center;
    position: relative;
}

.step-circle {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: white;
    border: 3px solid #e0e0e0;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 8px;
    font-weight: 700;
    color: #9e9e9e;
    transition: all 0.3s ease;
}

.step.active .step-circle {
    background: linear-gradient(135deg, var(--google-blue), var(--purple));
    border-color: var(--google-blue);
    color: white;
    box-shadow: var(--shadow-2);
    animation: scaleIn 0.5s ease-out;
}

.step.done .step-circle {
    background: var(--google-green);
    border-color: var(--google-green);
    color: white;
}

@keyframes scaleIn {
    from { transform: scale(0.8); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
}

/* 工作卡片 */
.job-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin: 12px 0;
    box-shadow: var(--shadow-1);
    transition: all 0.3s ease;
    border-left: 4px solid var(--google-blue);
}

.job-card:hover {
    box-shadow: var(--shadow-3);
    transform: translateX(4px);
}

.job-title {
    font-size: 18px;
    font-weight: 700;
    color: #202124;
    margin-bottom: 8px;
}

.job-company {
    font-size: 14px;
    color: #5f6368;
    margin-bottom: 12px;
}

.job-link {
    display: inline-block;
    color: var(--google-blue);
    text-decoration: none;
    font-weight: 500;
    transition: all 0.2s ease;
}

.job-link:hover {
    color: var(--deep-purple);
    text-decoration: underline;
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

/* Streamlit 组件覆盖 */
.stButton > button {
    background: linear-gradient(135deg, var(--google-blue) 0%, var(--deep-purple) 100%);
    color: white;
    border: none;
    border-radius: 999px;
    padding: 12px 32px;
    font-weight: 500;
    box-shadow: var(--shadow-2);
    transition: all 0.3s ease;
}

.stButton > button:hover {
    box-shadow: var(--shadow-3);
    transform: translateY(-2px);
}

.stTextArea textarea, .stTextInput input {
    border-radius: 12px;
    border: 2px solid #e0e0e0;
    transition: all 0.3s ease;
}

.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--google-blue);
    box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.1);
}

/* 标签 */
.tag {
    display: inline-block;
    background: linear-gradient(135deg, rgba(66, 133, 244, 0.1), rgba(156, 39, 176, 0.1));
    color: var(--deep-purple);
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 500;
    margin: 4px;
}

/* 加载动画 */
.loading-spinner {
    display: inline-block;
    width: 40px;
    height: 40px;
    border: 4px solid rgba(66, 133, 244, 0.2);
    border-top-color: var(--google-blue);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* 隐藏 Streamlit 默认元素 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Hero 区域
st.markdown("""
<div class="hero-section">
    <div class="hero-badge">
        <span class="brand-dot"></span>
        AI-Powered • Material Design • Gemini Style
    </div>
    <h1 class="hero-title">AI 求职助手</h1>
    <p class="hero-subtitle">智能简历分析 • 自动职位匹配 • 面试准备 • 一站式求职解决方案</p>
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
steps = ["上传简历", "AI分析", "职位匹配", "生成报告"]
step_html = '<div class="step-indicator">'
for i, step_name in enumerate(steps, 1):
    status = "done" if i < st.session_state.step else ("active" if i == st.session_state.step else "")
    step_html += f'''
    <div class="step {status}">
        <div class="step-circle">{i}</div>
        <div style="font-size: 14px; color: #5f6368; font-weight: 500;">{step_name}</div>
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
            st.success(f"✅ 已上传: {uploaded_file.name}")
            st.session_state.step = max(st.session_state.step, 1)

            # 调用上传 API
            try:
                files = {'file': uploaded_file}
                response = requests.post('http://localhost:8000/api/upload', files=files)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        st.session_state.resume_text = data.get('resume_text', '')
                        st.info(f"📝 已解析 {len(st.session_state.resume_text)} 个字符")
            except Exception as e:
                st.error(f"上传失败: {str(e)}")

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
            if st.button("🚀 开始分析", use_container_width=True):
                if not st.session_state.resume_text:
                    st.error("请先上传或粘贴简历！")
                else:
                    st.session_state.step = 2
                    with st.spinner("AI 正在分析中..."):
                        try:
                            response = requests.post(
                                'http://localhost:8000/api/process',
                                json={'resume': st.session_state.resume_text}
                            )
                            if response.status_code == 200:
                                st.session_state.analysis_result = response.json()
                                st.session_state.step = 4
                                st.success("✅ 分析完成！")
                                st.rerun()
                            else:
                                st.error("分析失败，请重试")
                        except Exception as e:
                            st.error(f"错误: {str(e)}")

        with col_btn2:
            if st.button("📝 加载示例", use_container_width=True):
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
            if st.button("🔄 重置", use_container_width=True):
                st.session_state.resume_text = ""
                st.session_state.analysis_result = None
                st.session_state.step = 0
                st.rerun()

    with col2:
        st.markdown("### 📊 分析结果")

        if st.session_state.analysis_result:
            result = st.session_state.analysis_result

            # 职业分析
            with st.expander("🎯 职业分析", expanded=True):
                st.markdown(f"```\n{result.get('career_analysis', '暂无数据')}\n```")

            # 职位推荐
            with st.expander("💼 职位推荐", expanded=True):
                st.markdown(f"```\n{result.get('job_recommendations', '暂无数据')}\n```")

            # 优化简历
            with st.expander("✨ 优化简历", expanded=False):
                st.markdown(f"```\n{result.get('optimized_resume', '暂无数据')}\n```")

            # 面试准备
            with st.expander("🎤 面试准备", expanded=False):
                st.markdown(f"```\n{result.get('interview_prep', '暂无数据')}\n```")

            # 模拟面试
            with st.expander("🎭 模拟面试", expanded=False):
                st.markdown(f"```\n{result.get('mock_interview', '暂无数据')}\n```")

            # 下载按钮
            if st.button("📥 下载完整报告", use_container_width=True):
                report = f"""
{'='*50}
AI 求职助手 - 完整分析报告
{'='*50}

【职业分析】
{result.get('career_analysis', '暂无数据')}

【职位推荐】
{result.get('job_recommendations', '暂无数据')}

【优化简历】
{result.get('optimized_resume', '暂无数据')}

【面试准备】
{result.get('interview_prep', '暂无数据')}

【模拟面试】
{result.get('mock_interview', '暂无数据')}
"""
                st.download_button(
                    label="💾 下载 TXT 文件",
                    data=report,
                    file_name="ai_job_report.txt",
                    mime="text/plain"
                )
        else:
            st.info("👈 请先上传简历并点击「开始分析」")

    st.markdown('</div>', unsafe_allow_html=True)

    # 实时职位推荐
    if st.session_state.analysis_result:
        st.markdown('<div class="material-card">', unsafe_allow_html=True)
        st.markdown("### 🔥 实时职位推荐")

        try:
            seed = st.session_state.analysis_result.get('boss_seed', {})
            keywords = seed.get('keywords', [])
            location = seed.get('location', '')

            if keywords:
                params = {
                    'keywords': ','.join(keywords[:3]),
                    'location': location,
                    'limit': 6
                }
                response = requests.get('http://localhost:8000/api/jobs/search', params=params)
                if response.status_code == 200:
                    jobs_data = response.json()
                    if jobs_data.get('success'):
                        jobs = jobs_data.get('jobs', [])

                        if jobs:
                            cols = st.columns(2)
                            for idx, job in enumerate(jobs):
                                with cols[idx % 2]:
                                    st.markdown(f"""
                                    <div class="job-card">
                                        <div class="job-title">{job.get('title', '未知职位')}</div>
                                        <div class="job-company">
                                            🏢 {job.get('company', '未知公司')} |
                                            📍 {job.get('location', '未知地点')}
                                        </div>
                                        <div class="job-company">
                                            💰 {job.get('salary', '面议')} |
                                            🔖 {job.get('platform', '未知平台')}
                                        </div>
                                        <a href="{job.get('link', '#')}" target="_blank" class="job-link">
                                            🔗 查看职位详情 →
                                        </a>
                                    </div>
                                    """, unsafe_allow_html=True)
                        else:
                            st.info("暂无匹配职位")
        except Exception as e:
            st.warning(f"职位推荐加载失败: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="material-card">', unsafe_allow_html=True)
    st.markdown("### 🚀 自动投递功能")
    st.info("🚧 此功能正在开发中，敬请期待！")

    st.markdown("""
    #### 即将推出的功能：
    - ✅ 一键批量投递简历
    - ✅ 智能职位筛选
    - ✅ 自动填写申请表
    - ✅ 投递进度追踪
    - ✅ 面试邀请提醒
    """)
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="material-card">', unsafe_allow_html=True)
    st.markdown("### 📚 文档中心")

    doc_col1, doc_col2 = st.columns(2)

    with doc_col1:
        st.markdown("""
        #### 📖 使用指南
        - [快速开始](javascript:void(0))
        - [简历优化技巧](javascript:void(0))
        - [面试准备指南](javascript:void(0))
        - [职位搜索技巧](javascript:void(0))
        """)

    with doc_col2:
        st.markdown("""
        #### 🔧 API 文档
        - [API 接口说明](javascript:void(0))
        - [数据格式规范](javascript:void(0))
        - [错误代码说明](javascript:void(0))
        - [集成示例](javascript:void(0))
        """)

    st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="material-card">', unsafe_allow_html=True)
    st.markdown("### ❓ 帮助中心")

    with st.expander("❓ 如何上传简历？"):
        st.markdown("""
        1. 点击「上传简历」按钮
        2. 选择 PDF、DOCX 或 TXT 格式的简历文件
        3. 或直接在文本框中粘贴简历内容
        4. 点击「开始分析」按钮
        """)

    with st.expander("❓ 支持哪些文件格式？"):
        st.markdown("""
        - PDF (.pdf)
        - Word 文档 (.docx, .doc)
        - 纯文本 (.txt)
        - 图片 (.jpg, .jpeg, .png)
        """)

    with st.expander("❓ 分析需要多长时间？"):
        st.markdown("""
        通常需要 10-30 秒，具体取决于：
        - 简历长度
        - 服务器负载
        - AI 模型响应速度
        """)

    with st.expander("❓ 如何获取更多职位推荐？"):
        st.markdown("""
        1. 确保简历中包含详细的技能和经验
        2. 系统会自动提取关键词进行匹配
        3. 可以在简历中添加期望地点和职位类型
        """)

    with st.expander("❓ 数据安全吗？"):
        st.markdown("""
        - ✅ 所有数据仅用于分析
        - ✅ 不会存储您的个人信息
        - ✅ 使用加密传输
        - ✅ 符合数据保护法规
        """)

    st.markdown("---")
    st.markdown("""
    ### 📧 联系我们
    - 📮 邮箱: support@aijob.com
    - 💬 微信: AI_Job_Helper
    - 🌐 官网: https://aijob.com
    """)

    st.markdown('</div>', unsafe_allow_html=True)

# 页脚
st.markdown("""
<div style="text-align: center; padding: 32px; color: white; font-size: 14px;">
    <div class="brand-dot"></div>
    <strong>AI 求职助手</strong> | Powered by Gemini & Material Design
    <br>
    <span style="opacity: 0.8;">© 2026 All Rights Reserved</span>
</div>
""", unsafe_allow_html=True)
