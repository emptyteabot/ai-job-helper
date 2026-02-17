"""
智联招聘投递器测试用例
使用 pytest + unittest.mock 进行单元测试
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.auto_apply.zhilian_applier import ZhilianApplier


class TestZhilianApplier:
    """智联招聘投递器测试"""

    @pytest.fixture
    def config(self):
        """测试配置"""
        return {
            'platform': 'zhilian',
            'keywords': 'Python',
            'location': '上海',
            'blacklist_companies': ['外包公司', '劳务派遣'],
            'blacklist_keywords': ['实习', '兼职'],
            'min_salary': 15000,
            'max_salary': 50000
        }

    @pytest.fixture
    def applier(self, config):
        """创建投递器实例"""
        return ZhilianApplier(config)

    def test_init(self, applier, config):
        """测试初始化"""
        assert applier.config == config
        assert applier.applied_count == 0
        assert applier.failed_count == 0
        assert applier.BASE_URL == "https://www.zhaopin.com"
        assert applier.LOGIN_URL == "https://passport.zhaopin.com/login"
        assert applier.page is None
        assert applier.blacklist_companies == ['外包公司', '劳务派遣']
        assert applier.blacklist_keywords == ['实习', '兼职']
        assert applier.min_salary == 15000

    def test_config_values(self, applier):
        """测试配置值"""
        assert applier.config['platform'] == 'zhilian'
        assert applier.config['keywords'] == 'Python'
        assert applier.config['location'] == '上海'
        assert '外包公司' in applier.blacklist_companies
        assert '实习' in applier.blacklist_keywords

    def test_init_page(self, applier):
        """测试初始化页面"""
        with patch('app.services.auto_apply.zhilian_applier.ChromiumPage') as mock_page_class:
            mock_page = MagicMock()
            mock_page_class.return_value = mock_page

            applier._init_page()

            assert applier.page is not None
            mock_page.set.user_agent.assert_called_once()
            mock_page.set.timeouts.assert_called_once()

    def test_check_login_status_with_user_info(self, applier):
        """测试检查登录状态 - 有用户信息"""
        mock_page = MagicMock()
        mock_page.ele.return_value = MagicMock()  # 找到用户信息元素
        applier.page = mock_page

        result = applier._check_login_status()

        assert result is True

    def test_check_login_status_url_changed(self, applier):
        """测试检查登录状态 - URL已跳转"""
        mock_page = MagicMock()
        mock_page.ele.return_value = None  # 没有用户信息元素
        mock_page.url = 'https://www.zhaopin.com/home'  # 已跳转
        applier.page = mock_page

        result = applier._check_login_status()

        assert result is True

    def test_check_login_status_not_logged_in(self, applier):
        """测试检查登录状态 - 未登录"""
        mock_page = MagicMock()
        mock_page.ele.return_value = None
        mock_page.url = 'https://passport.zhaopin.com/login'
        applier.page = mock_page

        result = applier._check_login_status()

        assert result is False

    def test_should_apply_company_blacklist(self, applier):
        """测试黑名单过滤 - 公司黑名单"""
        job = {
            'title': 'Python开发',
            'company': '某外包公司',
            'salary': '20K'
        }

        result = applier._should_apply(job)

        assert result is False

    def test_should_apply_keyword_blacklist(self, applier):
        """测试黑名单过滤 - 关键词黑名单"""
        job = {
            'title': 'Python实习生',
            'company': '腾讯',
            'salary': '5K'
        }

        result = applier._should_apply(job)

        assert result is False

    def test_should_apply_salary_too_low(self, applier):
        """测试黑名单过滤 - 薪资过低"""
        job = {
            'title': 'Python开发',
            'company': '阿里巴巴',
            'salary': '10K-12K'
        }

        result = applier._should_apply(job)

        assert result is False

    def test_should_apply_salary_in_range(self, applier):
        """测试黑名单过滤 - 薪资符合"""
        job = {
            'title': 'Python开发',
            'company': '腾讯',
            'salary': '20K-30K'
        }

        result = applier._should_apply(job)

        assert result is True

    def test_should_apply_salary_negotiable(self, applier):
        """测试黑名单过滤 - 薪资面议"""
        job = {
            'title': 'Python开发',
            'company': '字节跳动',
            'salary': '面议'
        }

        result = applier._should_apply(job)

        assert result is True

    def test_should_apply_all_pass(self, applier):
        """测试黑名单过滤 - 全部通过"""
        job = {
            'title': 'Python高级开发工程师',
            'company': '百度',
            'salary': '25K-35K'
        }

        result = applier._should_apply(job)

        assert result is True

    def test_login_success(self, applier):
        """测试登录成功"""
        with patch.object(applier, '_init_page'):
            with patch.object(applier, '_check_login_status', return_value=True):
                mock_page = MagicMock()
                mock_page.get = MagicMock()
                mock_page.ele = MagicMock(return_value=MagicMock())
                applier.page = mock_page

                result = applier.login('test@example.com', 'password123')

                assert result is True

    def test_login_failure(self, applier):
        """测试登录失败"""
        with patch.object(applier, '_init_page'):
            with patch.object(applier, '_check_login_status', return_value=False):
                mock_page = MagicMock()
                mock_page.get = MagicMock()
                mock_page.ele = MagicMock(return_value=MagicMock())
                applier.page = mock_page

                result = applier.login('test@example.com', 'wrong_password')

                assert result is False

    def test_search_jobs_success(self, applier):
        """测试搜索职位成功"""
        with patch.object(applier, '_init_page'):
            mock_page = MagicMock()

            # Mock 职位元素
            mock_job1 = MagicMock()
            mock_job1.ele.side_effect = lambda sel: {
                '.joblist-box__job-title': MagicMock(text='Python开发工程师', attr=lambda x: 'http://test.com/job1'),
                '.joblist-box__company-name': MagicMock(text='腾讯'),
                '.joblist-box__job-salary': MagicMock(text='20K-30K'),
                '.joblist-box__job-location': MagicMock(text='上海')
            }.get(sel)

            mock_page.get = MagicMock()
            mock_page.wait.ele_displayed = MagicMock()
            mock_page.eles.return_value = [mock_job1]
            applier.page = mock_page

            jobs = applier.search_jobs('Python', '上海', {})

            assert len(jobs) == 1
            assert jobs[0]['title'] == 'Python开发工程师'
            assert jobs[0]['company'] == '腾讯'
            assert jobs[0]['platform'] == 'zhilian'

    def test_search_jobs_with_filters(self, applier):
        """测试带筛选条件的搜索"""
        with patch.object(applier, '_init_page'):
            mock_page = MagicMock()
            mock_page.get = MagicMock()
            mock_page.wait.ele_displayed = MagicMock()
            mock_page.eles.return_value = []
            applier.page = mock_page

            filters = {
                'salary_range': '10001-15000',
                'work_experience': '1-3年',
                'education': '本科'
            }

            jobs = applier.search_jobs('Python', '北京', filters)

            # 验证 URL 包含筛选参数
            call_args = mock_page.get.call_args[0][0]
            assert 'sl=10001-15000' in call_args
            assert 'gj=1-3年' in call_args
            assert 'xl=本科' in call_args

    def test_apply_job_success(self, applier):
        """测试投递职位成功"""
        with patch.object(applier, '_init_page'):
            mock_page = MagicMock()

            # Mock 申请按钮
            mock_apply_btn = MagicMock()
            mock_apply_btn.text = '申请职位'
            mock_apply_btn.click = MagicMock()

            # Mock 成功提示
            mock_success_tip = MagicMock()

            mock_page.get = MagicMock()
            mock_page.ele.side_effect = [
                mock_apply_btn,  # 第一次调用返回申请按钮
                None,  # 简历选择器
                None,  # 确认按钮
                mock_success_tip  # 成功提示
            ]

            applier.page = mock_page

            job = {
                'title': 'Python开发',
                'company': '腾讯',
                'url': 'http://test.com/job1'
            }

            result = applier.apply_job(job)

            assert result['success'] is True
            assert result['message'] == '投递成功'
            assert result['job'] == job

    def test_apply_job_already_applied(self, applier):
        """测试投递已投递的职位"""
        with patch.object(applier, '_init_page'):
            mock_page = MagicMock()

            # Mock 已投递按钮
            mock_apply_btn = MagicMock()
            mock_apply_btn.text = '已投递'

            mock_page.get = MagicMock()
            mock_page.ele.return_value = mock_apply_btn
            applier.page = mock_page

            job = {
                'title': 'Python开发',
                'company': '阿里巴巴',
                'url': 'http://test.com/job2'
            }

            result = applier.apply_job(job)

            assert result['success'] is False
            assert '已投递' in result['message']

    def test_apply_job_no_button(self, applier):
        """测试投递职位 - 找不到按钮"""
        with patch.object(applier, '_init_page'):
            mock_page = MagicMock()
            mock_page.get = MagicMock()
            mock_page.ele.return_value = None  # 找不到按钮
            applier.page = mock_page

            job = {
                'title': 'Python开发',
                'company': '百度',
                'url': 'http://test.com/job3'
            }

            result = applier.apply_job(job)

            assert result['success'] is False
            assert '未找到申请按钮' in result['message']

    def test_upload_resume_success(self, applier):
        """测试上传简历成功"""
        with patch.object(applier, '_init_page'):
            mock_page = MagicMock()

            # Mock 上传按钮和文件输入框
            mock_upload_btn = MagicMock()
            mock_file_input = MagicMock()
            mock_success_tip = MagicMock()

            mock_page.get = MagicMock()
            mock_page.ele.side_effect = [
                mock_upload_btn,  # 上传按钮
                mock_file_input,  # 文件输入框
                mock_success_tip  # 成功提示
            ]

            applier.page = mock_page

            result = applier.upload_resume('/path/to/resume.pdf')

            assert result is True
            mock_file_input.input.assert_called_once_with('/path/to/resume.pdf')

    def test_upload_resume_no_button(self, applier):
        """测试上传简历 - 找不到按钮"""
        with patch.object(applier, '_init_page'):
            mock_page = MagicMock()
            mock_page.get = MagicMock()
            mock_page.ele.return_value = None  # 找不到上传按钮
            applier.page = mock_page

            result = applier.upload_resume('/path/to/resume.pdf')

            assert result is False

    def test_batch_apply(self, applier):
        """测试批量投递"""
        jobs = [
            {'title': 'Job 1', 'company': 'Company 1', 'url': 'http://test.com/1'},
            {'title': 'Job 2', 'company': 'Company 2', 'url': 'http://test.com/2'},
            {'title': 'Job 3', 'company': 'Company 3', 'url': 'http://test.com/3'},
        ]

        # Mock apply_job
        def mock_apply(job):
            return {
                'success': True,
                'message': '投递成功',
                'job': job,
                'timestamp': datetime.now().isoformat()
            }

        with patch.object(applier, 'apply_job', side_effect=mock_apply):
            result = applier.batch_apply(jobs, max_count=2)

            assert result['applied'] == 2
            assert result['failed'] == 0
            assert result['total_attempted'] == 2

    def test_cleanup(self, applier):
        """测试资源清理"""
        mock_page = MagicMock()
        mock_page.quit = MagicMock()
        applier.page = mock_page

        applier.cleanup()

        mock_page.quit.assert_called_once()
        assert applier.page is None


class TestZhilianApplierEdgeCases:
    """智联招聘投递器边界测试"""

    @pytest.fixture
    def applier(self):
        config = {
            'platform': 'zhilian',
            'blacklist_companies': [],
            'blacklist_keywords': [],
            'min_salary': 0,
            'max_salary': 999999
        }
        return ZhilianApplier(config)

    def test_should_apply_empty_blacklist(self, applier):
        """测试空黑名单"""
        job = {
            'title': 'Python开发',
            'company': '任意公司',
            'salary': '10K'
        }

        result = applier._should_apply(job)

        assert result is True

    def test_should_apply_missing_fields(self, applier):
        """测试缺少字段的职位"""
        job = {'title': 'Python开发'}  # 缺少 company 和 salary

        result = applier._should_apply(job)

        assert result is True

    def test_should_apply_invalid_salary_format(self, applier):
        """测试无效的薪资格式"""
        job = {
            'title': 'Python开发',
            'company': '腾讯',
            'salary': '薪资面议'
        }

        result = applier._should_apply(job)

        assert result is True

    def test_should_apply_salary_with_k(self, applier):
        """测试带 K 的薪资格式"""
        applier.min_salary = 15000
        job = {
            'title': 'Python开发',
            'company': '阿里巴巴',
            'salary': '20K-30K'
        }

        result = applier._should_apply(job)

        assert result is True

    def test_should_apply_salary_without_range(self, applier):
        """测试没有范围的薪资"""
        job = {
            'title': 'Python开发',
            'company': '百度',
            'salary': '25K'
        }

        result = applier._should_apply(job)

        assert result is True

    def test_search_jobs_empty_result(self, applier):
        """测试搜索结果为空"""
        with patch.object(applier, '_init_page'):
            mock_page = MagicMock()
            mock_page.get = MagicMock()
            mock_page.wait.ele_displayed = MagicMock()
            mock_page.eles.return_value = []  # 空结果
            applier.page = mock_page

            jobs = applier.search_jobs('不存在的职位', '火星', {})

            assert len(jobs) == 0

    def test_apply_job_exception(self, applier):
        """测试投递职位异常"""
        with patch.object(applier, '_init_page'):
            mock_page = MagicMock()
            mock_page.get.side_effect = Exception('网络错误')
            applier.page = mock_page

            job = {'title': 'Test Job', 'url': 'http://test.com'}

            result = applier.apply_job(job)

            assert result['success'] is False
            assert '网络错误' in result['message']


class TestZhilianApplierPerformance:
    """智联招聘投递器性能测试"""

    @pytest.fixture
    def applier(self):
        config = {
            'platform': 'zhilian',
            'blacklist_companies': ['外包'] * 100,
            'blacklist_keywords': ['实习'] * 100,
            'min_salary': 10000
        }
        return ZhilianApplier(config)

    def test_should_apply_performance(self, applier):
        """测试黑名单过滤性能"""
        import time

        job = {
            'title': 'Python高级开发工程师',
            'company': '腾讯科技有限公司',
            'salary': '25K-35K'
        }

        start = time.time()
        for _ in range(1000):
            applier._should_apply(job)
        elapsed = time.time() - start

        # 1000 次过滤应该在 0.1 秒内完成
        assert elapsed < 0.1

    def test_batch_filter_performance(self, applier):
        """测试批量过滤性能"""
        import time

        jobs = [
            {
                'title': f'Python开发{i}',
                'company': f'公司{i}',
                'salary': '20K-30K'
            }
            for i in range(1000)
        ]

        start = time.time()
        filtered = [job for job in jobs if applier._should_apply(job)]
        elapsed = time.time() - start

        # 过滤 1000 个职位应该在 0.5 秒内完成
        assert elapsed < 0.5
        assert len(filtered) == 1000


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
