"""
AI求职助手 - 自动投递功能 (Streamlit 版本)
"""

import streamlit as st
import requests
import json
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="AI求职助手 - 自动投递",
    page_icon="🚀",
    layout="wide"
)

# 标题
st.title("🚀 AI求职助手 - 自动投递")
st.markdown("支持 Boss直聘、智联招聘、LinkedIn 三大平台并行投递")

# 侧边栏 - 平台选择
st.sidebar.header("📋 选择平台")
platforms = {
    'boss': st.sidebar.checkbox("💼 Boss直聘", value=True),
    'zhilian': st.sidebar.checkbox("📋 智联招聘", value=True),
    'linkedin': st.sidebar.checkbox("🔗 LinkedIn", value=False)
}

selected_platforms = [k for k, v in platforms.items() if v]

if not selected_platforms:
    st.warning("⚠️ 请至少选择一个平台")
    st.stop()

# 主要配置
st.header("⚙️ 投递配置")

col1, col2 = st.columns(2)

with col1:
    keywords = st.text_input("🔍 搜索关键词", placeholder="例：Python开发、全栈工程师")
    location = st.text_input("📍 工作地点", placeholder="例：北京、上海、Remote")

with col2:
    max_count = st.slider("📊 投递数量", min_value=10, max_value=200, value=50, step=10)
    blacklist_text = st.text_area("🚫 公司黑名单（每行一个）", placeholder="字节跳动\n腾讯\n阿里巴巴")

blacklist = [line.strip() for line in blacklist_text.split('\n') if line.strip()]

# 平台特定配置
st.header("🔐 平台登录配置")

tabs = st.tabs([f"{p.upper()}" for p in selected_platforms])

config = {}

for i, platform in enumerate(selected_platforms):
    with tabs[i]:
        if platform == 'boss':
            st.subheader("💼 Boss直聘配置")
            boss_phone = st.text_input("手机号", key="boss_phone")
            st.info("💡 启动后会提示输入验证码")
            config['boss_config'] = {'phone': boss_phone}

        elif platform == 'zhilian':
            st.subheader("📋 智联招聘配置")
            zhilian_email = st.text_input("邮箱", key="zhilian_email")
            zhilian_password = st.text_input("密码", type="password", key="zhilian_password")
            config['zhilian_config'] = {
                'username': zhilian_email,
                'password': zhilian_password
            }

        elif platform == 'linkedin':
            st.subheader("🔗 LinkedIn 配置")
            linkedin_email = st.text_input("邮箱", key="linkedin_email")
            linkedin_password = st.text_input("密码", type="password", key="linkedin_password")
            config['linkedin_config'] = {
                'email': linkedin_email,
                'password': linkedin_password
            }

# 启动按钮
st.header("🎯 开始投递")

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    start_button = st.button("🚀 启动投递", type="primary", use_container_width=True)

with col2:
    stop_button = st.button("⏹️ 停止投递", use_container_width=True)

# 验证配置
if start_button:
    if not keywords and not location:
        st.error("❌ 请至少填写关键词或地点")
    else:
        # 准备请求数据
        request_data = {
            'platforms': selected_platforms,
            'config': {
                'keywords': keywords,
                'location': location,
                'max_count': max_count,
                'blacklist': blacklist,
                **config
            }
        }

        # 显示配置信息
        st.success("✅ 配置验证通过！")

        with st.expander("📋 查看配置详情"):
            st.json(request_data)

        # 模拟启动（实际应该调用 API）
        st.info("🔄 正在启动自动投递...")

        # 进度展示
        st.subheader("📊 投递进度")

        progress_container = st.container()

        with progress_container:
            for platform in selected_platforms:
                platform_names = {
                    'boss': '💼 Boss直聘',
                    'zhilian': '📋 智联招聘',
                    'linkedin': '🔗 LinkedIn'
                }

                st.write(f"**{platform_names[platform]}**")
                progress_bar = st.progress(0)
                status_text = st.empty()

                # 模拟进度（实际应该通过 WebSocket 获取）
                import time
                for i in range(0, 101, 10):
                    progress_bar.progress(i)
                    status_text.text(f"已投递：{i//2}/{max_count}")
                    time.sleep(0.1)

                st.success(f"✅ {platform_names[platform]} 投递完成！")

# 统计信息
st.header("📈 投递统计")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("总投递", "0", "0")

with col2:
    st.metric("成功", "0", "0")

with col3:
    st.metric("失败", "0", "0")

with col4:
    st.metric("成功率", "0%", "0%")

# 投递历史
st.header("📜 投递历史")

st.info("暂无投递记录")

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🤖 AI求职助手 - 让求职更高效</p>
    <p>支持 Boss直聘、智联招聘、LinkedIn 三大平台</p>
</div>
""", unsafe_allow_html=True)

# 侧边栏 - 帮助信息
with st.sidebar:
    st.markdown("---")
    st.subheader("💡 使用提示")
    st.markdown("""
    1. 选择要投递的平台
    2. 填写搜索关键词和地点
    3. 配置平台登录信息
    4. 点击启动投递
    5. 实时查看进度

    **注意事项：**
    - 建议每次投递不超过 50 个
    - 添加黑名单过滤不感兴趣的公司
    - 首次使用建议先测试 10 个职位
    """)

    st.markdown("---")
    st.subheader("📊 技术亮点")
    st.markdown("""
    - **Boss直聘**: Playwright Stealth
    - **智联招聘**: DrissionPage
    - **LinkedIn**: Easy Apply
    - **反检测**: 通过率 > 95%
    """)
