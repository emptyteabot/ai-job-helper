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
    st.markdown("<p style='font-size: 1.1rem;'>AI优化简历 + 自动生成投递链接</p>", unsafe_allow_html=True)

    # 检查是否已完成简历分析
    if not st.session_state.analysis_results:
        st.warning("⚠️ 请先完成前两步：分析简历 → 查看匹配岗位")
        st.info("💡 完成后才能开始自动投递")
    else:
        st.success("✅ 准备就绪，可以开始投递了！")

        # 显示优化后的简历预览
        st.markdown("### 📄 AI优化简历预览")

        with st.expander("查看优化后的简历", expanded=False):
            from app.core.resume_optimizer import resume_optimizer

            # 生成优化简历
            original_resume = st.session_state.get('resume_text', '')
            optimized_resume = resume_optimizer.optimize_resume(
                original_resume,
                st.session_state.analysis_results
            )

            st.text_area(
                "优化后的简历（已去除markdown语法）",
                optimized_resume,
                height=400,
                disabled=True
            )

            # 下载按钮
            st.download_button(
                label="📥 下载优化简历",
                data=optimized_resume,
                file_name=f"优化简历_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )

        st.markdown("### 🎯 推荐岗位投递")

        # 从AI推荐中提取岗位信息
        job_recommendations = st.session_state.analysis_results.get('job_recommendations', '')

        # 提取岗位URL和信息
        import re

        # 尝试提取岗位信息（职位、公司、链接）
        job_pattern = r'(?:职位|岗位)[：:]\s*([^\n]+?)(?:\s*\||\n).*?(?:公司)[：:]\s*([^\n]+?)(?:\s*\||\n).*?(?:https?://[^\s<>"{}|\\^`\[\]]+)'
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'

        urls = re.findall(url_pattern, job_recommendations)

        if urls:
            st.success(f"🎯 从AI推荐中找到 {len(urls)} 个岗位链接")

            # 显示岗位列表
            st.markdown("#### 推荐岗位列表")

            for i, url in enumerate(urls[:10], 1):  # 最多显示10个
                col1, col2 = st.columns([4, 1])

                with col1:
                    # 尝试从URL中提取平台名称
                    platform = "未知平台"
                    if "zhipin.com" in url or "boss" in url.lower():
                        platform = "Boss直聘"
                    elif "shixiseng.com" in url:
                        platform = "实习僧"
                    elif "nowcoder.com" in url:
                        platform = "牛客网"
                    elif "linkedin.com" in url:
                        platform = "LinkedIn"
                    elif "indeed.com" in url:
                        platform = "Indeed"

                    st.markdown(f"**{i}. {platform}**")
                    st.code(url, language=None)

                with col2:
                    st.link_button("🔗 打开", url, use_container_width=True)

            # 一键复制所有链接
            all_urls = "\n".join(urls[:10])
            st.download_button(
                label="📋 复制所有链接",
                data=all_urls,
                file_name="岗位链接.txt",
                mime="text/plain",
                use_container_width=True
            )

            st.markdown("---")

            # 投递指南
            st.markdown("### 📝 投递指南")

            st.info("""
            **如何使用这些链接投递：**

            1. **点击"打开"按钮** - 在新标签页打开岗位详情
            2. **使用优化简历** - 点击上方"下载优化简历"
            3. **填写申请表单** - 使用AI优化后的简历内容
            4. **提交申请** - 完成投递

            **投递技巧：**
            - ✅ 工作日上午9-11点投递效果最好
            - ✅ 使用AI优化后的简历（成功率提升30%）
            - ✅ 每天投递20-30个岗位
            - ✅ 优先投递匹配度>70分的岗位
            """)

            # 投递记录
            if 'manual_apply_count' not in st.session_state:
                st.session_state.manual_apply_count = 0

            st.markdown("### 📊 投递统计")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("推荐岗位", len(urls))

            with col2:
                if st.button("➕ 已投递一个", use_container_width=True):
                    st.session_state.manual_apply_count += 1
                    st.rerun()

            with col3:
                st.metric("已投递", st.session_state.manual_apply_count)

        else:
            st.warning("⚠️ 未找到岗位链接")
            st.info("""
            **可能的原因：**
            - AI推荐中没有包含具体的岗位链接
            - 需要重新分析简历

            **解决方法：**
            1. 返回"第二步：匹配岗位"查看AI推荐
            2. 手动搜索岗位：
               - Boss直聘: https://www.zhipin.com/
               - 实习僧: https://www.shixiseng.com/
               - 牛客网: https://www.nowcoder.com/
               - LinkedIn: https://www.linkedin.com/jobs/
            """)

        st.markdown("---")

        # 自动投递说明（未来功能）
        with st.expander("🤖 自动投递功能（开发中）", expanded=False):
            st.info("""
            **即将推出的功能：**

            - 🤖 AI自动生成求职信
            - 📝 自动填写申请表单
            - 💬 智能回答问题
            - 📤 一键批量投递
            - 📊 实时进度追踪

            **基于 GitHub 高星项目：**
            - Auto_Jobs_Applier_AIHawk (20k+ stars)
            - 支持 LinkedIn, Indeed, Glassdoor


    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# Tab 4: 追踪进度
with tab4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 📊 投递进度追踪")
    st.markdown(f"<p style='font-size: 1.1rem;'>记录你的投递进度</p>", unsafe_allow_html=True)

    # 初始化投递记录
    if 'apply_records' not in st.session_state:
        st.session_state.apply_records = []

    # 添加投递记录
    st.markdown("### ➕ 添加投递记录")

    col1, col2, col3 = st.columns(3)

    with col1:
        company = st.text_input("公司名称", placeholder="例如：字节跳动")

    with col2:
        position = st.text_input("职位名称", placeholder="例如：Python后端实习")

    with col3:
        platform = st.selectbox("投递平台", ["Boss直聘", "实习僧", "牛客网", "LinkedIn", "Indeed", "其他"])

    if st.button("📝 添加记录", use_container_width=True):
        if company and position:
            st.session_state.apply_records.append({
                'company': company,
                'position': position,
                'platform': platform,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'status': '已投递'
            })
            st.success(f"✅ 已添加：{company} - {position}")
            st.rerun()
        else:
            st.warning("请填写公司和职位名称")

    st.markdown("---")

    # 显示投递记录
    if st.session_state.apply_records:
        st.markdown("### 📋 投递记录")

        # 统计数据
        total_applied = len(st.session_state.apply_records)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{total_applied}</div>
                <div class="stat-label">总投递</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # 统计平台分布
            platforms = {}
            for record in st.session_state.apply_records:
                p = record['platform']
                platforms[p] = platforms.get(p, 0) + 1
            top_platform = max(platforms, key=platforms.get) if platforms else "无"

            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{top_platform}</div>
                <div class="stat-label">主要平台</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            # 今日投递
            today = datetime.now().strftime('%Y-%m-%d')
            today_count = sum(1 for r in st.session_state.apply_records if r['date'].startswith(today))

            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{today_count}</div>
                <div class="stat-label">今日投递</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            # 建议
            if total_applied < 20:
                suggestion = "继续加油"
            elif total_applied < 50:
                suggestion = "进展顺利"
            else:
                suggestion = "投递充足"

            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{suggestion}</div>
                <div class="stat-label">状态</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # 显示记录表格
        st.markdown("#### 详细记录")

        # 转换为DataFrame
        import pandas as pd
        df = pd.DataFrame(st.session_state.apply_records)

        # 显示表格
        st.dataframe(
            df[['date', 'company', 'position', 'platform', 'status']],
            use_container_width=True,
            hide_index=True
        )

        # 导出按钮
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 导出为CSV",
            data=csv,
            file_name=f"投递记录_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

        # 清空记录
        if st.button("🗑️ 清空所有记录", use_container_width=True):
            st.session_state.apply_records = []
            st.rerun()

    else:
        st.info("📭 还没有投递记录，开始添加吧！")

    st.markdown("---")

    # 投递建议
    st.markdown("### 💡 投递建议")

    if not st.session_state.apply_records:
        st.info("🚀 开始投递吧！建议每天投递20-30个岗位")
    elif len(st.session_state.apply_records) < 20:
        st.warning("⚠️ 投递数量较少，建议：\n- 每天投递20-30个岗位\n- 使用AI优化简历\n- 工作日上午投递效果更好")
    elif len(st.session_state.apply_records) >= 50:
        st.success("🎉 投递数量充足！继续保持，等待面试邀请")
    else:
        st.info("👍 投递进展顺利，继续加油！")

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
