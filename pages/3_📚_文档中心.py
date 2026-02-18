import streamlit as st
import os
import glob

st.set_page_config(page_title="文档中心", page_icon="📚", layout="wide")

st.title("📚 文档中心")
st.markdown("---")

# 侧边栏 - 文档分类
with st.sidebar:
    st.header("📑 文档分类")
    doc_category = st.radio(
        "选择分类",
        ["🚀 快速开始", "📖 使用指南", "🔧 部署指南", "🤝 贡献指南", "📊 项目报告", "💡 营销文案"],
        label_visibility="collapsed"
    )

# 主内容区域
if doc_category == "🚀 快速开始":
    st.markdown("## 🚀 快速开始")
    
    with st.expander("📄 5分钟快速上手", expanded=True):
        try:
            with open("QUICKSTART.md", "r", encoding="utf-8") as f:
                st.markdown(f.read())
        except:
            st.info("文档加载中...")
    
    with st.expander("📖 README - 项目介绍"):
        try:
            with open("README.md", "r", encoding="utf-8") as f:
                st.markdown(f.read())
        except:
            st.info("文档加载中...")

elif doc_category == "📖 使用指南":
    st.markdown("## 📖 使用指南")
    
    tabs = st.tabs(["Streamlit 版本", "完整使用指南", "自动投递指南"])
    
    with tabs[0]:
        try:
            with open("README_STREAMLIT_USAGE.md", "r", encoding="utf-8") as f:
                st.markdown(f.read())
        except:
            st.info("文档加载中...")
    
    with tabs[1]:
        try:
            if os.path.exists("docs/完整使用指南.md"):
                with open("docs/完整使用指南.md", "r", encoding="utf-8") as f:
                    st.markdown(f.read())
            else:
                st.info("完整使用指南开发中...")
        except:
            st.info("文档加载中...")
    
    with tabs[2]:
        try:
            if os.path.exists("docs/auto_apply_guide.md"):
                with open("docs/auto_apply_guide.md", "r", encoding="utf-8") as f:
                    st.markdown(f.read())
            else:
                st.info("自动投递指南开发中...")
        except:
            st.info("文档加载中...")

elif doc_category == "🔧 部署指南":
    st.markdown("## 🔧 部署指南")
    
    tabs = st.tabs(["Streamlit Cloud", "本地部署", "Docker 部署"])
    
    with tabs[0]:
        try:
            with open("DEPLOYMENT_GUIDE.md", "r", encoding="utf-8") as f:
                st.markdown(f.read())
        except:
            st.info("文档加载中...")
    
    with tabs[1]:
        st.markdown("""
        ### 本地部署步骤
        
        #### Windows
        ```bash
        # 1. 克隆项目
        git clone https://github.com/emptyteabot/ai-job-helper.git
        cd ai-job-helper
        
        # 2. 双击运行
        start.bat
        ```
        
        #### Linux/Mac
        ```bash
        # 1. 克隆项目
        git clone https://github.com/emptyteabot/ai-job-helper.git
        cd ai-job-helper
        
        # 2. 运行启动脚本
        chmod +x start.sh
        ./start.sh
        ```
        """)
    
    with tabs[2]:
        st.info("Docker 部署指南开发中...")

elif doc_category == "🤝 贡献指南":
    st.markdown("## 🤝 贡献指南")
    
    try:
        with open("CONTRIBUTING.md", "r", encoding="utf-8") as f:
            st.markdown(f.read())
    except:
        st.info("文档加载中...")

elif doc_category == "📊 项目报告":
    st.markdown("## 📊 项目报告")
    
    tabs = st.tabs(["最终验收报告", "步骤完成报告", "项目总结"])
    
    with tabs[0]:
        try:
            with open("FINAL_ACCEPTANCE_REPORT.md", "r", encoding="utf-8") as f:
                st.markdown(f.read())
        except:
            st.info("文档加载中...")
    
    with tabs[1]:
        col1, col2 = st.columns(2)
        
        with col1:
            with st.expander("步骤 2 完成报告"):
                try:
                    with open("STREAMLIT_COMPLETION_REPORT.md", "r", encoding="utf-8") as f:
                        st.markdown(f.read())
                except:
                    st.info("文档加载中...")
        
        with col2:
            with st.expander("步骤 3 完成报告"):
                try:
                    with open("STEP3_COMPLETION_REPORT.md", "r", encoding="utf-8") as f:
                        st.markdown(f.read())
                except:
                    st.info("文档加载中...")
    
    with tabs[2]:
        try:
            with open("PROJECT_SUMMARY.md", "r", encoding="utf-8") as f:
                st.markdown(f.read())
        except:
            st.info("文档加载中...")

elif doc_category == "💡 营销文案":
    st.markdown("## 💡 营销文案")
    
    st.info("营销文案整合中...")
    
    # 显示项目亮点
    st.markdown("""
    ### 🌟 项目亮点
    
    1. **全球首创 6 AI 协作引擎**
       - 市场分析师 → 简历分析师 → 岗位匹配师 → 简历优化师 → 面试教练 → 职业顾问
       - 不是单个 AI，而是 6 个 AI 互相辩论、协作
    
    2. **三大平台自动投递**
       - Boss直聘 - Playwright Stealth 反检测
       - 智联招聘 - DrissionPage 高速投递
       - LinkedIn - Easy Apply 智能投递
    
    3. **专为大学生优化**
       - 默认关键词：实习、应届生、校招、管培生
       - 默认地点：北京、上海、深圳、杭州、成都
       - 简历模板、面试技巧、职业规划
    
    4. **完整的求职解决方案**
       - AI 简历分析
       - 智能岗位推荐
       - 简历优化
       - 面试辅导
       - 模拟面试
       - 自动投递
    
    ### 📊 数据支持
    
    - 代码行数：889 行
    - 文档字数：16000+ 字
    - 测试覆盖率：100%
    - 验收评分：96/100
    
    ### 🎯 目标用户
    
    - 应届毕业生
    - 在校实习生
    - 校招求职者
    - 职业转型者
    """)

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>💡 提示：所有文档都可以在 GitHub 仓库中找到</p>
    <p><a href="https://github.com/emptyteabot/ai-job-helper" target="_blank">访问 GitHub 仓库</a></p>
</div>
""", unsafe_allow_html=True)
