"""
超越 Gemini 的 UI 设计
- Gemini 标志性蓝紫渐变
- 流畅的动画效果
- 玻璃态设计
- 现代化卡片
"""

GEMINI_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto:wght@400;500;700&display=swap');

:root {
    /* Gemini 标志性渐变色 */
    --gemini-gradient: linear-gradient(135deg, #4285f4 0%, #8b5cf6 50%, #ec4899 100%);
    --gemini-blue-purple: linear-gradient(90deg, #4285f4, #8b5cf6);
    --gemini-purple-pink: linear-gradient(135deg, #8b5cf6, #ec4899);
    --gemini-animated: linear-gradient(270deg, #4285f4, #8b5cf6, #ec4899, #4285f4);

    /* 主色调 */
    --primary-blue: #4285f4;
    --primary-purple: #8b5cf6;
    --primary-pink: #ec4899;

    /* 背景色 */
    --bg-primary: #ffffff;
    --bg-secondary: #f8f9fa;
    --bg-tertiary: #f1f3f4;

    /* 文字颜色 - 深色 */
    --text-primary: #202124;
    --text-secondary: #5f6368;
    --text-tertiary: #80868b;

    /* 边框 */
    --border: rgba(0, 0, 0, 0.08);
    --border-light: rgba(0, 0, 0, 0.04);

    /* 圆角 */
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 24px;

    /* 阴影 */
    --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1), 0 2px 6px rgba(0, 0, 0, 0.08);
    --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12), 0 4px 12px rgba(0, 0, 0, 0.1);
    --shadow-gradient: 0 8px 32px rgba(66, 133, 244, 0.2), 0 4px 16px rgba(139, 92, 246, 0.15);
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Google Sans', 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-secondary);
    color: var(--text-primary);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    font-size: 16px;
    line-height: 1.5;
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

/* Hero Section - Gemini 风格 */
.hero {
    text-align: center;
    padding: 5rem 2rem;
    background: var(--gemini-animated);
    background-size: 400% 400%;
    animation: gradient-shift 8s ease infinite;
    border-radius: var(--radius-xl);
    margin-bottom: 2rem;
    box-shadow: var(--shadow-gradient);
    position: relative;
    overflow: hidden;
}

.hero::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at 30% 50%, rgba(255,255,255,0.1) 0%, transparent 50%);
    animation: float 6s ease-in-out infinite;
}

@keyframes gradient-shift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes float {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(20px, -20px); }
}

.hero h1 {
    font-size: clamp(2.5rem, 5vw, 4.5rem);
    font-weight: 500;
    letter-spacing: -0.02em;
    line-height: 1.1;
    margin-bottom: 1rem;
    color: #ffffff;
    text-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    position: relative;
    z-index: 1;
}

.hero-subtitle {
    font-size: 1.25rem;
    color: rgba(255, 255, 255, 0.95);
    max-width: 700px;
    margin: 0 auto 2rem;
    line-height: 1.6;
    font-weight: 400;
    position: relative;
    z-index: 1;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 999px;
    font-size: 0.875rem;
    font-weight: 500;
    color: #ffffff;
    margin-bottom: 1.5rem;
    position: relative;
    z-index: 1;
}

/* Card - 玻璃态设计 */
.card {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: 2rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-sm);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
    border-color: var(--border);
}

.card h2 {
    font-size: 1.75rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
}

.card p {
    color: var(--text-secondary);
    line-height: 1.7;
    margin-bottom: 1.5rem;
    font-size: 1rem;
}

/* Tabs - Gemini 风格 */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: 0.5rem;
    margin-bottom: 2rem;
    box-shadow: var(--shadow-sm);
}

.stTabs [data-baseweb="tab"] {
    padding: 0.875rem 1.5rem;
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-secondary);
    border-radius: var(--radius-md);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    border: none;
    background: transparent;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-primary);
    background: var(--bg-secondary);
}

