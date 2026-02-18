"""
伪进度条组件 - 让等待更有趣
"""

import streamlit as st
import time
import random


class FakeProgressBar:
    """伪进度条 - 在 AI 思考时显示动画进度"""

    def __init__(self, total_time: float = 30.0):
        """
        Args:
            total_time: 预计总时间（秒）
        """
        self.total_time = total_time
        self.progress_bar = None
        self.status_text = None

    def start(self, message: str = "AI 正在思考..."):
        """开始显示进度"""
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        self.status_text.info(f"🤔 {message}")

    def update(self, progress: float, message: str = None):
        """更新进度"""
        if self.progress_bar:
            self.progress_bar.progress(min(progress, 0.99))  # 最多到 99%

        if message and self.status_text:
            self.status_text.info(f"🤔 {message}")

    def finish(self, message: str = "完成！"):
        """完成"""
        if self.progress_bar:
            self.progress_bar.progress(1.0)

        if self.status_text:
            self.status_text.success(f"✅ {message}")

    def simulate(self, messages: list = None):
        """模拟进度（在后台线程中运行）"""

        if not messages:
            messages = [
                "正在分析简历结构...",
                "提取关键信息...",
                "匹配岗位数据库...",
                "生成推荐方案...",
                "优化输出结果..."
            ]

        import threading

        def _simulate():
            progress = 0.0
            step = 1.0 / len(messages)

            for i, msg in enumerate(messages):
                # 随机速度
                duration = random.uniform(2, 5)
                steps = int(duration * 10)

                for j in range(steps):
                    progress = min((i + j / steps) * step, 0.99)
                    self.update(progress, msg)
                    time.sleep(0.1)

        thread = threading.Thread(target=_simulate, daemon=True)
        thread.start()


def show_thinking_animation(container, agent_name: str):
    """显示思考动画"""

    thinking_messages = [
        f"🤔 {agent_name}正在深度思考...",
        f"💡 {agent_name}正在分析数据...",
        f"🔍 {agent_name}正在查找最佳方案...",
        f"✨ {agent_name}正在优化结果..."
    ]

    for i in range(4):
        container.info(thinking_messages[i % len(thinking_messages)])
        time.sleep(0.5)


def show_typing_effect(container, text: str, speed: float = 0.03):
    """打字机效果"""

    displayed_text = ""

    for char in text:
        displayed_text += char
        container.markdown(displayed_text)
        time.sleep(speed)


def show_loading_dots(container, message: str, duration: float = 3.0):
    """加载点动画"""

    start_time = time.time()

    while time.time() - start_time < duration:
        for dots in [".", "..", "..."]:
            container.info(f"{message}{dots}")
            time.sleep(0.3)


def show_progress_with_steps(steps: list, total_time: float = 30.0):
    """显示分步进度"""

    progress_bar = st.progress(0)
    status_text = st.empty()

    step_time = total_time / len(steps)

    for i, step in enumerate(steps):
        status_text.info(f"🔄 {step}")

        # 模拟该步骤的进度
        for j in range(10):
            progress = (i + j / 10) / len(steps)
            progress_bar.progress(progress)
            time.sleep(step_time / 10)

    progress_bar.progress(1.0)
    status_text.success("✅ 全部完成！")
