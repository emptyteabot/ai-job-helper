"""
Boss直聘投递器测试用例
使用 pytest + unittest.mock 进行单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
from app.services.auto_apply.boss_applier import BossApplier


class TestBossApplier:
    """Boss直聘投递器测试"""

    @pytest.fixture
    def config(self):
        """测试配置"""
        return {
            'platform': 'boss',
            'max_apply_per_session': 50,
            'keywords': 'Python开发',
            'location': '北京',
            'headless': True,
            'random_delay_min': 0.1,
            'random_delay_max': 0.2,
            'company_blacklist': ['外包', '劳务派遣'],
            'title_blacklist': ['实习', '兼职'],
            'greeting': '您好，我对这个职位很感兴趣。'
        }

    @pytest.fixture
    def applier(self, config):
        """创建投递器实例"""
        return BossApplier(config)

    def test_init(self, applier, config):
        """测试初始化"""
        assert applier.config == config
        assert applier.applied_count == 0
        assert applier.failed_count == 0
        assert applier.base_url == "https://www.zhipin.com"
        assert applier.login_url == "https://login.zhipin.com/"
        assert applier.browser is None
        assert applier.page is None

    def test_config_values(self, applier):
        """测试配置值"""
        assert applier.config['platform'] == 'boss'
        assert applier.config['max_apply_per_session'] == 50
        assert applier.config['keywords'] == 'Python开发'
        assert '外包' in applier.config['company_blacklist']
        assert '实习' in applier.config['title_blacklist']

    @pytest.mark.asyncio
    async def test_init_browser(self, applier):
        """测试浏览器初始化"""
        with patch('app.services.auto_apply.boss_applier.async_playwright') as mock_playwright:
            # Mock Playwright 对象
            mock_pw = MagicMock()
            mock_browser = MagicMock()
            mock_context = MagicMock()
            mock_page = MagicMock()

            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)
            mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_context.new_page = AsyncMock(return_value=mock_page)

            # Mock stealth_async
            with patch('app.services.auto_apply.boss_applier.stealth_async', new_callable=AsyncMock):
                result = await applier._init_browser()
                assert result is True
                assert applier.browser is not None

    def test_generate_human_track(self, applier):
        """测试生成人类拖动轨迹"""
        distance = 260
        tracks = applier._generate_human_track(distance)

        assert isinstance(tracks, list)
        assert len(tracks) > 0
        assert all(isinstance(t, int) for t in tracks)
        # 总距离应该接近目标距离
        total = sum(tracks)
        assert abs(total - distance) < 50  # 允许一定误差

    def test_filter_blacklist_company(self, applier):
        """测试公司黑名单过滤"""
        jobs = [
            {'title': 'Python开发', 'company': '某外包公司', 'salary': '15-20K'},
            {'title': 'Python开发', 'company': '字节跳动', 'salary': '20-30K'},
            {'title': 'Python开发', 'company': '劳务派遣有限公司', 'salary': '10-15K'},
        ]

        filtered = applier._filter_blacklist(jobs)

        # 只有字节跳动应该通过
        assert len(filtered) == 1
        assert filtered[0]['company'] == '字节跳动'

    def test_filter_blacklist_title(self, applier):
        """测试职位标题黑名单过滤"""
        jobs = [
            {'title': 'Python实习生', 'company': '腾讯', 'salary': '5-8K'},
            {'title': 'Python开发工程师', 'company': '阿里巴巴', 'salary': '20-30K'},
            {'title': 'Python兼职开发', 'company': '百度', 'salary': '10-15K'},
        ]

        filtered = applier._filter_blacklist(jobs)

        # 只有阿里巴巴应该通过
        assert len(filtered) == 1
        assert filtered[0]['company'] == '阿里巴巴'

    def test_filter_blacklist_all_pass(self, applier):
        """测试黑名单过滤 - 全部通过"""
        jobs = [
            {'title': 'Python开发', 'company': '腾讯', 'salary': '20-30K'},
            {'title': 'Java开发', 'company': '阿里巴巴', 'salary': '25-35K'},
        ]

        filtered = applier._filter_blacklist(jobs)

        assert len(filtered) == 2

    @pytest.mark.asyncio
    async def test_random_delay(self, applier):
        """测试随机延迟"""
        import time
        start = time.time()
        await applier._random_delay(0.1, 0.2)
        elapsed = time.time() - start

        # 延迟应该在 0.1 到 0.2 秒之间
        assert 0.1 <= elapsed <= 0.3  # 允许一点误差

    @pytest.mark.asyncio
    async def test_simulate_mouse_move(self, applier):
        """测试模拟鼠标移动"""
        mock_page = MagicMock()
        mock_page.mouse.move = AsyncMock()
        applier.page = mock_page

        await applier._simulate_mouse_move()

        # 验证鼠标移动被调用
        mock_page.mouse.move.assert_called_once()

    @pytest.mark.asyncio
    async def test_simulate_scroll(self, applier):
        """测试模拟页面滚动"""
        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock()
        applier.page = mock_page

        await applier._simulate_scroll()

        # 验证滚动被调用
        mock_page.evaluate.assert_called_once()

    def test_login_sync_wrapper(self, applier):
        """测试登录同步包装器"""
        with patch.object(applier, '_async_login', return_value=True) as mock_login:
            with patch('asyncio.run', return_value=True):
                result = applier.login('13800138000')
                # 由于 asyncio.run 被 mock，这里只验证调用
                assert result is True

    @pytest.mark.asyncio
    async def test_parse_job_list(self, applier):
        """测试解析职位列表"""
        # Mock 页面和职位卡片
        mock_page = MagicMock()
        mock_card1 = MagicMock()
        mock_card2 = MagicMock()

        # Mock 职位信息元素
        mock_title1 = MagicMock()
        mock_title1.inner_text = AsyncMock(return_value='Python开发工程师')
        mock_salary1 = MagicMock()
        mock_salary1.inner_text = AsyncMock(return_value='20-30K')
        mock_company1 = MagicMock()
        mock_company1.inner_text = AsyncMock(return_value='腾讯')
        mock_link1 = MagicMock()
        mock_link1.get_attribute = AsyncMock(return_value='/job_detail/123')

        mock_card1.query_selector = AsyncMock(side_effect=lambda sel: {
            '.job-name': mock_title1,
            '.salary': mock_salary1,
            '.company-name': mock_company1,
            'a.job-card-left': mock_link1
        }.get(sel))

        mock_page.wait_for_selector = AsyncMock()
        mock_page.query_selector_all = AsyncMock(return_value=[mock_card1])

        applier.page = mock_page

        jobs = await applier._parse_job_list()

        assert len(jobs) == 1
        assert jobs[0]['title'] == 'Python开发工程师'
        assert jobs[0]['salary'] == '20-30K'
        assert jobs[0]['company'] == '腾讯'
        assert jobs[0]['platform'] == 'boss'

    def test_batch_apply_integration(self, applier):
        """测试批量投递（集成测试）"""
        jobs = [
            {'id': '1', 'title': 'Python开发', 'company': '公司A', 'url': 'http://test.com/1'},
            {'id': '2', 'title': 'Java开发', 'company': '公司B', 'url': 'http://test.com/2'},
            {'id': '3', 'title': 'Go开发', 'company': '公司C', 'url': 'http://test.com/3'},
        ]

        # Mock apply_job 方法
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
            assert result['success_rate'] == 1.0

    def test_batch_apply_with_failures(self, applier):
        """测试批量投递（包含失败）"""
        jobs = [
            {'id': '1', 'title': 'Job 1'},
            {'id': '2', 'title': 'Job 2'},
            {'id': '3', 'title': 'Job 3'},
        ]

        # Mock apply_job - 第二个失败
        def mock_apply(job):
            if job['id'] == '2':
                return {
                    'success': False,
                    'message': '投递失败',
                    'job': job,
                    'timestamp': datetime.now().isoformat()
                }
            return {
                'success': True,
                'message': '投递成功',
                'job': job,
                'timestamp': datetime.now().isoformat()
            }

        with patch.object(applier, 'apply_job', side_effect=mock_apply):
            result = applier.batch_apply(jobs, max_count=10)

            assert result['applied'] == 2
            assert result['failed'] == 1
            assert result['total_attempted'] == 3
            assert result['success_rate'] == pytest.approx(0.666, 0.01)

    def test_stop(self, applier):
        """测试停止投递"""
        applier.is_running = True
        applier.stop()
        assert applier.is_running is False

    def test_get_status(self, applier):
        """测试获取状态"""
        applier.applied_count = 10
        applier.failed_count = 2
        applier.is_running = True

        status = applier.get_status()

        assert status['applied_count'] == 10
        assert status['failed_count'] == 2
        assert status['is_running'] is True
        assert status['total_history'] == 0

    def test_get_history(self, applier):
        """测试获取历史记录"""
        # 添加一些历史记录
        applier._save_history({'success': True, 'job': {'title': 'Job 1'}})
        applier._save_history({'success': False, 'job': {'title': 'Job 2'}})

        history = applier.get_history()

        assert len(history) == 2
        assert history[0]['success'] is True
        assert history[1]['success'] is False

    @pytest.mark.asyncio
    async def test_cleanup(self, applier):
        """测试资源清理"""
        # Mock 浏览器对象
        mock_page = MagicMock()
        mock_page.close = AsyncMock()
        mock_context = MagicMock()
        mock_context.close = AsyncMock()
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()
        mock_playwright = MagicMock()
        mock_playwright.stop = AsyncMock()

        applier.page = mock_page
        applier.context = mock_context
        applier.browser = mock_browser
        applier.playwright = mock_playwright

        await applier._async_cleanup()

        # 验证所有资源都被清理
        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()


class TestBossApplierEdgeCases:
    """Boss直聘投递器边界测试"""

    @pytest.fixture
    def applier(self):
        config = {
            'platform': 'boss',
            'company_blacklist': [],
            'title_blacklist': []
        }
        return BossApplier(config)

    def test_empty_job_list(self, applier):
        """测试空职位列表"""
        jobs = []
        filtered = applier._filter_blacklist(jobs)
        assert len(filtered) == 0

    def test_job_without_company(self, applier):
        """测试没有公司信息的职位"""
        jobs = [{'title': 'Python开发', 'salary': '20K'}]
        filtered = applier._filter_blacklist(jobs)
        assert len(filtered) == 1

    def test_job_without_title(self, applier):
        """测试没有标题的职位"""
        jobs = [{'company': '腾讯', 'salary': '20K'}]
        filtered = applier._filter_blacklist(jobs)
        assert len(filtered) == 1

    def test_generate_track_zero_distance(self, applier):
        """测试生成零距离轨迹"""
        tracks = applier._generate_human_track(0)
        assert isinstance(tracks, list)

    def test_generate_track_negative_distance(self, applier):
        """测试生成负距离轨迹"""
        tracks = applier._generate_human_track(-100)
        assert isinstance(tracks, list)


# 性能测试
class TestBossApplierPerformance:
    """Boss直聘投递器性能测试"""

    @pytest.fixture
    def applier(self):
        config = {
            'platform': 'boss',
            'company_blacklist': ['外包'] * 100,  # 大量黑名单
            'title_blacklist': ['实习'] * 100
        }
        return BossApplier(config)

    def test_filter_large_job_list(self, applier):
        """测试过滤大量职位"""
        import time

        # 生成 1000 个职位
        jobs = [
            {
                'title': f'Python开发{i}',
                'company': f'公司{i}',
                'salary': '20K'
            }
            for i in range(1000)
        ]

        start = time.time()
        filtered = applier._filter_blacklist(jobs)
        elapsed = time.time() - start

        # 过滤 1000 个职位应该在 1 秒内完成
        assert elapsed < 1.0
        assert len(filtered) == 1000

    def test_generate_track_performance(self, applier):
        """测试轨迹生成性能"""
        import time

        start = time.time()
        for _ in range(100):
            applier._generate_human_track(260)
        elapsed = time.time() - start

        # 生成 100 次轨迹应该在 0.1 秒内完成
        assert elapsed < 0.1


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