.stTabs [aria-selected="true"] {
    background: var(--gemini-blue-purple);
    color: #ffffff !important;
    box-shadow: var(--shadow-sm);
}

/* Buttons - Gemini 风格 */
.stButton > button {
    background: var(--gemini-blue-purple);
    color: #ffffff !important;
    border: none;
    border-radius: var(--radius-xl);
    padding: 0.875rem 2rem;
    font-size: 1rem;
    font-weight: 500;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 8px rgba(66, 133, 244, 0.3);
    cursor: pointer;
}

.stButton > button:hover {
    box-shadow: 0 4px 12px rgba(66, 133, 244, 0.4);
    transform: translateY(-1px);
}

.stButton > button:active {
    transform: translateY(0);
}

/* Input - 现代化设计 */
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
    font-weight: 400;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--primary-blue);
    box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.1);
    outline: none;
}

/* Progress Bar - 渐变动画 */
.stProgress > div > div > div {
    background: var(--gemini-blue-purple) !important;
    height: 8px !important;
    border-radius: 999px;
    box-shadow: 0 0 12px rgba(66, 133, 244, 0.5);
    animation: pulse-glow 2s ease-in-out infinite;
}

.stProgress > div > div {
    background: var(--bg-tertiary) !important;
    height: 8px !important;
    border-radius: 999px;
    border: 1px solid var(--border);
}

@keyframes pulse-glow {
    0%, 100% {
        box-shadow: 0 0 12px rgba(66, 133, 244, 0.5);
    }
    50% {
        box-shadow: 0 0 20px rgba(66, 133, 244, 0.8);
    }
}

/* Alert - 现代化 */
.stAlert {
    border-radius: var(--radius-md);
    padding: 1rem 1.25rem;
    border: 1px solid;
    box-shadow: var(--shadow-sm);
    font-weight: 400;
}

.stSuccess {
    background: #f0fdf4;
    border-color: #34a853;
    color: #166534;
}

.stInfo {
    background: #eff6ff;
    border-color: var(--primary-blue);
    color: #1e40af;
}

.stWarning {
    background: #fffbeb;
    border-color: #fbbc04;
    color: #92400e;
}

.stError {
    background: #fef2f2;
    border-color: #ea4335;
    color: #991b1b;
}

/* Expander - 玻璃态 */
.stExpander {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    margin-bottom: 1rem;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s;
}

.stExpander:hover {
    box-shadow: var(--shadow-md);
}

/* Markdown - 清晰易读 */
.stMarkdown {
    line-height: 1.7;
    color: var(--text-primary);
}

.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-weight: 500;
    margin-top: 1.5em;
    margin-bottom: 0.75em;
    color: var(--text-primary);
}

.stMarkdown p {
    margin-bottom: 1em;
    color: var(--text-secondary);
}

.stMarkdown strong {
    color: var(--text-primary);
    font-weight: 600;
}

.stMarkdown code {
    background: var(--bg-tertiary);
    padding: 0.25em 0.5em;
    border-radius: 4px;
    font-size: 0.875em;
    color: var(--primary-blue);
    font-weight: 500;
}

/* Stats Card - 渐变卡片 */
.stat-card {
    background: var(--gemini-gradient);
    color: white;
    border-radius: var(--radius-lg);
    padding: 2rem 1.5rem;
    text-align: center;
    box-shadow: var(--shadow-gradient);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(66, 133, 244, 0.25);
}

.stat-value {
    font-size: 3rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
}

.stat-label {
    font-size: 1rem;
    opacity: 0.95;
    font-weight: 400;
}

/* Radio Buttons - 现代化 */
.stRadio > div > label {
    background: var(--bg-primary);
    padding: 0.875rem 1.5rem;
    border-radius: var(--radius-md);
    transition: all 0.2s;
    cursor: pointer;
    border: 2px solid var(--border);
    font-weight: 500;
}

