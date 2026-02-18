"""
AI求职助手 - 简化版
专注于简历分析 + 自动投递
"""
import streamlit as st

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
.error-box{background:#fff8f8;border:1px solid #f0d5d5;border-radius:12px;padding:20px;margin:20px 0}
.error-box h3{color:#933333;font-size:20px;margin-bottom:10px}
.error-box p{color:#666;font-size:16px;line-height:1.6}
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

# 错误提示
st.markdown('''
<div class="error-box">
    <h3>⚠️ 后端服务需要更新</h3>
    <p><strong>当前问题：</strong></p>
    <p>• Railway 后端部署的代码版本过旧，缺少必要的 API 端点</p>
    <p>• 简历分析功能需要 <code>/api/process</code> 端点</p>
    <p>• 自动投递功能需要 <code>/api/auto-apply/*</code> 端点</p>
    <br>
    <p><strong>解决方案：</strong></p>
    <p>1. 推送最新的 web_app.py 到 GitHub</p>
    <p>2. Railway 会自动重新部署</p>
    <p>3. 或者在本地运行：<code>python web_app.py</code></p>
    <br>
    <p><strong>本地运行命令：</strong></p>
    <p><code>cd "C:\\Users\\陈盈桦\\Desktop\\Desktop_整理_2026-02-09_172732\\Folders\\自动投简历"</code></p>
    <p><code>python web_app.py</code></p>
    <p>然后访问：<a href="http://localhost:8000" target="_blank">http://localhost:8000</a></p>
</div>
''', unsafe_allow_html=True)

# 标签页
tab1, tab2 = st.tabs(["📄 简历分析", "🚀 自动投递"])

with tab1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("## 📄 AI 简历分析")

    col1, col2 = st.columns([2, 1])

    with col1:
        method = st.radio("选择输入方式", ["上传文件", "文本输入"], horizontal=True)

        if method == "上传文件":
            f = st.file_uploader("支持 PDF、Word、图片", type=["pdf", "doc", "docx", "png", "jpg", "jpeg"])
            if f:
                st.success(f"✓ 已上传: {f.name}")
                if st.button("开始分析", type="primary"):
                    st.error("❌ 后端 API 不可用，请先更新 Railway 部署或在本地运行")
        else:
            txt = st.text_area("粘贴简历内容", height=280, placeholder="请在此粘贴您的简历内容...")
            if txt and st.button("开始分析", type="primary"):
                st.error("❌ 后端 API 不可用，请先更新 Railway 部署或在本地运行")

    with col2:
        st.markdown("""### 分析内容
- 🎯 职业分析
- 💼 岗位推荐
- ✍️ 简历优化
- 📚 面试准备
- 🎤 模拟面试
- 📈 技能分析""")

    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("## 🚀 自动投递")

    p = st.multiselect("选择平台", ["Boss直聘", "智联招聘", "LinkedIn"], default=["Boss直聘"])

    if p:
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("搜索关键词", value="实习生,应届生")
            st.text_input("工作地点", value="北京,上海,深圳")
        with c2:
            st.number_input("投递数量", 1, 500, 50)
            st.slider("投递间隔（秒）", 3, 30, 5)

        if st.button("开始投递", type="primary"):
            st.error("❌ 后端 API 不可用，请先更新 Railway 部署或在本地运行")

    st.markdown('</div>', unsafe_allow_html=True)

# 页脚
st.markdown("---")
st.markdown('''
<div style="text-align:center;color:var(--muted);padding:32px 0;font-size:16px">
    <p>💼 祝你求职顺利</p>
    <p>
        <a href="https://github.com/emptyteabot/ai-job-helper" style="color:var(--text);margin:0 16px">GitHub</a>
        <a href="https://ai-job-hunter-production-2730.up.railway.app" style="color:var(--text);margin:0 16px">Railway 后端</a>
    </p>
</div>
''', unsafe_allow_html=True)
