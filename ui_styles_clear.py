"""
高对比度 UI 风格 - 清晰易读
参考现代 SaaS 产品设计（Linear, Notion, Vercel）
"""

CLEAR_UI_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    /* 高对比度配色 */
    --bg-primary: #ffffff;
    --bg-secondary: #f5f5f5;
    --bg-tertiary: #e8e8e8;

    /* 深色文字 - 高对比度 */
    --text-primary: #0a0a0a;
    --text-secondary: #404040;
    --text-tertiary: #737373;

    /* 主色调 - 鲜明的橙色 */
    --accent: #ff6b35;
    --accent-hover: #ff5722;
    --accent-light: #fff3f0;

    /* 功能色 */
    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
    --info: #3b82f6;

    /* 边框 */
    --border: #d4d4d4;
    --border-light: #e5e5e5;

    /* 圆角 */
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;

    /* 阴影 - 更明显 */
    --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.08);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);
    --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15), 0 10px 10px rgba(0, 0, 0, 0.04);
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-secondary);
    color: var(--text-primary);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    font-size: 15px;
    line-height: 1.6;
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
    padding: 2rem 2rem 4rem;
}

/* Hero Section - 高对比度 */
.hero {
    text-align: center;
    padding: 4rem 2rem;
    background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%);
    border-radius: var(--radius-lg);
    margin-bottom: 2rem;
    box-shadow: var(--shadow-lg);
}

.hero h1 {
    font-size: clamp(2.5rem, 5vw, 4rem);
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin-bottom: 1rem;
    color: #ffffff;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.hero-subtitle {
    font-size: 1.25rem;
    color: rgba(255, 255, 255, 0.95);
    max-width: 700px;
    margin: 0 auto 2rem;
    line-height: 1.6;
    font-weight: 500;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1.25rem;
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 999px;
    font-size: 0.875rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 1.5rem;
}

/* Card - 清晰的边框和阴影 */
.card {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: 2rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
}

.card:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--border);
}

.card h2 {
    font-size: 1.75rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
}

.card p {
    color: var(--text-secondary);
    line-height: 1.7;
    margin-bottom: 1.5rem;
    font-size: 1rem;
}

/* Tabs - 高对比度 */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    padding: 0.5rem;
    margin-bottom: 2rem;
}

.stTabs [data-baseweb="tab"] {
    padding: 0.875rem 1.5rem;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-secondary);
    border-radius: var(--radius-sm);
    transition: all 0.2s;
    border: none;
    background: transparent;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-primary);
    background: var(--bg-secondary);
}

.stTabs [aria-selected="true"] {
    background: var(--accent);
    color: #ffffff !important;
    box-shadow: var(--shadow-sm);
}

/* Buttons - 超级明显 */
.stButton > button {
    background: var(--accent);
    color: #ffffff !important;
    border: none;
    border-radius: var(--radius-md);
    padding: 0.875rem 2rem;
    font-size: 1rem;
    font-weight: 600;
    transition: all 0.2s;
    box-shadow: var(--shadow-md);
    cursor: pointer;
}

.stButton > button:hover {
    background: var(--accent-hover);
    box-shadow: var(--shadow-lg);
    transform: translateY(-2px);
}

.stButton > button:active {
    transform: translateY(0);
    box-shadow: var(--shadow-sm);
}

/* 主要按钮 - 更突出 */
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background: var(--accent);
    font-size: 1.0625rem;
    padding: 1rem 2.5rem;
    font-weight: 700;
}

/* Input - 清晰的边框 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    border: 2px solid var(--border);
    border-radius: var(--radius-md);
    padding: 0.875rem 1rem;
    font-size: 1rem;
    transition: all 0.2s;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-weight: 500;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-light);
    outline: none;
}

.stTextArea > div > div > textarea {
    min-height: 200px;
    line-height: 1.7;
}

/* Progress Bar - 超级明显 */
.stProgress > div > div > div {
    background: var(--accent) !important;
    height: 12px !important;
    border-radius: 999px;
    box-shadow: 0 0 10px rgba(255, 107, 53, 0.5);
}

.stProgress > div > div {
    background: var(--bg-tertiary) !important;
    height: 12px !important;
    border-radius: 999px;
    border: 1px solid var(--border);
}

/* Alert - 高对比度 */
.stAlert {
    border-radius: var(--radius-md);
    padding: 1rem 1.25rem;
    border: 2px solid;
    box-shadow: var(--shadow-sm);
    font-weight: 500;
}

.stSuccess {
    background: #f0fdf4;
    border-color: var(--success);
    color: #166534;
}

.stInfo {
    background: #eff6ff;
    border-color: var(--info);
    color: #1e40af;
}

.stWarning {
    background: #fffbeb;
    border-color: var(--warning);
    color: #92400e;
}

.stError {
    background: #fef2f2;
    border-color: var(--error);
    color: #991b1b;
}

