import React, { useState } from 'react';
import { Alert, Button, Progress, Space, Tabs } from 'antd';
import { CheckCircleOutlined, RobotOutlined } from '@ant-design/icons';
import CinematicLegacyShell from '../components/CinematicLegacyShell';
import { apiUrl, authHeaders } from '../lib/api';

const { TabPane } = Tabs;

const AnalysisBlock: React.FC<{ text: string }> = ({ text }) => (
  <div className="whitespace-pre-wrap text-cyan-100/80 leading-relaxed">{text}</div>
);

interface AnalysisResults {
  career_analysis?: string;
  job_recommendations?: string;
  interview_preparation?: string;
  skill_gap_analysis?: string;
}

const ResumeAnalysis: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [currentStage, setCurrentStage] = useState('');
  const [progress, setProgress] = useState(0);

  const startAnalysis = async () => {
    const resumeResponse = await fetch(apiUrl('/api/resume/list'), { headers: authHeaders() });
    const resumeResult = await resumeResponse.json();
    if (!resumeResult.resumes || resumeResult.resumes.length === 0) {
      alert('请先上传简历');
      return;
    }

    const firstResume = resumeResult.resumes[0];
    const textResponse = await fetch(apiUrl(`/api/resume/text/${firstResume.filename}`), { headers: authHeaders() });
    const textResult = await textResponse.json();

    setLoading(true);
    setResults(null);
    setProgress(0);

    try {
      const stages = [
        { name: '职业分析师正在深度思考...', progress: 25 },
        { name: '岗位推荐专家正在匹配...', progress: 50 },
        { name: '面试辅导专家正在准备...', progress: 75 },
        { name: '质量审核官正在检查...', progress: 90 },
      ];

      let currentProgress = 0;
      const progressInterval = setInterval(() => {
        if (currentProgress < stages.length) {
          setCurrentStage(stages[currentProgress].name);
          setProgress(stages[currentProgress].progress);
          currentProgress += 1;
        }
      }, 5000);

      const analysisResponse = await fetch(apiUrl('/api/analysis/resume'), {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          resume_text: textResult.text,
          analysis_type: 'full',
        }),
      });
      const result = await analysisResponse.json();

      clearInterval(progressInterval);
      setProgress(100);
      setResults(result.results);
    } catch (error) {
      console.error('分析失败', error);
      alert('分析失败: ' + error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <CinematicLegacyShell
      sectionId="analysis"
      title="简历分析"
      highlight="四 Agent 深度分析"
      subtitle="这个页面负责把一份简历拆成职业分析、岗位推荐、面试辅导和技能差距，不是只给一段泛泛而谈的总结。"
      terminalLabel="Analysis::Terminal"
      terminalPrompt={loading ? currentStage || '正在调度分析 Agent...' : '等待启动新一轮简历分析...'}
      primaryCta="启动 AI 分析"
      onPrimaryClick={startAnalysis}
      terminalLines={[
        { time: '10:51:01', level: 'LOAD', text: 'Preparing resume analysis chain...' },
        { time: '10:51:05', level: 'RUN', text: currentStage || 'Analysis not started yet.' },
        { time: '10:51:09', level: 'READY', text: results ? 'Results available for review.' : 'Waiting for operator trigger.' },
      ]}
    >
      <div className="space-y-6">
        <Alert
          message="AI 简历分析"
          description="使用 4 个专职 AI Agent 深度分析你的简历：职业分析师、岗位推荐专家、面试辅导专家、质量审核官。"
          type="info"
          showIcon
          style={{ background: 'rgba(34,211,238,0.08)', borderColor: 'rgba(34,211,238,0.25)', color: '#e0f2fe' }}
        />

        <div className="glass-panel rounded-2xl p-8">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Button type="primary" size="large" icon={<RobotOutlined />} onClick={startAnalysis} loading={loading} block>
              {loading ? '分析中...' : '开始 AI 分析'}
            </Button>
            {loading ? (
              <>
                <Progress percent={progress} status="active" />
                <div className="text-center text-cyan-100/70">{currentStage}</div>
              </>
            ) : null}
          </Space>
        </div>

        {results ? (
          <div className="glass-panel rounded-2xl p-8">
            <Tabs defaultActiveKey="1">
              {results.career_analysis ? <TabPane tab={<span><CheckCircleOutlined /> 职业分析</span>} key="1"><AnalysisBlock text={results.career_analysis} /></TabPane> : null}
              {results.job_recommendations ? <TabPane tab={<span><CheckCircleOutlined /> 岗位推荐</span>} key="2"><AnalysisBlock text={results.job_recommendations} /></TabPane> : null}
              {results.interview_preparation ? <TabPane tab={<span><CheckCircleOutlined /> 面试辅导</span>} key="3"><AnalysisBlock text={results.interview_preparation} /></TabPane> : null}
              {results.skill_gap_analysis ? <TabPane tab={<span><CheckCircleOutlined /> 质量审核</span>} key="4"><AnalysisBlock text={results.skill_gap_analysis} /></TabPane> : null}
            </Tabs>
          </div>
        ) : null}
      </div>
    </CinematicLegacyShell>
  );
};

export default ResumeAnalysis;

