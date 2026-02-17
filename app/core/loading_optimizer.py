"""
加载优化 - 添加美观的加载动画和进度提示
"""

LOADING_ANIMATIONS = """
<!-- 加载动画CSS -->
<style>
/* 全局加载遮罩 */
.global-loader {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    opacity: 1;
    transition: opacity 0.5s ease;
}

.global-loader.hidden {
    opacity: 0;
    pointer-events: none;
}

/* 加载动画 */
.loader-animation {
    width: 80px;
    height: 80px;
    position: relative;
    margin-bottom: 2rem;
}

.loader-circle {
    width: 100%;
    height: 100%;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #10a37f;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* 加载文本 */
.loader-text {
    font-size: 1.2rem;
    color: #333;
    font-weight: 500;
    margin-bottom: 0.5rem;
    animation: pulse 1.5s ease-in-out infinite;
}

.loader-subtext {
    font-size: 0.9rem;
    color: #666;
}

/* 骨架屏 */
.skeleton {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: loading 1.5s ease-in-out infinite;
}

@keyframes loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

.skeleton-text {
    height: 1rem;
    margin: 0.5rem 0;
    border-radius: 4px;
}

.skeleton-title {
    height: 1.5rem;
    width: 60%;
    margin: 1rem 0;
    border-radius: 4px;
}

/* 渐进式加载 */
.fade-in {
    animation: fadeIn 0.6s ease;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* 懒加载图片 */
img.lazy {
    opacity: 0;
    transition: opacity 0.3s;
}

img.lazy.loaded {
    opacity: 1;
}

/* 优化按钮点击反馈 */
.btn {
    position: relative;
    overflow: hidden;
}

.btn::after {
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

.btn:active::after {
    width: 300px;
    height: 300px;
}

/* 加载进度条 */
.progress-bar-top {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #10a37f, #1a7f64);
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.3s ease;
    z-index: 10000;
}

.progress-bar-top.loading {
    animation: progressBar 2s ease-in-out infinite;
}

@keyframes progressBar {
    0% { transform: scaleX(0); }
    50% { transform: scaleX(0.7); }
    100% { transform: scaleX(1); }
}
</style>

<!-- 全局加载器HTML -->
<div class="global-loader" id="globalLoader">
    <div class="loader-animation">
        <div class="loader-circle"></div>
    </div>
    <div class="loader-text">AI求职助手</div>
    <div class="loader-subtext">正在加载...</div>
</div>

<!-- 顶部进度条 -->
<div class="progress-bar-top" id="topProgressBar"></div>

<!-- 加载优化JavaScript -->
<script>
// 页面加载完成后隐藏加载器
window.addEventListener('load', function() {
    setTimeout(() => {
        document.getElementById('globalLoader').classList.add('hidden');
    }, 500);
});

// 显示顶部进度条
function showTopProgress() {
    const bar = document.getElementById('topProgressBar');
    bar.classList.add('loading');
}

// 隐藏顶部进度条
function hideTopProgress() {
    const bar = document.getElementById('topProgressBar');
    bar.classList.remove('loading');
}

// 懒加载图片
document.addEventListener('DOMContentLoaded', function() {
    const lazyImages = document.querySelectorAll('img.lazy');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
});

// 优化AJAX请求
const originalFetch = window.fetch;
window.fetch = function(...args) {
    showTopProgress();
    return originalFetch.apply(this, args)
        .finally(() => {
            setTimeout(hideTopProgress, 300);
        });
};

// 添加渐进式加载
function addFadeInAnimation() {
    const elements = document.querySelectorAll('.fade-in');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    });
    
    elements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        observer.observe(el);
    });
}

// 页面加载后执行
window.addEventListener('load', addFadeInAnimation);
</script>
"""

def inject_loading_animations(html: str) -> str:
    """注入加载动画到HTML"""
    # 在</head>前插入
    if '</head>' in html:
        html = html.replace('</head>', LOADING_ANIMATIONS + '</head>')
    return html

