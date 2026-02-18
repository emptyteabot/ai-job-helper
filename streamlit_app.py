"""
AI求职助手 - Streamlit 主应用
整合简历分析和自动投递功能
"""
import streamlit as st

# 页面配置
st.set_page_config(
    page_title="AI求职助手 - 大学生实习版",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .feature-card {
        padding: 1.5rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: 1rem 0;
    }
    .stat-box {
        padding: 1rem;
        border-radius: 8px;
        background: #f0f2f6;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏导航
with st.sidebar:
    st.markdown("# 🎓 AI求职助手")
    st.markdown("### 专为大学生实习设计")
    st.markdown("---")

    # 导航菜单
    page = st.radio(
        "功能导航",
        ["🏠 首页", "📄 简历分析", "🚀 自动投递"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("### 📊 快速统计")
    st.metric("今日分析", "0", "0")
    st.metric("今日投递", "0", "0")

    st.markdown("---")
    st.markdown("### 💡 使用提示")
    st.info("""
    **新手指南：**
    1. 先进行简历分析
    2. 根据建议优化简历
    3. 使用自动投递功能
    4. 定期查看投递反馈
    """)

# 主内容区域
if page == "🏠 首页":
    # 首页内容
    st.markdown('<div class="main-header">🎓 AI求职助手</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">专为大学生实习求职打造的智能助手</div>', unsafe_allow_html=True)

    st.markdown("---")

    # 功能介绍
    st.markdown("## 🌟 核心功能")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 📄 AI 简历分析

        **6 大 AI 协作深度分析**
        - 🎯 职业分析 - 评估职业背景
        - 💼 岗位推荐 - 智能匹配职位
        - ✍️ 简历优化 - 提供改进建议
        - 📚 面试准备 - 面试技巧指导
        - 🎤 模拟面试 - 常见问题解答
        - 📈 技能分析 - 技能提升建议

        **支持格式**
        - PDF、Word 文档
        - 图片（PNG、JPG）
        - 文本输入
        """)

    with col2:
        st.markdown("""
        ### 🚀 自动投递

        **三大平台同步投递**
        - 🟦 Boss直聘 - 国内主流平台
        - 🟨 智联招聘 - 传统招聘网站
        - 🟦 LinkedIn - 国际职场社交

        **智能功能**
        - 多平台并行投递
        - 实时进度追踪
        - 投递数据统计
        - 黑名单管理
        - 自动招呼语
        """)

    st.markdown("---")

    # 使用流程
    st.markdown("## 📋 使用流程")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="stat-box">
            <h3>1️⃣ 简历分析</h3>
            <p>上传简历，获取AI分析报告</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="stat-box">
            <h3>2️⃣ 优化简历</h3>
            <p>根据建议优化简历内容</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="stat-box">
            <h3>3️⃣ 自动投递</h3>
            <p>批量投递，提高效率</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 数据展示
    st.markdown("## 📊 平台数据")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("累计分析", "0", "0")
    with col2:
        st.metric("累计投递", "0", "0")
    with col3:
        st.metric("成功率", "0%", "0%")
    with col4:
        st.metric("活跃用户", "0", "0")

    st.markdown("---")

    # 快速开始
    st.markdown("## 🚀 快速开始")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📄 开始简历分析", type="primary", use_container_width=True):
            st.switch_page("pages/1_📄_简历分析.py")

    with col2:
        if st.button("🚀 开始自动投递", type="primary", use_container_width=True):
            st.switch_page("pages/2_🚀_自动投递.py")

    st.markdown("---")

    # 常见问题
    with st.expander("❓ 常见问题"):
        st.markdown("""
        **Q: 简历分析需要多长时间？**
        A: 通常 30-60 秒即可完成分析。

        **Q: 自动投递会被平台检测吗？**
        A: 我们使用了反检测技术，并设置了合理的投递间隔，安全性较高。

        **Q: 支持哪些简历格式？**
        A: 支持 PDF、Word、图片和文本输入。

        **Q: 投递失败怎么办？**
        A: 系统会自动记录失败原因，您可以在日志中查看详情。

        **Q: 数据安全吗？**
        A: 我们不会存储您的简历内容，所有数据仅用于分析。
        """)

    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>💼 祝你求职顺利！</p>
        <p style='font-size: 0.9rem;'>如有问题，请联系技术支持</p>
    </div>
    """, unsafe_allow_html=True)

elif page == "📄 简历分析":
    # 跳转到简历分析页面
    st.switch_page("pages/1_📄_简历分析.py")

elif page == "🚀 自动投递":
    # 跳转到自动投递页面
    st.switch_page("pages/2_🚀_自动投递.py")
