"""
LinkedIn 自动投递器
整合自 GodsScion/Auto_job_applier_linkedIn 项目
"""

from typing import List, Dict, Any, Optional
import time
import random
import logging
from datetime import datetime

try:
    import undetected_chromedriver as uc
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import NoSuchElementException, TimeoutException
except ImportError:
    raise ImportError("请安装依赖: pip install selenium undetected-chromedriver")

from .base_applier import BaseApplier
from .session_manager import SessionManager
from .question_handler import QuestionHandler

logger = logging.getLogger(__name__)


class LinkedInApplier(BaseApplier):
    """LinkedIn 自动投递器"""

    def __init__(self, config: Dict[str, Any], llm_client=None):
        """
        初始化 LinkedIn 投递器

        Args:
            config: 配置字典
            llm_client: LLM 客户端（用于 AI 回答问题）
        """
        super().__init__(config)
        self.session_manager = SessionManager('linkedin')
        self.question_handler = QuestionHandler(llm_client, config.get('user_profile', {}))
        self.wait = None
        self.actions = None

    def _init_driver(self):
        """初始化浏览器驱动"""
        try:
            options = uc.ChromeOptions()

            # 配置选项
            if self.config.get('headless', False):
                options.add_argument('--headless')

            # 使用用户配置文件（保持登录状态）
            if self.config.get('use_profile', True) and self.config.get('profile_path'):
                options.add_argument(f'--user-data-dir={self.config["profile_path"]}')

            # 其他选项
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')

            # 创建驱动
            self.driver = uc.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, self.config.get('timeout', 30))
            self.actions = ActionChains(self.driver)

            logger.info("浏览器驱动初始化成功")
            return True

        except Exception as e:
            logger.error(f"初始化浏览器失败: {e}")
            return False

    def login(self, email: str, password: str) -> bool:
        """
        登录 LinkedIn

        Args:
            email: 邮箱
            password: 密码

        Returns:
            bool: 是否登录成功
        """
        try:
            if not self.driver:
                if not self._init_driver():
                    return False

            # 尝试加载已保存的会话
            self.driver.get("https://www.linkedin.com")
            time.sleep(2)

            if self.session_manager.load_cookies(self.driver, email):
                self.driver.refresh()
                time.sleep(3)

                # 检查是否已登录
                if self._is_logged_in():
                    logger.info("使用已保存的会话登录成功")
                    return True

            # 需要重新登录
            logger.info("开始登录 LinkedIn")
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)

            # 填写用户名
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.clear()
            username_field.send_keys(email)
            self._random_delay()

            # 填写密码
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            self._random_delay()

            # 点击登录按钮
            login_button = self.driver.find_element(
                By.XPATH, '//button[@type="submit"]'
            )
            login_button.click()

            # 等待登录完成
            time.sleep(5)

            # 检查是否需要验证
            if "checkpoint" in self.driver.current_url or "challenge" in self.driver.current_url:
                logger.warning("需要人工验证，请在浏览器中完成验证")
                # 等待用户完成验证（最多5分钟）
                for _ in range(60):
                    time.sleep(5)
                    if self._is_logged_in():
                        break

            # 验证登录状态
            if self._is_logged_in():
                logger.info("登录成功")
                # 保存会话
                self.session_manager.save_cookies(self.driver, email)
                return True
            else:
                logger.error("登录失败")
                return False

        except Exception as e:
            logger.exception(f"登录过程出错: {e}")
            return False

    def _is_logged_in(self) -> bool:
        """检查是否已登录"""
        try:
            # 检查是否在 feed 页面
            if "feed" in self.driver.current_url:
                return True

            # 检查是否有登录按钮
            try:
                self.driver.find_element(By.LINK_TEXT, "Sign in")
                return False
            except NoSuchElementException:
                return True

        except Exception:
            return False

    def search_jobs(self, keywords: str, location: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        搜索职位

        Args:
            keywords: 搜索关键词
            location: 工作地点
            filters: 筛选条件

        Returns:
            List[Dict]: 职位列表
        """
        try:
            if not self.driver:
                logger.error("浏览器未初始化")
                return []

            # 构建搜索 URL
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}"
            if location:
                search_url += f"&location={location}"

            # 添加 Easy Apply 过滤
            search_url += "&f_AL=true"  # Easy Apply only

            logger.info(f"搜索职位: {search_url}")
            self.driver.get(search_url)
            time.sleep(3)

            # 等待职位列表加载
            self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//li[@data-occludable-job-id]")
                )
            )

            # 获取所有职位
            job_elements = self.driver.find_elements(
                By.XPATH, "//li[@data-occludable-job-id]"
            )

            jobs = []
            for job_elem in job_elements[:50]:  # 限制最多50个
                try:
                    job_id = job_elem.get_attribute("data-occludable-job-id")
                    title_elem = job_elem.find_element(By.CLASS_NAME, "job-card-list__title")
                    company_elem = job_elem.find_element(By.CLASS_NAME, "job-card-container__company-name")
                    location_elem = job_elem.find_element(By.CLASS_NAME, "job-card-container__metadata-item")

                    job = {
                        'id': job_id,
                        'title': title_elem.text.strip(),
                        'company': company_elem.text.strip(),
                        'location': location_elem.text.strip(),
                        'url': f"https://www.linkedin.com/jobs/view/{job_id}",
                        'element': job_elem
                    }

                    # 应用过滤
                    if self._should_apply(job):
                        jobs.append(job)

                except Exception as e:
                    logger.warning(f"解析职位信息失败: {e}")
                    continue

            logger.info(f"找到 {len(jobs)} 个符合条件的职位")
            return jobs

        except Exception as e:
            logger.exception(f"搜索职位失败: {e}")
            return []

    def _should_apply(self, job: Dict[str, Any]) -> bool:
        """判断是否应该申请该职位"""
        # 检查公司黑名单
        blacklist = self.config.get('company_blacklist', [])
        if any(company.lower() in job['company'].lower() for company in blacklist):
            logger.info(f"跳过黑名单公司: {job['company']}")
            return False

        # 检查职位标题黑名单
        title_blacklist = self.config.get('title_blacklist', [])
        if any(keyword.lower() in job['title'].lower() for keyword in title_blacklist):
            logger.info(f"跳过黑名单职位: {job['title']}")
            return False

        # 检查白名单（如果设置了白名单，只申请白名单中的）
        whitelist = self.config.get('company_whitelist', [])
        if whitelist:
            if not any(company.lower() in job['company'].lower() for company in whitelist):
                return False

        return True

    def apply_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        申请单个职位

        Args:
            job: 职位信息

        Returns:
            Dict: 申请结果
        """
        try:
            logger.info(f"开始申请: {job['title']} @ {job['company']}")

            # 点击职位卡片
            if 'element' in job:
                job['element'].click()
            else:
                self.driver.get(job['url'])

            time.sleep(2)

            # 查找 Easy Apply 按钮
            try:
                easy_apply_button = self.wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(@class,'jobs-apply-button') and contains(., 'Easy Apply')]"
                    ))
                )
                easy_apply_button.click()
                time.sleep(2)
            except TimeoutException:
                return {
                    'success': False,
                    'message': '未找到 Easy Apply 按钮',
                    'job': job,
                    'timestamp': datetime.now().isoformat()
                }

            # 处理申请表单
            result = self._fill_application_form(job)

            self._random_delay()
            return result

        except Exception as e:
            logger.exception(f"申请职位失败: {e}")
            return {
                'success': False,
                'message': str(e),
                'job': job,
                'timestamp': datetime.now().isoformat()
            }

    def _fill_application_form(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """填写申请表单"""
        try:
            # 查找弹窗
            modal = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "jobs-easy-apply-modal"))
            )

            # 循环处理多页表单
            page_count = 0
            max_pages = 10

            while page_count < max_pages:
                page_count += 1
                logger.info(f"处理表单页面 {page_count}")

                # 回答问题
                self._answer_questions_in_modal(modal, job)

                time.sleep(1)

                # 查找下一步按钮
                try:
                    # 检查是否是最后一页（Review 按钮）
                    review_button = modal.find_element(
                        By.XPATH, './/button[contains(., "Review") or contains(., "Submit")]'
                    )

                    # 如果配置了提交前暂停
                    if self.config.get('pause_before_submit', False):
                        logger.info("提交前暂停，等待人工审核...")
                        input("按 Enter 继续提交...")

                    review_button.click()
                    time.sleep(2)

                    # 查找最终提交按钮
                    try:
                        submit_button = modal.find_element(
                            By.XPATH, './/button[contains(., "Submit application")]'
                        )
                        submit_button.click()
                        logger.info("✓ 申请已提交")

                        return {
                            'success': True,
                            'message': '申请成功',
                            'job': job,
                            'timestamp': datetime.now().isoformat()
                        }
                    except NoSuchElementException:
                        # 可能已经在 Review 页面直接提交了
                        time.sleep(2)
                        return {
                            'success': True,
                            'message': '申请成功',
                            'job': job,
                            'timestamp': datetime.now().isoformat()
                        }

                except NoSuchElementException:
                    # 还有下一页，点击 Next
                    try:
                        next_button = modal.find_element(
                            By.XPATH, './/button[contains(., "Next")]'
                        )
                        next_button.click()
                        time.sleep(2)
                    except NoSuchElementException:
                        logger.error("未找到 Next 或 Submit 按钮")
                        return {
                            'success': False,
                            'message': '表单导航失败',
                            'job': job,
                            'timestamp': datetime.now().isoformat()
                        }

            return {
                'success': False,
                'message': f'表单页面过多（>{max_pages}）',
                'job': job,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.exception(f"填写表单失败: {e}")
            return {
                'success': False,
                'message': str(e),
                'job': job,
                'timestamp': datetime.now().isoformat()
            }

    def _answer_questions_in_modal(self, modal, job: Dict[str, Any]):
        """回答弹窗中的问题"""
        try:
            # 获取所有表单元素
            questions = modal.find_elements(
                By.XPATH, ".//div[@data-test-form-element]"
            )

            for question_elem in questions:
                try:
                    # 获取问题标签
                    label_elem = question_elem.find_element(By.TAG_NAME, "label")
                    question_text = label_elem.text.strip()

                    if not question_text:
                        continue

                    # 处理下拉选择框
                    select_elem = self._try_find(question_elem, By.TAG_NAME, "select")
                    if select_elem:
                        answer = self.question_handler.answer_question(
                            question_text, "dropdown", job_context=job
                        )
                        if answer:
                            Select(select_elem).select_by_visible_text(answer)
                            logger.info(f"下拉选择: {question_text[:30]}... -> {answer}")
                        continue

                    # 处理单选按钮
                    radio_fieldset = self._try_find(
                        question_elem,
                        By.XPATH,
                        './/fieldset[@data-test-form-builder-radio-button-form-component="true"]'
                    )
                    if radio_fieldset:
                        # 获取所有选项
                        options = [opt.text for opt in radio_fieldset.find_elements(By.TAG_NAME, "label")]
                        answer = self.question_handler.answer_question(
                            question_text, "radio", options=options, job_context=job
                        )
                        if answer:
                            option_elem = radio_fieldset.find_element(
                                By.XPATH, f".//label[normalize-space()='{answer}']"
                            )
                            self.actions.move_to_element(option_elem).click().perform()
                            logger.info(f"单选: {question_text[:30]}... -> {answer}")
                        continue

                    # 处理文本输入框
                    text_input = self._try_find(question_elem, By.XPATH, ".//input[@type='text']")
                    if text_input:
                        answer = self.question_handler.answer_question(
                            question_text, "text", job_context=job
                        )
                        if answer:
                            text_input.clear()
                            text_input.send_keys(answer)
                            logger.info(f"文本输入: {question_text[:30]}... -> {answer[:30]}...")
                        continue

                    # 处理文本域
                    textarea = self._try_find(question_elem, By.TAG_NAME, "textarea")
                    if textarea:
                        answer = self.question_handler.answer_question(
                            question_text, "textarea", job_context=job
                        )
                        if answer:
                            textarea.clear()
                            textarea.send_keys(answer)
                            logger.info(f"文本域: {question_text[:30]}... -> {answer[:50]}...")
                        continue

                except Exception as e:
                    logger.warning(f"处理问题失败: {e}")
                    continue

        except Exception as e:
            logger.warning(f"回答问题时出错: {e}")

    def _try_find(self, parent, by, value):
        """尝试查找元素，失败返回 None"""
        try:
            return parent.find_element(by, value)
        except NoSuchElementException:
            return None

    def _random_delay(self):
        """随机延迟（模拟人类行为）"""
        min_delay = self.config.get('random_delay_min', 2)
        max_delay = self.config.get('random_delay_max', 5)
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
