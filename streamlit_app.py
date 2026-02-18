"""
AI求职助手 - Streamlit 完整版
简历分析（老版本代码）+ 自动投递（GitHub高星项目）
"""
import streamlit as st
import sys
import os
import asyncio
import io

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

# 配置 API Key（直接写在代码里）
os.environ['OPENAI_API_KEY'] = 'sk-SnQQxqPPxqxqxqxqxqxqxqxqxqxqxqxqxqxqxqxqxqxqxqxq'
os.environ['OPENAI_BASE_URL'] = 'https://oneapi.gemiaude.com/v1'

# 文件解析函数（老版本代码 - 优化版）
def parse_uploaded_file(uploaded_file):
    """解析上传的文件 - 支持 PDF/Word/图片（OCR）"""
    try:
        file_content = uploaded_file.read()
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        resume_text = ""

        if file_ext == '.txt':
            # 文本文件
            try:
                resume_text = file_content.decode('utf-8')
            except:
                try:
                    resume_text = file_content.decode('gbk', errors='ignore')
                except:
                    resume_text = file_content.decode('latin-1', errors='ignore')

        elif file_ext == '.pdf':
            # PDF文件
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))

                if len(pdf_reader.pages) == 0:
                    st.error("PDF 文件为空")
                    return None

                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text:
                        resume_text += text + "\n"

                if not resume_text.strip():
                    st.warning("PDF 可能是扫描件，尝试使用图片上传方式")
                    return None

            except Exception as e:
                st.error(f"PDF 解析失败: {str(e)}")
                st.info("💡 提示：如果是扫描版 PDF，请转换为图片后上传")
                return None

        elif file_ext in ['.docx', '.doc']:
            # Word文件
            try:
                from docx import Document
                doc = Document(io.BytesIO(file_content))

                # 提取段落文本
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        resume_text += paragraph.text + "\n"

                # 提取表格文本
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            if cell.text.strip():
                                resume_text += cell.text + " "
                        resume_text += "\n"

                if not resume_text.strip():
                    st.error("Word 文档为空或无法提取文字")
                    return None

            except Exception as e:
                st.error(f"Word 文档解析失败: {str(e)}")
                st.info("💡 提示：请确保文件未损坏，或尝试另存为 .docx 格式")
                return None

        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            # 图片文件 - 使用OCR
            try:
                from PIL import Image
                import pytesseract

                # 打开图片
                image = Image.open(io.BytesIO(file_content))

                # 显示图片预览
                st.image(image, caption="上传的图片", use_container_width=True)

                # OCR识别（支持中英文）
                with st.spinner("🔍 正在识别图片中的文字..."):
                    resume_text = pytesseract.image_to_string(image, lang='chi_sim+eng')

                if not resume_text.strip():
                    st.error("图片识别失败，未能提取到文字")
                    st.info("💡 提示：请确保图片清晰、文字可读，或尝试调整图片亮度和对比度")
                    return None

            except ImportError:
                st.error("❌ 图片 OCR 功能未安装")
                st.info("""
                **安装方法：**

                1. 安装 pytesseract：
                ```bash
                pip install pytesseract
                ```

                2. 安装 Tesseract OCR 引擎：
                - Windows: https://github.com/UB-Mannheim/tesseract/wiki
                - Mac: `brew install tesseract`
                - Linux: `sudo apt-get install tesseract-ocr`

                或者使用文本输入方式
                """)
                return None
            except Exception as e:
                st.error(f"图片识别失败: {str(e)}")
                st.info("💡 提示：请确保已安装 Tesseract OCR 引擎")
                return None

        else:
            st.error(f"不支持的文件格式: {file_ext}")
            return None

        # 检查提取的文本长度
        if resume_text and len(resume_text.strip()) < 50:
            st.warning("⚠️ 提取的文字内容较少，可能影响分析质量")

        return resume_text.strip() if resume_text else None

    except Exception as e:
        st.error(f"文件解析失败: {str(e)}")
        return None

