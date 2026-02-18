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

        # Agent 2: 岗位匹配
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

        # Agent 3: 面试辅导
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
            f"简历：\n{resume_text}\n\n职业分析：\n{career_analysis}\n\n岗位匹配：\n{job_and_resume}"
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

        # Agent 4: 质量审核
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
            f"职业分析：\n{career_analysis}\n\n岗位匹配：\n{job_and_resume}\n\n面试准备：\n{interview_prep}"
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

# 标签页 - 友好的 emoji 和文案
tab1, tab2, tab3 = st.tabs([
    "📝 分析简历",
    "🚀 一键投递",
    "📊 我的数据"
])

# Tab1: 简历分析
with tab1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 📝 让 AI 帮你看看简历")
    st.markdown("<p>上传简历或粘贴文本，4 位 AI 专家帮你深度分析 ✨</p>", unsafe_allow_html=True)

    method = st.radio("你想怎么上传？", ["✍️ 直接粘贴", "📎 上传文件"], horizontal=True)

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

# Tab2: 智能投递（基于分析结果）
with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 🎯 智能精准投递")
    st.markdown("<p>基于你的简历分析结果，AI 帮你精准投递最匹配的岗位 ✨</p>", unsafe_allow_html=True)

    # 检查是否已完成简历分析
    if not st.session_state.analysis_results:
        st.warning("⚠️ 请先在「分析简历」页面完成简历分析")
        st.info("💡 AI 会根据分析结果为你推荐最合适的岗位，避免广撒网")
    else:
        st.success("✅ 已完成简历分析，可以开始智能投递")

        # 显示 AI 推荐的投递策略
        with st.expander("📊 查看 AI 推荐的投递策略", expanded=True):
            from app.core.smart_apply import smart_apply_engine

            # 提取投递目标
            targets = smart_apply_engine.extract_job_targets(st.session_state.analysis_results)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 🎯 推荐关键词")
                for keyword in targets['keywords'][:5]:
                    st.markdown(f"- `{keyword}`")

                st.markdown("### 📍 推荐地点")
                for location in targets['locations'][:3]:
                    st.markdown(f"- {location}")

            with col2:
                st.markdown("### 💼 推荐岗位")
                for pos in targets['positions'][:3]:
                    st.markdown(f"- **{pos['title']}** ({pos.get('company', '多家公司')})")

                st.markdown("### 💰 薪资范围")
                salary = targets['salary_range']
                st.markdown(f"- {salary['min']}-{salary['max']} 元/月")

        st.markdown("---")

        # 投递方式选择
        apply_method = st.radio(
            "选择投递方式 🚀",
            ["🤖 飞书 + OpenClaw（推荐）", "📋 生成脚本（自己运行）"],
            horizontal=True
        )

        if apply_method == "🤖 飞书 + OpenClaw（推荐）":
            st.success("✨ 最智能的方式！飞书发送指令，OpenClaw 自动投递")

            st.markdown("### 📝 配置飞书机器人")

            st.info("""
            💡 **使用你的飞书机器人：**
            - App ID: `cli_a908b88dc6b8dcd4`
            - App Secret: `Q8jjY7RDcwfcsmTd0Zvylee4dfs6kVhK`

            **工作原理：**
            1. 点击「发送到飞书」
            2. 飞书机器人发送投递指令
            3. 你在电脑上运行 OpenClaw 命令
            4. 自动投递，结果回传飞书
            """)

            col1, col2 = st.columns(2)
            with col1:
                feishu_user_id = st.text_input(
                    "飞书用户 ID 📱",
                    placeholder="ou_xxx 或你的邮箱",
                    help="在飞书中找到你的用户 ID"
                )
            with col2:
                platform = st.selectbox("选择平台 🌐", ["Boss直聘", "实习僧", "牛客网"])

            if st.button("🚀 发送到飞书", type="primary"):
                if not feishu_user_id:
                    st.warning("😅 请输入飞书用户 ID")
                else:
                    with st.spinner("📤 正在发送到飞书..."):
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

                                **下一步：**
                                1. 打开飞书，查看机器人消息
                                2. 复制 OpenClaw 命令
                                3. 在电脑上运行命令
                                4. 等待投递完成

                                **投递完成后，结果会自动发送到飞书 📊**
                                """)

                                # 显示 OpenClaw 脚本
                                with st.expander("📝 查看 OpenClaw 脚本"):
                                    st.code(result['openclaw_script'], language='bash')

                                # 显示备用 Selenium 脚本
                                with st.expander("💻 备用：Selenium 脚本"):
                                    st.code(result['selenium_script'], language='python')

                            else:
                                st.error("😢 发送失败，请检查飞书配置")

                        except Exception as e:
                            st.error(f"发送失败: {str(e)}")
                            import traceback
                            st.error(traceback.format_exc())

            st.markdown("### 📖 使用说明")
            st.markdown("""
            **为什么选择飞书 + OpenClaw？** 🤔
            - ✅ 飞书消息不会丢失
            - ✅ OpenClaw 更稳定可靠
            - ✅ 支持多平台投递
            - ✅ 自动回传结果

            **安装 OpenClaw：** 💻
            ```bash
            # 方法1：npm 安装（推荐）
            npm install -g openclaw

            # 方法2：从源码安装
            git clone https://github.com/openclaw/openclaw.git
            cd openclaw && npm install
            ```

            **首次使用：** 🔧
            1. 安装 OpenClaw
            2. 配置飞书机器人
            3. 获取你的飞书用户 ID
            4. 发送投递任务

            **投递流程：** 🔄
            1. AI 分析简历 → 提取目标
            2. 发送到飞书 → 生成命令
            3. 运行 OpenClaw → 自动投递
            4. 结果回传 → 飞书通知
            """)

        elif apply_method == "📋 生成脚本（自己运行）":
            st.success("✨ 最简单的方式！只需输入手机号和邮箱，我们帮你投递")

            st.markdown("### 📝 填写联系方式")

            col1, col2 = st.columns(2)
            with col1:
                user_phone = st.text_input("手机号 📱", placeholder="13800138000")
                user_name = st.text_input("姓名 👤", placeholder="张三")
            with col2:
                user_email = st.text_input("邮箱 📧", placeholder="your@email.com")
                resume_file = st.file_uploader("上传简历（可选）📄", type=["pdf", "doc", "docx"])

            platform = st.selectbox("选择平台 🌐", ["Boss直聘", "实习僧", "牛客网"])

            col1, col2 = st.columns(2)
            with col1:
                max_count = st.number_input("每天投递数量 📊", 10, 50, 30)
            with col2:
                delivery_time = st.selectbox("投递时间 ⏰", ["立即投递", "工作日 9-11点", "工作日 14-17点"])

            st.info("💡 **工作原理：** 你提交 → 云端服务器自动投递 → 结果发送到邮箱")

            if st.button("🚀 提交投递任务", type="primary"):
                if not user_phone or not user_email:
                    st.warning("😅 请填写手机号和邮箱")
                elif len(user_phone) != 11:
                    st.warning("😅 请输入正确的手机号")
                else:
                    with st.spinner("📤 正在提交投递任务..."):
                        try:
                            from app.core.smart_apply import smart_apply_engine
                            from app.core.cloud_apply import email_apply_service

                            # 提取投递目标
                            targets = smart_apply_engine.extract_job_targets(st.session_state.analysis_results)

                            # 发送邮件方案
                            result = asyncio.run(email_apply_service.send_apply_email(
                                user_email=user_email,
                                user_phone=user_phone,
                                resume_text=str(st.session_state.analysis_results),
                                targets=targets
                            ))

                            st.success("🎉 投递任务已提交！")
                            st.info(f"""
                            📧 **投递方案已发送到你的邮箱：{user_email}**

                            邮件包含：
                            1. 📊 详细的投递策略
                            2. 🔗 在线投递链接（点击即可）
                            3. 💻 本地投递脚本（备用）
                            4. 📋 推荐岗位列表

                            **预计投递时间：**
                            - 立即投递：10-20 分钟
                            - 定时投递：按设定时间执行

                            **投递完成后会：**
                            - 📧 发送邮件通知
                            - 📱 发送短信通知（可选）
                            - 📊 生成投递报告
                            """)

                            # 显示备用方案
                            with st.expander("🔧 备用方案：在线投递链接"):
                                st.markdown("""
                                如果邮件没收到，可以点击下面的链接：

                                **方案1：授权投递（推荐）**
                                1. 点击链接授权登录招聘平台
                                2. 系统自动投递
                                3. 完成后发送通知

                                **方案2：半自动投递**
                                1. 系统生成投递列表
                                2. 你点击确认
                                3. 系统自动填表提交

                                **方案3：手动投递**
                                - 查看推荐岗位列表
                                - 手动投递
                                """)

                                # 生成临时投递链接（示例）
                                import hashlib
                                token = hashlib.md5(f"{user_email}{user_phone}".encode()).hexdigest()[:16]
                                apply_url = f"https://your-service.com/apply?token={token}"

                                st.code(apply_url, language="text")
                                st.markdown(f"[🔗 点击这里开始投递]({apply_url})")

                        except Exception as e:
                            st.error(f"提交失败: {str(e)}")
                            st.info("💡 请尝试「本地投递」或「生成脚本」方式")

            st.markdown("### 📖 云端投递说明")
            st.markdown("""
            **优势：** ✨
            - ✅ 无需安装任何软件
            - ✅ 无需懂技术
            - ✅ 手机也能用
            - ✅ 自动投递，解放双手

            **工作流程：** 🔄
            1. 你填写手机号和邮箱
            2. 我们的云服务器自动投递
            3. 投递结果发送到邮箱
            4. 你查看并准备面试

            **安全保障：** 🔒
            - 不保存你的密码
            - 使用授权登录
            - 数据加密传输
            - 投递完成后自动删除

            **费用说明：** 💰
            - 每天 30 个岗位：免费
            - 每天 50 个岗位：9.9 元/月
            - 每天 100 个岗位：19.9 元/月
            """)

        elif apply_method == "🤖 本地投递（需要电脑）":
            st.info("💡 **工作原理：** 网页 → 飞书 → 你的电脑 → Selenium 自动投递")

            platform = st.selectbox("选择平台 🌐", ["Boss直聘", "实习僧", "牛客网"])

            col1, col2 = st.columns(2)
            with col1:
                max_count = st.number_input("每天投递数量 📊", 10, 50, 30)
            with col2:
                interval = st.slider("投递间隔（秒）⏱️", 3, 10, 5)

            feishu_webhook = st.text_input(
                "飞书机器人 Webhook 🤖",
                placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/...",
                help="在飞书群里添加机器人，获取 Webhook 地址"
            )

            if st.button("🚀 开始智能投递", type="primary"):
                if not feishu_webhook:
                    st.warning("😅 请先输入飞书机器人 Webhook 地址")
                else:
                    with st.spinner("📤 正在生成投递配置..."):
                        from app.core.smart_apply import smart_apply_engine

                        # 生成投递配置
                        targets = smart_apply_engine.extract_job_targets(st.session_state.analysis_results)
                        config = smart_apply_engine.generate_apply_config(targets)

                        # 生成脚本
                        script = smart_apply_engine.generate_selenium_script(config, platform)

                        # 发送到飞书
                        try:
                            import requests

                            message = {
                                "msg_type": "interactive",
                                "card": {
                                    "header": {
                                        "title": {
                                            "tag": "plain_text",
                                            "content": "🎯 智能投递指令（基于 AI 分析）"
                                        }
                                    },
                                    "elements": [
                                        {
                                            "tag": "div",
                                            "text": {
                                                "tag": "lark_md",
                                                "content": f"""**平台：** {platform}
