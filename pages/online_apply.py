"""
在线投递页面 - 用户授权后自动投递
访问链接：https://your-service.com/apply?token=xxx
"""

import streamlit as st
import asyncio
from typing import Dict, Any


def render_online_apply_page(token: str):
    """渲染在线投递页面"""

    st.set_page_config(
        page_title="在线投递 - AI求职助手",
        page_icon="🚀",
        layout="centered"
    )

    st.markdown("""
    <style>
    .main {
        max-width: 800px;
        margin: 0 auto;
    }
    .step-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .step-number {
        display: inline-block;
        width: 32px;
        height: 32px;
        line-height: 32px;
        text-align: center;
        background: linear-gradient(135deg, #ffb6b9 0%, #fae3d9 100%);
        color: white;
        border-radius: 50%;
        font-weight: bold;
        margin-right: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

    # 标题
    st.markdown("# 🚀 在线投递")
    st.markdown("### 三步完成自动投递，无需安装任何软件")

    # 验证 token
    user_data = verify_token(token)

    if not user_data:
        st.error("❌ 链接已失效，请重新生成")
        return

    st.success(f"✅ 欢迎，{user_data['name']}！")

    # 显示投递策略
    with st.expander("📊 查看投递策略", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**关键词：**")
            for keyword in user_data['targets']['keywords'][:3]:
                st.markdown(f"- `{keyword}`")

        with col2:
            st.markdown("**地点：**")
            for location in user_data['targets']['locations'][:2]:
                st.markdown(f"- {location}")

        st.markdown(f"**每天投递：** {user_data['max_count']} 个")

    # 步骤1：选择平台
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.markdown('<span class="step-number">1</span> **选择投递平台**', unsafe_allow_html=True)

    platform = st.selectbox(
        "选择平台",
        ["Boss直聘", "实习僧", "牛客网"],
        label_visibility="collapsed"
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # 步骤2：授权登录
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.markdown('<span class="step-number">2</span> **授权登录**', unsafe_allow_html=True)

    st.info("💡 我们不会保存你的密码，使用 OAuth 授权登录")

    if platform == "Boss直聘":
        auth_method = st.radio(
            "登录方式",
            ["扫码登录（推荐）", "手机验证码登录"],
            horizontal=True,
            label_visibility="collapsed"
        )

        if auth_method == "扫码登录（推荐）":
            st.markdown("请使用 Boss 直聘 App 扫描下方二维码：")

            # 生成二维码（示例）
            qr_code_url = generate_qr_code(platform, token)
            st.image(qr_code_url, width=200)

            if st.button("我已扫码", type="primary"):
                with st.spinner("正在验证..."):
                    import time
                    time.sleep(2)
                    st.success("✅ 授权成功！")
                    st.session_state.authorized = True

        else:
            phone = st.text_input("手机号", value=user_data.get('phone', ''))
            code = st.text_input("验证码")

            col1, col2 = st.columns([3, 1])
            with col1:
                pass
            with col2:
                if st.button("获取验证码"):
                    st.success("✅ 验证码已发送")

            if st.button("登录", type="primary"):
                st.success("✅ 登录成功！")
                st.session_state.authorized = True

    st.markdown('</div>', unsafe_allow_html=True)

    # 步骤3：开始投递
    if st.session_state.get('authorized', False):
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.markdown('<span class="step-number">3</span> **开始投递**', unsafe_allow_html=True)

        st.success("🎉 一切准备就绪！")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 立即开始投递", type="primary", use_container_width=True):
                start_apply_task(user_data, platform)

        with col2:
            if st.button("⏰ 定时投递", use_container_width=True):
                st.info("将在工作日 9-11 点自动投递")

        st.markdown('</div>', unsafe_allow_html=True)

        # 投递进度
        if st.session_state.get('applying', False):
            st.markdown("### 📊 投递进度")

            progress_bar = st.progress(0)
            status_text = st.empty()

            # 模拟投递进度
            for i in range(100):
                import time
                time.sleep(0.1)
                progress_bar.progress(i + 1)
                status_text.text(f"正在投递第 {i+1}/30 个岗位...")

            st.success("🎉 投递完成！")

            # 显示结果
            st.markdown("### 📋 投递结果")

            results = [
                {"position": "Python后端实习生", "company": "字节跳动", "status": "✅ 成功"},
                {"position": "Django开发实习", "company": "美团", "status": "✅ 成功"},
                {"position": "Web开发实习", "company": "腾讯", "status": "✅ 成功"},
                {"position": "后端实习生", "company": "阿里巴巴", "status": "⏳ 待审核"},
                {"position": "Python实习", "company": "百度", "status": "❌ 已满"},
            ]

            for result in results:
                st.markdown(f"- **{result['position']}** - {result['company']} - {result['status']}")

            st.info("📧 详细报告已发送到你的邮箱")

    # 底部说明
    st.markdown("---")
    st.markdown("""
    ### 💡 温馨提示

    **安全保障：**
    - 🔒 使用 OAuth 授权，不保存密码
    - 🛡️ 数据加密传输
    - 🗑️ 投递完成后自动删除授权

    **投递策略：**
    - 🎯 只投递匹配度 ≥ 70% 的岗位
    - ⏱️ 间隔 5-10 秒，避免被检测
    - 📊 每天最多 30 个，提高质量

    **遇到问题？**
    - 📧 发送邮件到 support@example.com
    - 💬 加入 QQ 群：123456789
    """)


def verify_token(token: str) -> Dict[str, Any]:
    """验证 token 并返回用户数据"""

    # 从数据库或缓存中查询
    # 这里返回示例数据

    return {
        "name": "张三",
        "phone": "13800138000",
        "email": "zhangsan@example.com",
        "targets": {
            "keywords": ["Python", "Django", "后端"],
            "locations": ["北京", "上海"],
            "positions": []
        },
        "max_count": 30
    }


def generate_qr_code(platform: str, token: str) -> str:
    """生成二维码"""

    # 使用 qrcode 库生成
    # 返回二维码图片 URL

    return "https://via.placeholder.com/200x200?text=QR+Code"


def start_apply_task(user_data: Dict, platform: str):
    """开始投递任务"""

    st.session_state.applying = True

    # 调用后端 API 开始投递
    # 或者直接在这里执行 Selenium 脚本

    st.success("🚀 投递任务已启动！")


if __name__ == "__main__":
    # 从 URL 参数获取 token
    import sys
    token = sys.argv[1] if len(sys.argv) > 1 else "demo_token"

    render_online_apply_page(token)