# 异步函数包装器
def run_async(coro):
    """运行异步函数的同步包装器"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(coro)
        loop.close()
        return result
    except Exception as e:
        st.error(f"执行出错: {str(e)}")
        return None

# 初始化 session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# 标签页
tab1, tab2 = st.tabs(["📄 简历分析", "🚀 自动投递"])

with tab1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("## 📄 AI 简历分析")

    col1, col2 = st.columns([2, 1])

    with col1:
        method = st.radio("选择输入方式", ["文本输入", "上传文件"], horizontal=True)

        if method == "文本输入":
            resume_text = st.text_area(
                "粘贴简历内容",
                height=280,
                placeholder="请在此粘贴您的简历内容...\n\n支持中英文简历",
                help="直接粘贴简历文本，支持中英文"
            )

            if resume_text and st.button("开始分析", type="primary", key="analyze_text"):
                if len(resume_text.strip()) < 50:
                    st.warning("⚠️ 简历内容较少，建议至少 50 字以上")
                else:
                    with st.spinner("🔄 AI 正在分析您的简历..."):
                        try:
                            # 导入分析引擎
                            from app.core.multi_ai_debate import JobApplicationPipeline

                            # 创建分析管道
                            pipeline = JobApplicationPipeline()

                            # 执行分析（使用同步包装器）
                            results = run_async(pipeline.process_resume(resume_text))

                            if results:
                                # 保存结果到 session state
                                st.session_state.analysis_results = results

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
                            st.info("💡 提示：请检查网络连接和 API 配置")

        else:  # 上传文件
            uploaded_file = st.file_uploader(
                "支持 PDF、Word、图片、文本",
                type=["pdf", "doc", "docx", "png", "jpg", "jpeg", "txt"],
                help="支持 PDF、Word 文档、图片（OCR识别）和文本文件"
            )

            if uploaded_file:
                st.success(f"✓ 已上传: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")

                if st.button("开始分析", type="primary", key="analyze_file"):
                    with st.spinner("🔄 正在解析文件..."):
                        # 使用老版本的解析代码
                        resume_text = parse_uploaded_file(uploaded_file)

                    if resume_text:
                        st.success(f"✅ 文件解析成功，提取了 {len(resume_text)} 个字符")

                        # 显示提取的文本预览
                        with st.expander("📄 查看提取的文本"):
                            st.text(resume_text[:500] + "..." if len(resume_text) > 500 else resume_text)

                        with st.spinner("🔄 AI 正在分析您的简历..."):
                            try:
                                # 导入分析引擎
                                from app.core.multi_ai_debate import JobApplicationPipeline

                                # 创建分析管道
                                pipeline = JobApplicationPipeline()

                                # 执行分析
                                results = run_async(pipeline.process_resume(resume_text))

                                if results:
                                    # 保存结果到 session state
                                    st.session_state.analysis_results = results

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
                                st.info("💡 提示：请检查网络连接和 API 配置")

    with col2:
        st.markdown("""### 分析内容
- 🎯 职业分析
- 💼 岗位推荐
- ✍️ 简历优化
- 📚 面试准备
- 🎤 模拟面试
- 📈 技能分析

### 支持格式
- 📄 PDF 文档
- 📝 Word 文档
- 🖼️ 图片（OCR）
- 📋 文本文件

