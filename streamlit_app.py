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

# 全局样式 - Gemini 极简风格
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Noto+Sans+SC:wght@400;500;700&display=swap');

:root {
    --gemini-blue: #1a73e8;
    --gemini-blue-hover: #1557b0;
    --text: #1f1f1f;
    --text-light: #5f6368;
    --border: #e8eaed;
    --bg: #ffffff;
    --bg-hover: #f8f9fa;
}

* {
    font-family: 'Google Sans', 'Noto Sans SC', sans-serif;
}

#MainMenu, footer, header {visibility: hidden}

.main .block-container {
    max-width: 900px;
    padding: 1rem 1.5rem 3rem;
}

/* 顶部 Logo */
.logo {
    font-size: 1.375rem;
    font-weight: 500;
    color: var(--text);
    padding: 1rem 0;
    margin-bottom: 2rem;
}

/* Hero */
.hero {
    margin-bottom: 3rem;
}

.hero h1 {
    font-size: 2.75rem;
    font-weight: 400;
    color: var(--text);
    line-height: 1.3;
    margin-bottom: 0.75rem;
}

.hero p {
    font-size: 1rem;
    color: var(--text-light);
    line-height: 1.5;
}

/* 按钮 */
.stButton > button {
    background: var(--gemini-blue);
    color: white;
    border: none;
    border-radius: 24px;
    padding: 0.625rem 1.5rem;
    font-size: 0.875rem;
    font-weight: 500;
    transition: background 0.2s;
}

.stButton > button:hover {
    background: var(--gemini-blue-hover);
}

/* 输入框 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.75rem;
    font-size: 0.875rem;
    transition: border 0.2s;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--gemini-blue);
    outline: none;
}

.stTextArea > div > div > textarea {
    min-height: 180px;
}

/* 标签页 */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid var(--border);
}

.stTabs [data-baseweb="tab"] {
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-light);
    border: none;
}

.stTabs [aria-selected="true"] {
    color: var(--gemini-blue);
    border-bottom: 2px solid var(--gemini-blue);
}

/* Radio */
.stRadio > div {
    gap: 1rem;
}

.stRadio label {
    font-size: 0.875rem;
    color: var(--text);
}

/* 信息框 */
.stAlert {
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg-hover);
}

/* 文件上传 */
.stFileUploader {
    border: 1px dashed var(--border);
    border-radius: 8px;
    padding: 1.5rem;
}

/* 移除多余装饰 */
.stExpander {
    border: none;
    box-shadow: none;
}
</style>
""", unsafe_allow_html=True)

# Logo
st.markdown('<div class="logo">AI 求职助手</div>', unsafe_allow_html=True)

# Hero
st.markdown('''
<div class="hero">
    <h1>让 AI 帮你找到理想工作</h1>
    <p>分析简历，推荐岗位，自动投递</p>
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
tab1, tab2 = st.tabs(["简历分析", "自动投递"])

with tab1:
    st.markdown("### 简历分析")

    method = st.radio("", ["文本输入", "上传文件"], horizontal=True, label_visibility="collapsed")

    if method == "文本输入":
        resume_text = st.text_area(
            "",
            height=180,
            placeholder="粘贴你的简历内容...",
            label_visibility="collapsed"
        )

        if resume_text and st.button("分析", type="primary", key="analyze_text"):
            if len(resume_text.strip()) < 50:
                st.warning("简历内容较少，建议至少 50 字以上")
            else:
                with st.spinner("分析中..."):
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
                            st.success("完成")

                            # 使用标签页显示结果
                            result_tabs = st.tabs(["职业分析", "岗位推荐", "简历优化", "面试准备", "模拟面试", "技能分析"])

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
                        st.error(f"分析失败: {str(e)}")

    else:  # 上传文件
        uploaded_file = st.file_uploader(
            "",
            type=["pdf", "doc", "docx", "png", "jpg", "jpeg", "txt"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            if st.button("分析", type="primary", key="analyze_file"):
                with st.spinner("解析中..."):
                    # 使用老版本的解析代码
                    resume_text = parse_uploaded_file(uploaded_file)

                if resume_text:
                    with st.spinner("分析中..."):
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
                                st.success("完成")

                                # 显示各个分析结果
                                with st.expander("职业分析", expanded=True):
                                    st.write(results.get('career_analysis', '暂无数据'))

                                with st.expander("岗位推荐"):
                                    st.write(results.get('job_recommendations', '暂无数据'))

                                with st.expander("简历优化"):
                                    st.write(results.get('resume_optimization', '暂无数据'))

                                with st.expander("面试准备"):
                                    st.write(results.get('interview_preparation', '暂无数据'))

                                with st.expander("模拟面试"):
                                    st.write(results.get('mock_interview', '暂无数据'))

                                with st.expander("技能分析"):
                                    st.write(results.get('skill_gap_analysis', '暂无数据'))

                    except Exception as e:
                        st.error(f"分析失败: {str(e)}")

with tab2:
    st.markdown("### 自动投递")

    st.info("基于 GitHub 高星项目 [GodsScion/Auto_job_applier_linkedIn](https://github.com/GodsScion/Auto_job_applier_linkedIn)")

    platforms = st.multiselect(
        "平台",
        ["LinkedIn (Easy Apply)", "Boss直聘", "智联招聘"],
        default=["LinkedIn (Easy Apply)"]
    )

    if platforms:
        col1, col2 = st.columns(2)

        with col1:
            keywords = st.text_input("关键词", value="Python Developer")
            locations = st.text_input("地点", value="Remote")

        with col2:
            max_count = st.number_input("数量", 1, 500, 50)
            interval = st.slider("间隔（秒）", 3, 30, 5)

        if st.button("开始投递", type="primary"):
            st.warning("需要本地运行")

            with st.expander("本地运行指南"):
                st.markdown("""
                ```bash
                # 克隆项目
                git clone https://github.com/GodsScion/Auto_job_applier_linkedIn.git
                cd Auto_job_applier_linkedIn

                # 安装依赖
                pip install -r requirements.txt

                # 配置 config.yaml
                # 填写你的 LinkedIn 账号和投递参数

                # 运行
                python main.py
                ```
                """)

# 页脚
st.markdown('''
<div style="text-align:center;color:var(--text-light);padding:2rem 0;font-size:0.75rem;border-top:1px solid var(--border);margin-top:3rem">
    <a href="https://github.com/emptyteabot/ai-job-helper" style="color:var(--text-light);margin:0 1rem;text-decoration:none">GitHub</a>
    <a href="https://github.com/GodsScion/Auto_job_applier_linkedIn" style="color:var(--text-light);margin:0 1rem;text-decoration:none">高星项目</a>
</div>
''', unsafe_allow_html=True)