/* Expander - 清晰的边框 */
.stExpander {
    background: var(--bg-primary);
    border: 2px solid var(--border-light);
    border-radius: var(--radius-md);
    margin-bottom: 1rem;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s;
}

.stExpander:hover {
    border-color: var(--border);
    box-shadow: var(--shadow-md);
}

.stExpander > div > div {
    padding: 1.5rem;
}

/* Markdown 内容 - 高对比度 */
.stMarkdown {
    line-height: 1.8;
    color: var(--text-primary);
}

.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-weight: 700;
    margin-top: 1.5em;
    margin-bottom: 0.75em;
    color: var(--text-primary);
}

.stMarkdown h1 {
    font-size: 2rem;
}

.stMarkdown h2 {
    font-size: 1.5rem;
}

.stMarkdown h3 {
    font-size: 1.25rem;
}

.stMarkdown p {
    margin-bottom: 1em;
    color: var(--text-secondary);
}

.stMarkdown strong {
    color: var(--text-primary);
    font-weight: 700;
}

.stMarkdown ul, .stMarkdown ol {
    margin: 1em 0;
    padding-left: 1.75em;
}

.stMarkdown li {
    margin-bottom: 0.5em;
    line-height: 1.8;
    color: var(--text-secondary);
}

.stMarkdown code {
    background: var(--bg-tertiary);
    padding: 0.25em 0.5em;
    border-radius: 4px;
    font-size: 0.875em;
    color: var(--accent);
    font-weight: 600;
    border: 1px solid var(--border);
}

.stMarkdown pre {
    background: var(--bg-tertiary);
    padding: 1.25rem;
    border-radius: var(--radius-md);
    overflow-x: auto;
    border: 2px solid var(--border);
}

/* Stats Card - 鲜明的渐变 */
.stat-card {
    background: linear-gradient(135deg, var(--accent) 0%, #ff8c42 100%);
    color: white;
    border-radius: var(--radius-lg);
    padding: 2rem 1.5rem;
    text-align: center;
    box-shadow: var(--shadow-lg);
    transition: all 0.2s;
}

.stat-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-xl);
}

.stat-value {
    font-size: 3rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-label {
    font-size: 1rem;
    opacity: 0.95;
    font-weight: 600;
}

/* Radio Buttons - 清晰的边框 */
.stRadio > div {
    gap: 1rem;
}

.stRadio > div > label {
    background: var(--bg-primary);
    padding: 0.875rem 1.5rem;
    border-radius: var(--radius-md);
    transition: all 0.2s;
    cursor: pointer;
    border: 2px solid var(--border);
    font-weight: 600;
    color: var(--text-primary);
}

.stRadio > div > label:hover {
    border-color: var(--accent);
    background: var(--accent-light);
}

/* Spinner - 明显的加载动画 */
.stSpinner > div {
    border-color: var(--accent) !important;
    border-width: 3px !important;
}

/* Slider - 鲜明的颜色 */
.stSlider > div > div > div {
    background: var(--accent) !important;
}

/* File Uploader - 清晰的边框 */
.stFileUploader {
    border: 3px dashed var(--border);
    border-radius: var(--radius-lg);
    padding: 2rem;
    background: var(--bg-primary);
    transition: all 0.2s;
}

.stFileUploader:hover {
    border-color: var(--accent);
    background: var(--accent-light);
}

/* 页脚 */
.footer {
    text-align: center;
    color: var(--text-tertiary);
    padding: 2.5rem 0;
    font-size: 0.9375rem;
    border-top: 2px solid var(--border-light);
    margin-top: 3rem;
}

.footer a {
    color: var(--accent);
    text-decoration: none;
    margin: 0 1rem;
    transition: all 0.2s;
    font-weight: 600;
}

.footer a:hover {
    color: var(--accent-hover);
    text-decoration: underline;
}

/* 滚动条 */
::-webkit-scrollbar {
    width: 12px;
    height: 12px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: var(--accent);
    border-radius: 10px;
    border: 2px solid var(--bg-secondary);
}

::-webkit-scrollbar-thumb:hover {
    background: var(--accent-hover);
}

/* 顶部导航 */
.top {
    background: var(--bg-primary);
    padding: 1rem 2rem;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid var(--border-light);
}

.brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--accent);
}

.dot {
    width: 12px;
    height: 12px;
    background: var(--accent);
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% {
        transform: scale(1);
        opacity: 1;
    }
    50% {
        transform: scale(1.3);
        opacity: 0.7;
    }
}

/* 确保所有文字都是深色 */
h1, h2, h3, h4, h5, h6, p, span, div, label {
    color: var(--text-primary) !important;
}

/* 按钮文字必须是白色 */
.stButton > button,
.stButton > button * {
    color: #ffffff !important;
}

/* Tab 选中时文字是白色 */
.stTabs [aria-selected="true"],
.stTabs [aria-selected="true"] * {
    color: #ffffff !important;
}
</style>
"""
