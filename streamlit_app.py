"""
AI 求职助手 - Streamlit 云端版
集成自动投递功能
"""
import streamlit as st
import requests
import time
from datetime import datetime

# ==================== 配置 ====================

# 后端 API 地址（通过 ngrok 内网穿透）
# 启动 ngrok 后，将这里的地址替换成你的 ngrok 地址
API_URL = "https://unleisured-polly-welcomingly.ngrok-free.dev"  # ✅ 你的 ngrok 地址

# ==================== 页面配置 ====================

st.set_page_config(
    page_title="AI 求职助手",
    page_icon="🚀",
    layout="wide"
)

# ==================== 样式 ====================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1890ff;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .success-log {
        background: #f6ffed;
        border-left: 4px solid #52c41a;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    .error-log {
        background: #fff2f0;
        border-left: 4px solid #ff4d4f;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 工具函数 ====================

def check_backend_status():
    """检查后端服务是否可用"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def login_user(phone: str, code: str = "123456"):
    """用户登录/注册"""
    try:
        # 先尝试登录
        response = requests.post(
            f"{API_URL}/api/auth/login",
            json={"phone": phone, "code": code},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data
        
        # 如果登录失败，尝试注册
        response = requests.post(
            f"{API_URL}/api/auth/register",
            json={"phone": phone, "code": code, "nickname": phone},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data
        
        return None
    except Exception as e:
        st.error(f"登录失败: {str(e)}")
        return None

def upgrade_plan(token: str, plan: str):
    """升级套餐"""
    try:
        response = requests.post(
            f"{API_URL}/api/user/upgrade",
            headers={"Authorization": f"Bearer {token}"},
            json={"plan": plan},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data
        return None
    except Exception as e:
        st.error(f"升级失败: {str(e)}")
        return None

def submit_apply_task(token: str, keyword: str, city: str, max_count: int, resume_text: str):
    """提交投递任务（同步版本）"""
    try:
        response = requests.post(
            f"{API_URL}/api/apply/boss/batch",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "keyword": keyword,
                "city": city,
                "max_count": max_count,
                "greeting_template": "您好，我对{position}岗位很感兴趣，期待与您沟通！"
            },
            timeout=300  # 5 分钟超时
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"投递失败: {str(e)}")
        return None

# ==================== 主界面 ====================

st.markdown('<div class="main-header">🚀 AI 求职助手 - 云端版</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">自动搜索岗位并批量投递，AI 生成个性化求职信</div>', unsafe_allow_html=True)

# 检查后端状态
if not check_backend_status():
    st.error("⚠️ 后端服务未启动或无法连接")
    st.info("""
    请确保：
    1. 已启动后端服务（双击 `启动云端后端.bat`）
    2. 已启动 ngrok（`ngrok http 8765`）
    3. 已将 ngrok 地址填入代码的 API_URL
    """)
    st.stop()

st.success("✅ 后端服务连接正常")

# ==================== 用户登录 ====================

if 'token' not in st.session_state:
    st.subheader("📱 登录 / 注册")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        phone = st.text_input("手机号", placeholder="请输入手机号")
        
        st.info("💡 开发环境提示：验证码自动填充为 123456，直接点击登录即可")
        
        if st.button("登录 / 注册", type="primary", use_container_width=True):
            if phone:
                with st.spinner("登录中..."):
                    result = login_user(phone)
                    if result:
                        st.session_state['token'] = result['token']
                        st.session_state['user'] = result['user']
                        st.success("✅ 登录成功！")
                        st.rerun()
                    else:
                        st.error("❌ 登录失败，请重试")
            else:
                st.warning("请输入手机号")
    
    with col2:
        st.info("""
        **新用户福利**
        
        注册即送 5 次免费投递
        
        **套餐价格**
        - 基础版：¥19.9/月
        - 专业版：¥39.9/月
        - 年费版：¥199/年
        """)

else:
    # 已登录，显示主界面
    user = st.session_state['user']
    
    # ==================== 用户信息卡片 ====================
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; opacity: 0.9;">当前套餐</div>
            <div style="font-size: 1.8rem; font-weight: bold; margin-top: 0.5rem;">
                {user.get('plan', 'free').upper()}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; opacity: 0.9;">剩余次数</div>
            <div style="font-size: 1.8rem; font-weight: bold; margin-top: 0.5rem;">
                {user.get('remaining_quota', 0)} 次
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; opacity: 0.9;">手机号</div>
            <div style="font-size: 1.2rem; font-weight: bold; margin-top: 0.5rem;">
                {user.get('phone', '')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        if st.button("🔄 刷新信息", use_container_width=True):
            st.rerun()
        if st.button("🚪 退出登录", use_container_width=True):
            del st.session_state['token']
            del st.session_state['user']
            st.rerun()
    
    st.markdown("---")
    
    # ==================== 升级套餐 ====================
    
    with st.expander("💎 升级套餐", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **基础版**
            
            ¥19.9/月
            
            - 每天 30 次投递
            - AI 生成求职信
            - 投递记录管理
            """)
            if st.button("升级到基础版", key="upgrade_basic"):
                result = upgrade_plan(st.session_state['token'], 'basic')
                if result and result.get('success'):
                    st.session_state['user'] = result['user']
                    st.success("✅ 升级成功！")
                    st.rerun()
        
        with col2:
            st.markdown("""
            **专业版** 🔥
            
            ¥39.9/月
            
            - 每天 100 次投递
            - 优先投递
            - 简历优化建议
            - 数据分析报告
            """)
            if st.button("升级到专业版", key="upgrade_pro"):
                result = upgrade_plan(st.session_state['token'], 'pro')
                if result and result.get('success'):
                    st.session_state['user'] = result['user']
                    st.success("✅ 升级成功！")
                    st.rerun()
        
        with col3:
            st.markdown("""
            **年费版** ⭐
            
            ¥199/年
            
            - 无限次投递
            - 所有功能
            - 专属客服
            - 优先更新
            """)
            if st.button("升级到年费版", key="upgrade_yearly"):
                result = upgrade_plan(st.session_state['token'], 'yearly')
                if result and result.get('success'):
                    st.session_state['user'] = result['user']
                    st.success("✅ 升级成功！")
                    st.rerun()
        
        st.info("💡 开发环境提示：点击升级按钮即可模拟升级，无需实际支付")
    
    st.markdown("---")
    
    # ==================== 自动投递表单 ====================
    
    st.subheader("🎯 自动投递")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        keyword = st.text_input("🔍 搜索关键词", placeholder="例如：Python实习、前端开发", value="Python实习")
        city = st.text_input("📍 城市", placeholder="例如：北京、上海、全国", value="北京")
        max_count = st.number_input("📊 投递数量", min_value=1, max_value=50, value=5)
        resume_text = st.text_area("📄 简历内容", placeholder="粘贴你的简历内容...", height=200)
    
    with col2:
        st.info("""
        **使用说明**
        
        1. 输入关键词和城市
        2. 设置投递数量
        3. 粘贴简历内容
        4. 点击开始投递
        
        **注意事项**
        
        - 每次投递消耗 1 次额度
        - 建议先测试 3-5 个
        - 投递间隔 3-6 秒
        """)
    
    # 投递按钮
    if st.button("🚀 开始自动投递", type="primary", use_container_width=True):
        # 检查额度
        if user.get('remaining_quota', 0) <= 0:
            st.error("❌ 投递次数已用完，请升级套餐")
        elif not resume_text.strip():
            st.warning("⚠️ 请输入简历内容")
        else:
            # 开始投递
            st.info(f"🔄 正在投递 {max_count} 个岗位，请稍候...")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with st.spinner("投递中..."):
                result = submit_apply_task(
                    st.session_state['token'],
                    keyword,
                    city,
                    max_count,
                    resume_text
                )
                
                progress_bar.progress(100)
                
                if result:
                    st.success(f"✅ 投递完成！成功 {result.get('success', 0)} 个，失败 {result.get('failed', 0)} 个")
                    
                    # 显示投递日志
                    if 'details' in result:
                        st.subheader("📋 投递日志")
                        for detail in result['details']:
                            if detail['status'] == 'success':
                                st.markdown(f"""
                                <div class="success-log">
                                    ✅ <strong>{detail['job']}</strong> - {detail['company']}
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div class="error-log">
                                    ❌ <strong>{detail['job']}</strong> - {detail['company']}
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # 刷新用户信息
                    st.info("🔄 刷新页面查看最新额度")
                else:
                    st.error("❌ 投递失败，请重试")
    
    st.markdown("---")
    
    # ==================== 使用统计 ====================
    
    st.subheader("📊 使用统计")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("今日投递", "0 个")
    
    with col2:
        st.metric("本周投递", "0 个")
    
    with col3:
        st.metric("总投递", "0 个")
    
    st.info("💡 投递记录功能开发中...")

# ==================== 页脚 ====================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; padding: 2rem 0;">
    <p>AI 求职助手 v2.0 | 让找工作更简单</p>
    <p>GitHub: <a href="https://github.com/emptyteabot/ai-job-helper" target="_blank">emptyteabot/ai-job-helper</a></p>
</div>
""", unsafe_allow_html=True)