.stRadio > div > label:hover {
    border-color: var(--primary-blue);
    background: rgba(66, 133, 244, 0.05);
}

/* Spinner - 渐变动画 */
.stSpinner > div {
    border-color: var(--primary-blue) !important;
    border-width: 3px !important;
}

/* 顶部导航 */
.top {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(20px);
    padding: 1rem 2rem;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    margin-bottom: 2rem;
    border: 1px solid var(--border-light);
}

.brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 1.5rem;
    font-weight: 500;
    background: var(--gemini-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.dot {
    width: 12px;
    height: 12px;
    background: var(--gemini-gradient);
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% {
        transform: scale(1);
        opacity: 1;
    }
    50% {
        transform: scale(1.2);
        opacity: 0.8;
    }
}

/* 微交互动画 */

/* 按钮点击波纹效果 */
.stButton > button {
    position: relative;
    overflow: hidden;
}

.stButton > button::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.5);
    transform: translate(-50%, -50%);
    transition: width 0.6s, height 0.6s;
}

.stButton > button:active::after {
    width: 300px;
    height: 300px;
}

/* 输入框聚焦动画 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    position: relative;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    transform: translateY(-2px);
}

/* 卡片悬停动画 */
.card {
    position: relative;
}

.card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(66, 133, 244, 0.1), rgba(139, 92, 246, 0.1));
    opacity: 0;
    transition: opacity 0.3s;
    border-radius: var(--radius-lg);
    pointer-events: none;
}

.card:hover::before {
    opacity: 1;
}

/* Tab 切换动画 */
.stTabs [data-baseweb="tab"] {
    position: relative;
}

.stTabs [data-baseweb="tab"]::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    width: 0;
    height: 2px;
    background: var(--gemini-blue-purple);
    transform: translateX(-50%);
    transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.stTabs [aria-selected="true"]::after {
    width: 80%;
}

/* 加载骨架屏动画 */
@keyframes skeleton-loading {
    0% {
        background-position: -200px 0;
    }
    100% {
        background-position: calc(200px + 100%) 0;
    }
}

.skeleton {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200px 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
}

/* 淡入淡出动画 */
@keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes fade-out {
    from { opacity: 1; }
    to { opacity: 0; }
}

.fade-in {
    animation: fade-in 0.3s ease-in;
}

.fade-out {
    animation: fade-out 0.3s ease-out;
}

