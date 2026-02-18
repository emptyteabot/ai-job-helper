import streamlit as st

st.set_page_config(page_title="帮助中心", page_icon="❓", layout="wide")

st.title("❓ 帮助中心")
st.markdown("---")

# 侧边栏 - 问题分类
with st.sidebar:
    st.header("🔍 问题分类")
    help_category = st.radio(
        "选择分类",
        ["🚀 快速开始", "📄 简历分析", "🚀 自动投递", "⚙️ 配置问题", "🐛 常见错误", "💬 联系我们"],
        label_visibility="collapsed"
    )

# 主内容区域
if help_category == "🚀 快速开始":
    st.markdown("## 🚀 快速开始")
    
    with st.expander("❓ 如何快速上手？", expanded=True):
        st.markdown("""
        ### 方式一：在线体验（最快）
        
        直接访问：https://ai-job-hunter-production-2730.up.railway.app
        
        1. 打开网页
        2. 上传简历或粘贴文本
        3. 点击开始AI分析
        4. 查看分析结果
        
        ### 方式二：本地运行
        
        **Windows 用户：**
        ```bash
        git clone https://github.com/emptyteabot/ai-job-helper.git
        cd ai-job-helper
        start.bat
        ```
        
        **Mac/Linux 用户：**
        ```bash
        git clone https://github.com/emptyteabot/ai-job-helper.git
        cd ai-job-helper
        ./start.sh
        ```
        """)
    
    with st.expander("❓ 需要什么前置条件？"):
        st.markdown("""
        - Python 3.8 或更高版本
        - 稳定的网络连接
        - （可选）DeepSeek API Key（用于完整功能）
        """)
    
    with st.expander("❓ 如何获取 API Key？"):
        st.markdown("""
        1. 访问 [DeepSeek](https://platform.deepseek.com/)
        2. 注册账号
        3. 在控制台创建 API Key
        4. 复制到 .env 文件中
        """)

elif help_category == "📄 简历分析":
    st.markdown("## 📄 简历分析")
    
    with st.expander("❓ 支持哪些简历格式？", expanded=True):
        st.markdown("""
        支持以下格式：
        - PDF (.pdf)
        - Word (.doc, .docx)
        - 图片 (.png, .jpg, .jpeg)
        - 纯文本
        """)
    
    with st.expander("❓ 分析需要多长时间？"):
        st.markdown("""
        通常 30-60 秒即可完成分析。
        
        影响因素：
        - 简历长度
        - 网络速度
        - API 响应时间
        """)
    
    with st.expander("❓ 分析结果包含什么？"):
        st.markdown("""
        6 大维度分析：
        
        1. **职业分析** - 评估职业背景和发展方向
        2. **岗位推荐** - 推荐适合的职位
        3. **简历优化** - 提供改进建议
        4. **面试准备** - 面试技巧和注意事项
        5. **模拟面试** - 常见问题和参考答案
        6. **技能差距分析** - 技能提升方向建议
        """)
    
    with st.expander("❓ 分析失败怎么办？"):
        st.markdown("""
        可能的原因和解决方法：
        
        1. **网络问题**
           - 检查网络连接
           - 尝试刷新页面
        
        2. **文件太大**
           - 简历文件不要超过 10MB
           - 尝试压缩图片
        
        3. **API 问题**
           - 检查 API Key 是否正确
           - 查看 API 额度是否用完
        
        4. **格式问题**
           - 确保文件格式正确
           - 尝试转换为 PDF 格式
        """)

