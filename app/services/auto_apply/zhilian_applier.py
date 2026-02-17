"""
智联招聘自动投递器
使用 DrissionPage 实现高速自动化投递
"""

from typing import List, Dict, Any, Optional
import logging
import time
from datetime import datetime
from DrissionPage import ChromiumPage
from DrissionPage.errors import ElementNotFoundError, WaitTimeoutError

from .base_applier import BaseApplier
from .session_manager import SessionManager

logger = logging.getLogger(__name__)


class ZhilianApplier(BaseApplier):
    """智联招聘自动投递器"""

    # 智联招聘 URL
    BASE_URL = "https://www.zhaopin.com"
    LOGIN_URL = "https://passport.zhaopin.com/login"
    SEARCH_URL = "https://www.zhaopin.com/sou"
    RESUME_URL = "https://i.zhaopin.com/resume/manage"

    def __init__(self, config: Dict[str, Any]):
        """
        初始化智联招聘投递器

        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.page: Optional[ChromiumPage] = None
        self.session_manager = SessionManager('zhilian')
        self.blacklist_companies = config.get('blacklist_companies', [])
        self.blacklist_keywords = config.get('blacklist_keywords', [])
        self.min_salary = config.get('min_salary', 0)
        self.max_salary = config.get('max_salary', 999999)

    def _init_page(self):
        """初始化 DrissionPage 页面"""
        try:
            if self.page:
                return

            logger.info("正在初始化 DrissionPage...")
            self.page = ChromiumPage()

            # 配置反爬虫
            self.page.set.user_agent(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            # 设置超时
            self.page.set.timeouts(base=10, page_load=30)

            logger.info("DrissionPage 初始化成功")

        except Exception as e:
            logger.error(f"初始化 DrissionPage 失败: {e}")
            raise

    def login(self, username: str, password: str) -> bool:
        """
        登录智联招聘

        Args:
            username: 用户名（手机号/邮箱）
            password: 密码

        Returns:
            bool: 登录是否成功
        """
        try:
            self._init_page()

            # 检查是否已有有效会话
            if self.session_manager.is_session_valid(username):
                logger.info("检测到有效会话，尝试使用缓存登录...")
                self.page.get(self.BASE_URL)
                if self.session_manager.load_cookies(self.page, username):
                    self.page.refresh()
                    time.sleep(2)

                    # 验证登录状态
                    if self._check_login_status():
                        logger.info("✓ 使用缓存登录成功")
                        return True
                    else:
                        logger.info("缓存会话已失效，需要重新登录")

            # 打开登录页
            logger.info("正在打开登录页...")
            self.page.get(self.LOGIN_URL)
            time.sleep(2)

            # 切换到账号密码登录
            try:
                password_tab = self.page.ele('text:密码登录')
                if password_tab:
                    password_tab.click()
                    time.sleep(1)
            except:
                pass

            # 输入账号
            logger.info("正在输入账号...")
            username_input = self.page.ele('#loginname') or self.page.ele('@@placeholder=请输入手机号/邮箱')
            if not username_input:
                raise Exception("未找到用户名输入框")
            username_input.input(username)
            time.sleep(0.5)

            # 输入密码
            logger.info("正在输入密码...")
            password_input = self.page.ele('#password') or self.page.ele('@@type=password')
            if not password_input:
                raise Exception("未找到密码输入框")
            password_input.input(password)
            time.sleep(0.5)

            # 点击登录按钮
            logger.info("正在点击登录按钮...")
            login_btn = self.page.ele('.submit-btn') or self.page.ele('text:登录')
            if not login_btn:
                raise Exception("未找到登录按钮")
            login_btn.click()

            # 等待登录完成（URL 变化或出现用户信息）
            logger.info("等待登录完成...")
            time.sleep(3)

            # 检查是否需要验证码
            if self._handle_captcha():
                logger.info("已处理验证码")
                time.sleep(2)

            # 验证登录状态
            if self._check_login_status():
                logger.info("✓ 登录成功")
                # 保存 Cookie
                self.session_manager.save_cookies(self.page, username)
                return True
            else:
                logger.error("✗ 登录失败，请检查账号密码")
                return False

        except Exception as e:
            logger.error(f"登录过程出错: {e}")
            return False

    def _check_login_status(self) -> bool:
        """
        检查登录状态

        Returns:
            bool: 是否已登录
        """
        try:
            # 检查是否有用户信息元素
            user_info = self.page.ele('.user-info') or self.page.ele('.user-name') or self.page.ele('.avatar')
            if user_info:
                return True

            # 检查 URL 是否跳转
            current_url = self.page.url
            if 'passport.zhaopin.com' not in current_url:
                return True

            return False

        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False

    def _handle_captcha(self) -> bool:
        """
        处理验证码（如果有）

        Returns:
            bool: 是否处理了验证码
        """
        try:
            # 检查是否有滑块验证码
            captcha = self.page.ele('.captcha') or self.page.ele('.verify-code')
            if captcha:
                logger.warning("检测到验证码，需要手动处理")
                logger.info("请在 30 秒内完成验证码验证...")
                time.sleep(30)
                return True

            return False

        except Exception as e:
            logger.error(f"处理验证码失败: {e}")
            return False

    def search_jobs(self, keywords: str, location: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        搜索职位

        Args:
            keywords: 搜索关键词
            location: 工作地点
            filters: 筛选条件 {
                'salary_range': '10001-15000',  # 薪资范围
                'company_type': '上市公司',      # 公司类型
                'work_experience': '1-3年',     # 工作经验
                'education': '本科',            # 学历要求
            }

        Returns:
            List[Dict]: 职位列表
        """
        try:
            self._init_page()

            # 构建搜索 URL
            search_params = {
                'jl': location,  # 工作地点
                'kw': keywords,  # 关键词
            }

            # 添加筛选条件
            if filters.get('salary_range'):
                search_params['sl'] = filters['salary_range']
            if filters.get('work_experience'):
                search_params['gj'] = filters['work_experience']
            if filters.get('education'):
                search_params['xl'] = filters['education']

            # 构建 URL
            url = f"{self.SEARCH_URL}?"
            url += "&".join([f"{k}={v}" for k, v in search_params.items()])

            logger.info(f"正在搜索职位: {url}")
            self.page.get(url)
            time.sleep(2)

            # 等待职位列表加载
            self.page.wait.ele_displayed('.joblist-box', timeout=10)

            # 解析职位列表
            jobs = []
            job_elements = self.page.eles('.joblist-box__item')

            logger.info(f"找到 {len(job_elements)} 个职位")

            for idx, job_elem in enumerate(job_elements):
                try:
                    # 提取职位信息
                    title_elem = job_elem.ele('.joblist-box__job-title')
                    company_elem = job_elem.ele('.joblist-box__company-name')
                    salary_elem = job_elem.ele('.joblist-box__job-salary')
                    location_elem = job_elem.ele('.joblist-box__job-location')

                    if not all([title_elem, company_elem, salary_elem, location_elem]):
                        continue

                    job = {
                        'title': title_elem.text.strip(),
                        'company': company_elem.text.strip(),
                        'salary': salary_elem.text.strip(),
                        'location': location_elem.text.strip(),
                        'url': title_elem.attr('href') or title_elem.parent().attr('href'),
                        'platform': 'zhilian',
                        'search_keywords': keywords,
                        'search_location': location
                    }

                    # 过滤黑名单
                    if self._should_apply(job):
                        jobs.append(job)
                        logger.info(f"  [{idx+1}] {job['title']} - {job['company']} - {job['salary']}")
                    else:
                        logger.info(f"  [{idx+1}] 已过滤: {job['title']} - {job['company']}")

                except Exception as e:
                    logger.warning(f"解析职位 {idx+1} 失败: {e}")
                    continue

            logger.info(f"✓ 搜索完成，找到 {len(jobs)} 个符合条件的职位")
            return jobs

        except Exception as e:
            logger.error(f"搜索职位失败: {e}")
            return []

    def apply_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        投递单个职位

        Args:
            job: 职位信息字典

        Returns:
            Dict: 投递结果 {'success': bool, 'message': str, 'job': dict}
        """
        try:
            # 打开职位详情页
            logger.info(f"正在打开职位: {job['title']}")
            self.page.get(job['url'])
            time.sleep(2)

            # 查找"申请职位"按钮
            apply_btn = (
                self.page.ele('.apply-btn') or
                self.page.ele('text:申请职位') or
                self.page.ele('text:立即申请') or
                self.page.ele('.btn-apply')
            )

            if not apply_btn:
                return {
                    'success': False,
                    'message': '未找到申请按钮（可能已投递或职位已关闭）',
                    'job': job,
                    'timestamp': datetime.now().isoformat()
                }

            # 检查按钮状态
            btn_text = apply_btn.text.strip()
            if '已投递' in btn_text or '已申请' in btn_text:
                return {
                    'success': False,
                    'message': '该职位已投递过',
                    'job': job,
                    'timestamp': datetime.now().isoformat()
                }

            # 点击申请按钮
            logger.info("正在点击申请按钮...")
            apply_btn.click()
            time.sleep(2)

            # 处理简历选择（如果有多个简历）
            resume_selector = self.page.ele('.resume-selector') or self.page.ele('.resume-list')
            if resume_selector:
                logger.info("检测到简历选择器，选择第一个简历...")
                first_resume = self.page.ele('.resume-item:first-child') or self.page.ele('.resume-card:first-child')
                if first_resume:
                    first_resume.click()
                    time.sleep(1)

            # 查找确认投递按钮
            confirm_btn = (
                self.page.ele('.confirm-apply') or
                self.page.ele('text:确认投递') or
                self.page.ele('text:确定') or
                self.page.ele('.btn-confirm')
            )

            if confirm_btn:
                logger.info("正在确认投递...")
                confirm_btn.click()
                time.sleep(2)

            # 检查投递结果
            success_tip = (
                self.page.ele('.success-tip') or
                self.page.ele('text:投递成功') or
                self.page.ele('text:申请成功')
            )

            if success_tip:
                logger.info(f"✓ 投递成功: {job['title']}")
                return {
                    'success': True,
                    'message': '投递成功',
                    'job': job,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # 没有明确的成功提示，但也没有错误，认为成功
                logger.info(f"✓ 投递完成: {job['title']}")
                return {
                    'success': True,
                    'message': '投递完成',
                    'job': job,
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"投递失败: {e}")
            return {
                'success': False,
                'message': f'投递异常: {str(e)}',
                'job': job,
                'timestamp': datetime.now().isoformat()
            }

    def upload_resume(self, resume_path: str) -> bool:
        """
        上传简历到智联招聘

        Args:
            resume_path: 简历文件路径（支持 PDF、DOC、DOCX）

        Returns:
            bool: 上传是否成功
        """
        try:
            self._init_page()

            # 打开简历管理页
            logger.info("正在打开简历管理页...")
            self.page.get(self.RESUME_URL)
            time.sleep(2)

            # 查找上传按钮
            upload_btn = (
                self.page.ele('.upload-btn') or
                self.page.ele('text:上传简历') or
                self.page.ele('text:添加简历')
            )

            if not upload_btn:
                raise Exception("未找到上传按钮")

            upload_btn.click()
            time.sleep(1)

            # 查找文件输入框
            file_input = self.page.ele('input[type="file"]')
            if not file_input:
                raise Exception("未找到文件输入框")

            # 上传文件
            logger.info(f"正在上传简历: {resume_path}")
            file_input.input(resume_path)
            time.sleep(3)

            # 等待上传完成
            success_tip = self.page.ele('.upload-success') or self.page.ele('text:上传成功')
            if success_tip:
                logger.info("✓ 简历上传成功")
                return True
            else:
                logger.warning("未检测到上传成功提示，但可能已上传")
                return True

        except Exception as e:
            logger.error(f"上传简历失败: {e}")
            return False

    def _should_apply(self, job: Dict[str, Any]) -> bool:
        """
        判断是否应该投递该职位（黑名单过滤）

        Args:
            job: 职位信息

        Returns:
            bool: 是否应该投递
        """
        # 检查公司黑名单
        company = job.get('company', '').lower()
        for blacklist_company in self.blacklist_companies:
            if blacklist_company.lower() in company:
                logger.info(f"公司在黑名单中: {job['company']}")
                return False

        # 检查关键词黑名单
        title = job.get('title', '').lower()
        for blacklist_keyword in self.blacklist_keywords:
            if blacklist_keyword.lower() in title:
                logger.info(f"职位标题包含黑名单关键词: {blacklist_keyword}")
                return False

        # 检查薪资范围（如果有）
        salary = job.get('salary', '')
        if salary and salary != '面议':
            try:
                # 解析薪资（例如：10K-15K、10000-15000）
                salary_clean = salary.replace('K', '000').replace('k', '000')
                if '-' in salary_clean:
                    min_sal, max_sal = salary_clean.split('-')
                    min_sal = int(''.join(filter(str.isdigit, min_sal)))
                    max_sal = int(''.join(filter(str.isdigit, max_sal)))

                    # 检查薪资是否在范围内
                    if max_sal < self.min_salary:
                        logger.info(f"薪资过低: {salary}")
                        return False
            except:
                pass

        return True

    def cleanup(self):
        """清理资源"""
        if self.page:
            try:
                self.page.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器失败: {e}")
        self.page = None
