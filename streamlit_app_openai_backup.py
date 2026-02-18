"""
AI求职助手 - Gemini + Material Design 风格
酷炫的渐变、动画和现代设计
"""
import streamlit as st

# 页面配置
st.set_page_config(
    page_title="AI求职助手",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 导入完整的 CSS 和 HTML
exec(open('streamlit_gemini_style.py', 'r', encoding='utf-8').read())
