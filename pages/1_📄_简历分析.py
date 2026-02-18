import streamlit as st
import requests
import json
import time
from io import BytesIO
import base64

st.set_page_config(
    page_title="简历分析",
    page_icon="📄",
    layout="wide"
)

# 页面标题
st.title("📄 AI 简历分析")
st.markdown("---")

# 初始化 session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'processing' not in st.session_state:
    st.session_state.processing = False

# 侧边栏 - 输入方式选择
with st.sidebar:
    st.header("📥 简历输入")
    input_method = st.radio(
        "选择输入方式",
        ["上传文件", "文本输入"],
        label_visibility="collapsed"
    )

    resume_content = None
    file_name = None

    if input_method == "上传文件":
        uploaded_file = st.file_uploader(
            "上传简历文件",
            type=["pdf", "doc", "docx", "png", "jpg", "jpeg"],
            help="支持 PDF、Word 文档和图片格式"
        )

        if uploaded_file:
            file_name = uploaded_file.name
            resume_content = uploaded_file.read()
            st.success(f"✅ 已上传: {file_name}")

    else:  # 文本输入
        resume_text = st.text_area(
            "粘贴简历内容",
            height=300,
            placeholder="请在此粘贴您的简历内容..."
        )
        if resume_text:
            resume_content = resume_text.encode('utf-8')
            file_name = "resume_text.txt"

    st.markdown("---")

    # 分析按钮
    analyze_button = st.button(
        "🚀 开始分析",
        type="primary",
        use_container_width=True,
        disabled=not resume_content or st.session_state.processing
    )

# 主内容区域
if analyze_button and resume_content:
    st.session_state.processing = True
    st.session_state.analysis_results = None

    # 创建进度显示
    progress_container = st.container()
    with progress_container:
        st.info("🔄 正在分析您的简历，请稍候...")
        progress_bar = st.progress(0)
        status_text = st.empty()

    try:
        # 准备请求数据
        if input_method == "文本输入":
            # 文本输入方式
            data = {
                "resume_text": resume_text
            }
            response = requests.post(
                "https://ai-job-hunter-production-2730.up.railway.app/api/process",
                json=data,
                timeout=300
            )
        else:
            # 文件上传方式
            files = {
                "file": (file_name, resume_content)
            }
            response = requests.post(
                "https://ai-job-hunter-production-2730.up.railway.app/api/process",
                files=files,
                timeout=300
            )

        # 模拟进度更新
        for i in range(100):
            progress_bar.progress(i + 1)
            if i < 30:
                status_text.text("📖 正在读取简历内容...")
            elif i < 60:
                status_text.text("🤖 AI 正在深度分析...")
            elif i < 90:
                status_text.text("✨ 生成分析报告...")
            else:
                status_text.text("✅ 分析完成！")
            time.sleep(0.01)

        if response.status_code == 200:
            st.session_state.analysis_results = response.json()
            progress_container.empty()
            st.success("✅ 分析完成！")
        else:
            st.error(f"❌ 分析失败: {response.status_code} - {response.text}")

    except requests.exceptions.Timeout:
        st.error("❌ 请求超时，请稍后重试")
    except Exception as e:
        st.error(f"❌ 发生错误: {str(e)}")

    finally:
        st.session_state.processing = False