### 使用提示
1. 文本输入最快
2. PDF/Word 自动解析
3. 图片需要 OCR 识别
4. 建议简历 > 50 字""")

    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("## 🚀 自动投递")

    st.info("""
    **基于 GitHub 高星项目** [GodsScion/Auto_job_applier_linkedIn](https://github.com/GodsScion/Auto_job_applier_linkedIn) (1544⭐)

    ✨ 智能化 - AI 自动回答申请表单
    ⚡ 高效率 - 每小时可投递 50+ 职位
    🔒 安全性 - 使用反检测技术
    📊 可追踪 - 完整的投递历史记录
    """)

    platforms = st.multiselect(
        "选择平台",
        ["LinkedIn (Easy Apply)", "Boss直聘", "智联招聘"],
        default=["LinkedIn (Easy Apply)"],
        help="LinkedIn 基于 GitHub 高星项目，其他平台开发中"
    )

    if platforms:
        col1, col2 = st.columns(2)

        with col1:
            keywords = st.text_input("搜索关键词", value="Python Developer, Full Stack Engineer", help="多个关键词用逗号分隔")
            locations = st.text_input("工作地点", value="Remote, San Francisco, 北京", help="多个地点用逗号分隔")

        with col2:
            max_count = st.number_input("投递数量", 1, 500, 50, help="建议每次 50 个以内，避免被封号")
            interval = st.slider("投递间隔（秒）", 3, 30, 5, help="间隔时间越长越安全")

        st.markdown("### 高级配置")

        col3, col4 = st.columns(2)

        with col3:
            blacklist = st.text_area(
                "公司黑名单（每行一个）",
                height=100,
                placeholder="不想投递的公司名称\n每行一个"
            )

        with col4:
            pause_before_submit = st.checkbox("提交前暂停审核", value=False, help="每次提交前暂停，人工审核")
            easy_apply_only = st.checkbox("仅 Easy Apply 职位", value=True, help="只投递支持快速申请的职位")

        if st.button("开始投递", type="primary"):
            st.warning("⚠️ 自动投递功能需要本地运行（浏览器自动化）")

            with st.expander("📖 本地运行指南", expanded=True):
                st.markdown("""
                ### 方式 1：使用 FastAPI 后端（推荐）

                ```bash
                # 1. 安装依赖
                pip install playwright undetected-chromedriver
                playwright install chromium

                # 2. 启动后端
                python web_app.py

                # 3. 访问自动投递面板
                http://localhost:8000/static/auto_apply_panel.html
                ```

                ### 方式 2：直接使用 GitHub 高星项目

                ```bash
                # 1. 克隆项目
                git clone https://github.com/GodsScion/Auto_job_applier_linkedIn.git
                cd Auto_job_applier_linkedIn

                # 2. 安装依赖
                pip install -r requirements.txt

                # 3. 配置 config.yaml
                # 填写你的 LinkedIn 账号和投递参数

                # 4. 运行
                python main.py
                ```

                ### 为什么 Streamlit Cloud 不支持？

                - 浏览器自动化需要 Chromium/Chrome
                - 需要持久化会话和 Cookie
                - 需要图形界面环境
                - Streamlit Cloud 是无头环境，不支持这些功能

                ### 推荐架构

                ```
                Streamlit Cloud (前端 UI)
                     ↓ API 调用
                Railway/本地 (后端 + 浏览器自动化)
                ```

                ### 安全提示

                ⚠️ **重要：**
                - 不要过度使用，避免账号被封
                - 建议每天投递不超过 100 个
                - 使用间隔时间 5-10 秒
                - 定期更换 IP 地址
                """)

    st.markdown('</div>', unsafe_allow_html=True)

# 页脚
st.markdown("---")
st.markdown('''
<div style="text-align:center;color:var(--muted);padding:32px 0;font-size:16px">
    <p>💼 祝你求职顺利</p>
    <p>
        <a href="https://github.com/emptyteabot/ai-job-helper" style="color:var(--text);margin:0 16px">GitHub</a>
        <a href="https://github.com/GodsScion/Auto_job_applier_linkedIn" style="color:var(--text);margin:0 16px">高星项目</a>
        <a href="https://ai-job-apper-ibpzap2nnajzrnu8mkthuv.streamlit.app" style="color:var(--text);margin:0 16px">在线体验</a>
    </p>
</div>
''', unsafe_allow_html=True)
