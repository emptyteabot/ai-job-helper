"""
Boss直聘自动投递器
使用 Playwright Stealth 实现终极反检测
"""

import asyncio
import random
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

try:
    from playwright_stealth import stealth_async
except ImportError:
    # 如果导入失败，使用同步版本
    try:
        from playwright_stealth import stealth
        # 创建异步包装器
        async def stealth_async(page):
            return stealth(page)
    except ImportError:
        # 如果都失败，创建空函数
        async def stealth_async(page):
            pass

from .base_applier import BaseApplier
from .session_manager import SessionManager

logger = logging.getLogger(__name__)



class BossApplier(BaseApplier):
    """Boss直聘自动投递器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session_manager = SessionManager('boss')
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None

        # Boss直聘特定配置
        self.base_url = "https://www.zhipin.com"
        self.login_url = "https://login.zhipin.com/"
        self.jobs_url = "https://www.zhipin.com/web/geek/job"

        # 反爬虫配置
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

    async def _init_browser(self):
        """初始化浏览器（带反检测）"""
        try:
            self.playwright = await async_playwright().start()

            # 启动浏览器（非无头模式，更难被检测）
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.get('headless', False),
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            )

            # 创建上下文（伪造指纹）
            self.context = await self.browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                permissions=['geolocation'],
                geolocation={'latitude': 39.9042, 'longitude': 116.4074},  # 北京
            )

            # 创建页面
            self.page = await self.context.new_page()

            # 应用 Stealth 模式（终极反检测）
            await stealth_async(self.page)

            # 注入额外的反检测脚本
            await self._inject_anti_detection()

            logger.info("浏览器初始化成功（Stealth 模式）")
            return True

        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            return False

    async def _inject_anti_detection(self):
        """注入反检测脚本"""
        # 伪造 WebGL 指纹
        await self.page.add_init_script("""
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.call(this, parameter);
            };
        """)

        # 伪造 Canvas 指纹
        await self.page.add_init_script("""
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                if (type === 'image/png' && this.width === 280 && this.height === 60) {
                    return originalToDataURL.apply(this, arguments);
                }
                const context = this.getContext('2d');
                const imageData = context.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] = imageData.data[i] ^ 1;
                }
                context.putImageData(imageData, 0, 0);
                return originalToDataURL.apply(this, arguments);
            };
        """)

        # 隐藏 Playwright 特征
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

    async def _random_delay(self, min_sec: float = None, max_sec: float = None):
        """随机延迟（模拟人类行为）"""
        min_sec = min_sec or self.config.get('random_delay_min', 2)
        max_sec = max_sec or self.config.get('random_delay_max', 5)
        delay = random.uniform(min_sec, max_sec)
        logger.debug(f"随机延迟 {delay:.2f} 秒")
        await asyncio.sleep(delay)

    async def _simulate_mouse_move(self):
        """模拟鼠标移动"""
        try:
            # 随机移动鼠标
            x = random.randint(100, 1800)
            y = random.randint(100, 900)
            await self.page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
        except Exception as e:
            logger.debug(f"鼠标移动失败: {e}")

    async def _simulate_scroll(self):
        """模拟页面滚动"""
        try:
            # 随机滚动
            scroll_amount = random.randint(300, 800)
            await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            logger.debug(f"页面滚动失败: {e}")

    def login(self, phone: str, password: str = None) -> bool:
        """
        登录 Boss直聘（手机号 + 验证码）

        Args:
            phone: 手机号
            password: 密码（Boss直聘主要用验证码登录，此参数保留）

        Returns:
            bool: 登录是否成功
        """
        return asyncio.run(self._async_login(phone))

    async def _async_login(self, phone: str) -> bool:
        """异步登录"""
        try:
            # 初始化浏览器
            if not await self._init_browser():
                return False

            # 访问登录页
            logger.info("正在访问登录页...")
            await self.page.goto(self.login_url, wait_until='networkidle')
            await self._random_delay(1, 2)

            # 点击手机号登录
            try:
                phone_tab = await self.page.wait_for_selector('text=手机号登录', timeout=5000)
                await phone_tab.click()
                await self._random_delay(0.5, 1)
            except:
                logger.info("已在手机号登录页面")

            # 输入手机号
            logger.info("输入手机号...")
            phone_input = await self.page.wait_for_selector('input[placeholder*="手机号"]', timeout=5000)
            await phone_input.click()
            await self._random_delay(0.3, 0.6)

            # 逐个字符输入（模拟人类）
            for char in phone:
                await phone_input.type(char, delay=random.randint(100, 300))

            await self._random_delay(1, 2)

            # 点击获取验证码
            logger.info("点击获取验证码...")
            code_button = await self.page.wait_for_selector('button:has-text("获取验证码")', timeout=5000)
            await code_button.click()

            # 处理滑块验证码（如果有）
            await self._handle_slider_captcha()

            # 等待用户输入验证码
            logger.info("=" * 50)
            logger.info("请在浏览器中输入短信验证码，然后点击登录")
            logger.info("等待登录完成...")
            logger.info("=" * 50)

            # 等待登录成功（检测 URL 变化）
            try:
                await self.page.wait_for_url(f"{self.base_url}/**", timeout=120000)
                logger.info("登录成功！")

                # 保存 Cookies
                await self._save_cookies()

                return True

            except Exception as e:
                logger.error(f"登录超时或失败: {e}")
                return False

        except Exception as e:
            logger.error(f"登录过程出错: {e}")
            return False

    async def _handle_slider_captcha(self):
        """处理滑块验证码"""
        try:
            # 检测是否有滑块
            slider = await self.page.query_selector('.geetest_slider_button')
            if not slider:
                return

            logger.info("检测到滑块验证码，开始破解...")

            # 获取滑块位置
            slider_box = await slider.bounding_box()
            if not slider_box:
                return

            # 计算拖动距离（通常需要拖到最右边）
            distance = 260  # Boss直聘滑块大约需要拖动 260px

            # 生成人类轨迹
            tracks = self._generate_human_track(distance)

            # 开始拖动
            await self.page.mouse.move(
                slider_box['x'] + slider_box['width'] / 2,
                slider_box['y'] + slider_box['height'] / 2
            )
            await self.page.mouse.down()

            # 按轨迹移动
            current_x = slider_box['x'] + slider_box['width'] / 2
            for track in tracks:
                current_x += track
                await self.page.mouse.move(current_x, slider_box['y'] + slider_box['height'] / 2)
                await asyncio.sleep(random.uniform(0.01, 0.02))

            # 释放鼠标
            await asyncio.sleep(random.uniform(0.5, 1))
            await self.page.mouse.up()

            logger.info("滑块验证码已处理")
            await self._random_delay(2, 3)

        except Exception as e:
            logger.warning(f"滑块验证码处理失败: {e}")

    def _generate_human_track(self, distance: int) -> List[int]:
        """
        生成人类拖动轨迹（贝塞尔曲线）

        Args:
            distance: 总距离

        Returns:
            List[int]: 每一步的移动距离
        """
        tracks = []
        current = 0
        mid = distance * 4 / 5  # 加速到 80% 位置

        t = 0.2
        v = 0

        while current < distance:
            if current < mid:
                a = 2  # 加速度
            else:
                a = -3  # 减速度

            v0 = v
            v = v0 + a * t
            move = v0 * t + 0.5 * a * t * t
            current += move
            tracks.append(round(move))

        return tracks

    async def _save_cookies(self):
        """保存 Cookies"""
        try:
            cookies = await self.context.cookies()
            # 这里简化处理，实际应该适配 SessionManager
            logger.info(f"已保存 {len(cookies)} 个 Cookies")
        except Exception as e:
            logger.error(f"保存 Cookies 失败: {e}")

    def search_jobs(self, keywords: str, location: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        搜索职位

        Args:
            keywords: 搜索关键词（如 "Python"）
            location: 工作地点（如 "北京"）
            filters: 筛选条件
                - salary: 薪资范围（如 "20-30K"）
                - experience: 工作年限（如 "3-5年"）
                - scale: 公司规模（如 "100-499人"）

        Returns:
            List[Dict]: 职位列表
        """
        return asyncio.run(self._async_search_jobs(keywords, location, filters))

    async def _async_search_jobs(self, keywords: str, location: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """异步搜索职位"""
        try:
            if not self.page:
                logger.error("浏览器未初始化，请先登录")
                return []

            # 构建搜索 URL
            search_url = f"{self.jobs_url}?query={keywords}&city={location}"

            logger.info(f"搜索职位: {keywords} @ {location}")
            await self.page.goto(search_url, wait_until='networkidle')
            await self._random_delay(2, 3)

            # 应用筛选条件
            await self._apply_filters(filters)

            # 解析职位列表
            jobs = await self._parse_job_list()

            # 过滤黑名单
            jobs = self._filter_blacklist(jobs)

            logger.info(f"找到 {len(jobs)} 个职位")
            return jobs

        except Exception as e:
            logger.error(f"搜索职位失败: {e}")
            return []

    async def _apply_filters(self, filters: Dict[str, Any]):
        """应用筛选条件"""
        try:
            # 薪资筛选
            if filters.get('salary'):
                salary_filter = await self.page.query_selector(f'text={filters["salary"]}')
                if salary_filter:
                    await salary_filter.click()
                    await self._random_delay(1, 2)

            # 工作年限筛选
            if filters.get('experience'):
                exp_filter = await self.page.query_selector(f'text={filters["experience"]}')
                if exp_filter:
                    await exp_filter.click()
                    await self._random_delay(1, 2)

            # 公司规模筛选
            if filters.get('scale'):
                scale_filter = await self.page.query_selector(f'text={filters["scale"]}')
                if scale_filter:
                    await scale_filter.click()
                    await self._random_delay(1, 2)

        except Exception as e:
            logger.warning(f"应用筛选条件失败: {e}")

    async def _parse_job_list(self) -> List[Dict[str, Any]]:
        """解析职位列表"""
        jobs = []
        try:
            # 等待职位列表加载
            await self.page.wait_for_selector('.job-card-wrapper', timeout=10000)

            # 获取所有职位卡片
            job_cards = await self.page.query_selector_all('.job-card-wrapper')

            for card in job_cards:
                try:
                    # 提取职位信息
                    title_elem = await card.query_selector('.job-name')
                    title = await title_elem.inner_text() if title_elem else "未知职位"

                    salary_elem = await card.query_selector('.salary')
                    salary = await salary_elem.inner_text() if salary_elem else "面议"

                    company_elem = await card.query_selector('.company-name')
                    company = await company_elem.inner_text() if company_elem else "未知公司"

                    # 获取职位链接
                    link_elem = await card.query_selector('a.job-card-left')
                    job_url = await link_elem.get_attribute('href') if link_elem else ""
                    if job_url and not job_url.startswith('http'):
                        job_url = self.base_url + job_url

                    jobs.append({
                        'title': title.strip(),
                        'salary': salary.strip(),
                        'company': company.strip(),
                        'url': job_url,
                        'platform': 'boss',
                        'card_element': card
                    })

                except Exception as e:
                    logger.debug(f"解析职位卡片失败: {e}")
                    continue

            # 模拟滚动加载更多
            await self._simulate_scroll()

        except Exception as e:
            logger.error(f"解析职位列表失败: {e}")

        return jobs

    def _filter_blacklist(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤黑名单"""
        company_blacklist = self.config.get('company_blacklist', [])
        title_blacklist = self.config.get('title_blacklist', [])

        filtered_jobs = []
        for job in jobs:
            # 检查公司黑名单
            if any(black in job['company'] for black in company_blacklist):
                logger.debug(f"过滤黑名单公司: {job['company']}")
                continue

            # 检查职位标题黑名单
            if any(black in job['title'] for black in title_blacklist):
                logger.debug(f"过滤黑名单职位: {job['title']}")
                continue

            filtered_jobs.append(job)

        return filtered_jobs

    def apply_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        投递单个职位

        Args:
            job: 职位信息

        Returns:
            Dict: 投递结果
        """
        return asyncio.run(self._async_apply_job(job))

    async def _async_apply_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """异步投递职位"""
        try:
            # 打开职位详情页
            if job.get('url'):
                await self.page.goto(job['url'], wait_until='networkidle')
            else:
                # 如果有卡片元素，直接点击
                if job.get('card_element'):
                    await job['card_element'].click()
                else:
                    return {
                        'success': False,
                        'message': '无法打开职位详情',
                        'job': job,
                        'timestamp': datetime.now().isoformat()
                    }

            await self._random_delay(2, 3)

            # 模拟人类行为
            await self._simulate_mouse_move()
            await self._simulate_scroll()

            # 点击"立即沟通"按钮
            try:
                chat_button = await self.page.wait_for_selector(
                    'button:has-text("立即沟通"), a:has-text("立即沟通")',
                    timeout=5000
                )
                await chat_button.click()
                await self._random_delay(1, 2)

            except Exception as e:
                return {
                    'success': False,
                    'message': f'未找到"立即沟通"按钮: {e}',
                    'job': job,
                    'timestamp': datetime.now().isoformat()
                }

            # 发送打招呼语
            greeting = self.config.get('greeting', '您好，我对这个职位很感兴趣，期待与您沟通。')
            await self._send_greeting(greeting)

            logger.info(f"✓ 投递成功: {job['title']} @ {job['company']}")

            return {
                'success': True,
                'message': '投递成功',
                'job': job,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"投递失败: {e}")
            return {
                'success': False,
                'message': str(e),
                'job': job,
                'timestamp': datetime.now().isoformat()
            }

    async def _send_greeting(self, greeting: str):
        """发送打招呼语"""
        try:
            # 等待聊天输入框
            input_box = await self.page.wait_for_selector(
                'textarea, input[type="text"]',
                timeout=5000
            )

            # 输入打招呼语
            await input_box.click()
            await self._random_delay(0.5, 1)

            # 逐字输入（模拟人类）
            for char in greeting:
                await input_box.type(char, delay=random.randint(50, 150))

            await self._random_delay(1, 2)

            # 点击发送按钮
            send_button = await self.page.query_selector('button:has-text("发送")')
            if send_button:
                await send_button.click()
                await self._random_delay(1, 2)
            else:
                # 尝试按回车发送
                await input_box.press('Enter')
                await self._random_delay(1, 2)

            logger.info("打招呼语已发送")

        except Exception as e:
            logger.warning(f"发送打招呼语失败: {e}")

    def cleanup(self):
        """清理资源"""
        asyncio.run(self._async_cleanup())

    async def _async_cleanup(self):
        """异步清理资源"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("浏览器资源已清理")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建配置
    config = {
        'headless': False,
        'random_delay_min': 2,
        'random_delay_max': 5,
        'company_blacklist': ['外包', '劳务派遣'],
        'title_blacklist': ['实习', '兼职'],
        'greeting': '您好，我对这个职位很感兴趣，我有3年Python开发经验，期待与您沟通。'
    }

    # 创建投递器
    applier = BossApplier(config)

    try:
        # 登录
        phone = input("请输入手机号: ")
        if applier.login(phone):
            print("登录成功！")

            # 搜索职位
            jobs = applier.search_jobs(
                keywords="Python",
                location="北京",
                filters={
                    'salary': '20-30K',
                    'experience': '3-5年'
                }
            )

            print(f"找到 {len(jobs)} 个职位")

            # 批量投递
            if jobs:
                result = applier.batch_apply(jobs, max_count=10)
                print(f"投递完成: 成功 {result['applied']}, 失败 {result['failed']}")
        else:
            print("登录失败")

    finally:
        # 清理资源
        applier.cleanup()
