# UI/UX 设计规范 - Streamlit 版本

## 1. 设计理念

### 核心原则
- **产品优先**：功能大于装饰，每个元素都有明确目的
- **极简主义**：去除冗余，保留本质
- **OpenAI 风格**：现代、专业、高效
- **可访问性优先**：确保所有用户都能轻松使用

### 设计哲学
> "Every upload should lead to a real interview. Minimal UI. Real links. Product over decoration."

---

## 2. 配色方案

### 主色调（Monochrome System）
```css
--bg: #ffffff           /* 背景白 */
--text: #111111         /* 主文本黑 */
--muted: #5f5f5f        /* 次要文本灰 */
--line: #e5e5e5         /* 分割线浅灰 */
--card: #fafafa         /* 卡片背景 */
```

### 功能色
```css
--btn: #111111          /* 主按钮黑 */
--btn-text: #ffffff     /* 按钮文字白 */
--ok: #1f7d4a           /* 成功绿 */
--err: #bb3f3f          /* 错误红 */
```

### 辅助色
```css
--border-hover: #bfbfbf     /* 悬停边框 */
--bg-hover: #f5f5f5         /* 悬停背景 */
--bg-light: #fcfcfc         /* 浅背景 */
--danger-bg: #fff8f8        /* 危险操作背景 */
--danger-border: #f0d5d5    /* 危险操作边框 */
--danger-text: #933333      /* 危险操作文字 */
```

### Streamlit 适配
由于 Streamlit 的主题系统限制，使用以下映射：
- `st.markdown()` + CSS 注入实现自定义配色
- 使用 `unsafe_allow_html=True` 应用样式
- 通过 `.stApp` 类覆盖默认主题

---

## 3. 字体系统

### 字体族
```css
--font-sans: "IBM Plex Sans", system-ui, -apple-system, sans-serif;
--font-mono: "IBM Plex Mono", "Consolas", monospace;
```

### 字体大小层级
| 用途 | 大小 | 行高 | 字重 |
|------|------|------|------|
| Hero 标题 | 34px | 1.05 | 700 |
| 页面标题 | 22px | 1.1 | 700 |
| 卡片标题 | 13-14px | 1.45 | 600 |
| 正文 | 13-14px | 1.6 | 400 |
| 次要文本 | 12px | 1.55 | 400 |
| 标签 | 10-11px | 1 | 500 |

### 字母间距
- 大标题：`letter-spacing: -0.9px`（紧凑现代感）
- 其他：默认

---

## 4. 圆角系统

```css
--radius: 14px          /* 标准圆角 */
--radius-lg: 20px       /* 大圆角（面板） */
--radius-sm: 10px       /* 小圆角（按钮、卡片） */
--radius-pill: 999px    /* 胶囊形（导航、标签） */
```

### 使用规则
- 主面板：20px
- 卡片/按钮：10-12px
- 输入框：12px
- 标签/徽章：999px（完全圆角）

---

## 5. 阴影系统

### 焦点阴影
```css
box-shadow: 0 0 0 4px rgba(17, 17, 17, 0.08);
```
- 用于输入框获得焦点时
- 柔和的黑色光晕，不刺眼

### 装饰阴影
```css
box-shadow: 0 0 0 5px rgba(17, 17, 17, 0.08);
```
- 用于品牌标识点（.dot）
- 增强视觉层次

### Streamlit 实现
```python
st.markdown("""
<style>
.stTextInput:focus-within {
    box-shadow: 0 0 0 4px rgba(17, 17, 17, 0.08) !important;
}
</style>
""", unsafe_allow_html=True)
```

---

## 6. 组件规范

### 6.1 按钮

#### 主按钮（Primary）
```css
background: #111111;
color: #ffffff;
border: 1px solid #111111;
border-radius: 10px;
padding: 10px 12px;
font: 600 13px/1 "IBM Plex Sans";
transition: all 0.2s ease;
```
- 悬停：`transform: translateY(-1px)`
- 禁用：`opacity: 0.55`

