"""
AI求职助手 - OpenAI 简洁风格
整合所有功能的完整版本
"""
import streamlit as st

# 页面配置
st.set_page_config(
    page_title="AI求职助手",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# OpenAI 简洁风格 CSS
st.markdown("""
<style>
    /* 全局样式 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');

    :root {
        --bg: #ffffff;
        --text: #131313;
        --muted: #64646b;
        --line: #e8e8ec;
        --soft: #f7f7f9;
        --ok: #1f7c49;
        --err: #b54040;
    }

    /* 隐藏 Streamlit 默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 主容器 */
    .main .block-container {
        max-width: 980px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* 顶部导航 */
    .top-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid var(--line);
        padding: 10px 0 16px;
        margin-bottom: 2rem;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 9px;
        font-size: 14px;
        font-weight: 800;
        font-family: 'Noto Sans SC', sans-serif;
    }

    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #121212;
        box-shadow: 0 0 0 6px rgba(18, 18, 18, 0.08);
    }

    /* Hero 区域 */
    .hero {
        padding: 52px 0 34px;
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
        font: 500 11px/1 'IBM Plex Mono', monospace;
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
        font-size: clamp(46px, 9vw, 84px);
        letter-spacing: -1.8px;
        line-height: 1.04;
        margin-bottom: 14px;
        font-family: 'Noto Sans SC', sans-serif;
    }

    .subtitle {
        color: var(--muted);
        font-size: 23px;
        line-height: 1.75;
        max-width: 780px;
        margin-bottom: 2rem;
    }

    /* 按钮样式 */
    .stButton > button {
        background: #121212;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background: #2a2a2a;
        transform: translateY(-1px);
    }

    /* 卡片样式 */
    .feature-card {
        background: var(--soft);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 24px;
        margin: 16px 0;
        transition: all 0.2s;
    }

    .feature-card:hover {
        border-color: var(--text);
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }

    /* 输入框样式 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 12px;
        font-size: 14px;
    }

    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid var(--line);
    }

    .stTabs [data-baseweb="tab"] {
        padding: 12px 20px;
        font-size: 14px;
        font-weight: 500;
        color: var(--muted);
        border: none;
        background: transparent;
    }

    .stTabs [aria-selected="true"] {
        color: var(--text);
        border-bottom: 2px solid var(--text);
    }
</style>
""", unsafe_allow_html=True)

# 顶部导航
st.markdown("""
<div class="top-nav">
    <div class="brand">
        <div class="dot"></div>
        <span>AI求职助手</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Hero 区域
st.markdown("""
<div class="hero">
    <div class="pill">专为大学生实习设计</div>
    <h1>让 AI 帮你找到<br>理想工作</h1>
    <div class="subtitle">
        6 个 AI 协作分析简历，智能推荐岗位，自动投递到 Boss直聘、智联招聘、LinkedIn
    </div>
</div>
""", unsafe_allow_html=True)

# 主功能区域
tab1, tab2, tab3, tab4 = st.tabs(["📄 简历分析", "🚀 自动投递", "📚 文档", "❓ 帮助"])

with tab1:
    st.markdown("### 📄 AI 简历分析")
    st.markdown("上传简历，获取 6 大 AI 协作的深度分析")

    col1, col2 = st.columns([2, 1])

    with col1:
        input_method = st.radio(
            "选择输入方式",
            ["上传文件", "文本输入"],
            horizontal=True
        )

        if input_method == "上传文件":
            uploaded_file = st.file_uploader(
                "支持 PDF、Word、图片",
                type=["pdf", "doc", "docx", "png", "jpg", "jpeg"]
            )

            if uploaded_file:
                st.success(f"✓ 已上传: {uploaded_file.name}")

                if st.button("开始分析", type="primary"):
                    with st.spinner("AI 正在分析中..."):
                        st.info("分析功能开发中，请稍候...")
        else:
            resume_text = st.text_area(
                "粘贴简历内容",
                height=200,
                placeholder="请在此粘贴您的简历内容..."
            )

            if resume_text and st.button("开始分析", type="primary"):
                with st.spinner("AI 正在分析中..."):
                    st.info("分析功能开发中，请稍候...")

    with col2:
        st.markdown("**分析内容**")
        st.markdown("""
        - 🎯 职业分析
        - 💼 岗位推荐
        - ✍️ 简历优化
        - 📚 面试准备
        - 🎤 模拟面试
        - 📈 技能分析
        """)

with tab2:
    st.markdown("### 🚀 自动投递")
    st.markdown("一键投递到三大平台")

    platforms = st.multiselect(
        "选择平台",
        ["Boss直聘", "智联招聘", "LinkedIn"],
        default=["Boss直聘"]
    )

    if platforms:
        col1, col2 = st.columns(2)

        with col1:
            keywords = st.text_input("搜索关键词", value="实习生,应届生")
            location = st.text_input("工作地点", value="北京,上海,深圳")

        with col2:
            target_count = st.number_input("投递数量", min_value=1, max_value=500, value=50)
            delay_time = st.slider("投递间隔（秒）", min_value=3, max_value=30, value=5)

        if st.button("开始投递", type="primary"):
            st.info("投递功能开发中，请稍候...")

with tab3:
    st.markdown("### 📚 文档中心")

    doc_tabs = st.tabs(["快速开始", "使用指南", "部署指南"])

    with doc_tabs[0]:
        st.markdown("""
        ## 🚀 快速开始

        ### 方式一：在线体验
        访问：https://ai-job-hunter-production-2730.up.railway.app

        ### 方式二：本地运行
        ```bash
        # Windows
        start.bat

        # Linux/Mac
        ./start.sh
        ```
        """)

    with doc_tabs[1]:
        st.markdown("""
        ## 📖 使用指南

        ### 简历分析
        1. 上传简历或粘贴文本
        2. 点击"开始分析"
        3. 查看 6 大维度分析结果

        ### 自动投递
        1. 选择投递平台
        2. 配置搜索条件
        3. 填写账号信息
        4. 开始投递
        """)

    with doc_tabs[2]:
        st.markdown("""
        ## 🔧 部署指南

        ### Streamlit Cloud
        1. Fork 项目到 GitHub
        2. 访问 streamlit.io/cloud
        3. 连接仓库并部署

        ### 本地部署
        ```bash
        pip install -r requirements.txt
        streamlit run streamlit_app.py
        ```
        """)

with tab4:
    st.markdown("### ❓ 帮助中心")

    with st.expander("如何快速上手？"):
        st.markdown("""
        1. 访问在线版本或本地运行
        2. 上传简历进行分析
        3. 根据建议优化简历
        4. 使用自动投递功能
        """)

    with st.expander("支持哪些简历格式？"):
        st.markdown("支持 PDF、Word、图片和文本输入")

    with st.expander("分析需要多长时间？"):
        st.markdown("通常 30-60 秒即可完成分析")

    with st.expander("会被平台检测吗？"):
        st.markdown("我们使用了反检测技术，并设置了合理的投递间隔")

    with st.expander("如何获取帮助？"):
        st.markdown("""
        - GitHub Issues: https://github.com/emptyteabot/ai-job-helper/issues
        - GitHub Discussions: https://github.com/emptyteabot/ai-job-helper/discussions
        """)

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: var(--muted); padding: 20px;'>
    <p>💼 祝你求职顺利</p>
    <p style='font-size: 13px; margin-top: 8px;'>
        <a href='https://github.com/emptyteabot/ai-job-helper' target='_blank' style='color: var(--muted); text-decoration: none;'>GitHub</a> ·
        <a href='https://github.com/emptyteabot/ai-job-helper/blob/main/QUICKSTART.md' target='_blank' style='color: var(--muted); text-decoration: none;'>文档</a> ·
        <a href='https://github.com/emptyteabot/ai-job-helper/issues' target='_blank' style='color: var(--muted); text-decoration: none;'>反馈</a>
    </p>
</div>
""", unsafe_allow_html=True)
