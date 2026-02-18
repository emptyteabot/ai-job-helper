import streamlit as st
import requests
import json
import time
from datetime import datetime

st.set_page_config(page_title="自动投递", page_icon="🚀", layout="wide")

# 初始化 session state
if 'task_id' not in st.session_state:
    st.session_state.task_id = None
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'stats' not in st.session_state:
    st.session_state.stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

st.title("🚀 自动投递")
st.markdown("---")

# API 配置
API_BASE_URL = "https://ai-job-hunter-production-2730.up.railway.app"

# 平台选择
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📱 选择投递平台")
    platforms = st.multiselect(
        "选择一个或多个平台",
        ["boss", "zhilian", "linkedin"],
        default=["boss"],
        format_func=lambda x: {"boss": "Boss直聘", "zhilian": "智联招聘", "linkedin": "LinkedIn"}[x],
        help="可以同时选择多个平台进行投递"
    )

with col2:
    st.subheader("📊 当前状态")
    if st.session_state.is_running:
        st.success("🟢 运行中")
    else:
        st.info("⚪ 未运行")

st.markdown("---")

# 基础配置
st.subheader("⚙️ 基础配置")

col1, col2, col3 = st.columns(3)

with col1:
    keywords = st.text_input(
        "搜索关键词",
        value="实习生,应届生,前端开发",
        help="多个关键词用逗号分隔"
    )

    location = st.text_input(
        "工作地点",
        value="北京,上海,深圳",
        help="多个地点用逗号分隔"
    )

with col2:
    target_count = st.number_input(
        "投递数量",
        min_value=1,
        max_value=500,
        value=50,
        help="本次计划投递的简历数量"
    )

    delay_time = st.slider(
        "投递间隔（秒）",
        min_value=3,
        max_value=30,
        value=5,
        help="每次投递之间的等待时间"
    )

with col3:
    blacklist = st.text_area(
        "公司黑名单",
        placeholder="一行一个公司名称",
        height=100,
        help="这些公司将被自动跳过"
    )

st.markdown("---")

# 平台账号配置
if platforms:
    st.subheader("🔐 平台账号配置")

    tabs = st.tabs([{"boss": "Boss直聘", "zhilian": "智联招聘", "linkedin": "LinkedIn"}[p] for p in platforms])

    platform_configs = {}

    for idx, platform in enumerate(platforms):
        with tabs[idx]:
            platform_names = {'boss': 'Boss直聘', 'zhilian': '智联招聘', 'linkedin': 'LinkedIn'}
            st.markdown(f"### {platform_names[platform]} 配置")

            col1, col2 = st.columns(2)

            with col1:
                if platform == "linkedin":
                    email = st.text_input(
                        "邮箱",
                        key=f"{platform}_email",
                        help="LinkedIn 登录邮箱"
                    )
                    platform_configs[platform] = {"email": email}
                else:
                    phone = st.text_input(
                        "手机号",
                        key=f"{platform}_phone",
                        help=f"登录手机号"
                    )
                    platform_configs[platform] = {"phone": phone}

            with col2:
                password = st.text_input(
                    "密码",
                    type="password",
                    key=f"{platform}_password",
                    help="账号密码"
                )
                if platform in platform_configs:
                    platform_configs[platform]["password"] = password

            # 平台特定选项
            if platform == "boss":
                online_only = st.checkbox("只投递在线HR", value=True, key=f"{platform}_online_only")
                active_first = st.checkbox("优先投递活跃职位", value=True, key=f"{platform}_active_first")
                platform_configs[platform].update({
                    "online_only": online_only,
                    "active_first": active_first
                })

            elif platform == "zhilian":
                education = st.selectbox(
                    "学历筛选",
                    ["不限", "大专", "本科", "硕士", "博士"],
                    key=f"{platform}_education"
                )
                experience = st.selectbox(
                    "经验要求",
                    ["不限", "应届生", "1年以下", "1-3年"],
                    key=f"{platform}_experience"
                )
                platform_configs[platform].update({
                    "education": education,
                    "experience": experience
                })

            elif platform == "linkedin":
                job_type = st.selectbox(
                    "职位类型",
                    ["全部", "全职", "兼职", "实习", "合同工"],
                    index=3,
                    key=f"{platform}_job_type"
                )
                easy_apply = st.checkbox("Easy Apply 优先", value=True, key=f"{platform}_easy_apply")
                platform_configs[platform].update({
                    "job_type": job_type,
                    "easy_apply": easy_apply
                })

st.markdown("---")