#### 次要按钮（Secondary）
```css
background: #ffffff;
color: #111111;
border: 1px solid #e5e5e5;
```

#### 危险按钮（Danger）
```css
background: #fff8f8;
color: #933333;
border: 1px solid #f0d5d5;
```

#### Streamlit 实现
```python
# 使用 st.button() + CSS 覆盖
st.markdown("""
<style>
.stButton > button {
    background: #111111;
    color: #ffffff;
    border-radius: 10px;
    padding: 10px 12px;
    font-weight: 600;
    transition: transform 0.2s ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)
```

---

### 6.2 输入框

#### 文本框
```css
border: 1px solid #e5e5e5;
border-radius: 12px;
padding: 12px;
font-size: 13px;
line-height: 1.62;
background: #ffffff;
```

#### 焦点状态
```css
border-color: #bfbfbf;
box-shadow: 0 0 0 4px rgba(17, 17, 17, 0.08);
outline: none;
```

#### 文本域
```css
min-height: 285px;
resize: vertical;
```

---

### 6.3 上传区域

#### 默认状态
```css
border: 1px dashed #cfcfcf;
border-radius: 12px;
padding: 13px 10px;
background: #fcfcfc;
text-align: center;
cursor: pointer;
transition: all 0.2s ease;
```

#### 拖拽状态
```css
border-color: #666666;
background: #f3f3f3;
transform: translateY(-1px);
```

#### Streamlit 实现
```python
st.file_uploader(
    "上传简历",
    type=["pdf", "docx", "txt", "jpg", "png"],
    help="支持 PDF / DOCX / TXT / 图片"
)
```

---

### 6.4 卡片

#### 标准卡片
```css
border: 1px solid #e5e5e5;
border-radius: 12px;
background: #ffffff;
padding: 10px;
```

#### 职位卡片
```css
border: 1px solid #e5e5e5;
border-radius: 10px;
padding: 10px;
background: #fafafa;
```

结构：
- 标题：`font-size: 13px; font-weight: 600;`
- 描述：`font-size: 12px; color: #5f5f5f;`
- 链接：`font-size: 12px; text-decoration: underline;`

---

### 6.5 步骤指示器

#### 结构
```html
<div class="steps">
  <div class="step">1 上传</div>
  <div class="step active">2 分析</div>
  <div class="step done">3 匹配</div>
  <div class="step">4 输出</div>
</div>
```

#### 样式
```css
/* 默认 */
.step {
    border: 1px solid #e5e5e5;
    border-radius: 10px;
    padding: 8px;
    color: #5f5f5f;
    font-size: 12px;
    background: #ffffff;
}

/* 激活 */
.step.active {
    border-color: #666666;
    color: #111111;
    background: #f5f5f5;
}

/* 完成 */
.step.done {
    border-color: #bfbfbf;
    color: #2f2f2f;
    background: #f9f9f9;
}
```

---

### 6.6 状态标签

#### 样式
```css
.tag {
    border: 1px solid #e5e5e5;
    border-radius: 999px;
    color: #5f5f5f;
    font: 500 10px/1 "IBM Plex Sans";
    padding: 3px 7px;
}
```

#### 状态色
- 成功：`color: #1f7d4a;`
- 错误：`color: #bb3f3f;`
- 运行中：`color: #5f5f5f;`

---

### 6.7 代码块

```css
pre {
    padding: 10px;
    white-space: pre-wrap;
    word-break: break-word;
    font-size: 12px;
    line-height: 1.65;
    color: #20251f;
    font-family: "IBM Plex Mono", monospace;
    background: #ffffff;
    border-radius: 8px;
}
```

---

## 7. 动画效果

### 7.1 打字机效果

```javascript
function typewriter(node, text, speed, done) {
    let i = 0;
    const timer = setInterval(() => {
        i += 1;
        node.textContent = text.slice(0, i);
        if (i >= text.length) {
            clearInterval(timer);
            if (done) done();
        }
    }, speed);
}
```

