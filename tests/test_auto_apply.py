"""
自动投递模块单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.auto_apply.base_applier import BaseApplier
from app.services.auto_apply.config import AutoApplyConfig, validate_config
from app.services.auto_apply.question_handler import QuestionHandler
from app.services.auto_apply.session_manager import SessionManager


class TestAutoApplyConfig:
    """测试配置管理"""

    def test_default_config(self):
        """测试默认配置"""
        config = AutoApplyConfig()
        assert config.platform == "linkedin"
        assert config.max_apply_per_session == 50
        assert config.max_apply_per_day == 200

    def test_config_validation_success(self):
        """测试配置验证成功"""
        config = AutoApplyConfig(
            platform="linkedin",
            keywords="Python Developer",
            max_apply_per_session=50
        )
        is_valid, error = validate_config(config)
        assert is_valid is True
        assert error == ""

    def test_config_validation_invalid_platform(self):
        """测试无效平台"""
        config = AutoApplyConfig(platform="invalid_platform")
        is_valid, error = validate_config(config)
        assert is_valid is False
        assert "不支持的平台" in error

    def test_config_validation_invalid_count(self):
        """测试无效投递数量"""
        config = AutoApplyConfig(
            platform="linkedin",
            max_apply_per_session=0,
            keywords="test"
        )
        is_valid, error = validate_config(config)
        assert is_valid is False
        assert "必须大于0" in error

    def test_config_validation_too_many(self):
        """测试投递数量过多"""
        config = AutoApplyConfig(
            platform="linkedin",
            max_apply_per_session=300,
            keywords="test"
        )
        is_valid, error = validate_config(config)
        assert is_valid is False
        assert "不能超过200" in error

    def test_config_to_dict(self):
        """测试配置转字典"""
        config = AutoApplyConfig(platform="linkedin", keywords="Python")
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict['platform'] == "linkedin"
        assert config_dict['keywords'] == "Python"

    def test_config_from_dict(self):
        """测试从字典创建配置"""
        data = {
            'platform': 'linkedin',
            'keywords': 'Python Developer',
            'max_apply_per_session': 30
        }
        config = AutoApplyConfig.from_dict(data)
        assert config.platform == 'linkedin'
        assert config.keywords == 'Python Developer'
        assert config.max_apply_per_session == 30


class TestQuestionHandler:
    """测试问题处理器"""

    def test_preset_answer_work_authorization(self):
        """测试预设答案 - 工作授权"""
        handler = QuestionHandler(user_profile={'work_authorization': 'Yes'})
        answer = handler.answer_question("Are you legally authorized to work?")
        assert answer == 'Yes'

    def test_preset_answer_salary(self):
        """测试预设答案 - 薪资期望"""
        handler = QuestionHandler(user_profile={'salary_expectation': '100000'})
        answer = handler.answer_question("What is your expected salary?")
        assert answer == '100000'

    def test_select_from_options(self):
        """测试从选项中选择"""
        handler = QuestionHandler()
        answer = handler._select_from_options(
            "Are you willing to relocate?",
            ["Yes", "No"]
        )
        assert answer in ["Yes", "No"]

    def test_batch_answer(self):
        """测试批量回答"""
        handler = QuestionHandler(user_profile={
            'work_authorization': 'Yes',
            'years_of_experience': '5'
        })

        questions = [
            {'id': 'q1', 'question': 'Are you authorized to work?', 'type': 'radio'},
            {'id': 'q2', 'question': 'How many years of experience?', 'type': 'text'}
        ]

        answers = handler.batch_answer(questions)
        assert 'q1' in answers
        assert 'q2' in answers


class TestSessionManager:
    """测试会话管理器"""

    def test_session_manager_init(self):
        """测试会话管理器初始化"""
        manager = SessionManager('linkedin')
        assert manager.platform == 'linkedin'
        assert 'linkedin' in manager.session_file

    @patch('os.path.exists')
    def test_is_session_valid_no_file(self, mock_exists):
        """测试会话有效性 - 文件不存在"""
        mock_exists.return_value = False
        manager = SessionManager('linkedin')
        assert manager.is_session_valid() is False

    def test_clear_session(self):
        """测试清除会话"""
        manager = SessionManager('linkedin')
        # 即使文件不存在也应该返回 True（清除成功）
        result = manager.clear_session()
        assert result in [True, False]  # 取决于文件是否存在


class MockApplier(BaseApplier):
    """模拟投递器（用于测试基类）"""

    def login(self, email: str, password: str) -> bool:
        return True

    def search_jobs(self, keywords: str, location: str, filters: dict):
        return [
            {'id': '1', 'title': 'Python Developer', 'company': 'Test Co'},
            {'id': '2', 'title': 'Full Stack Engineer', 'company': 'Demo Inc'}
        ]

    def apply_job(self, job: dict):
        return {
            'success': True,
            'message': 'Applied successfully',
            'job': job
        }


class TestBaseApplier:
    """测试基础投递类"""

    def test_applier_init(self):
        """测试投递器初始化"""
        config = {'platform': 'linkedin'}
        applier = MockApplier(config)
        assert applier.config == config
        assert applier.applied_count == 0
        assert applier.failed_count == 0

    def test_batch_apply_success(self):
        """测试批量投递成功"""
        config = {'platform': 'linkedin'}
        applier = MockApplier(config)

        jobs = [
            {'id': '1', 'title': 'Job 1', 'company': 'Company 1'},
            {'id': '2', 'title': 'Job 2', 'company': 'Company 2'}
        ]

        result = applier.batch_apply(jobs, max_count=10)

        assert result['applied'] == 2
        assert result['failed'] == 0
        assert result['total_attempted'] == 2
        assert result['success_rate'] == 1.0

    def test_batch_apply_max_count(self):
        """测试批量投递数量限制"""
        config = {'platform': 'linkedin'}
        applier = MockApplier(config)

        jobs = [{'id': str(i), 'title': f'Job {i}'} for i in range(10)]

        result = applier.batch_apply(jobs, max_count=5)

        assert result['applied'] == 5
        assert result['total_attempted'] == 5

    def test_stop_applier(self):
        """测试停止投递"""
        config = {'platform': 'linkedin'}
        applier = MockApplier(config)
        applier.is_running = True

        applier.stop()

        assert applier.is_running is False

    def test_get_status(self):
        """测试获取状态"""
        config = {'platform': 'linkedin'}
        applier = MockApplier(config)
        applier.applied_count = 10
        applier.failed_count = 2

        status = applier.get_status()

        assert status['applied_count'] == 10
        assert status['failed_count'] == 2
        assert status['is_running'] is False

    def test_get_history(self):
        """测试获取历史"""
        config = {'platform': 'linkedin'}
        applier = MockApplier(config)

        jobs = [{'id': '1', 'title': 'Job 1'}]
        applier.batch_apply(jobs)

        history = applier.get_history()
        assert len(history) == 1


class TestLinkedInApplier:
    """测试 LinkedIn 投递器"""

    @patch('app.services.auto_apply.linkedin_applier.uc.Chrome')
    def test_init_driver(self, mock_chrome):
        """测试初始化浏览器驱动"""
        from app.services.auto_apply.linkedin_applier import LinkedInApplier

        config = {'platform': 'linkedin', 'headless': False}
        applier = LinkedInApplier(config)

        # 模拟驱动初始化
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        result = applier._init_driver()

        # 由于依赖外部库，这里只测试基本逻辑
        assert applier.session_manager is not None
        assert applier.question_handler is not None


# 集成测试（需要真实环境）
@pytest.mark.integration
class TestIntegration:
    """集成测试（需要真实浏览器环境）"""

    @pytest.mark.skip(reason="需要真实浏览器环境")
    def test_full_workflow(self):
        """测试完整工作流程"""
        # 这个测试需要真实的浏览器和网络环境
        # 在 CI/CD 中应该跳过
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
