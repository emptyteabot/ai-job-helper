"""
温暖人性化 UI 风格 - Instagram + 小红书风格
柔和色彩 + 圆润设计 + 友好语言
"""

WARM_UI_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');

:root {
    /* 温暖色调 - 更简洁 */
    --bg-primary: #ffffff;
    --bg-secondary: #fafafa;
    --bg-card: #ffffff;
    --text-primary: #1a1a1a;
    --text-secondary: #4a4a4a;
    --text-muted: #8a8a8a;

    /* 渐变色 - 柔和温暖 */
    --gradient-warm: linear-gradient(135deg, #ffb6b9 0%, #fae3d9 100%);
    --gradient-sunset: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
    --gradient-ocean: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    --gradient-purple: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%);

    /* 主色调 - 温暖橙粉 */
    --accent: #ff8a80;
    --accent-light: #ffab91;
    --accent-lighter: #ffccbc;
    --success: #81c784;
    --warning: #ffd54f;
    --info: #64b5f6;

    /* 圆角 - 更圆润 */
    --radius-sm: 12px;
    --radius-md: 20px;
    --radius-lg: 28px;
    --radius-xl: 36px;

    /* 柔和阴影 */
    --shadow-soft: 0 4px 20px rgba(255, 107, 107, 0.08);
    --shadow-medium: 0 8px 30px rgba(255, 107, 107, 0.12);
    --shadow-large: 0 12px 40px rgba(255, 107, 107, 0.15);

    /* 动画 */
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-secondary);
    color: var(--text-primary);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    font-weight: 400;
}

/* 隐藏 Streamlit 默认元素 */
#MainMenu, footer, header,
.stDeployButton,
button[kind="header"],
[data-testid="stToolbar"],
[data-testid="manage-app"],
.viewerBadge_container__1QSob,
.styles_viewerBadge__1yB5_ {
    display: none !important;
}

.main .block-container {
    max-width: 1200px;
    padding: 1.5rem 2rem 4rem;
}

/* 顶部导航 - 小红书风格 */
.top {
    background: var(--bg-card);
    padding: 1rem 2rem;
    border-radius: 0 0 var(--radius-lg) var(--radius-lg);
    box-shadow: var(--shadow-soft);
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--accent);
}

.dot {
    width: 12px;
    height: 12px;
    background: var(--gradient-warm);
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.2); opacity: 0.8; }
}

/* Hero Section - Instagram 风格 */
.hero {
    text-align: center;
    padding: 3rem 2rem;
    background: var(--gradient-sunset);
    border-radius: var(--radius-xl);
    margin-bottom: 2rem;
    box-shadow: var(--shadow-large);
    position: relative;
    overflow: hidden;
}

.hero::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%);
    animation: float 6s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(-20px, -20px); }
}

.hero h1 {
    font-size: clamp(2rem, 5vw, 3.5rem);
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.2;
    margin-bottom: 1rem;
    color: white;
    text-shadow: 0 2px 10px rgba(0,0,0,0.1);
    position: relative;
    z-index: 1;
}

.hero-subtitle {
    font-size: 1.125rem;
    color: rgba(255,255,255,0.95);
    max-width: 600px;
    margin: 0 auto 1.5rem;
    line-height: 1.7;
    position: relative;
    z-index: 1;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1.25rem;
    background: rgba(255,255,255,0.95);
    border-radius: 999px;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--accent);
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-soft);
    position: relative;
    z-index: 1;
}

/* Card - 小红书卡片风格 */
.card {
    background: var(--bg-card);
    border-radius: var(--radius-lg);
    padding: 2rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-soft);
    transition: var(--transition);
    border: 1px solid rgba(255, 107, 107, 0.08);
}

.card:hover {
    box-shadow: var(--shadow-medium);
    transform: translateY(-2px);
}

.card h2 {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
    color: var(--text-primary);
}

.card p {
    color: var(--text-secondary);
    line-height: 1.8;
    margin-bottom: 1.5rem;
}

/* Tabs - 温暖风格 */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.75rem;
    background: transparent;
    border: none;
    margin-bottom: 2rem;
    padding: 0;
}

.stTabs [data-baseweb="tab"] {
    padding: 0.875rem 1.75rem;
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-secondary);
    border-radius: var(--radius-md);
    transition: var(--transition);
    border: 2px solid transparent;
    background: var(--bg-card);
    box-shadow: var(--shadow-soft);
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--accent);
    border-color: var(--accent-lighter);
}

.stTabs [aria-selected="true"] {
    background: var(--gradient-warm);
    color: white;
    border-color: transparent;
    box-shadow: var(--shadow-medium);
    transform: translateY(-2px);
}

/* Buttons - 可爱圆润 */
.stButton > button {
    background: var(--gradient-warm);
    color: white;
    border: none;
    border-radius: var(--radius-md);
    padding: 0.875rem 2.5rem;
    font-size: 1rem;
    font-weight: 600;
    transition: var(--transition);
    box-shadow: var(--shadow-soft);
    letter-spacing: 0.02em;
}

.stButton > button:hover {
    box-shadow: var(--shadow-medium);
    transform: translateY(-3px) scale(1.02);
}

.stButton > button:active {
    transform: translateY(-1px) scale(0.98);
}