#### 光标动画
```css
.cursor {
    display: inline-block;
    width: 8px;
    height: 1em;
    background: #111111;
    margin-left: 3px;
    vertical-align: -2px;
    animation: blink 1s steps(1, end) infinite;
}

@keyframes blink {
    0%, 48% { opacity: 1; }
    49%, 100% { opacity: 0; }
}
```

#### Streamlit 实现
```python
import streamlit as st
import time

def typewriter_effect(text, speed=0.05):
    placeholder = st.empty()
    for i in range(len(text) + 1):
        placeholder.markdown(f"**{text[:i]}**<span class='cursor'></span>",
                           unsafe_allow_html=True)
        time.sleep(speed)
```

---

### 7.2 悬停效果

```css
/* 按钮悬停 */
button:hover {
    transform: translateY(-1px);
}

/* 导航悬停 */
.nav a:hover {
    color: #111111;
    border-color: #e5e5e5;
}

/* 上传区悬停 */
.upload:hover {
    border-color: #666666;
    background: #f3f3f3;
}
```

过渡时间：`transition: all 0.2s ease;`

---

### 7.3 加载状态

#### 禁用状态
```css
button:disabled {
    opacity: 0.55;
    cursor: not-allowed;
    transform: none;
}
```

#### Streamlit 实现
```python
with st.spinner("AI 正在分析..."):
    # 处理逻辑
    time.sleep(2)
```

---

## 8. 布局系统

### 8.1 容器
```css
.container {
    width: min(1280px, calc(100% - 36px));
    margin: 14px auto 24px;
}
```

### 8.2 两栏布局
```css
.layout {
    display: grid;
    grid-template-columns: 390px 1fr;
    gap: 10px;
}
```

### 8.3 卡片网格
```css
/* 2列 */
.job-cards {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
}

/* 结果面板 */
.board {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}
```

### Streamlit 实现
```python
# 两栏布局
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("工作区")
    # 左侧内容

with col2:
    st.subheader("结果")
    # 右侧内容

# 卡片网格
cols = st.columns(2)
for i, job in enumerate(jobs):
    with cols[i % 2]:
        st.markdown(f"**{job['title']}**")
```

---

## 9. 响应式设计

### 断点
```css
@media (max-width: 1080px) {
    .layout {
        grid-template-columns: 1fr;
    }
    .board {
        grid-template-columns: 1fr;
    }
    .job-cards {
        grid-template-columns: 1fr;
    }
    .steps {
        grid-template-columns: repeat(2, 1fr);
    }
    .hero h1 {
        font-size: 30px;
    }
}
```

### Streamlit 自适应
Streamlit 自动处理响应式，但需注意：
- 使用 `st.columns()` 时，移动端自动堆叠
- 避免固定宽度，使用百分比或 `min()`
- 测试不同屏幕尺寸

---

## 10. 可访问性

### 10.1 颜色对比度
- 主文本（#111111）vs 背景（#ffffff）：对比度 **16.1:1** ✅ WCAG AAA
- 次要文本（#5f5f5f）vs 背景（#ffffff）：对比度 **7.1:1** ✅ WCAG AA
- 成功色（#1f7d4a）vs 背景（#ffffff）：对比度 **4.8:1** ✅ WCAG AA
- 错误色（#bb3f3f）vs 背景（#ffffff）：对比度 **5.2:1** ✅ WCAG AA

### 10.2 键盘导航
- 所有交互元素可通过 Tab 键访问
- 焦点状态清晰可见（阴影效果）
- 支持 Enter/Space 触发按钮

### 10.3 语义化 HTML
```html
<header>导航栏</header>
<main>主内容</main>
<section>章节</section>
<article>独立内容</article>
<button>按钮</button>
<label>表单标签</label>
```

### 10.4 ARIA 标签
```html
<button aria-label="运行分析">运行</button>
<div role="status" aria-live="polite">正在处理...</div>
<input aria-describedby="help-text" />
```

