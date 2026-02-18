"""
AI求职助手 - OpenAI 打字机风格
超大字体 + 打字机光标 + 极简设计
"""
import streamlit as st

st.set_page_config(page_title="AI求职助手", page_icon="✨", layout="wide", initial_sidebar_state="collapsed")

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

st.markdown('<div class="top-nav"><div class="brand"><div class="dot"></div><span>AI求职助手</span></div></div>', unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="pill">专为大学生实习设计</div><h1>让 AI 帮你找到<br>理想工作<span class="cursor"></span></h1><div class="hero-subtitle">6 个 AI 协作分析简历，智能推荐岗位，自动投递到 Boss直聘、智联招聘、LinkedIn</div></div>', unsafe_allow_html=True)

tab1,tab2,tab3,tab4=st.tabs(["📄 简历分析","🚀 自动投递","📚 文档","❓ 帮助"])

with tab1:
    st.markdown('<div class="panel">',unsafe_allow_html=True)
    st.markdown("## 📄 AI 简历分析")
    col1,col2=st.columns([2,1])
    with col1:
        method=st.radio("选择输入方式",["上传文件","文本输入"],horizontal=True)
        if method=="上传文件":
            f=st.file_uploader("支持 PDF、Word、图片",type=["pdf","doc","docx","png","jpg","jpeg"])
            if f:
                st.success(f"✓ 已上传: {f.name}")
                if st.button("开始分析",type="primary"):st.info("分析功能开发中...")
        else:
            txt=st.text_area("粘贴简历内容",height=280,placeholder="请在此粘贴您的简历内容...")
            if txt and st.button("开始分析",type="primary"):st.info("分析功能开发中...")
    with col2:
        st.markdown("""### 分析内容
- 🎯 职业分析
- 💼 岗位推荐
- ✍️ 简历优化
- 📚 面试准备
- 🎤 模拟面试
- 📈 技能分析""")
    st.markdown('</div>',unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="panel">',unsafe_allow_html=True)
    st.markdown("## 🚀 自动投递")
    p=st.multiselect("选择平台",["Boss直聘","智联招聘","LinkedIn"],default=["Boss直聘"])
    if p:
        c1,c2=st.columns(2)
        with c1:
            st.text_input("搜索关键词",value="实习生,应届生")
            st.text_input("工作地点",value="北京,上海,深圳")
        with c2:
            st.number_input("投递数量",1,500,50)
            st.slider("投递间隔（秒）",3,30,5)
        if st.button("开始投递",type="primary"):st.info("投递功能开发中...")
    st.markdown('</div>',unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="panel">',unsafe_allow_html=True)
    st.markdown("## 📚 文档中心")
    with st.expander("🚀 快速开始",expanded=True):
        st.markdown("""### 在线体验
https://ai-job-hunter-production-2730.up.railway.app

### 本地运行
```bash
start.bat  # Windows
./start.sh # Linux/Mac
```""")
    st.markdown('</div>',unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="panel">',unsafe_allow_html=True)
    st.markdown("## ❓ 帮助中心")
    with st.expander("如何快速上手？"):st.markdown("""1. 上传简历
2. 开始分析
3. 查看结果
4. 自动投递""")
    with st.expander("支持哪些格式？"):st.markdown("PDF、Word、图片、文本")
    st.markdown('</div>',unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align:center;color:var(--muted);padding:32px 0;font-size:16px"><p>💼 祝你求职顺利</p><p><a href="https://github.com/emptyteabot/ai-job-helper" style="color:var(--text);margin:0 16px">GitHub</a><a href="https://github.com/emptyteabot/ai-job-helper/blob/main/QUICKSTART.md" style="color:var(--text);margin:0 16px">文档</a></p></div>',unsafe_allow_html=True)