/* Input - 柔和风格 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    border: 2px solid rgba(255, 107, 107, 0.15);
    border-radius: var(--radius-md);
    padding: 0.875rem 1.25rem;
    font-size: 0.9375rem;
    transition: var(--transition);
    background: var(--bg-card);
    color: var(--text-primary);
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent-light);
    box-shadow: 0 0 0 4px rgba(255, 107, 107, 0.1);
    outline: none;
}

.stTextArea > div > div > textarea {
    min-height: 200px;
    line-height: 1.8;
}

/* Progress Bar - 可爱风格 */
.stProgress > div > div > div {
    background: var(--gradient-warm) !important;
    height: 8px !important;
    border-radius: 999px;
}

.stProgress > div > div {
    background: rgba(255, 107, 107, 0.1) !important;
    height: 8px !important;
    border-radius: 999px;
}

/* Alert - 温暖提示 */
.stAlert {
    border-radius: var(--radius-md);
    padding: 1.25rem 1.5rem;
    border: none;
    box-shadow: var(--shadow-soft);
    font-size: 0.9375rem;
}

.stSuccess {
    background: linear-gradient(135deg, #d3f9d8 0%, #b2f2bb 100%);
    color: #2b8a3e;
}

.stInfo {
    background: linear-gradient(135deg, #d0ebff 0%, #a5d8ff 100%);
    color: #1864ab;
}

.stWarning {
    background: linear-gradient(135deg, #fff3bf 0%, #ffec99 100%);
    color: #e67700;
}

.stError {
    background: linear-gradient(135deg, #ffe0e0 0%, #ffc9c9 100%);
    color: #c92a2a;
}

/* Expander - 卡片风格 */
.stExpander {
    background: var(--bg-card);
    border: 2px solid rgba(255, 107, 107, 0.08);
    border-radius: var(--radius-md);
    margin-bottom: 1rem;
    overflow: hidden;
    box-shadow: var(--shadow-soft);
    transition: var(--transition);
}

.stExpander:hover {
    border-color: var(--accent-lighter);
    box-shadow: var(--shadow-medium);
}

.stExpander > div > div {
    padding: 1.5rem;
}

/* Markdown 内容 - 更易读 */
.stMarkdown {
    line-height: 1.9;
    color: var(--text-primary);
}

.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-weight: 600;
    margin-top: 1.75em;
    margin-bottom: 0.875em;
    color: var(--text-primary);
}

.stMarkdown p {
    margin-bottom: 1.25em;
}

.stMarkdown ul, .stMarkdown ol {
    margin: 1.25em 0;
    padding-left: 1.75em;
}

.stMarkdown li {
    margin-bottom: 0.75em;
    line-height: 1.9;
}

.stMarkdown strong {
    color: var(--accent);
    font-weight: 600;
}

.stMarkdown code {
    background: rgba(255, 107, 107, 0.08);
    padding: 0.25em 0.5em;
    border-radius: 6px;
    font-size: 0.875em;
    color: var(--accent);
}

.stMarkdown pre {
    background: var(--bg-secondary);
    padding: 1.25rem;
    border-radius: var(--radius-md);
    overflow-x: auto;
    border: 2px solid rgba(255, 107, 107, 0.08);
}

/* Stats Card - 渐变卡片 */
.stat-card {
    background: var(--gradient-warm);
    color: white;
    border-radius: var(--radius-lg);
    padding: 2rem 1.5rem;
    text-align: center;
    box-shadow: var(--shadow-medium);
    transition: var(--transition);
}

.stat-card:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-large);
}

.stat-value {
    font-size: 2.75rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    text-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.stat-label {
    font-size: 0.9375rem;
    opacity: 0.95;
    font-weight: 500;
}

/* Radio Buttons - 可爱风格 */
.stRadio > div {
    gap: 1rem;
}

.stRadio > div > label {
    background: var(--bg-card);
    padding: 0.75rem 1.5rem;
    border-radius: var(--radius-md);
    transition: var(--transition);
    cursor: pointer;
    border: 2px solid rgba(255, 107, 107, 0.08);
    box-shadow: var(--shadow-soft);
}

.stRadio > div > label:hover {
    border-color: var(--accent-lighter);
    transform: translateY(-2px);
}

/* Spinner - 可爱加载 */
.stSpinner > div {
    border-color: var(--accent) !important;
}

/* Slider - 温暖滑块 */
.stSlider > div > div > div {
    background: var(--gradient-warm) !important;
}

/* File Uploader - 友好上传 */
.stFileUploader {
    border: 2px dashed rgba(255, 107, 107, 0.3);
    border-radius: var(--radius-lg);
    padding: 2rem;
    background: var(--bg-card);
    transition: var(--transition);
}

.stFileUploader:hover {
    border-color: var(--accent);
    background: rgba(255, 107, 107, 0.02);
}

/* 页脚 */
.footer {
    text-align: center;
    color: var(--text-muted);
    padding: 2.5rem 0;
    font-size: 0.9375rem;
    border-top: 2px solid rgba(255, 107, 107, 0.08);
    margin-top: 3rem;
}

.footer a {
    color: var(--accent);
    text-decoration: none;
    margin: 0 1rem;
    transition: var(--transition);
    font-weight: 500;
}

.footer a:hover {
    color: var(--accent-light);
    text-decoration: underline;
}

/* 滚动条美化 */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: var(--gradient-warm);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--accent);
}
</style>
"""