加载优化 - 添加美观的加载动画和进度提示
"""

LOADING_ANIMATIONS = """
<!-- 加载动画CSS -->
<style>
/* 全局加载遮罩 */
.global-loader {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    opacity: 1;
    transition: opacity 0.5s ease;
}

.global-loader.hidden {
    opacity: 0;
    pointer-events: none;
}

/* 加载动画 */
.loader-animation {
    width: 80px;
    height: 80px;
    position: relative;
    margin-bottom: 2rem;
}

.loader-circle {
    width: 100%;
    height: 100%;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #10a37f;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* 加载文本 */
.loader-text {
    font-size: 1.2rem;
    color: #333;
    font-weight: 500;
    margin-bottom: 0.5rem;
    animation: pulse 1.5s ease-in-out infinite;
}

.loader-subtext {
    font-size: 0.9rem;
    color: #666;
}

/* 骨架屏 */
.skeleton {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: loading 1.5s ease-in-out infinite;
}

@keyframes loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

.skeleton-text {
    height: 1rem;
    margin: 0.5rem 0;
    border-radius: 4px;
}

.skeleton-title {
    height: 1.5rem;
    width: 60%;
    margin: 1rem 0;
    border-radius: 4px;
}

/* 渐进式加载 */
.fade-in {
    animation: fadeIn 0.6s ease;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* 懒加载图片 */
img.lazy {
    opacity: 0;
    transition: opacity 0.3s;
}

img.lazy.loaded {
    opacity: 1;
}

/* 优化按钮点击反馈 */
.btn {
    position: relative;
    overflow: hidden;
}

.btn::after {
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

.btn:active::after {
    width: 300px;
    height: 300px;
}

/* 加载进度条 */
.progress-bar-top {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #10a37f, #1a7f64);
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.3s ease;
    z-index: 10000;
}

.progress-bar-top.loading {
    animation: progressBar 2s ease-in-out infinite;
}

@keyframes progressBar {
    0% { transform: scaleX(0); }
    50% { transform: scaleX(0.7); }
    100% { transform: scaleX(1); }
}
</style>

<!-- 全局加载器HTML -->
<div class="global-loader" id="globalLoader">
    <div class="loader-animation">
        <div class="loader-circle"></div>
    </div>
    <div class="loader-text">AI求职助手</div>
    <div class="loader-subtext">正在加载...</div>
</div>

<!-- 顶部进度条 -->
<div class="progress-bar-top" id="topProgressBar"></div>

<!-- 加载优化JavaScript -->
<script>
// 页面加载完成后隐藏加载器
window.addEventListener('load', function() {
    setTimeout(() => {
        document.getElementById('globalLoader').classList.add('hidden');
    }, 500);
});

// 显示顶部进度条
function showTopProgress() {
    const bar = document.getElementById('topProgressBar');
    bar.classList.add('loading');
}

// 隐藏顶部进度条
function hideTopProgress() {
    const bar = document.getElementById('topProgressBar');
    bar.classList.remove('loading');
}

// 懒加载图片
document.addEventListener('DOMContentLoaded', function() {
    const lazyImages = document.querySelectorAll('img.lazy');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
});

// 优化AJAX请求
const originalFetch = window.fetch;
window.fetch = function(...args) {
    showTopProgress();
    return originalFetch.apply(this, args)
        .finally(() => {
            setTimeout(hideTopProgress, 300);
        });
};

// 添加渐进式加载
function addFadeInAnimation() {
    const elements = document.querySelectorAll('.fade-in');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    });
    
    elements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        observer.observe(el);
    });
}

// 页面加载后执行
window.addEventListener('load', addFadeInAnimation);
</script>
"""

def inject_loading_animations(html: str) -> str:
    """注入加载动画到HTML"""
    # 在</head>前插入
    if '</head>' in html:
        html = html.replace('</head>', LOADING_ANIMATIONS + '</head>')
    return html

加载优化 - 添加美观的加载动画和进度提示
"""

