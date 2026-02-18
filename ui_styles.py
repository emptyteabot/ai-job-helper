"""
现代化 UI 样式 - Google Material Design 3 + OpenAI + Antigravity
"""

MODERN_UI_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f8f9fa;
    --bg-tertiary: #f1f3f4;
    --text-primary: #1f1f1f;
    --text-secondary: #5f6368;
    --text-tertiary: #80868b;
    --border: #e8eaed;
    --accent: #1a73e8;
    --accent-hover: #1557b0;
    --success: #1e8e3e;
    --warning: #f9ab00;
    --error: #d93025;
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --shadow-sm: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
    --shadow-md: 0 1px 3px 0 rgba(60,64,67,0.3), 0 4px 8px 3px rgba(60,64,67,0.15);
    --shadow-lg: 0 2px 6px 2px rgba(60,64,67,0.15), 0 8px 24px 4px rgba(60,64,67,0.15);
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

/* Hero Section - OpenAI 风格 */
.hero {
    text-align: center;
    padding: 4rem 0 3rem;
    background: linear-gradient(180deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    border-radius: var(--radius-lg);
    margin-bottom: 2rem;
}

.hero h1 {
    font-size: clamp(2.5rem, 5vw, 4rem);
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.1;
    margin-bottom: 1rem;
    background: linear-gradient(135deg, var(--text-primary) 0%, var(--text-secondary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-subtitle {
    font-size: 1.25rem;
    color: var(--text-secondary);
    max-width: 700px;
    margin: 0 auto 2rem;
    line-height: 1.6;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: var(--bg-tertiary);
    border-radius: 999px;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
}

/* Card - Material Design 3 */
.card {
    background: var(--bg-primary);
    border-radius: var(--radius-lg);
    padding: 2rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
    box-shadow: var(--shadow-md);
}

.card h2 {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.card p {
    color: var(--text-secondary);
    line-height: 1.6;
    margin-bottom: 1.5rem;
}

/* Tabs - Google 风格 */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: var(--bg-tertiary);
    border-radius: var(--radius-md);
    padding: 0.25rem;
    margin-bottom: 2rem;
    border: none;
}

.stTabs [data-baseweb="tab"] {
    padding: 0.75rem 1.5rem;
    font-size: 0.9375rem;
    font-weight: 500;
    color: var(--text-secondary);
    border-radius: var(--radius-sm);
    transition: all 0.2s;
    border: none;
    background: transparent;
}

.stTabs [aria-selected="true"] {
    background: var(--bg-primary);
    color: var(--accent);
    box-shadow: var(--shadow-sm);
}

/* Buttons - Material Design 3 */
.stButton > button {
    background: var(--accent);
    color: white;
    border: none;
    border-radius: var(--radius-md);
    padding: 0.75rem 2rem;
    font-size: 0.9375rem;
    font-weight: 500;
    transition: all 0.2s;
    box-shadow: var(--shadow-sm);
}

.stButton > button:hover {
    background: var(--accent-hover);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}

/* Input - Google 风格 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 0.75rem 1rem;
    font-size: 0.9375rem;
    transition: all 0.2s;
    background: var(--bg-primary);
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(26, 115, 232, 0.1);
    outline: none;
}

.stTextArea > div > div > textarea {
    min-height: 200px;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1.6;
}

/* Progress Bar - 可见的进度条 */
.stProgress > div > div > div {
    background: var(--accent) !important;
    height: 6px !important;
    border-radius: 999px;
}

.stProgress > div > div {
    background: var(--bg-tertiary) !important;
    height: 6px !important;
    border-radius: 999px;
}

/* Alert - Material Design */
.stAlert {
    border-radius: var(--radius-md);
    padding: 1rem 1.25rem;
    border: none;
    box-shadow: var(--shadow-sm);
}

.stSuccess {
    background: rgba(30, 142, 62, 0.1);
    color: var(--success);
}

.stInfo {
    background: rgba(26, 115, 232, 0.1);
    color: var(--accent);
}

.stWarning {
    background: rgba(249, 171, 0, 0.1);
    color: var(--warning);
}

.stError {
    background: rgba(217, 48, 37, 0.1);
    color: var(--error);
}

/* Expander - Antigravity 风格 */
.stExpander {
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    margin-bottom: 1rem;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
}

.stExpander > div > div {
    padding: 1.25rem;
}

/* Markdown 内容 */
.stMarkdown {
    line-height: 1.7;
    color: var(--text-primary);
}

.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-weight: 600;
    margin-top: 1.5em;
    margin-bottom: 0.75em;
}

.stMarkdown p {
    margin-bottom: 1em;
}

.stMarkdown ul, .stMarkdown ol {
    margin: 1em 0;
    padding-left: 1.5em;
}

.stMarkdown li {
    margin-bottom: 0.5em;
    line-height: 1.7;
}

.stMarkdown code {
    background: var(--bg-tertiary);
    padding: 0.2em 0.4em;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.875em;
}

.stMarkdown pre {
    background: var(--bg-tertiary);
    padding: 1rem;
    border-radius: var(--radius-md);
    overflow-x: auto;
}

/* Stats Card */
.stat-card {
    background: linear-gradient(135deg, var(--accent) 0%, #1557b0 100%);
    color: white;
    border-radius: var(--radius-md);
    padding: 1.5rem;
    text-align: center;
    box-shadow: var(--shadow-md);
}

.stat-value {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
}

.stat-label {
    font-size: 0.875rem;
    opacity: 0.9;
}

/* Radio Buttons */
.stRadio > div {
    gap: 1rem;
}

.stRadio > div > label {
    background: var(--bg-tertiary);
    padding: 0.5rem 1rem;
    border-radius: var(--radius-md);
    transition: all 0.2s;
    cursor: pointer;
}

.stRadio > div > label:hover {
    background: var(--border);
}

/* Spinner */
.stSpinner > div {
    border-color: var(--accent) !important;
}

/* Slider */
.stSlider > div > div > div {
    background: var(--accent) !important;
}
</style>
"""
