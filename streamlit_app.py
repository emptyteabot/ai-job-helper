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

# 全局样式 - Gemini 风格
from ui_styles_gemini import GEMINI_STYLE
st.markdown(GEMINI_STYLE, unsafe_allow_html=True)

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

# 简历分析函数（流式显示 + 伪进度条）
def analyze_resume_streaming(resume_text, progress_placeholder=None, result_containers=None):
    """简历分析 - 流式显示每个 Agent 的结果 + 伪进度条"""
    try:
        from app.core.optimized_pipeline import OptimizedJobPipeline
        from app.components.progress import FakeProgressBar
        import time
        import threading

        if progress_placeholder:
            progress_placeholder.info("🔄 初始化 AI 引擎...")

        pipeline = OptimizedJobPipeline()

        # 创建结果字典
        results = {}

        # Agent 1: 职业分析
        try:
            if progress_placeholder:
                progress_placeholder.info("🤖 职业分析师正在深度思考...")

            # 创建伪进度条
            fake_progress = FakeProgressBar(total_time=30.0)
            progress_bar = st.progress(0)

            # 在后台线程中更新伪进度
            def update_fake_progress():
                for i in range(95):  # 到 95%
                    progress_bar.progress(i / 100)
                    time.sleep(0.3)

            thread = threading.Thread(target=update_fake_progress, daemon=True)
            thread.start()

            start_time = time.time()
            career_analysis = pipeline._ai_think(
                "career_analyst",
                f"请分析以下简历：\n\n{resume_text}"
            )
            results['career_analysis'] = career_analysis

            # 完成进度条
            progress_bar.progress(1.0)

            # 立即显示结果
            if result_containers and 'career' in result_containers:
                result_containers['career'].markdown(career_analysis)

            if progress_placeholder:
                elapsed = time.time() - start_time
                progress_placeholder.success(f"✅ 职业分析完成！耗时 {elapsed:.1f} 秒")
                time.sleep(0.5)
        except Exception as e:
            progress_bar.progress(1.0)
            if result_containers and 'career' in result_containers:
                result_containers['career'].error(f"❌ 职业分析失败: {str(e)}")
            if progress_placeholder:
                progress_placeholder.warning(f"⚠️ 职业分析跳过，继续下一步...")
            career_analysis = "分析失败"

        # Agent 2: 岗位匹配
        try:
            if progress_placeholder:
                progress_placeholder.info("💼 岗位匹配专家正在工作...")

            progress_bar2 = st.progress(0)

            def update_fake_progress2():
                for i in range(95):
                    progress_bar2.progress(i / 100)
                    time.sleep(0.4)

            thread2 = threading.Thread(target=update_fake_progress2, daemon=True)
            thread2.start()

            start_time = time.time()
            job_and_resume = pipeline._ai_think(
                "job_matcher",
                f"简历：\n{resume_text}\n\n职业分析：\n{career_analysis}"
            )
            results['job_recommendations'] = job_and_resume
            results['resume_optimization'] = job_and_resume

            progress_bar2.progress(1.0)

            # 立即显示结果
            if result_containers and 'job' in result_containers:
                result_containers['job'].markdown(job_and_resume)

            if progress_placeholder:
                elapsed = time.time() - start_time
                progress_placeholder.success(f"✅ 岗位匹配完成！耗时 {elapsed:.1f} 秒")
                time.sleep(0.5)
        except Exception as e:
            progress_bar2.progress(1.0)
            if result_containers and 'job' in result_containers:
                result_containers['job'].error(f"❌ 岗位匹配失败: {str(e)}")
            if progress_placeholder:
                progress_placeholder.warning(f"⚠️ 岗位匹配跳过，继续下一步...")

        # Agent 3: 面试辅导
        try:
            if progress_placeholder:
                progress_placeholder.info("🎤 面试辅导专家正在准备...")

            progress_bar3 = st.progress(0)

            def update_fake_progress3():
                for i in range(95):
                    progress_bar3.progress(i / 100)
                    time.sleep(0.3)

            thread3 = threading.Thread(target=update_fake_progress3, daemon=True)
            thread3.start()

            start_time = time.time()
            interview_prep = pipeline._ai_think(
                "interview_coach",
                f"简历：\n{resume_text}\n\n职业分析：\n{results.get('career_analysis', '无')}\n\n岗位匹配：\n{results.get('job_recommendations', '无')}"
            )
            results['interview_preparation'] = interview_prep
            results['mock_interview'] = interview_prep

            progress_bar3.progress(1.0)

            # 立即显示结果
            if result_containers and 'interview' in result_containers:
                result_containers['interview'].markdown(interview_prep)

            if progress_placeholder:
                elapsed = time.time() - start_time
                progress_placeholder.success(f"✅ 面试准备完成！耗时 {elapsed:.1f} 秒")
                time.sleep(0.5)
        except Exception as e:
            progress_bar3.progress(1.0)
            if result_containers and 'interview' in result_containers:
                result_containers['interview'].error(f"❌ 面试准备失败: {str(e)}")
            if progress_placeholder:
                progress_placeholder.warning(f"⚠️ 面试准备跳过，继续下一步...")
            interview_prep = "分析失败"

        # Agent 4: 质量审核
        try:
            if progress_placeholder:
                progress_placeholder.info("✅ 质量审核官正在检查...")

            progress_bar4 = st.progress(0)

            def update_fake_progress4():
                for i in range(95):
                    progress_bar4.progress(i / 100)
                    time.sleep(0.2)

            thread4 = threading.Thread(target=update_fake_progress4, daemon=True)
            thread4.start()

            start_time = time.time()
            quality_audit = pipeline._ai_think(
                "quality_auditor",
                f"职业分析：\n{results.get('career_analysis', '无')}\n\n岗位匹配：\n{results.get('job_recommendations', '无')}\n\n面试准备：\n{results.get('interview_preparation', '无')}"
            )
            results['skill_gap_analysis'] = quality_audit
            results['quality_audit'] = quality_audit

            progress_bar4.progress(1.0)

            # 立即显示结果
            if result_containers and 'quality' in result_containers:
                result_containers['quality'].markdown(quality_audit)

            if progress_placeholder:
                elapsed = time.time() - start_time
                progress_placeholder.success(f"✅ 质量审核完成！耗时 {elapsed:.1f} 秒")
        except Exception as e:
            progress_bar4.progress(1.0)
            if result_containers and 'quality' in result_containers:
                result_containers['quality'].error(f"❌ 质量审核失败: {str(e)}")
            if progress_placeholder:
                progress_placeholder.warning(f"⚠️ 质量审核跳过")

        return results

    except Exception as e:
        if progress_placeholder:
            progress_placeholder.error(f"❌ 分析失败: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# 初始化 session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'show_welcome' not in st.session_state:
    st.session_state.show_welcome = True

# 欢迎页面
if st.session_state.show_welcome:
    # Hero - 超大渐变背景
    st.markdown('''
    <div class="hero" style="min-height: 80vh; display: flex; align-items: center; justify-content: center;">
        <div style="max-width: 900px; margin: 0 auto;">
            <div class="hero-badge">✨ 由 DeepSeek AI 驱动</div>
            <h1 style="font-size: 4.5rem; margin-bottom: 1.5rem;">AI 驱动的智能求职平台</h1>
            <div class="hero-subtitle" style="font-size: 1.5rem; margin-bottom: 3rem;">
                4 个 AI Agent 协作分析简历，精准匹配岗位，自动投递<br>让求职效率提升 10 倍
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # 居中按钮
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 立即开始", type="primary", use_container_width=True, key="start_app"):
            st.session_state.show_welcome = False
            st.rerun()

    # 特性展示
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("## 为什么选择我们？")
    st.markdown("<p style='text-align: center; color: var(--text-secondary); font-size: 1.25rem; margin-bottom: 3rem;'>AI 多角色协作，让求职更智能、更高效</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('''
        <div class="card" style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🤖</div>
            <h3>4-AI 协作引擎</h3>
            <p>职业分析师、岗位匹配专家、面试辅导教练、质量审核官协同工作</p>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('''
        <div class="card" style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🚀</div>
            <h3>飞书 + OpenClaw</h3>
            <p>集成飞书机器人和 OpenClaw，一键自动投递 Boss直聘、实习僧</p>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        st.markdown('''
        <div class="card" style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🎯</div>
            <h3>智能精准匹配</h3>
            <p>基于简历深度分析，AI 自动提取关键词、技能、地点，精准匹配岗位</p>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('''
        <div class="card" style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🎤</div>
            <h3>面试全程辅导</h3>
            <p>AI 面试教练提供专业建议，针对目标岗位准备常见问题</p>
        </div>
        ''', unsafe_allow_html=True)

    with col3:
        st.markdown('''
        <div class="card" style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
            <h3>流式实时显示</h3>
            <p>每个 AI Agent 完成后立即显示结果，伪进度条减少等待焦虑</p>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('''
        <div class="card" style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">✨</div>
            <h3>Gemini 风格 UI</h3>
            <p>蓝紫粉渐变色、玻璃态设计、流畅动画，现代化界面</p>
        </div>
        ''', unsafe_allow_html=True)

    # 工作流程
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("## 简单 3 步，开启智能求职")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('''
        <div class="card" style="text-align: center;">
            <div style="width: 50px; height: 50px; background: var(--gemini-gradient); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 500; margin: 0 auto 1rem;">1</div>
            <h3>上传简历</h3>
            <p>支持 PDF、Word、文本</p>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        st.markdown('''
        <div class="card" style="text-align: center;">
            <div style="width: 50px; height: 50px; background: var(--gemini-gradient); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 500; margin: 0 auto 1rem;">2</div>
            <h3>AI 分析</h3>
            <p>4 个 Agent 协作分析</p>
        </div>
        ''', unsafe_allow_html=True)

    with col3:
        st.markdown('''
        <div class="card" style="text-align: center;">
            <div style="width: 50px; height: 50px; background: var(--gemini-gradient); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 500; margin: 0 auto 1rem;">3</div>
            <h3>自动投递</h3>
            <p>飞书 + OpenClaw 一键投递</p>
        </div>
        ''', unsafe_allow_html=True)

    # 底部 CTA
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 免费开始使用", type="primary", use_container_width=True, key="start_app_bottom"):
            st.session_state.show_welcome = False
            st.rerun()

    st.stop()

# 主应用（原有代码）
# 顶部导航
st.markdown('''
<div class="top">
    <div class="brand">
        <div class="dot"></div>
        <span>AI求职助手</span>
    </div>
</div>
''', unsafe_allow_html=True)

# Hero - Gemini 风格
st.markdown('''
<div class="hero">
    <div class="hero-badge">✨ AI 驱动 · 智能求职助手</div>
    <h1>找实习，让 AI 帮你</h1>
    <div class="hero-subtitle">4 位 AI 专家深度分析，精准推荐，自动投递</div>
</div>
''', unsafe_allow_html=True)

# 标签页 - 按照求职 SOP 顺序
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 第一步：分析简历",
    "🎯 第二步：匹配岗位",
    "🚀 第三步：自动投递",
    "📊 第四步：追踪进度"
])

# Tab1: 简历分析
with tab1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 📝 先让 AI 看看你的简历")
    st.markdown("<p style='font-size: 1.1rem;'>上传简历，4 位 AI 专家帮你深度分析，找出亮点和改进空间</p>", unsafe_allow_html=True)

    method = st.radio("选择上传方式", ["✍️ 直接粘贴文本", "📎 上传文件（PDF/Word）"], horizontal=True, label_visibility="collapsed")

    if method == "✍️ 直接粘贴":
        resume_text = st.text_area("把简历内容粘贴到这里吧 👇", height=200, placeholder="粘贴你的简历内容...", label_visibility="collapsed")

        if resume_text and st.button("✨ 开始分析", type="primary", key="analyze_text"):
            if len(resume_text.strip()) < 50:
                st.warning("😅 简历内容有点少哦，建议至少 50 字以上")
            else:
                # 创建进度显示区域
                progress_placeholder = st.empty()

                # 创建结果显示区域（提前创建，流式显示）
                st.markdown("### 📊 分析结果（实时更新）")

                result_tabs = st.tabs(["🎯 职业分析", "💼 岗位推荐", "🎤 面试准备", "✅ 质量审核"])

                result_containers = {
                    'career': result_tabs[0].empty(),
                    'job': result_tabs[1].empty(),
                    'interview': result_tabs[2].empty(),
                    'quality': result_tabs[3].empty()
                }

                # 开始分析（流式显示）
                import time
                start_time = time.time()

                results = analyze_resume_streaming(resume_text, progress_placeholder, result_containers)

                elapsed = time.time() - start_time
                progress_placeholder.success(f"🎉 全部完成！总耗时 {elapsed:.1f} 秒")

                if results:
                    st.session_state.analysis_results = results

    else:
        uploaded_file = st.file_uploader("选择你的简历文件 📄", type=["pdf", "doc", "docx", "txt"], label_visibility="collapsed")

        if uploaded_file:
            if st.button("✨ 开始分析", type="primary", key="analyze_file"):
                with st.spinner("🔄 正在读取文件..."):
                    resume_text = parse_uploaded_file(uploaded_file)

                if resume_text:
                    progress_placeholder = st.empty()

                    # 创建结果展示区域（每个 Agent 完成后立即显示）
                    result_tabs = st.tabs(["🎯 职业分析", "💼 岗位推荐", "🎤 面试准备", "✅ 质量审核"])

                    result_containers = {
                        'career': result_tabs[0].empty(),
                        'job': result_tabs[1].empty(),
                        'interview': result_tabs[2].empty(),
                        'quality': result_tabs[3].empty()
                    }

                    # 开始分析（流式显示）
                    import time
                    start_time = time.time()

                    results = analyze_resume_streaming(resume_text, progress_placeholder, result_containers)

                    elapsed = time.time() - start_time
                    progress_placeholder.success(f"🎉 全部完成！总耗时 {elapsed:.1f} 秒")

                    if results:
                        st.session_state.analysis_results = results

    st.markdown('</div>', unsafe_allow_html=True)

# Tab2: 查看分析结果
with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 🎯 AI 帮你找到最匹配的岗位")
    st.markdown("<p style='font-size: 1.1rem;'>基于简历分析，AI 已经帮你筛选出最适合的岗位和关键词</p>", unsafe_allow_html=True)

    # 检查是否已完成简历分析
    if not st.session_state.analysis_results:
        st.warning("⚠️ 请先完成第一步：分析简历")
        st.info("💡 完成简历分析后，AI 会自动推荐最匹配的岗位")
    else:
        st.success("✅ 简历分析已完成，查看 AI 推荐")

        # 显示 AI 推荐的投递策略
        from app.core.smart_apply import smart_apply_engine

        # 提取投递目标
        targets = smart_apply_engine.extract_job_targets(st.session_state.analysis_results)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🎯 推荐关键词")
            st.markdown("<p style='font-size: 0.95rem; color: var(--text-secondary);'>AI 从你的简历中提取的核心技能</p>", unsafe_allow_html=True)
            for keyword in targets['keywords'][:5]:
                st.markdown(f"- `{keyword}`")

            st.markdown("### 📍 推荐地点")
            st.markdown("<p style='font-size: 0.95rem; color: var(--text-secondary);'>根据你的意向和市场需求</p>", unsafe_allow_html=True)
            for location in targets['locations'][:3]:
                st.markdown(f"- {location}")

        with col2:
            st.markdown("### 💼 推荐岗位")
            st.markdown("<p style='font-size: 0.95rem; color: var(--text-secondary);'>最适合你的岗位类型</p>", unsafe_allow_html=True)
            for pos in targets['positions'][:3]:
                st.markdown(f"- **{pos['title']}** ({pos.get('company', '多家公司')})")

            st.markdown("### 💰 薪资范围")
            st.markdown("<p style='font-size: 0.95rem; color: var(--text-secondary);'>市场平均水平</p>", unsafe_allow_html=True)
            salary = targets['salary_range']
            st.markdown(f"- {salary['min']}-{salary['max']} 元/月")

        st.markdown("---")
        st.info("💡 **下一步：** 点击「第三步：自动投递」开始投递")

    st.markdown('</div>', unsafe_allow_html=True)

# Tab3: 自动投递
with tab3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 🚀 一键自动投递")
    st.markdown("<p style='font-size: 1.1rem;'>飞书机器人通过 WebSocket 连接本地 OpenClaw，全自动投递，解放双手</p>", unsafe_allow_html=True)

    # 检查是否已完成简历分析
    if not st.session_state.analysis_results:
        st.warning("⚠️ 请先完成前两步：分析简历 → 查看匹配岗位")
        st.info("💡 完成后才能开始自动投递")
    else:
        st.success("✅ 准备就绪，可以开始投递了！")

        st.markdown("### 🤖 飞书 + OpenClaw 自动投递")

        st.info("""
        💡 **工作原理：**
        1. 你点击「发送到飞书」
        2. 飞书机器人通过 WebSocket 发送指令到你的本地 OpenClaw
        3. OpenClaw 自动打开浏览器投递
        4. 投递结果自动回传到飞书

        **前提条件：**
        - ✅ 你的飞书机器人已配置（App ID: cli_a908b88dc6b8dcd4）
        - ✅ 本地 OpenClaw 已安装并连接到飞书
        """)

        col1, col2 = st.columns(2)
        with col1:
            feishu_user_id = st.text_input(
                "你的飞书邮箱或 open_id",
                placeholder="your@company.com 或 ou_xxx",
                help="输入你的飞书邮箱（推荐）或 open_id"
            )
            st.caption("⚠️ 不支持手机号，请使用飞书邮箱")
        with col2:
            platform = st.selectbox("投递平台", ["Boss直聘", "实习僧", "牛客网"])

        if st.button("🚀 发送投递任务到飞书", type="primary", use_container_width=True):
            if not feishu_user_id:
                st.warning("😅 请输入飞书邮箱或 open_id")
            elif feishu_user_id.isdigit():
                st.error("❌ 不支持手机号！请使用飞书邮箱（如：your@company.com）")
            else:
                with st.spinner("📤 正在发送到飞书机器人..."):
                    try:
                        from app.core.smart_apply import smart_apply_engine
                        from app.core.feishu_openclaw_bridge import feishu_openclaw_bridge

                        # 提取投递目标
                        targets = smart_apply_engine.extract_job_targets(st.session_state.analysis_results)

                        # 发送到飞书
                        result = feishu_openclaw_bridge.send_apply_task(
                            receive_id=feishu_user_id,
                            targets=targets,
                            platform=platform
                        )

                        if result['status'] == 'sent':
                            st.success("🎉 投递任务已发送到飞书！")

                            st.info(f"""
                            📧 **任务 ID：** {result['task_id']}

                            **接下来会发生什么：**
                            1. 飞书机器人通过 WebSocket 发送指令到你的本地 OpenClaw
                            2. OpenClaw 自动打开浏览器开始投递
                            3. 投递进度实时显示在终端
                            4. 完成后结果自动回传到飞书

                            **你只需要：**
                            - 确保本地 OpenClaw 正在运行
                            - 等待飞书通知投递结果 📊
                            """)

                            # 显示 OpenClaw 脚本（备用）
                            with st.expander("📝 备用：手动运行 OpenClaw 命令"):
                                st.markdown("如果 WebSocket 连接失败，可以手动复制命令运行：")
                                st.code(result['openclaw_script'], language='bash')

                        else:
                            st.error("😢 发送失败，请检查飞书配置")

                    except Exception as e:
                        st.error(f"发送失败: {str(e)}")
                        import traceback
                        st.error(traceback.format_exc())

        st.markdown("---")
        st.markdown("### 📖 首次使用？")

        with st.expander("🔧 配置 OpenClaw + 飞书"):
            st.markdown("""
            **1. 安装 OpenClaw：**
            ```bash
            npm install -g openclaw
            ```

            **2. 连接到飞书机器人：**
            ```bash
            openclaw connect --feishu-app-id cli_a908b88dc6b8dcd4
            ```

            **3. 保持 OpenClaw 运行：**
            ```bash
            openclaw listen
            ```

            **4. 获取你的飞书用户 ID：**
            - 打开飞书 → 个人设置 → 查看用户 ID
            - 或者直接使用你的飞书邮箱

            **完整教程：** [查看文档](https://github.com/emptyteabot/ai-job-helper/blob/main/docs/飞书OpenClaw使用指南.md)
            """)

    st.markdown('</div>', unsafe_allow_html=True)

# Tab4: 追踪进度
with tab4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 📊 我的求职数据")
    st.markdown(f"<p style='font-size: 1.1rem;'>用户ID: {st.session_state.user_id[:8]}... （只有你能看到自己的数据哦 🔒）</p>", unsafe_allow_html=True)

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
<div class="footer">
    <p>💼 祝你找到心仪的实习，加油鸭！</p>
    <p style="margin-top:12px">
        <a href="https://github.com/emptyteabot/ai-job-helper">GitHub 开源</a>
        <a href="https://github.com/GodsScion/Auto_job_applier_linkedIn">参考项目</a>
    </p>
</div>
''', unsafe_allow_html=True)