# 控制按钮
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("▶️ 开始投递", type="primary", disabled=st.session_state.is_running or not platforms):
        # 准备请求数据
        request_data = {
            "platforms": platforms,
            "keywords": keywords,
            "locations": location.split(","),
            "target_count": target_count,
            "delay": delay_time,
            "blacklist": [line.strip() for line in blacklist.split("\n") if line.strip()],
            "configs": platform_configs
        }

        try:
            # 调用后端 API
            response = requests.post(
                f"{API_BASE_URL}/api/auto-apply/start-multi",
                json=request_data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                st.session_state.task_id = result.get("task_id")
                st.session_state.is_running = True
                st.success(f"✅ 投递任务已启动！任务ID: {st.session_state.task_id}")
                st.rerun()
            else:
                st.error(f"❌ 启动失败: {response.text}")

        except Exception as e:
            st.error(f"❌ 错误: {str(e)}")

with col2:
    if st.button("⏸️ 停止", disabled=not st.session_state.is_running):
        if st.session_state.task_id:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/auto-apply/stop",
                    json={"task_id": st.session_state.task_id},
                    timeout=10
                )
                if response.status_code == 200:
                    st.session_state.is_running = False
                    st.success("✅ 已停止投递")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ 停止失败: {str(e)}")

with col3:
    if st.button("🔄 重置"):
        st.session_state.task_id = None
        st.session_state.is_running = False
        st.session_state.stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}
        st.rerun()

st.markdown("---")

# 实时进度
if st.session_state.is_running and st.session_state.task_id:
    st.subheader("📈 投递进度")

    # 获取任务状态
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/auto-apply/status/{st.session_state.task_id}",
            timeout=10
        )

        if response.status_code == 200:
            status_data = response.json()

            # 进度条
            progress = status_data.get("progress", 0)
            total = status_data.get("total", target_count)
            progress_bar = st.progress(progress / total if total > 0 else 0)
            st.caption(f"进度: {progress}/{total}")

            # 统计数据
            col1, col2, col3, col4 = st.columns(4)

            stats = status_data.get("stats", {})
            with col1:
                st.metric("总计", stats.get("total", 0))
            with col2:
                st.metric("成功", stats.get("success", 0))
            with col3:
                st.metric("失败", stats.get("failed", 0))
            with col4:
                st.metric("跳过", stats.get("skipped", 0))

            # 自动刷新
            if status_data.get("status") == "running":
                time.sleep(2)
                st.rerun()
            elif status_data.get("status") == "completed":
                st.session_state.is_running = False
                st.success("🎉 投递完成！")

    except Exception as e:
        st.error(f"❌ 获取状态失败: {str(e)}")

# 历史记录
st.markdown("---")
st.subheader("📋 投递历史")

try:
    response = requests.get(f"{API_BASE_URL}/api/auto-apply/history", timeout=10)

    if response.status_code == 200:
        history = response.json()

        if history:
            for record in history[:10]:  # 显示最近10条
                with st.expander(f"任务 {record.get('task_id', 'N/A')} - {record.get('created_at', 'N/A')}"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**平台**: {', '.join(record.get('platforms', []))}")
                        st.write(f"**关键词**: {record.get('keywords', 'N/A')}")

                    with col2:
                        st.write(f"**状态**: {record.get('status', 'N/A')}")
                        st.write(f"**进度**: {record.get('progress', 0)}/{record.get('total', 0)}")

                    with col3:
                        stats = record.get('stats', {})
                        st.write(f"**成功**: {stats.get('success', 0)}")
                        st.write(f"**失败**: {stats.get('failed', 0)}")
        else:
            st.info("暂无投递历史")

except Exception as e:
    st.warning(f"无法加载历史记录: {str(e)}")

# 使用提示
with st.expander("💡 使用提示"):
    st.markdown("""
    ### 投递建议

    1. **关键词优化**
       - 使用多个相关关键词提高匹配率
       - 针对不同平台调整关键词策略

    2. **投递时间**
       - 工作日 9:00-11:00 和 14:00-17:00 HR 活跃度高
       - 避免在深夜或周末大量投递

    3. **投递间隔**
       - 建议设置 5-10 秒间隔
       - 过快可能被平台识别为机器人

    4. **黑名单管理**
       - 及时添加不合适的公司
       - 定期更新黑名单

    ### 注意事项

    - ⚠️ 首次使用请先测试少量投递
    - ⚠️ 确保账号信息正确，避免被封号
    - ⚠️ 定期检查投递效果，优化策略
    - ⚠️ 遵守各平台的使用规则
    """)

# 页脚
st.markdown("---")
st.caption("💼 祝你求职顺利！记得定期查看投递反馈哦～")