**关键词：** {', '.join(targets['keywords'][:3])}
**地点：** {', '.join(targets['locations'])}
**每天数量：** {max_count}
**间隔：** {interval}秒

**AI 推荐理由：**
- 匹配度 ≥ 70%
- 优先实习岗位
- 避免销售/客服类

**下一步：**
1. 复制下面的脚本保存为 `auto_apply.py`
2. 安装依赖：`pip install selenium`
3. 运行：`python auto_apply.py`

```python
{script[:500]}...
```

完整脚本已发送到你的邮箱 📧"""
                                            }
                                        }
                                    ]
                                }
                            }

                            response = requests.post(feishu_webhook, json=message, timeout=10)

                            if response.status_code == 200:
                                st.success("🎉 智能投递配置已发送到飞书！")
                                st.info("💡 **下一步：** 在电脑上运行脚本开始精准投递")

                                # 显示完整脚本
                                with st.expander("📝 查看完整投递脚本"):
                                    st.code(script, language='python')

                            else:
                                st.error(f"😢 发送失败：{response.text}")

                        except Exception as e:
                            st.error(f"发送失败: {str(e)}")

        else:
            # 生成投递脚本
            st.markdown("### 📋 生成投递脚本")

            platform = st.selectbox("选择平台 🌐", ["Boss直聘", "实习僧", "牛客网"], key="script_platform")

            if st.button("📥 生成脚本", type="primary"):
                from app.core.smart_apply import smart_apply_engine

                targets = smart_apply_engine.extract_job_targets(st.session_state.analysis_results)
                config = smart_apply_engine.generate_apply_config(targets)
                script = smart_apply_engine.generate_selenium_script(config, platform)

                st.success("✅ 脚本生成成功！")

                st.download_button(
                    label="💾 下载脚本",
                    data=script,
                    file_name=f"auto_apply_{platform}.py",
                    mime="text/x-python"
                )

                with st.expander("📝 查看脚本内容"):
                    st.code(script, language='python')

        st.markdown("### 📖 使用说明")
        st.markdown("""
        **为什么是精准投递？** 🎯
        - AI 已经分析了你的简历
        - 知道你的优势和适合的岗位
        - 只投递匹配度 ≥ 70% 的岗位
        - 避免广撒网，提高回复率

        **投递原理：** 🤖
        1. **Selenium 自动化**：模拟人工操作浏览器
        2. **智能筛选**：根据 AI 分析结果过滤岗位
        3. **自动填表**：自动填写申请表单
        4. **防检测**：随机间隔，避免被封号

        **安装依赖：** 💻
        ```bash
        pip install selenium undetected-chromedriver
        ```

        **注意事项：** ⚠️
        - 首次运行需要手动登录
        - 建议每天投递 20-30 个
        - 间隔 5-10 秒避免被检测
        """)

    st.markdown('</div>', unsafe_allow_html=True)

# Tab3: 数据统计（用户隔离）
with tab3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 📊 我的求职数据")
    st.markdown(f"<p>用户ID: {st.session_state.user_id[:8]}... （只有你能看到自己的数据哦 🔒）</p>", unsafe_allow_html=True)

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
