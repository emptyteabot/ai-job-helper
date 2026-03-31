import React, { useState } from 'react';
import { Alert, Button, Card, Progress, Space, Tabs, message } from 'antd';
import { CheckCircleOutlined, RobotOutlined } from '@ant-design/icons';
import { authFetch } from '../utils/network';

interface AnalysisResults {
  career_analysis?: string;
  job_recommendations?: string;
  interview_preparation?: string;
  skill_gap_analysis?: string;
  quality_audit?: string;
}

const renderBlock = (text: string) => (
  <div style={{ padding: 16, background: '#f8fafc', borderRadius: 8, whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>
    {text}
  </div>
);

const ResumeAnalysis: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [currentStage, setCurrentStage] = useState('等待开始');
  const [progress, setProgress] = useState(0);

  const startAnalysis = async () => {
    setLoading(true);
    setResults(null);
    setProgress(0);
    setCurrentStage('读取简历中...');

    const stages = ['读取简历中...', '职业定位分析中...', '岗位匹配分析中...', '面试准备生成中...', '质量审核中...'];
    let stageIndex = 0;
    const ticker = setInterval(() => {
      stageIndex = Math.min(stageIndex + 1, stages.length - 1);
      setCurrentStage(stages[stageIndex]);
      setProgress((prev) => Math.min(prev + 15, 92));
    }, 900);

    try {
      const listResp = await authFetch('/api/resume/list');
      const listData = await listResp.json();
      if (!listResp.ok || !listData.success) {
        throw new Error(listData.detail || listData.message || '获取简历列表失败');
      }

      if (!listData.resumes?.length) {
        throw new Error('请先上传一份简历再分析');
      }

      const firstResume = listData.resumes[0];
      const textResp = await authFetch(`/api/resume/text/${encodeURIComponent(firstResume.filename)}`);
      const textData = await textResp.json();
      if (!textResp.ok || !textData.success) {
        throw new Error(textData.detail || textData.message || '读取简历内容失败');
      }

      setCurrentStage('多 Agent 协同分析中...');
      const analysisResp = await authFetch('/api/analysis/resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume_text: textData.text,
          analysis_type: 'full',
        }),
      });
      const analysisData = await analysisResp.json();
      if (!analysisResp.ok || !analysisData.success) {
        throw new Error(analysisData.detail || analysisData.message || '分析失败');
      }

      setResults(analysisData.results || {});
      setProgress(100);
      setCurrentStage('分析完成');
      message.success('简历分析完成');
    } catch (error: any) {
      message.error(error?.message || '分析失败');
    } finally {
      clearInterval(ticker);
      setLoading(false);
    }
  };

  const tabItems = [
    { key: 'career', label: (<span><CheckCircleOutlined /> 职业分析</span>), content: results?.career_analysis },
    { key: 'jobs', label: (<span><CheckCircleOutlined /> 岗位推荐</span>), content: results?.job_recommendations },
    { key: 'interview', label: (<span><CheckCircleOutlined /> 面试准备</span>), content: results?.interview_preparation },
    {
      key: 'quality',
      label: (<span><CheckCircleOutlined /> 质量审核</span>),
      content: results?.quality_audit || results?.skill_gap_analysis,
    },
  ].filter((item) => Boolean(item.content));

  return (
    <div>
      <h1>简历分析 - 多 Agent 协同</h1>

      <Alert
        message="4 角色 Agent 分析"
        description="包含职业分析、岗位匹配、面试准备、质量审核四步，输出可直接用于求职执行。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Button type="primary" size="large" icon={<RobotOutlined />} onClick={startAnalysis} loading={loading} block>
            {loading ? '分析中...' : '开始 AI 分析'}
          </Button>

          {(loading || progress > 0) && (
            <>
              <Progress percent={progress} status={loading ? 'active' : 'normal'} />
              <div style={{ textAlign: 'center', color: '#64748b' }}>{currentStage}</div>
            </>
          )}
        </Space>
      </Card>

      {results && tabItems.length > 0 && (
        <Card title="分析结果">
          <Tabs
            items={tabItems.map((item) => ({
              key: item.key,
              label: item.label,
              children: renderBlock(item.content || ''),
            }))}
          />
        </Card>
      )}
    </div>
  );
};

export default ResumeAnalysis;