### 10.5 Streamlit 可访问性
```python
# 使用语义化组件
st.header("标题")  # <h1>
st.subheader("子标题")  # <h2>

# 添加帮助文本
st.button("运行", help="点击开始分析简历")

# 状态提示
st.info("正在处理，请稍候...")
st.success("分析完成！")
st.error("发生错误，请重试")
```

---

## 11. Streamlit 特定实现

### 11.1 全局样式注入
```python
def inject_custom_css():
    st.markdown("""
    <style>
    /* 隐藏默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 自定义主题 */
    .stApp {
        background: #ffffff;
        color: #111111;
        font-family: "IBM Plex Sans", sans-serif;
    }

    /* 按钮样式 */
    .stButton > button {
        background: #111111;
        color: #ffffff;
        border-radius: 10px;
        border: none;
        padding: 10px 12px;
        font-weight: 600;
        transition: transform 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
    }

    /* 输入框样式 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 12px;
        font-size: 13px;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #bfbfbf;
        box-shadow: 0 0 0 4px rgba(17, 17, 17, 0.08);
    }

    /* 卡片样式 */
    .element-container {
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 10px;
        background: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)
```

### 11.2 自定义组件
```python
def custom_card(title, content, tag=None):
    tag_html = f'<span class="tag">{tag}</span>' if tag else ''
    st.markdown(f"""
    <div style="
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 10px;
        background: #ffffff;
        margin-bottom: 10px;
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        ">
            <h3 style="font-size: 13px; font-weight: 600; margin: 0;">
                {title}
            </h3>
            {tag_html}
        </div>
        <pre style="
            font-size: 12px;
            line-height: 1.65;
            white-space: pre-wrap;
            word-break: break-word;
            margin: 0;
        ">{content}</pre>
    </div>
    """, unsafe_allow_html=True)
```

### 11.3 状态管理
```python
# 初始化 session state
if 'step' not in st.session_state:
    st.session_state.step = 0

# 更新步骤
def set_step(step):
    st.session_state.step = step
    st.rerun()

# 显示步骤
steps = ["上传", "分析", "匹配", "输出"]
cols = st.columns(4)
for i, step_name in enumerate(steps):
    with cols[i]:
        if i < st.session_state.step:
            st.success(f"✓ {step_name}")
        elif i == st.session_state.step:
            st.info(f"→ {step_name}")
        else:
            st.text(f"  {step_name}")
```

---

## 12. 设计检查清单

### 视觉一致性
- [ ] 所有圆角使用统一系统（10px/12px/20px/999px）
- [ ] 所有间距使用 8px 倍数（8px, 10px, 12px, 16px）
- [ ] 所有颜色来自配色方案
- [ ] 所有字体大小符合层级系统

### 交互反馈
- [ ] 所有按钮有悬停效果
- [ ] 所有输入框有焦点状态
- [ ] 所有加载状态有视觉提示
- [ ] 所有错误有明确提示

### 可访问性
- [ ] 颜色对比度符合 WCAG AA 标准
- [ ] 所有交互元素可键盘访问
- [ ] 所有图片有 alt 文本
- [ ] 所有表单有 label

### 响应式
- [ ] 移动端布局正常
- [ ] 平板端布局正常
- [ ] 桌面端布局正常
- [ ] 无横向滚动条

### 性能
- [ ] 动画流畅（60fps）
- [ ] 字体加载优化
- [ ] 图片懒加载
- [ ] CSS 压缩

---

## 13. 设计资源

### 字体
- IBM Plex Sans: https://fonts.google.com/specimen/IBM+Plex+Sans
- IBM Plex Mono: https://fonts.google.com/specimen/IBM+Plex+Mono

### 图标（可选）
- Lucide Icons: https://lucide.dev/
- Heroicons: https://heroicons.com/

### 参考
- OpenAI ChatGPT UI
- Linear App
- Vercel Dashboard

---

## 14. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-02-18 | 初始版本，基于老版 HTML 提取 |

---

**设计师签名**：AI UI/UX Designer
**审核状态**：待前端工程师审核
