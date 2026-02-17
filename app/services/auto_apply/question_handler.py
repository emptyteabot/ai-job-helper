"""
智能问题回答处理器
使用 AI 自动回答申请表单中的附加问题
"""

from typing import Dict, Any, Optional, List
import logging
import re

logger = logging.getLogger(__name__)


class QuestionHandler:
    """智能问题处理器"""

    def __init__(self, llm_client=None, user_profile: Dict[str, Any] = None):
        """
        初始化问题处理器

        Args:
            llm_client: LLM 客户端（用于 AI 回答）
            user_profile: 用户资料（用于预设答案）
        """
        self.llm_client = llm_client
        self.user_profile = user_profile or {}

        # 预设答案库
        self.preset_answers = self._load_preset_answers()

    def _load_preset_answers(self) -> Dict[str, Any]:
        """加载预设答案"""
        return {
            # 工作授权相关
            'work_authorization': {
                'patterns': [
                    r'work authorization',
                    r'legally authorized',
                    r'visa sponsorship',
                    r'工作许可',
                    r'工作签证'
                ],
                'answer': self.user_profile.get('work_authorization', 'Yes')
            },

            # 薪资期望
            'salary_expectation': {
                'patterns': [
                    r'salary expectation',
                    r'expected salary',
                    r'compensation',
                    r'期望薪资',
                    r'薪资要求'
                ],
                'answer': self.user_profile.get('salary_expectation', '')
            },

            # 工作经验年限
            'years_of_experience': {
                'patterns': [
                    r'years of experience',
                    r'how many years',
                    r'工作年限',
                    r'工作经验'
                ],
                'answer': self.user_profile.get('years_of_experience', '')
            },

            # 可入职时间
            'availability': {
                'patterns': [
                    r'when can you start',
                    r'availability',
                    r'notice period',
                    r'入职时间',
                    r'到岗时间'
                ],
                'answer': self.user_profile.get('availability', 'Immediately')
            },

            # 是否愿意搬迁
            'willing_to_relocate': {
                'patterns': [
                    r'willing to relocate',
                    r'relocation',
                    r'是否愿意搬迁',
                    r'是否接受调动'
                ],
                'answer': self.user_profile.get('willing_to_relocate', 'Yes')
            },

            # 学历
            'education_level': {
                'patterns': [
                    r'education level',
                    r'degree',
                    r'学历',
                    r'最高学历'
                ],
                'answer': self.user_profile.get('education_level', "Bachelor's Degree")
            },

            # 语言能力
            'language_proficiency': {
                'patterns': [
                    r'language proficiency',
                    r'english level',
                    r'语言能力',
                    r'英语水平'
                ],
                'answer': self.user_profile.get('language_proficiency', 'Fluent')
            }
        }

    def answer_question(self, question: str, question_type: str = "text",
                       options: List[str] = None, job_context: Dict[str, Any] = None) -> Optional[str]:
        """
        回答单个问题

        Args:
            question: 问题文本
            question_type: 问题类型 (text, radio, checkbox, dropdown)
            options: 选项列表（如果是选择题）
            job_context: 职位上下文信息

        Returns:
            str: 答案文本，如果无法回答则返回 None
        """
        try:
            # 1. 尝试从预设答案匹配
            preset_answer = self._match_preset_answer(question)
            if preset_answer:
                logger.info(f"使用预设答案: {question[:50]}... -> {preset_answer}")
                return preset_answer

            # 2. 如果有选项，尝试智能选择
            if options and question_type in ['radio', 'dropdown']:
                selected = self._select_from_options(question, options, job_context)
                if selected:
                    logger.info(f"从选项中选择: {question[:50]}... -> {selected}")
                    return selected

            # 3. 使用 AI 生成答案
            if self.llm_client:
                ai_answer = self._generate_ai_answer(question, question_type, options, job_context)
                if ai_answer:
                    logger.info(f"AI 生成答案: {question[:50]}... -> {ai_answer[:50]}...")
                    return ai_answer

            # 4. 无法回答
            logger.warning(f"无法回答问题: {question[:50]}...")
            return None

        except Exception as e:
            logger.error(f"回答问题时出错: {e}")
            return None

    def _match_preset_answer(self, question: str) -> Optional[str]:
        """从预设答案中匹配"""
        question_lower = question.lower()

        for category, data in self.preset_answers.items():
            for pattern in data['patterns']:
                if re.search(pattern, question_lower):
                    return data['answer']

        return None

    def _select_from_options(self, question: str, options: List[str],
                            job_context: Dict[str, Any] = None) -> Optional[str]:
        """从选项中智能选择"""
        question_lower = question.lower()

        # 简单的关键词匹配逻辑
        # 可以根据需要扩展更复杂的选择逻辑

        # 示例：如果问题包含 "yes/no"，优先选择 "Yes"
        if any(opt.lower() in ['yes', 'no'] for opt in options):
            if 'willing' in question_lower or 'able' in question_lower:
                return 'Yes' if 'Yes' in options else options[0]

        # 默认选择第一个选项
        return options[0] if options else None

    def _generate_ai_answer(self, question: str, question_type: str,
                           options: List[str] = None, job_context: Dict[str, Any] = None) -> Optional[str]:
        """使用 AI 生成答案"""
        if not self.llm_client:
            return None

        try:
            # 构建提示词
            prompt = self._build_ai_prompt(question, question_type, options, job_context)

            # 调用 LLM
            response = self.llm_client.generate(prompt, max_tokens=200)

            # 提取答案
            answer = response.strip()

            # 验证答案
            if question_type in ['radio', 'dropdown'] and options:
                # 如果是选择题，确保答案在选项中
                if answer not in options:
                    # 尝试模糊匹配
                    for opt in options:
                        if answer.lower() in opt.lower() or opt.lower() in answer.lower():
                            return opt
                    return options[0]  # 默认第一个

            return answer

        except Exception as e:
            logger.error(f"AI 生成答案失败: {e}")
            return None

    def _build_ai_prompt(self, question: str, question_type: str,
                        options: List[str] = None, job_context: Dict[str, Any] = None) -> str:
        """构建 AI 提示词"""
        prompt = f"""你是一个求职助手，需要帮助用户回答职位申请表单中的问题。

用户资料：
{self._format_user_profile()}

职位信息：
{self._format_job_context(job_context)}

问题类型：{question_type}
问题：{question}
"""

        if options:
            prompt += f"\n可选项：{', '.join(options)}"

        prompt += """

请根据用户资料和职位信息，给出最合适的答案。
要求：
1. 答案要简洁、专业
2. 如果是选择题，必须从可选项中选择一个
3. 如果是文本题，答案不超过100字
4. 只返回答案内容，不要解释

答案："""

        return prompt

    def _format_user_profile(self) -> str:
        """格式化用户资料"""
        if not self.user_profile:
            return "（未提供）"

        lines = []
        for key, value in self.user_profile.items():
            if value:
                lines.append(f"- {key}: {value}")

        return "\n".join(lines) if lines else "（未提供）"

    def _format_job_context(self, job_context: Dict[str, Any] = None) -> str:
        """格式化职位上下文"""
        if not job_context:
            return "（未提供）"

        lines = []
        for key in ['title', 'company', 'location', 'description']:
            if key in job_context and job_context[key]:
                lines.append(f"- {key}: {job_context[key][:100]}...")

        return "\n".join(lines) if lines else "（未提供）"

    def batch_answer(self, questions: List[Dict[str, Any]],
                    job_context: Dict[str, Any] = None) -> Dict[str, str]:
        """
        批量回答问题

        Args:
            questions: 问题列表，每个问题是一个字典包含 question, type, options
            job_context: 职位上下文

        Returns:
            Dict: 问题ID到答案的映射
        """
        answers = {}

        for q in questions:
            question_id = q.get('id', q.get('question'))
            answer = self.answer_question(
                question=q.get('question', ''),
                question_type=q.get('type', 'text'),
                options=q.get('options'),
                job_context=job_context
            )

            if answer:
                answers[question_id] = answer

        return answers