LOADING_ANIMATIONS = """
<!-- 加载动画CSS -->
<style>
/* 全局加载遮罩 */
.global-loader {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    opacity: 1;
    transition: opacity 0.5s ease;
}

.global-loader.hidden {
    opacity: 0;
    pointer-events: none;
}

/* 加载动画 */
.loader-animation {
    width: 80px;
    height: 80px;
    position: relative;
    margin-bottom: 2rem;
}

.loader-circle {
    width: 100%;
    height: 100%;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #10a37f;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* 加载文本 */
.loader-text {
    font-size: 1.2rem;
    color: #333;
    font-weight: 500;
    margin-bottom: 0.5rem;
    animation: pulse 1.5s ease-in-out infinite;
}

.loader-subtext {
    font-size: 0.9rem;
    color: #666;
}

/* 骨架屏 */
.skeleton {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: loading 1.5s ease-in-out infinite;
}

@keyframes loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

.skeleton-text {
    height: 1rem;
    margin: 0.5rem 0;
    border-radius: 4px;
}

.skeleton-title {
    height: 1.5rem;
    width: 60%;
    margin: 1rem 0;
    border-radius: 4px;
}

/* 渐进式加载 */
.fade-in {
    animation: fadeIn 0.6s ease;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* 懒加载图片 */
img.lazy {
    opacity: 0;
    transition: opacity 0.3s;
}

img.lazy.loaded {
    opacity: 1;
}

/* 优化按钮点击反馈 */
.btn {
    position: relative;
    overflow: hidden;
}

.btn::after {
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

.btn:active::after {
    width: 300px;
    height: 300px;
}

/* 加载进度条 */
.progress-bar-top {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #10a37f, #1a7f64);
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.3s ease;
    z-index: 10000;
}

.progress-bar-top.loading {
    animation: progressBar 2s ease-in-out infinite;
}

@keyframes progressBar {
    0% { transform: scaleX(0); }
    50% { transform: scaleX(0.7); }
    100% { transform: scaleX(1); }
}
</style>

<!-- 全局加载器HTML -->
<div class="global-loader" id="globalLoader">
    <div class="loader-animation">
        <div class="loader-circle"></div>
    </div>
    <div class="loader-text">AI求职助手</div>
    <div class="loader-subtext">正在加载...</div>
</div>

<!-- 顶部进度条 -->
<div class="progress-bar-top" id="topProgressBar"></div>

<!-- 加载优化JavaScript -->
<script>
// 页面加载完成后隐藏加载器
window.addEventListener('load', function() {
    setTimeout(() => {
        document.getElementById('globalLoader').classList.add('hidden');
    }, 500);
});

// 显示顶部进度条
function showTopProgress() {
    const bar = document.getElementById('topProgressBar');
    bar.classList.add('loading');
}

// 隐藏顶部进度条
function hideTopProgress() {
    const bar = document.getElementById('topProgressBar');
    bar.classList.remove('loading');
}

// 懒加载图片
document.addEventListener('DOMContentLoaded', function() {
    const lazyImages = document.querySelectorAll('img.lazy');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
});

// 优化AJAX请求
const originalFetch = window.fetch;
window.fetch = function(...args) {
    showTopProgress();
    return originalFetch.apply(this, args)
        .finally(() => {
            setTimeout(hideTopProgress, 300);
        });
};

// 添加渐进式加载
function addFadeInAnimation() {
    const elements = document.querySelectorAll('.fade-in');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    });
    
    elements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        observer.observe(el);
    });
}

// 页面加载后执行
window.addEventListener('load', addFadeInAnimation);
</script>
"""

def inject_loading_animations(html: str) -> str:
    """注入加载动画到HTML"""
    # 在</head>前插入
    if '</head>' in html:
        html = html.replace('</head>', LOADING_ANIMATIONS + '</head>')
    return html

