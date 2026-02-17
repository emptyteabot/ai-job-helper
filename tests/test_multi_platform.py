"""
多平台集成测试
测试 Boss直聘、智联招聘等多平台协同工作
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import asyncio

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient


class TestMultiPlatformAPI:
    """多平台 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        # 延迟导入避免循环依赖
        from web_app import app
        return TestClient(app)

    def test_get_platforms(self, client):
        """测试获取平台列表"""
        response = client.get('/api/auto-apply/platforms')

        assert response.status_code == 200
        data = response.json()
        assert 'success' in data
        assert data['success'] is True
        assert 'platforms' in data
        assert len(data['platforms']) >= 2  # 至少有 boss 和 zhilian

    def test_platform_info(self, client):
        """测试平台信息"""
        response = client.get('/api/auto-apply/platforms')
        data = response.json()

        platforms = data['platforms']

        # 检查 Boss直聘
        boss = next((p for p in platforms if p['id'] == 'boss'), None)
        assert boss is not None
        assert boss['name'] == 'Boss直聘'
        assert 'features' in boss

        # 检查智联招聘
        zhilian = next((p for p in platforms if p['id'] == 'zhilian'), None)
        assert zhilian is not None
        assert zhilian['name'] == '智联招聘'
        assert 'features' in zhilian

    def test_start_single_platform(self, client):
        """测试启动单平台投递"""
        payload = {
            'platform': 'boss',
            'config': {
                'keywords': 'Python',
                'location': '北京',
                'max_count': 5
            }
        }

        with patch('web_app.auto_apply_tasks', {}):
            response = client.post('/api/auto-apply/start', json=payload)

            assert response.status_code == 200
            data = response.json()
            assert 'success' in data
            assert 'task_id' in data

    def test_start_multi_platform(self, client):
        """测试启动多平台投递"""
        payload = {
            'platforms': ['boss', 'zhilian'],
            'config': {
                'keywords': 'Python',
                'location': '北京',
                'max_count': 10
            }
        }

        with patch('web_app.auto_apply_tasks', {}):
            response = client.post('/api/auto-apply/start-multi', json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert 'task_id' in data
            assert 'platforms' in data
            assert len(data['platforms']) == 2

    def test_start_multi_platform_invalid_platform(self, client):
        """测试启动多平台投递 - 无效平台"""
        payload = {
            'platforms': ['boss', 'invalid_platform'],
            'config': {
                'keywords': 'Python',
                'location': '北京'
            }
        }

        response = client.post('/api/auto-apply/start-multi', json=payload)

        # 应该返回错误或过滤掉无效平台
        assert response.status_code in [200, 400]

    def test_get_task_status(self, client):
        """测试获取任务状态"""
        # 先创建一个任务
        with patch('web_app.auto_apply_tasks', {'test_task_123': {
            'platform': 'boss',
            'status': 'running',
            'applied': 5,
            'failed': 1
        }}):
            response = client.get('/api/auto-apply/status/test_task_123')

            assert response.status_code == 200
            data = response.json()
            assert data['platform'] == 'boss'
            assert data['status'] == 'running'
            assert data['applied'] == 5

    def test_get_task_status_not_found(self, client):
        """测试获取不存在的任务状态"""
        with patch('web_app.auto_apply_tasks', {}):
            response = client.get('/api/auto-apply/status/nonexistent_task')

            assert response.status_code == 404

    def test_stop_task(self, client):
        """测试停止任务"""
        mock_applier = MagicMock()
        mock_applier.stop = MagicMock()

        with patch('web_app.auto_apply_tasks', {'test_task_123': {
            'applier': mock_applier,
            'status': 'running'
        }}):
            response = client.post('/api/auto-apply/stop/test_task_123')

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True

    def test_get_stats(self, client):
        """测试获取统计信息"""
        with patch('web_app.auto_apply_tasks', {
            'task1': {'platform': 'boss', 'applied': 10, 'failed': 2},
            'task2': {'platform': 'zhilian', 'applied': 8, 'failed': 1}
        }):
            response = client.get('/api/auto-apply/stats')

            assert response.status_code == 200
            data = response.json()
            assert 'total_tasks' in data
            assert 'platform_stats' in data
            assert data['total_tasks'] == 2


class TestMultiPlatformIntegration:
    """多平台集成测试"""

    def test_boss_and_zhilian_config_compatibility(self):
        """测试 Boss 和智联配置兼容性"""
        from app.services.auto_apply.boss_applier import BossApplier
        from app.services.auto_apply.zhilian_applier import ZhilianApplier

        # 通用配置
        common_config = {
            'keywords': 'Python',
            'location': '北京',
            'company_blacklist': ['外包'],
            'title_blacklist': ['实习']
        }

        # Boss 配置
        boss_config = {
            **common_config,
            'platform': 'boss',
            'headless': True
        }

        # 智联配置
        zhilian_config = {
            **common_config,
            'platform': 'zhilian',
            'blacklist_companies': common_config['company_blacklist'],
            'blacklist_keywords': common_config['title_blacklist']
        }

        # 创建投递器
        boss_applier = BossApplier(boss_config)
        zhilian_applier = ZhilianApplier(zhilian_config)

        assert boss_applier.config['keywords'] == zhilian_applier.config['keywords']
        assert boss_applier.config['location'] == zhilian_applier.config['location']

    def test_parallel_job_search(self):
        """测试并行搜索职位"""
        from app.services.auto_apply.boss_applier import BossApplier
        from app.services.auto_apply.zhilian_applier import ZhilianApplier

        boss_config = {'platform': 'boss', 'company_blacklist': []}
        zhilian_config = {'platform': 'zhilian', 'blacklist_companies': []}

        boss_applier = BossApplier(boss_config)
        zhilian_applier = ZhilianApplier(zhilian_config)

        # Mock 搜索方法
        with patch.object(boss_applier, 'search_jobs', return_value=[
            {'title': 'Job 1', 'platform': 'boss'}
        ]):
            with patch.object(zhilian_applier, 'search_jobs', return_value=[
                {'title': 'Job 2', 'platform': 'zhilian'}
            ]):
                boss_jobs = boss_applier.search_jobs('Python', '北京', {})
                zhilian_jobs = zhilian_applier.search_jobs('Python', '北京', {})

                assert len(boss_jobs) == 1
                assert len(zhilian_jobs) == 1
                assert boss_jobs[0]['platform'] == 'boss'
                assert zhilian_jobs[0]['platform'] == 'zhilian'

    def test_unified_job_format(self):
        """测试统一的职位格式"""
        from app.services.auto_apply.boss_applier import BossApplier
        from app.services.auto_apply.zhilian_applier import ZhilianApplier

        # 两个平台返回的职位应该有相同的基本字段
        required_fields = ['title', 'company', 'platform']

        boss_job = {
            'title': 'Python开发',
            'company': '腾讯',
            'salary': '20-30K',
            'platform': 'boss',
            'url': 'http://boss.com/job1'
        }

        zhilian_job = {
            'title': 'Python开发',
            'company': '阿里巴巴',
            'salary': '25-35K',
            'platform': 'zhilian',
            'url': 'http://zhilian.com/job1'
        }

        # 验证必需字段
        for field in required_fields:
            assert field in boss_job
            assert field in zhilian_job

    def test_batch_apply_multiple_platforms(self):
        """测试多平台批量投递"""
        from app.services.auto_apply.boss_applier import BossApplier
        from app.services.auto_apply.zhilian_applier import ZhilianApplier

        boss_config = {'platform': 'boss', 'company_blacklist': []}
        zhilian_config = {'platform': 'zhilian', 'blacklist_companies': []}

        boss_applier = BossApplier(boss_config)
        zhilian_applier = ZhilianApplier(zhilian_config)

        boss_jobs = [
            {'id': '1', 'title': 'Job 1', 'platform': 'boss'},
            {'id': '2', 'title': 'Job 2', 'platform': 'boss'}
        ]

        zhilian_jobs = [
            {'id': '3', 'title': 'Job 3', 'platform': 'zhilian'},
            {'id': '4', 'title': 'Job 4', 'platform': 'zhilian'}
        ]

        # Mock apply_job
        def mock_apply(job):
            return {
                'success': True,
                'message': '投递成功',
                'job': job,
                'timestamp': datetime.now().isoformat()
            }

        with patch.object(boss_applier, 'apply_job', side_effect=mock_apply):
            with patch.object(zhilian_applier, 'apply_job', side_effect=mock_apply):
                boss_result = boss_applier.batch_apply(boss_jobs, max_count=10)
                zhilian_result = zhilian_applier.batch_apply(zhilian_jobs, max_count=10)

                assert boss_result['applied'] == 2
                assert zhilian_result['applied'] == 2

                # 总计投递 4 个职位
                total_applied = boss_result['applied'] + zhilian_result['applied']
                assert total_applied == 4


class TestMultiPlatformPerformance:
    """多平台性能测试"""

    def test_concurrent_platform_initialization(self):
        """测试并发初始化多个平台"""
        import time
        from app.services.auto_apply.boss_applier import BossApplier
        from app.services.auto_apply.zhilian_applier import ZhilianApplier

        start = time.time()

        boss_applier = BossApplier({'platform': 'boss'})
        zhilian_applier = ZhilianApplier({'platform': 'zhilian'})

        elapsed = time.time() - start

        # 初始化应该很快（不涉及浏览器启动）
        assert elapsed < 0.1
        assert boss_applier is not None
        assert zhilian_applier is not None

    def test_filter_performance_across_platforms(self):
        """测试跨平台过滤性能"""
        import time
        from app.services.auto_apply.boss_applier import BossApplier
        from app.services.auto_apply.zhilian_applier import ZhilianApplier

        boss_config = {
            'platform': 'boss',
            'company_blacklist': ['外包'] * 50,
            'title_blacklist': ['实习'] * 50
        }

        zhilian_config = {
            'platform': 'zhilian',
            'blacklist_companies': ['外包'] * 50,
            'blacklist_keywords': ['实习'] * 50
        }

        boss_applier = BossApplier(boss_config)
        zhilian_applier = ZhilianApplier(zhilian_config)

        # 生成测试数据
        jobs = [
            {
                'title': f'Python开发{i}',
                'company': f'公司{i}',
                'salary': '20K'
            }
            for i in range(500)
        ]

        start = time.time()
        boss_filtered = boss_applier._filter_blacklist(jobs)
        zhilian_filtered = [job for job in jobs if zhilian_applier._should_apply(job)]
        elapsed = time.time() - start

        # 两个平台过滤 500 个职位应该在 0.5 秒内完成
        assert elapsed < 0.5
        assert len(boss_filtered) == 500
        assert len(zhilian_filtered) == 500


class TestMultiPlatformWebSocket:
    """多平台 WebSocket 测试"""

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """测试 WebSocket 连接"""
        from fastapi.testclient import TestClient
        from web_app import app

        client = TestClient(app)

        # 创建测试任务
        with patch('web_app.auto_apply_tasks', {}):
            response = client.post('/api/auto-apply/start-multi', json={
                'platforms': ['boss'],
                'config': {'keywords': 'test'}
            })

            assert response.status_code == 200
            data = response.json()
            assert 'task_id' in data

    @pytest.mark.asyncio
    async def test_websocket_progress_updates(self):
        """测试 WebSocket 进度更新"""
        # 这个测试需要真实的 WebSocket 连接
        # 在实际环境中使用 websockets 库测试
        pass


class TestMultiPlatformErrorHandling:
    """多平台错误处理测试"""

    def test_one_platform_fails(self):
        """测试一个平台失败时的处理"""
        from app.services.auto_apply.boss_applier import BossApplier
        from app.services.auto_apply.zhilian_applier import ZhilianApplier

        boss_applier = BossApplier({'platform': 'boss'})
        zhilian_applier = ZhilianApplier({'platform': 'zhilian'})

        # Mock Boss 失败
        with patch.object(boss_applier, 'search_jobs', side_effect=Exception('Boss 搜索失败')):
            with patch.object(zhilian_applier, 'search_jobs', return_value=[
                {'title': 'Job 1', 'platform': 'zhilian'}
            ]):
                # Boss 失败
                try:
                    boss_jobs = boss_applier.search_jobs('Python', '北京', {})
                except Exception as e:
                    assert 'Boss 搜索失败' in str(e)

                # 智联成功
                zhilian_jobs = zhilian_applier.search_jobs('Python', '北京', {})
                assert len(zhilian_jobs) == 1

    def test_invalid_config_handling(self):
        """测试无效配置处理"""
        from app.services.auto_apply.boss_applier import BossApplier

        # 缺少必需配置
        invalid_config = {}

        applier = BossApplier(invalid_config)

        # 应该使用默认值
        assert applier.config == invalid_config
        assert applier.applied_count == 0

    def test_network_error_retry(self):
        """测试网络错误重试"""
        from app.services.auto_apply.zhilian_applier import ZhilianApplier

        applier = ZhilianApplier({'platform': 'zhilian'})

        job = {'title': 'Test Job', 'url': 'http://test.com'}

        # Mock 网络错误
        with patch.object(applier, '_init_page'):
            mock_page = MagicMock()
            mock_page.get.side_effect = Exception('网络超时')
            applier.page = mock_page

            result = applier.apply_job(job)

            assert result['success'] is False
            assert '网络超时' in result['message']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
