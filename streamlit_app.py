"""
AI求职助手 - Streamlit 完整版
简历分析 + 自动投递 - 全部功能集成
"""
import streamlit as st
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="AI求职助手",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 全局样式 - OpenAI 打字机风格
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');
:root{--bg:#fff;--text:#131313;--muted:#64646b;--line:#e8e8ec;--soft:#f7f7f9}
*{font-family:'Noto Sans SC',sans-serif;box-sizing:border-box}
#MainMenu,footer,header{visibility:hidden}
.main .block-container{max-width:980px;padding:1.5rem 1rem 3rem}
.top-nav{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line);padding:10px 0 16px;margin-bottom:2rem}
.brand{display:flex;align-items:center;gap:9px;font-size:16px;font-weight:800}
.dot{width:8px;height:8px;border-radius:50%;background:#121212;box-shadow:0 0 0 6px rgba(18,18,18,0.08)}
.hero{padding:52px 0 34px}
.pill{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--line);border-radius:999px;background:#fff;color:var(--muted);padding:6px 11px;font:500 12px/1 'IBM Plex Mono',monospace;margin-bottom:16px}
.pill::before{content:"";width:5px;height:5px;border-radius:50%;background:#121212}
.hero h1{font-size:clamp(48px,9vw,84px);font-weight:800;letter-spacing:-1.8px;line-height:1.04;margin-bottom:20px}
.hero-subtitle{color:var(--muted);font-size:24px;line-height:1.75;max-width:780px}
.cursor{display:inline-block;width:8px;height:1em;margin-left:4px;background:#151515;vertical-align:-2px;animation:blink 1s steps(1,end) infinite}
@keyframes blink{0%,48%{opacity:1}49%,100%{opacity:0}}
.panel{border:1px solid var(--line);border-radius:18px;background:#fff;padding:28px;margin-bottom:20px}
.panel h2{font-size:28px;font-weight:700;margin-bottom:16px}
.panel p{font-size:18px;color:var(--muted);line-height:1.6;margin-bottom:20px}
.stButton>button{border:1px solid #121212;background:#121212;color:white;border-radius:12px;padding:16px 28px;font-size:18px;font-weight:700}
.stButton>button:hover{background:#2a2a2a;transform:translateY(-1px)}
.stTextInput>div>div>input,.stTextArea>div>div>textarea{border:1px solid var(--line);border-radius:14px;padding:16px;font-size:18px}
.stTextArea>div>div>textarea{min-height:280px}
.stTabs [data-baseweb="tab-list"]{gap:12px;border-bottom:1px solid var(--line)}
.stTabs [data-baseweb="tab"]{padding:14px 24px;font-size:18px;font-weight:500;color:var(--muted)}
.stTabs [aria-selected="true"]{color:var(--text);border-bottom:2px solid var(--text)}
</style>
""", unsafe_allow_html=True)

# 顶部导航
st.markdown('<div class="top-nav"><div class="brand"><div class="dot"></div><span>AI求职助手</span></div></div>', unsafe_allow_html=True)

# Hero 区域
st.markdown('''
<div class="hero">
    <div class="pill">专为大学生实习设计</div>
    <h1>让 AI 帮你找到<br>理想工作<span class="cursor"></span></h1>
    <div class="hero-subtitle">6 个 AI 协作分析简历，智能推荐岗位，自动投递到 Boss直聘、智联招聘、LinkedIn</div>
</div>
''', unsafe_allow_html=True)

# 标签页
tab1, tab2 = st.tabs(["📄 简历分析", "🚀 自动投递"])

with tab1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("## 📄 AI 简历分析")

    col1, col2 = st.columns([2, 1])

    with col1:
        method = st.radio("选择输入方式", ["上传文件", "文本输入"], horizontal=True)

        if method == "上传文件":
            uploaded_file = st.file_uploader("支持 PDF、Word、图片", type=["pdf", "doc", "docx", "png", "jpg", "jpeg"])
            if uploaded_file:
                st.success(f"✓ 已上传: {uploaded_file.name}")

                if st.button("开始分析", type="primary", key="analyze_file"):
                    with st.spinner("🔄 AI 正在分析您的简历..."):
                        try:
                            # 导入分析引擎
                            from app.core.multi_ai_debate import JobApplicationPipeline

                            # 读取文件内容
                            file_content = uploaded_file.read()

                            # 如果是文本文件，直接解码
                            if uploaded_file.type == "text/plain":
                                resume_text = file_content.decode('utf-8')
                            else:
                                # 对于 PDF/Word/图片，需要 OCR 或解析
                                # 这里简化处理，提示用户使用文本输入
                                st.warning("⚠️ 文件解析功能开发中，请使用文本输入方式")
                                resume_text = None

                            if resume_text:
                                # 创建分析管道
                                pipeline = JobApplicationPipeline()

                                # 执行分析
                                results = await pipeline.process_resume(resume_text)

                                # 显示结果
                                st.success("✅ 分析完成！")

                                # 显示各个分析结果
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

                        except Exception as e:
                            st.error(f"❌ 分析失败: {str(e)}")
        else:
            resume_text = st.text_area("粘贴简历内容", height=280, placeholder="请在此粘贴您的简历内容...")

            if resume_text and st.button("开始分析", type="primary", key="analyze_text"):
                with st.spinner("🔄 AI 正在分析您的简历..."):
                    try:
                        # 导入分析引擎
                        from app.core.multi_ai_debate import JobApplicationPipeline
                        import asyncio

                        # 创建分析管道
                        pipeline = JobApplicationPipeline()

                        # 执行分析（同步方式）
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        results = loop.run_until_complete(pipeline.process_resume(resume_text))
                        loop.close()

                        # 显示结果
                        st.success("✅ 分析完成！")

                        # 使用标签页显示结果
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

                    except Exception as e:
                        st.error(f"❌ 分析失败: {str(e)}")
                        st.info("💡 提示：请确保已配置 API Key")

    with col2:
        st.markdown("""### 分析内容
- 🎯 职业分析
- 💼 岗位推荐
- ✍️ 简历优化
- 📚 面试准备
- 🎤 模拟面试
- 📈 技能分析""")

    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("## 🚀 自动投递")

    platforms = st.multiselect("选择平台", ["Boss直聘", "智联招聘", "LinkedIn"], default=["Boss直聘"])

    if platforms:
        col1, col2 = st.columns(2)

        with col1:
            keywords = st.text_input("搜索关键词", value="实习生,应届生")
            locations = st.text_input("工作地点", value="北京,上海,深圳")

        with col2:
            max_count = st.number_input("投递数量", 1, 500, 50)
            interval = st.slider("投递间隔（秒）", 3, 30, 5)

        if st.button("开始投递", type="primary"):
            st.warning("⚠️ 自动投递功能需要浏览器自动化环境")
            st.info("""
            **本地运行说明：**

            1. 安装依赖：
            ```bash
            pip install playwright
            playwright install chromium
            ```

            2. 运行后端：
            ```bash
            python web_app.py
            ```

            3. 访问：http://localhost:8000

            **注意：** Streamlit Cloud 不支持浏览器自动化，需要本地运行。
            """)

    st.markdown('</div>', unsafe_allow_html=True)

# 页脚
st.markdown("---")
st.markdown('''
<div style="text-align:center;color:var(--muted);padding:32px 0;font-size:16px">
    <p>💼 祝你求职顺利</p>
    <p>
        <a href="https://github.com/emptyteabot/ai-job-helper" style="color:var(--text);margin:0 16px">GitHub</a>
        <a href="https://ai-job-apper-ibpzap2nnajzrnu8mkthuv.streamlit.app" style="color:var(--text);margin:0 16px">在线体验</a>
    </p>
</div>
''', unsafe_allow_html=True)
