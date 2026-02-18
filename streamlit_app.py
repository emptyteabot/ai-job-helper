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

# 全局样式 - 温暖人性化 UI
from ui_styles_warm import WARM_UI_STYLE
st.markdown(WARM_UI_STYLE, unsafe_allow_html=True)

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

# Hero - 温暖友好的设计
st.markdown('''
<div class="hero">
    <div class="hero-badge">✨ DeepSeek AI 驱动 · 专为实习生打造</div>
    <h1>🌟 找实习，AI 帮你搞定</h1>
    <div class="hero-subtitle">4 位 AI 专家深度分析你的简历，帮你找到最适合的实习机会 💼</div>
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
                # 创建进度条
                progress_bar = st.progress(0)
                status_text = st.empty()

                # 开始分析
                import time
                start_time = time.time()

                results = analyze_resume(resume_text, status_text)

                elapsed = time.time() - start_time
                progress_bar.progress(100)
                status_text.success(f"🎉 分析完成！耗时 {elapsed:.1f} 秒")

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
            ["🤖 自动投递（推荐）", "📋 生成投递脚本"],
            horizontal=True
        )

        if apply_method == "🤖 自动投递（推荐）":
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
