import React from 'react';
import { Button, Card, Input, Progress, Space, Switch, Tag, message } from 'antd';
import { getAuthToken, wsUrl } from '../lib/api';
import { assistedGuidance, AssistedStatus } from './assistedGuidance';
import CinematicLegacyShell from '../components/CinematicLegacyShell';

const { TextArea } = Input;

const autoStatusCards = (selectedJobs: Array<Record<string, any>>, isRunning: boolean, progress: number, useAI: boolean) => [
  { label: '待提交岗位', value: `${selectedJobs.length} 个` },
  { label: 'AI 附言', value: useAI ? '已启用' : '关闭' },
  { label: '执行进度', value: `${Math.round(progress)}%` },
  { label: '批量状态', value: isRunning ? '运行中' : '空闲' },
];

const AutoApply: React.FC = () => {
  const [progress, setProgress] = React.useState(0);
  const [logs, setLogs] = React.useState<string[]>([]);
  const [isRunning, setIsRunning] = React.useState(false);
  const [resumeText, setResumeText] = React.useState('');
  const [useAI, setUseAI] = React.useState(true);
  const [selectedJobs, setSelectedJobs] = React.useState<Array<Record<string, any>>>([]);
  const [assistedStatus, setAssistedStatus] = React.useState<AssistedStatus>('standby');

  React.useEffect(() => {
    const jobs = localStorage.getItem('selectedJobs');
    if (jobs) {
      setSelectedJobs(JSON.parse(jobs));
    }
  }, []);

  const handleAssistedAction = () => {
    const guidance = assistedGuidance[assistedStatus];
    if (guidance.actionUrl) {
      window.open(guidance.actionUrl, '_blank', 'noopener');
    }
    if (assistedStatus === 'waiting_human') setAssistedStatus('resumed');
    if (assistedStatus === 'failed') setAssistedStatus('challenge_required');
  };

  const startApply = async () => {
    if (selectedJobs.length === 0) {
      message.warning('请先在搜索页选定岗位');
      return;
    }
    const token = getAuthToken();
    if (!token) {
      message.warning('请先登录工作台账号');
      return;
    }
    if (!resumeText.trim()) {
      message.warning('请完善简历文本');
      return;
    }

    setIsRunning(true);
    setProgress(0);
    setLogs([]);

    try {
      const ws = new WebSocket(wsUrl('/api/apply/ws/apply'));
      ws.onopen = () => {
        ws.send(JSON.stringify({ token, selected_jobs: selectedJobs, resume_text: resumeText, use_ai_cover_letter: useAI }));
        setLogs((prev) => [...prev, '正在发起批量投递...']);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.assisted_status) setAssistedStatus(data.assisted_status as AssistedStatus);
        if (data.error) {
          message.error(data.message);
          setLogs((prev) => [...prev, `失败 · ${data.message}`]);
          setIsRunning(false);
          return;
        }
        if (data.completed) {
          message.success(data.message);
          setLogs((prev) => [...prev, `完成 · ${data.message}`]);
          setIsRunning(false);
          localStorage.removeItem('selectedJobs');
          setAssistedStatus('resumed');
          return;
        }
        if (data.progress !== undefined) {
          setProgress(data.progress * 100);
          const status = data.success ? '成功' : '需复核';
          setLogs((prev) => [...prev, `[${data.current}/${data.total}] ${data.company} · ${data.job} · ${status}`]);
        }
      };

      ws.onerror = () => {
        message.error('连接异常，请稍后再试');
        setLogs((prev) => [...prev, '连接失败']);
        setIsRunning(false);
      };

      ws.onclose = () => setIsRunning(false);
    } catch (error) {
      message.error('调度失败，请稍后再试');
      setIsRunning(false);
    }
  };

  const assistance = assistedGuidance[assistedStatus];
  const statusCards = autoStatusCards(selectedJobs, isRunning, progress, useAI);

  return (
    <CinematicLegacyShell
      sectionId="autoapply"
      title="AutoApply"
      highlight="批量执行舱"
      subtitle="这里负责把已选岗位和简历文本推进成真实投递动作。不要再手工复制粘贴，这个页面就该接管批量执行。"
      terminalLabel="AutoApply::Terminal"
      terminalPrompt={isRunning ? '正在调度批量投递执行流...' : '等待批量投递任务输入...'}
      primaryCta={isRunning ? '执行中...' : '启动批量投递'}
      onPrimaryClick={startApply}
      terminalLines={logs.slice(-5).map((log, index) => ({ time: `10:3${index}:0${index}`, level: 'EXEC', text: log }))}
    >
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        <div className="md:col-span-8 space-y-6">
          <Card className="glass-panel" styles={{ body: { padding: 24 } }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <strong className="text-cyan-100">已选岗位：{selectedJobs.length} 个</strong>
              <TextArea rows={6} placeholder="粘贴履历片段，批量执行时会复用" value={resumeText} onChange={(e) => setResumeText(e.target.value)} disabled={isRunning} />
              <div>
                <Space>
                  <span className="text-cyan-100">自动附言</span>
                  <Switch checked={useAI} onChange={setUseAI} disabled={isRunning} />
                </Space>
              </div>
              <Progress percent={Math.round(progress)} status={isRunning ? 'active' : 'normal'} />
              <Button type="primary" onClick={startApply} disabled={isRunning || selectedJobs.length === 0} block size="large">
                {isRunning ? '执行中...' : `启动批量（${selectedJobs.length}）`}
              </Button>
            </Space>
          </Card>
        </div>

        <div className="md:col-span-4 space-y-6">
          <Card className="glass-panel" styles={{ body: { padding: 24 } }}>
            <div className="space-y-3">
              {statusCards.map((card) => (
                <div className="rounded-xl bg-black/30 p-4" key={card.label}>
                  <div className="text-xs uppercase tracking-widest text-cyan-100/60">{card.label}</div>
                  <div className="text-xl font-bold text-cyan-100 mt-1">{card.value}</div>
                </div>
              ))}
            </div>
          </Card>
          <Card className="glass-panel" styles={{ body: { padding: 24 } }}>
            <div className="text-cyan-300 font-bold mb-2">{assistance.label}</div>
            <p className="text-cyan-100/70 mb-3">{assistance.description}</p>
            {assistance.actionLabel ? <Button type="link" onClick={handleAssistedAction}>{assistance.actionLabel}</Button> : null}
          </Card>
          <Card className="glass-panel" title="运行日志" styles={{ body: { padding: 24 }, header: { color: '#67e8f9' } }}>
            <div className="space-y-3">
              {(logs.length ? logs : ['等待批量任务启动']).map((log, index) => (
                <Tag color="cyan" key={`${log}-${index}`}>{log}</Tag>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </CinematicLegacyShell>
  );
};

export default AutoApply;