# 显示分析结果
if st.session_state.analysis_results:
    results = st.session_state.analysis_results

    st.markdown("## 📊 分析结果")
    st.markdown("---")

    # 定义分析模块
    analysis_sections = [
        {
            "key": "career_analysis",
            "title": "🎯 职业分析",
            "icon": "🎯",
            "description": "基于您的背景和经验的职业发展分析"
        },
        {
            "key": "job_recommendations",
            "title": "💼 岗位推荐",
            "icon": "💼",
            "description": "适合您的职位推荐"
        },
        {
            "key": "resume_optimization",
            "title": "✍️ 简历优化",
            "icon": "✍️",
            "description": "简历改进建议"
        },
        {
            "key": "interview_preparation",
            "title": "📚 面试准备",
            "icon": "📚",
            "description": "面试技巧和准备要点"
        },
        {
            "key": "mock_interview",
            "title": "🎤 模拟面试",
            "icon": "🎤",
            "description": "常见面试问题和参考答案"
        },
        {
            "key": "skill_gap_analysis",
            "title": "📈 技能差距分析",
            "icon": "📈",
            "description": "技能提升建议"
        }
    ]

    # 使用标签页展示结果
    tabs = st.tabs([f"{section['icon']} {section['title']}" for section in analysis_sections])

    for idx, (tab, section) in enumerate(zip(tabs, analysis_sections)):
        with tab:
            st.markdown(f"### {section['title']}")
            st.caption(section['description'])
            st.markdown("---")

            content = results.get(section['key'], "暂无数据")

            if isinstance(content, dict):
                # 如果是字典，格式化显示
                for key, value in content.items():
                    st.markdown(f"**{key}:**")
                    st.write(value)
                    st.markdown("")
            elif isinstance(content, list):
                # 如果是列表，使用列表显示
                for item in content:
                    st.markdown(f"- {item}")
            else:
                # 纯文本显示
                st.markdown(content)

            # 添加下载按钮
            if content and content != "暂无数据":
                download_content = json.dumps(
                    {section['key']: content},
                    ensure_ascii=False,
                    indent=2
                )
                st.download_button(
                    label=f"📥 下载 {section['title']}",
                    data=download_content,
                    file_name=f"{section['key']}.json",
                    mime="application/json",
                    key=f"download_{section['key']}"
                )

    # 底部操作按钮
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        # 下载完整报告
        full_report = json.dumps(
            st.session_state.analysis_results,
            ensure_ascii=False,
            indent=2
        )
        st.download_button(
            label="📥 下载完整报告",
            data=full_report,
            file_name="resume_analysis_report.json",
            mime="application/json",
            use_container_width=True
        )

    with col2:
        # 重新分析按钮
        if st.button("🔄 重新分析", use_container_width=True):
            st.session_state.analysis_results = None
            st.rerun()

else:
    # 欢迎页面
    st.markdown("""
    ## 👋 欢迎使用 AI 简历分析工具

    ### 🌟 功能特点

    - **📄 多格式支持**: 支持 PDF、Word 文档、图片和文本输入
    - **🤖 AI 深度分析**: 6 大维度全面分析您的简历
    - **💡 个性化建议**: 提供针对性的优化建议
    - **📊 可视化报告**: 清晰直观的分析结果展示
    - **💾 结果导出**: 支持下载分析报告

    ### 📋 分析内容

    1. **🎯 职业分析** - 评估您的职业背景和发展方向
    2. **💼 岗位推荐** - 推荐适合您的职位
    3. **✍️ 简历优化** - 提供简历改进建议
    4. **📚 面试准备** - 面试技巧和注意事项
    5. **🎤 模拟面试** - 常见问题和参考答案
    6. **📈 技能差距分析** - 技能提升方向建议

    ### 🚀 开始使用

    请在左侧边栏上传您的简历或输入简历内容，然后点击"开始分析"按钮。
    """)

    # 添加示例展示
    with st.expander("💡 查看使用示例"):
        st.markdown("""
        **上传文件方式:**
        1. 点击左侧"上传文件"
        2. 选择您的简历文件（PDF/Word/图片）
        3. 点击"开始分析"按钮

        **文本输入方式:**
        1. 选择"文本输入"
        2. 在文本框中粘贴您的简历内容
        3. 点击"开始分析"按钮

        **分析时间:** 通常需要 30-60 秒完成分析
        """)

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>💡 提示：分析结果仅供参考，请结合实际情况使用</p>
    </div>
    """,
    unsafe_allow_html=True
)