加载优化 - 添加美观的加载动画和进度提示
"""

LOADING_ANIMATIONS = """
<!-- 加载动画CSS -->
<style>
/* 全局加载遮罩 */
.global-loader {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    opacity: 1;
    transition: opacity 0.5s ease;
}

.global-loader.hidden {
    opacity: 0;
    pointer-events: none;
}

/* 加载动画 */
.loader-animation {
    width: 80px;
    height: 80px;
    position: relative;
    margin-bottom: 2rem;
}

.loader-circle {
    width: 100%;
    height: 100%;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #10a37f;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* 加载文本 */
.loader-text {
    font-size: 1.2rem;
    color: #333;
    font-weight: 500;
    margin-bottom: 0.5rem;
    animation: pulse 1.5s ease-in-out infinite;
}

.loader-subtext {
    font-size: 0.9rem;
    color: #666;
}

/* 骨架屏 */
.skeleton {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: loading 1.5s ease-in-out infinite;
}

@keyframes loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

.skeleton-text {
    height: 1rem;
    margin: 0.5rem 0;
    border-radius: 4px;
}

.skeleton-title {
    height: 1.5rem;
    width: 60%;
    margin: 1rem 0;
    border-radius: 4px;
}

/* 渐进式加载 */
.fade-in {
    animation: fadeIn 0.6s ease;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* 懒加载图片 */
img.lazy {
    opacity: 0;
    transition: opacity 0.3s;
}

img.lazy.loaded {
    opacity: 1;
}

/* 优化按钮点击反馈 */
.btn {
    position: relative;
    overflow: hidden;
}

.btn::after {
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

.btn:active::after {
    width: 300px;
    height: 300px;
}

/* 加载进度条 */
.progress-bar-top {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #10a37f, #1a7f64);
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.3s ease;
    z-index: 10000;
}

.progress-bar-top.loading {
    animation: progressBar 2s ease-in-out infinite;
}

@keyframes progressBar {
    0% { transform: scaleX(0); }
    50% { transform: scaleX(0.7); }
    100% { transform: scaleX(1); }
}
</style>

<!-- 全局加载器HTML -->
<div class="global-loader" id="globalLoader">
    <div class="loader-animation">
        <div class="loader-circle"></div>
    </div>
    <div class="loader-text">AI求职助手</div>
    <div class="loader-subtext">正在加载...</div>
</div>

<!-- 顶部进度条 -->
<div class="progress-bar-top" id="topProgressBar"></div>

<!-- 加载优化JavaScript -->
<script>
// 页面加载完成后隐藏加载器
window.addEventListener('load', function() {
    setTimeout(() => {
        document.getElementById('globalLoader').classList.add('hidden');
    }, 500);
});

// 显示顶部进度条
function showTopProgress() {
    const bar = document.getElementById('topProgressBar');
    bar.classList.add('loading');
}

// 隐藏顶部进度条
function hideTopProgress() {
    const bar = document.getElementById('topProgressBar');
    bar.classList.remove('loading');
}

// 懒加载图片
document.addEventListener('DOMContentLoaded', function() {
    const lazyImages = document.querySelectorAll('img.lazy');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
});

// 优化AJAX请求
const originalFetch = window.fetch;
window.fetch = function(...args) {
    showTopProgress();
    return originalFetch.apply(this, args)
        .finally(() => {
            setTimeout(hideTopProgress, 300);
        });
};

// 添加渐进式加载
function addFadeInAnimation() {
    const elements = document.querySelectorAll('.fade-in');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    });
    
    elements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        observer.observe(el);
    });
}

// 页面加载后执行
window.addEventListener('load', addFadeInAnimation);
</script>
"""

def inject_loading_animations(html: str) -> str:
    """注入加载动画到HTML"""
    # 在</head>前插入
    if '</head>' in html:
        html = html.replace('</head>', LOADING_ANIMATIONS + '</head>')
    return html