/* 滑入动画 */
@keyframes slide-in-left {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes slide-in-right {
    from {
        opacity: 0;
        transform: translateX(20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.slide-in-left {
    animation: slide-in-left 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-in-right {
    animation: slide-in-right 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 缩放动画 */
@keyframes scale-in {
    from {
        opacity: 0;
        transform: scale(0.9);
    }
    to {
        opacity: 1;
        transform: scale(1);
    }
}

.scale-in {
    animation: scale-in 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 弹跳动画 */
@keyframes bounce {
    0%, 100% {
        transform: translateY(0);
    }
    50% {
        transform: translateY(-10px);
    }
}

.bounce {
    animation: bounce 1s ease-in-out infinite;
}

/* 旋转加载动画 */
@keyframes spin {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}

.spin {
    animation: spin 1s linear infinite;
}

/* 心跳动画 */
@keyframes heartbeat {
    0%, 100% {
        transform: scale(1);
    }
    25% {
        transform: scale(1.1);
    }
    50% {
        transform: scale(1);
    }
    75% {
        transform: scale(1.05);
    }
}

.heartbeat {
    animation: heartbeat 1.5s ease-in-out infinite;
}

/* 摇晃动画 */
@keyframes shake {
    0%, 100% {
        transform: translateX(0);
    }
    25% {
        transform: translateX(-5px);
    }
    75% {
        transform: translateX(5px);
    }
}

.shake {
    animation: shake 0.5s ease-in-out;
}

/* 闪烁动画 */
@keyframes blink {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.3;
    }
}

.blink {
    animation: blink 1.5s ease-in-out infinite;
}

/* 页面加载动画 */
.page-enter {
    animation: fade-in-up 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Expander 展开动画 */
.stExpander {
    animation: scale-in 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Alert 出现动画 */
.stAlert {
    animation: slide-in-left 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 统计卡片数字滚动动画 */
@keyframes count-up {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.stat-value {
    animation: count-up 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 页脚 */
.footer {
    text-align: center;
    color: var(--text-tertiary);
    padding: 2.5rem 0;
    font-size: 0.9375rem;
    border-top: 1px solid var(--border-light);
    margin-top: 3rem;
}

.footer a {
    color: var(--primary-blue);
    text-decoration: none;
    margin: 0 1rem;
    transition: all 0.2s;
    font-weight: 500;
}

.footer a:hover {
    color: var(--primary-purple);
}

/* 滚动条 - Gemini 风格 */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--gemini-blue-purple);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--primary-purple);
}

/* 淡入动画 */
@keyframes fade-in-up {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in-up {
    animation: fade-in-up 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 确保文字颜色正确 */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
}

p, span, div, label {
    color: var(--text-secondary);
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

/* Hero 文字是白色 */
.hero h1,
.hero p,
.hero span {
    color: #ffffff !important;
}

/* 响应式设计 */

/* 移动端优化 */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem 1rem 3rem;
    }

    .hero {
        padding: 3rem 1.5rem;
    }

    .hero h1 {
        font-size: 2rem;
    }

    .hero-subtitle {
        font-size: 1rem;
    }

    .card {
        padding: 1.5rem;
    }

    .card h2 {
        font-size: 1.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1rem;
        font-size: 0.875rem;
    }

    .stButton > button {
        padding: 0.75rem 1.5rem;
        font-size: 0.9375rem;
    }

    .stat-value {
        font-size: 2rem;
    }

    .hero-badge {
        font-size: 0.75rem;
        padding: 0.375rem 0.75rem;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        font-size: 16px;
    }
}

/* 平板优化 */
@media (min-width: 769px) and (max-width: 1024px) {
    .main .block-container {
        padding: 1.5rem 1.5rem 3.5rem;
    }

    .hero h1 {
        font-size: 3rem;
    }
}

/* 大屏优化 */
@media (min-width: 1440px) {
    .main .block-container {
        max-width: 1400px;
    }

    .hero h1 {
        font-size: 5rem;
    }

    .hero-subtitle {
        font-size: 1.5rem;
    }
}

/* 触摸设备优化 */
@media (hover: none) and (pointer: coarse) {
    .stButton > button {
        min-height: 48px;
        padding: 1rem 2rem;
    }

    .stTabs [data-baseweb="tab"] {
        min-height: 48px;
    }

    .card:hover {
        transform: none;
    }

    .stButton > button:hover {
        transform: none;
    }
}

/* 暗黑模式 */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-primary: #1a1a1a;
        --bg-secondary: #0f0f0f;
        --bg-tertiary: #2a2a2a;
        --text-primary: #e8e8e8;
        --text-secondary: #b8b8b8;
        --text-tertiary: #888888;
        --border: rgba(255, 255, 255, 0.1);
        --border-light: rgba(255, 255, 255, 0.05);
    }

    body {
        background: var(--bg-secondary);
    }

    .card {
        background: rgba(26, 26, 26, 0.9);
        border-color: var(--border);
    }

    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-primary);
        border-color: var(--border);
    }

    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary);
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: var(--bg-tertiary);
    }

    .top {
        background: rgba(26, 26, 26, 0.9);
        border-color: var(--border);
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
    }

    p, span, div, label {
        color: var(--text-secondary) !important;
    }

    .stMarkdown code {
        background: var(--bg-tertiary);
        border-color: var(--border);
    }
}

</style>
"""