elif help_category == "🚀 自动投递":
    st.markdown("## 🚀 自动投递")
    
    with st.expander("❓ 支持哪些平台？", expanded=True):
        st.markdown("""
        目前支持三大平台：
        
        1. **Boss直聘**
           - 使用 Playwright Stealth
           - 反检测通过率 > 95%
        
        2. **智联招聘**
           - 使用 DrissionPage
           - 速度快 10 倍
        
        3. **LinkedIn**
           - Easy Apply 功能
           - 国际职场社交
        """)
    
    with st.expander("❓ 会被平台检测吗？"):
        st.markdown("""
        我们使用了多种反检测技术：
        
        - 随机延迟
        - 行为模拟
        - User-Agent 轮换
        - Cookie 管理
        
        建议：
        - 设置合理的投递间隔（5-10秒）
        - 避免在深夜大量投递
        - 定期更换账号密码
        """)
    
    with st.expander("❓ 投递失败怎么办？"):
        st.markdown("""
        常见原因：
        
        1. **账号密码错误**
           - 检查账号信息
           - 尝试手动登录验证
        
        2. **验证码问题**
           - 某些平台需要手动验证
           - 建议先手动登录一次
        
        3. **平台限制**
           - 降低投递速度
           - 分批次投递
        
        4. **简历未上传**
           - 确保平台上已上传简历
           - 检查简历是否完整
        """)
    
    with st.expander("❓ 如何提高投递成功率？"):
        st.markdown("""
        建议：
        
        1. **完善简历**
           - 使用简历分析功能优化
           - 确保信息完整
        
        2. **精准关键词**
           - 使用多个相关关键词
           - 针对不同平台调整
        
        3. **合理时间**
           - 工作日 9:00-17:00
           - 避开高峰时段
        
        4. **黑名单管理**
           - 及时添加不合适的公司
           - 定期更新
        """)

elif help_category == "⚙️ 配置问题":
    st.markdown("## ⚙️ 配置问题")
    
    with st.expander("❓ 如何配置环境变量？", expanded=True):
        st.markdown("""
        1. 复制配置文件：
        ```bash
        cp .env.example .env
        ```
        
        2. 编辑 .env 文件：
        ```
        DEEPSEEK_API_KEY=your_api_key_here
        ```
        
        3. 重启应用
        """)
    
    with st.expander("❓ 端口被占用怎么办？"):
        st.markdown("""
        使用其他端口：
        ```bash
        streamlit run streamlit_app.py --server.port 8502
        ```
        """)
    
    with st.expander("❓ 依赖安装失败？"):
        st.markdown("""
        尝试以下方法：
        
        1. 升级 pip：
        ```bash
        pip install --upgrade pip
        ```
        
        2. 使用国内镜像：
        ```bash
        pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
        ```
        
        3. 单独安装失败的包：
        ```bash
        pip install package_name
        ```
        """)

elif help_category == "🐛 常见错误":
    st.markdown("## 🐛 常见错误")
    
    with st.expander("❌ ModuleNotFoundError", expanded=True):
        st.markdown("""
        **错误信息：**
        ```
        ModuleNotFoundError: No module named 'streamlit'
        ```
        
        **解决方法：**
        ```bash
        pip install streamlit
        ```
        """)
    
    with st.expander("❌ API Key 错误"):
        st.markdown("""
        **错误信息：**
        ```
        Invalid API Key
        ```
        
        **解决方法：**
        1. 检查 .env 文件中的 API Key
        2. 确保没有多余的空格
        3. 重新生成 API Key
        """)
    
    with st.expander("❌ 连接超时"):
        st.markdown("""
        **错误信息：**
        ```
        Connection timeout
        ```
        
        **解决方法：**
        1. 检查网络连接
        2. 尝试使用代理
        3. 增加超时时间
        """)
    
    with st.expander("❌ 文件上传失败"):
        st.markdown("""
        **可能原因：**
        - 文件太大（> 200MB）
        - 文件格式不支持
        - 网络不稳定
        
        **解决方法：**
        1. 压缩文件
        2. 转换文件格式
        3. 使用文本输入方式
        """)

elif help_category == "💬 联系我们":
    st.markdown("## 💬 联系我们")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📧 问题反馈
        
        如果你遇到问题或有建议：
        
        1. **GitHub Issues**
           - [提交 Issue](https://github.com/emptyteabot/ai-job-helper/issues)
           - 描述问题和复现步骤
           - 附上错误日志
        
        2. **GitHub Discussions**
           - [参与讨论](https://github.com/emptyteabot/ai-job-helper/discussions)
           - 分享使用经验
           - 提出功能建议
        """)
    
    with col2:
        st.markdown("""
        ### 🤝 参与贡献
        
        欢迎贡献代码：
        
        1. Fork 项目
        2. 创建分支
        3. 提交代码
        4. 发起 Pull Request
        
        详见：[贡献指南](https://github.com/emptyteabot/ai-job-helper/blob/main/CONTRIBUTING.md)
        """)
    
    st.markdown("---")
    
    st.info("""
    💡 **提示**：在提问前，请先查看文档和常见问题，可能已经有答案了！
    """)

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>💼 祝你求职顺利！</p>
    <p>如有问题，随时联系我们</p>
</div>
""", unsafe_allow_html=True)
