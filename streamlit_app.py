"""
自动投递 Streamlit 应用
简单、快速、易用的自动投递界面
"""

import streamlit as st
import requests
import json
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="自动投递 | AI求职助手",
    page_icon="🚀",
    layout="wide"
)

# 标题
st.title("🚀 自动投递控制台")
st.markdown("一键启动多平台自动投递，实时查看进度")

# 侧边栏 - 配置
with st.sidebar:
    st.header("⚙️ 投递配置")

    # 平台选择
    st.subheader("选择平台")
    boss_enabled = st.checkbox("💼 Boss直聘", value=True)
    zhilian_enabled = st.checkbox("📋 智联招聘", value=False)
    linkedin_enabled = st.checkbox("🔗 LinkedIn", value=False)

    selected_platforms = []
    if boss_enabled:
        selected_platforms.append('boss')
    if zhilian_enabled:
        selected_platforms.append('zhilian')
    if linkedin_enabled:
        selected_platforms.append('linkedin')

    st.divider()

    # 通用配置
    st.subheader("通用配置")
    keywords = st.text_input("职位关键词", placeholder="例如：Python开发、前端工程师")
    location = st.text_input("工作地点", placeholder="例如：北京、上海、深圳")
    max_count = st.slider("投递数量（每个平台）", 1, 200, 50)
    blacklist = st.text_area("公司黑名单（每行一个）", placeholder="不想投递的公司")

    st.divider()

    # 平台特定配置
    if boss_enabled:
        st.subheader("💼 Boss直聘")
        boss_phone = st.text_input("手机号", key="boss_phone")
        boss_code = st.text_input("验证码（如需要）", key="boss_code")

    if zhilian_enabled:
        st.subheader("📋 智联招聘")
        zhilian_username = st.text_input("邮箱/用户名", key="zhilian_username")
        zhilian_password = st.text_input("密码", type="password", key="zhilian_password")

    if linkedin_enabled:
        st.subheader("🔗 LinkedIn")
        linkedin_email = st.text_input("邮箱", key="linkedin_email")
        linkedin_password = st.text_input("密码", type="password", key="linkedin_password")

# 主区域
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    start_button = st.button("🚀 启动投递", type="primary", use_container_width=True)

with col2:
    stop_button = st.button("⏹️ 停止投递", use_container_width=True)

with col3:
    refresh_button = st.button("🔄 刷新", use_container_width=True)

st.divider()

# 初始化 session state
if 'task_id' not in st.session_state:
    st.session_state.task_id = None
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'logs' not in st.session_state:
    st.session_state.logs = []

# 启动投递
if start_button:
    if not keywords:
        st.error("❌ 请输入职位关键词")
    elif not selected_platforms:
        st.error("❌ 请至少选择一个平台")
    else:
        with st.spinner("正在启动投递任务..."):
            try:
                # 准备配置
                blacklist_list = [line.strip() for line in blacklist.split('\n') if line.strip()]

                config = {
                    "platforms": selected_platforms,
                    "config": {
                        "keywords": keywords,
                        "location": location,
                        "max_count": max_count,
                        "blacklist": blacklist_list
                    }
                }

                # 添加平台特定配置
                if boss_enabled:
                    config["config"]["boss_config"] = {
                        "phone": boss_phone,
                        "code": boss_code
                    }

                if zhilian_enabled:
                    config["config"]["zhilian_config"] = {
                        "username": zhilian_username,
                        "password": zhilian_password
                    }

                if linkedin_enabled:
                    config["config"]["linkedin_config"] = {
                        "email": linkedin_email,
                        "password": linkedin_password
                    }

                # 发送请求
                response = requests.post(
                    "http://localhost:8000/api/auto-apply/start-multi",
                    json=config,
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        st.session_state.task_id = data.get('task_id')
                        st.session_state.is_running = True
                        st.success(f"✅ 任务已启动！任务ID: {st.session_state.task_id}")
                        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 任务启动成功")
                    else:
                        st.error(f"❌ 启动失败: {data.get('error', '未知错误')}")
                else:
                    st.error(f"❌ 请求失败: HTTP {response.status_code}")

            except requests.exceptions.ConnectionError:
                st.error("❌ 无法连接到服务器，请确保后端服务正在运行")
            except Exception as e:
                st.error(f"❌ 启动失败: {str(e)}")

# 停止投递
if stop_button and st.session_state.task_id:
    with st.spinner("正在停止任务..."):
        try:
            response = requests.post(
                f"http://localhost:8000/api/auto-apply/stop/{st.session_state.task_id}",
                timeout=10
            )

            if response.status_code == 200:
                st.session_state.is_running = False
                st.session_state.task_id = None
                st.success("✅ 任务已停止")
                st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 任务已停止")
            else:
                st.error("❌ 停止失败")
        except Exception as e:
            st.error(f"❌ 停止失败: {str(e)}")

# 显示状态
if st.session_state.is_running and st.session_state.task_id:
    st.info(f"🔄 任务运行中... 任务ID: {st.session_state.task_id}")

    # 获取任务状态
    try:
        response = requests.get(
            f"http://localhost:8000/api/auto-apply/status/{st.session_state.task_id}",
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                task = data.get('task', {})
                progress = task.get('progress', {})

                # 显示进度
                st.subheader("📊 投递进度")

                # 总体统计
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("成功投递", progress.get('total_applied', 0))

                with col2:
                    st.metric("失败次数", progress.get('total_failed', 0))

                with col3:
                    total = progress.get('total_applied', 0) + progress.get('total_failed', 0)
                    st.metric("总计", total)

                with col4:
                    if total > 0:
                        rate = round(progress.get('total_applied', 0) / total * 100)
                    else:
                        rate = 0
                    st.metric("成功率", f"{rate}%")

                # 各平台进度
                platform_progress = progress.get('platform_progress', {})
                if platform_progress:
                    st.subheader("各平台进度")

                    for platform_id, platform_data in platform_progress.items():
                        platform_names = {
                            'boss': '💼 Boss直聘',
                            'zhilian': '📋 智联招聘',
                            'linkedin': '🔗 LinkedIn'
                        }

                        platform_name = platform_names.get(platform_id, platform_id)
                        applied = platform_data.get('applied', 0)
                        total = platform_data.get('total', 0)
                        status = platform_data.get('status', 'unknown')

                        if total > 0:
                            progress_pct = applied / total
                        else:
                            progress_pct = 0

                        st.write(f"**{platform_name}** - {status}")
                        st.progress(progress_pct, text=f"{applied}/{total}")

    except Exception as e:
        st.warning(f"⚠️ 无法获取任务状态: {str(e)}")

# 日志区域
if st.session_state.logs:
    st.subheader("📝 操作日志")
    log_container = st.container()
    with log_container:
        for log in st.session_state.logs[-20:]:  # 只显示最近20条
            st.text(log)

# 底部信息
st.divider()
st.caption("💡 提示：确保后端服务正在运行（python web_app.py）")
st.caption("🔗 后端地址：http://localhost:8000")

# 自动刷新
if st.session_state.is_running:
    st.rerun()
